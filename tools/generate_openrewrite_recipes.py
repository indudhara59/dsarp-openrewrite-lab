#!/usr/bin/env python3
"""Compile a validated recipe plan into a deterministic OpenRewrite recipe."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml
from jsonschema import Draft202012Validator


MINIMUM_PYTHON = (3, 10)
DEFAULT_SCHEMA = Path(__file__).with_name("recipe_plan_schema.json")
PACKAGE_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)+$")
RECIPE_FQN_PATTERN = re.compile(
    r"^[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+$"
)
AUTOMATION_CLASSES = {
    "DECLARATIVE_BUILT_IN",
    "CUSTOM_IMPERATIVE_RECIPE",
    "MANUAL_REFACTORING",
    "REJECTED_UNSAFE",
}

# Parameter insertion order is also the canonical YAML option order.
SUPPORTED_RECIPES: dict[str, dict[str, type]] = {
    "org.openrewrite.java.ChangePackage": {
        "oldPackageName": str,
        "newPackageName": str,
        "recursive": bool,
    },
    "org.openrewrite.java.ChangeType": {
        "oldFullyQualifiedTypeName": str,
        "newFullyQualifiedTypeName": str,
        "ignoreDefinition": bool,
    },
    "org.openrewrite.java.dependencies.ChangeDependency": {
        "oldGroupId": str,
        "oldArtifactId": str,
        "newGroupId": str,
        "newArtifactId": str,
        "newVersion": str,
        "versionPattern": str,
        "overrideManagedVersion": bool,
    },
    "org.openrewrite.java.dependencies.AddDependency": {
        "groupId": str,
        "artifactId": str,
        "version": str,
        "versionPattern": str,
        "scope": str,
        "releasesOnly": bool,
        "onlyIfUsing": str,
        "type": str,
        "classifier": str,
        "optional": bool,
        "familyPattern": str,
        "acceptTransitive": bool,
    },
    "org.openrewrite.java.dependencies.RemoveDependency": {
        "groupId": str,
        "artifactId": str,
        "scope": str,
    },
}

REQUIRED_PARAMETERS: dict[str, frozenset[str]] = {
    "org.openrewrite.java.ChangePackage": frozenset(
        {"oldPackageName", "newPackageName"}
    ),
    "org.openrewrite.java.ChangeType": frozenset(
        {"oldFullyQualifiedTypeName", "newFullyQualifiedTypeName"}
    ),
    "org.openrewrite.java.dependencies.ChangeDependency": frozenset(
        {"oldGroupId", "oldArtifactId", "newGroupId", "newArtifactId"}
    ),
    "org.openrewrite.java.dependencies.AddDependency": frozenset(
        {"groupId", "artifactId"}
    ),
    "org.openrewrite.java.dependencies.RemoveDependency": frozenset(
        {"groupId", "artifactId"}
    ),
}


class FoldedString(str):
    """Marker used solely to request YAML's folded block style."""


def _represent_folded(dumper: yaml.SafeDumper, value: FoldedString) -> yaml.Node:
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(value), style=">")


yaml.SafeDumper.add_representer(FoldedString, _represent_folded)


class GenerationError(Exception):
    """Raised for a fatal, safely reportable generation failure."""


@dataclass(frozen=True)
class GenerationResult:
    yaml_bytes: bytes | None
    report: dict[str, Any]
    exit_code: int


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise GenerationError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(raw.decode("utf-8")), raw
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GenerationError(f"malformed JSON in {path}: {exc}") from exc


def _json_path(error: Any) -> str:
    path = "$"
    for part in error.absolute_path:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return path


def validate_schema(plan: Any, schema_path: Path = DEFAULT_SCHEMA) -> list[str]:
    schema, _ = _read_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    return [
        f"{_json_path(error)}: {error.message}"
        for error in sorted(
            validator.iter_errors(plan),
            key=lambda item: (list(item.absolute_path), item.message),
        )
    ]


def _valid_package(value: str) -> bool:
    return bool(PACKAGE_PATTERN.fullmatch(value))


def _valid_recipe_fqn(value: str) -> bool:
    return bool(RECIPE_FQN_PATTERN.fullmatch(value))


