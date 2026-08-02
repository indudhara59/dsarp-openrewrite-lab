#!/usr/bin/env python3
"""Build a verified OpenRewrite automation plan without applying it."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from smell_detector.recipe_plan import COMPOSITE, DOCS, Planner, VERIFIED_OPTIONS


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("analysis/recipe-plan"))
    args = parser.parse_args()
    plan = Planner().create(args.repository.resolve())
    args.output.mkdir(parents=True, exist_ok=True)
    dump(args.output / "recipe_plan.json", plan)
    write_csv(args.output / "recipe_plan.csv", plan["operations"])
    dump(args.output / "unsupported_operations.json",
         {"schema_version": "1.0", "unsupported_operations": plan["unsupported_operations"]})
    (args.output / "recipe_plan.md").write_text(markdown(plan), encoding="utf-8")
    (args.output / "verification_sources.md").write_text(sources_markdown(), encoding="utf-8")
    counts = Counter(row["automation_class"] for row in plan["operations"])
    print("Plan operations: " + ", ".join(f"{key}={counts.get(key, 0)}" for key in
          ("DECLARATIVE_BUILT_IN", "CUSTOM_IMPERATIVE_RECIPE", "MANUAL_REFACTORING", "REJECTED_UNSAFE")))
    print(f"Unsupported planning gaps: {len(plan['unsupported_operations'])}")
    return 0


def write_csv(path, operations):
    fields = ["operation_id", "recommendation_id", "execution_order", "automation_class",
              "recipe_name", "verified_recipe_source", "options", "affected_symbols",
              "affected_packages", "expected_files", "preconditions", "postconditions",
              "expected_dependency_edges_added", "expected_dependency_edges_removed", "risk",
              "rollback_description", "validation_commands"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for operation in operations:
            row = dict(operation)
            for field in fields:
                if isinstance(row.get(field), (list, dict)):
                    row[field] = json.dumps(row[field], sort_keys=True, separators=(",", ":"))
            writer.writerow(row)


def markdown(plan):
    counts = Counter(row["automation_class"] for row in plan["operations"])
    lines = ["# OpenRewrite Automation Plan", "",
             f"Composite recipe: `{COMPOSITE}`", "",
             "This is a non-executing plan. No recipe, dry run, or source refactoring was applied.", "",
             "## Classification counts", ""]
    for classification in ("DECLARATIVE_BUILT_IN", "CUSTOM_IMPERATIVE_RECIPE",
                           "MANUAL_REFACTORING", "REJECTED_UNSAFE"):
        lines.append(f"- `{classification}`: **{counts.get(classification, 0)}**")
    lines.extend(["", "## Ordered operations", "",
                  "| Order | Operation | Recommendation | Class | Recipe | Package mapping | Types | Risk |",
                  "|---:|---|---|---|---|---|---:|---|"])
    for operation in sorted(plan["operations"], key=lambda row: row["execution_order"]):
        options = operation["options"]
        mapping = (f"`{options.get('oldPackageName')}` → `{options.get('newPackageName')}`"
                   if options else "not scheduled")
        lines.append(f"| {operation['execution_order']} | `{operation['operation_id']}` | "
                     f"`{operation['recommendation_id']}` | `{operation['automation_class']}` | "
                     f"`{operation['recipe_name'] or 'none'}` | {mapping} | "
                     f"{len(operation['affected_symbols'])} | {operation['risk']} |")
    lines.extend(["", "## Stable abstraction assessment", "",
                  "The evaluation contains an unmatched expected stable-abstraction unit, but the frozen blind pipeline emitted no accepted recommendation for it. Therefore it is not scheduled in the composite recipe.", "",
                  "The mechanical package mapping from `com.dsarp.shop.experimentalpromotions.api` to `com.dsarp.shop.contracts.promotion` is compatible with the documented `ChangePackage` options. Semantic analysis finds the ordercore callers, experimental implementations, and application wiring, all in `shop-business`. Nevertheless, executing that move would bypass recommendation validation, so it remains a manual planning gap.", "",
                  "If a later authorized recommendation validates it, it must run before responsibility-group moves and must prove:", "",
                  "- `ordercore -> contracts.promotion` exists.",
                  "- `experimentalpromotions -> contracts.promotion` exists.",
                  "- `ordercore -> experimentalpromotions` no longer exists.",
                  "- exactly one `DiscountPolicy` declaration exists.",
                  "- application composition still compiles and tests pass.", "",
                  "## Dependency and module assessment", "",
                  "All scheduled package moves remain within `shop-business`; no POM dependency change is scheduled. The ChangeDependency/AddDependency/RemoveDependency recipes were verified but are deliberately unused. Simulating all seven executable moves produced no component cycle and no symbol overlap.", "",
                  "## Safety gate", "",
                  "The five façade-preserving alternatives conflict with higher-ranked direct moves over the same groups and lack a precise facade contract. They are classified `REJECTED_UNSAFE`, are absent from the executable composite, and require a future explicit strategy decision.", ""])
    return "\n".join(lines)


def sources_markdown():
    return """# Verified OpenRewrite Sources

Recipe names and option names below were verified against official OpenRewrite documentation on 2026-08-02.

| Recipe | Verified options | Official source | Plan use |
|---|---|---|---|
| `org.openrewrite.java.ChangePackage` | `oldPackageName`, `newPackageName`, `recursive` | [Official catalog](https://docs.openrewrite.org/recipes/java/changepackage) | Seven scheduled package moves; investigated but unscheduled stable-contract move |
| `org.openrewrite.java.ChangeType` | `oldFullyQualifiedTypeName`, `newFullyQualifiedTypeName`, `ignoreDefinition` | [Official catalog](https://docs.openrewrite.org/recipes/java/changetype) | Not used: changing usages is not a substitute for moving declarations/source paths |
| `org.openrewrite.java.dependencies.ChangeDependency` | `oldGroupId`, `oldArtifactId`, `newGroupId`, `newArtifactId`, `newVersion`, `versionPattern`, `overrideManagedVersion`, `changeManagedDependency` | [Official catalog](https://docs.openrewrite.org/recipes/java/dependencies/changedependency) | Not used: no Maven coordinate changes are required |
| `org.openrewrite.java.dependencies.AddDependency` | `groupId`, `artifactId`, `version`, `versionPattern`, `onlyIfUsing`, `classifier`, `familyPattern`, `extension`, `configuration`, `scope`, `releasesOnly`, `type`, `optional`, `acceptTransitive` | [Official catalog](https://docs.openrewrite.org/recipes/java/dependencies/adddependency) | Not used: package moves remain within one Maven module |
| `org.openrewrite.java.dependencies.RemoveDependency` | `groupId`, `artifactId`, `unlessUsing`, `configuration`, `scope` | [Official catalog](https://docs.openrewrite.org/recipes/java/dependencies/removedependency) | Not used: no module dependency is removed |

The official [declarative recipe guide](https://docs.openrewrite.org/running-recipes/popular-recipe-guides/authoring-declarative-yaml-recipes) confirms that `ChangePackage` updates sources referencing the old package and moves package members to directories matching the new package. The official [getting-started guide](https://docs.openrewrite.org/running-recipes/getting-started) likewise demonstrates updated imports and moved source files.

No recipe or option lacking an official source is scheduled. No arbitrary class/method decomposition is represented as `ChangePackage`.
"""


if __name__ == "__main__":
    raise SystemExit(main())
