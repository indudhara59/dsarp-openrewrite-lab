#!/usr/bin/env python3
"""Deterministically report benchmark source size and component distribution."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "benchmark"
PACKAGE = re.compile(r"^\s*package\s+com\.dsarp\.shop\.([a-zA-Z0-9_]+)(?:\.|;)" )


def java_files(source_kind: str) -> list[Path]:
    pattern = f"*/src/{source_kind}/java/**/*.java"
    return sorted(BENCHMARK.glob(pattern), key=lambda path: path.as_posix())


def line_count(paths: list[Path]) -> int:
    return sum(len(path.read_text(encoding="utf-8").splitlines()) for path in paths)


def component(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        match = PACKAGE.match(line)
        if match:
            return match.group(1)
    raise ValueError(f"No benchmark package declaration in {path}")


def main() -> None:
    modules = sorted(path.parent.name for path in BENCHMARK.glob("*/pom.xml"))
    production = java_files("main")
    tests = java_files("test")
    components = Counter(component(path) for path in production)
    packages = {
        next(line.strip().removeprefix("package ").removesuffix(";")
             for line in path.read_text(encoding="utf-8").splitlines()
             if line.strip().startswith("package "))
        for path in production
    }

    print(f"Maven module count: {len(modules)}")
    print(f"Production Java class count: {len(production)}")
    print(f"Test Java class count: {len(tests)}")
    print(f"Production LOC: {line_count(production)}")
    print(f"Test LOC: {line_count(tests)}")
    print(f"Package count: {len(packages)}")
    print("Classes per top-level component:")
    for name, count in sorted(components.items()):
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