def _parameter_errors(operation: Mapping[str, Any]) -> list[str]:
    operation_id = operation["operation_id"]
    recipe_name = operation["recipe_name"]
    parameters = operation["options"]
    if recipe_name not in SUPPORTED_RECIPES:
        return [f"{operation_id}: unknown recipe mapping {recipe_name!r}"]

    allowed = SUPPORTED_RECIPES[recipe_name]
    errors: list[str] = []
    unknown = sorted(set(parameters) - set(allowed))
    missing = sorted(REQUIRED_PARAMETERS[recipe_name] - set(parameters))
    if unknown:
        errors.append(f"{operation_id}: unknown parameters: {', '.join(unknown)}")
    if missing:
        errors.append(f"{operation_id}: missing parameters: {', '.join(missing)}")
    for name in sorted(set(parameters) & set(allowed)):
        expected = allowed[name]
        value = parameters[name]
        if type(value) is not expected:  # bool must not be accepted as int.
            errors.append(
                f"{operation_id}: parameter {name} must be {expected.__name__}"
            )

    if recipe_name == "org.openrewrite.java.ChangePackage":
        for name in ("oldPackageName", "newPackageName"):
            value = parameters.get(name)
            if isinstance(value, str) and not _valid_package(value):
                errors.append(f"{operation_id}: invalid Java package in {name}: {value!r}")
    elif recipe_name == "org.openrewrite.java.ChangeType":
        for name in ("oldFullyQualifiedTypeName", "newFullyQualifiedTypeName"):
            value = parameters.get(name)
            if isinstance(value, str) and not _valid_recipe_fqn(value):
                errors.append(f"{operation_id}: invalid Java type in {name}: {value!r}")
    return errors


def _custom_artifact_exists(source: str | None, input_path: Path) -> bool:
    if not source or source.startswith(("http://", "https://")):
        return False
    candidate = Path(source)
    if not candidate.is_absolute():
        candidate = input_path.parent / candidate
    return candidate.is_file() and candidate.suffix in {".jar", ".class"}


