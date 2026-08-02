#!/usr/bin/env python3
"""CLI for deterministic blind architectural smell detection."""

from __future__ import annotations

import argparse
from pathlib import Path

from smell_detector.detector import Detector
from smell_detector.io import load_inputs, write_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Directory containing six analyzer JSON reports")
    parser.add_argument("--output", type=Path, required=True, help="Directory for baseline detection artifacts")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw, hashes = load_inputs(args.input)
    metadata = raw["metadata"]
    result = Detector().detect(
        raw["classes"]["classes"],
        raw["class_dependencies"]["class_dependencies"],
        raw["component_dependencies"]["component_dependencies"],
        raw["component_metrics"]["component_metrics"],
        raw["responsibility_clusters"]["responsibility_clusters"],
        metadata.get("git_commit_sha", "unavailable"),
        metadata.get("warnings", []),
    )
    write_outputs(args.output, raw, hashes, result)
    print(f"Detected {len(result.findings)} findings from {len(result.god_candidates)} components.")
    print(f"Warnings: {len(result.warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