def _semantic_validation(
    plan: Mapping[str, Any], input_path: Path
) -> tuple[list[str], list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    skipped: list[str] = []
    unsupported: list[str] = []
    operations = plan["operations"]

    ids = [operation["operation_id"] for operation in operations]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    for operation_id in duplicates:
        errors.append(f"duplicate operation ID: {operation_id}")

    moves: dict[str, tuple[str, str]] = {}
    for operation in operations:
        operation_id = operation["operation_id"]
        automation_class = operation["automation_class"]
        recipe_name = operation["recipe_name"]

        if automation_class == "DECLARATIVE_BUILT_IN":
            if not recipe_name or not _valid_recipe_fqn(recipe_name):
                errors.append(f"{operation_id}: invalid recipe FQN: {recipe_name!r}")
            else:
                errors.extend(_parameter_errors(operation))
            if recipe_name == "org.openrewrite.java.ChangePackage":
                old = operation["options"].get("oldPackageName")
                new = operation["options"].get("newPackageName")
                if isinstance(old, str) and isinstance(new, str):
                    previous = moves.get(old)
                    if previous and previous[0] != new:
                        errors.append(
                            f"conflicting package moves for {old}: "
                            f"{previous[0]} ({previous[1]}) and {new} ({operation_id})"
                        )
                    else:
                        moves[old] = (new, operation_id)
        elif automation_class == "CUSTOM_IMPERATIVE_RECIPE":
            if not recipe_name or not _valid_recipe_fqn(recipe_name):
                errors.append(f"{operation_id}: invalid custom recipe FQN: {recipe_name!r}")
            if operation["options"]:
                errors.append(f"{operation_id}: custom recipe references cannot have options")
            if not _custom_artifact_exists(operation["verified_recipe_source"], input_path):
                skipped.append(operation_id)
                unsupported.append(operation_id)
                warnings.append(f"{operation_id}: custom recipe implementation artifact is missing")
        elif automation_class in {"MANUAL_REFACTORING", "REJECTED_UNSAFE"}:
            skipped.append(operation_id)
            unsupported.append(operation_id)
            warnings.append(f"{operation_id}: excluded {automation_class} operation")

    for entry in plan["unsupported_operations"]:
        operation_id = entry["operation_id"]
        unsupported.append(operation_id)
        warnings.append(f"{operation_id}: plan marks operation unsupported")

    return (
        sorted(set(errors)),
        sorted(set(warnings)),
        sorted(set(skipped)),
        sorted(set(unsupported)),
    )


def _ordered_options(recipe_name: str, options: Mapping[str, Any]) -> dict[str, Any]:
    return {
        name: options[name]
        for name in SUPPORTED_RECIPES[recipe_name]
        if name in options
    }


def _yaml_document(plan: Mapping[str, Any], skipped: set[str]) -> bytes:
    recipe_list: list[Any] = []
    operations = sorted(
        plan["operations"], key=lambda item: (item["execution_order"], item["operation_id"])
    )
    for operation in operations:
        if operation["operation_id"] in skipped:
            continue
        automation_class = operation["automation_class"]
        recipe_name = operation["recipe_name"]
        if automation_class == "DECLARATIVE_BUILT_IN":
            recipe_list.append(
                {recipe_name: _ordered_options(recipe_name, operation["options"])}
            )
        elif automation_class == "CUSTOM_IMPERATIVE_RECIPE":
            recipe_list.append(recipe_name)

    document = {
        "type": "specs.openrewrite.org/v1beta/recipe",
        "name": plan["composite_recipe_name"],
        "displayName": "Refactor benchmark architecture",
        "description": FoldedString(
            "Applies validated architectural refactorings generated from DSARP recommendations."
        ),
        "recipeList": recipe_list,
    }
    rendered = yaml.safe_dump(
        document,
        allow_unicode=True,
        default_flow_style=False,
        explicit_start=True,
        sort_keys=False,
        width=76,
    )
    return rendered.replace("\r\n", "\n").encode("utf-8")


def generate(
    input_path: Path,
    *,
    strict: bool,
    schema_path: Path = DEFAULT_SCHEMA,
    timestamp: str | None = None,
) -> GenerationResult:
    timestamp = timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    validation_errors: list[str] = []
    warnings: list[str] = []
    skipped: list[str] = []
    unsupported: list[str] = []
    generated: list[str] = []
    input_digest = ""
    output_digest = ""
    yaml_bytes: bytes | None = None

    try:
        plan, raw = _read_json(input_path)
        input_digest = sha256(raw)
        validation_errors.extend(validate_schema(plan, schema_path))
        if not validation_errors:
            semantic_errors, warnings, skipped, unsupported = _semantic_validation(
                plan, input_path
            )
            validation_errors.extend(semantic_errors)
        if not validation_errors:
            strict_blocked = strict and bool(unsupported)
            if not strict_blocked:
                yaml_bytes = _yaml_document(plan, set(skipped))
                output_digest = sha256(yaml_bytes)
                generated = sorted(
                    operation["operation_id"]
                    for operation in plan["operations"]
                    if operation["operation_id"] not in set(skipped)
                )
    except (GenerationError, OSError, ValueError) as exc:
        validation_errors.append(str(exc))

    failed = bool(validation_errors) or (strict and bool(unsupported))
    report = {
        "generated_operation_ids": generated,
        "skipped_operation_ids": skipped,
        "unsupported_operation_ids": unsupported,
        "validation_errors": sorted(validation_errors),
        "warnings": warnings,
        "recipe_count": len(generated),
        "input_digest": input_digest,
        "output_digest": output_digest,
        "generation_timestamp": timestamp,
        "strict_mode": strict,
        "strict_mode_result": (
            "NOT_REQUESTED" if not strict else ("FAILED" if failed else "PASSED")
        ),
    }
    return GenerationResult(yaml_bytes, report, 1 if failed else 0)


def _write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _write_report(path: Path, report: Mapping[str, Any]) -> None:
    content = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    _write_bytes(path, content.encode("utf-8"))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a declarative OpenRewrite recipe from a validated plan."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    if sys.version_info < MINIMUM_PYTHON:
        print("Python 3.10 or newer is required", file=sys.stderr)
        return 2
    args = parse_args(argv)
    result = generate(args.input, strict=args.strict, schema_path=args.schema)
    if result.yaml_bytes is not None:
        _write_bytes(args.output, result.yaml_bytes)
    _write_report(args.report, result.report)
    for error in result.report["validation_errors"]:
        print(f"error: {error}", file=sys.stderr)
    if args.strict and result.report["unsupported_operation_ids"]:
        print("error: strict mode rejects unsupported operations", file=sys.stderr)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
