#!/usr/bin/env python3
"""Generate deterministic, ranked refactoring recommendations from blind findings."""

from __future__ import annotations

import argparse
from pathlib import Path

from smell_detector.recommendation_io import load, write
from smell_detector.recommender import Recommender


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("analysis/recommendations"))
    args = parser.parse_args()
    inputs = load(args.repository.resolve())
    result = Recommender().generate(
        inputs["findings"], inputs["metrics"], inputs["component_edges"],
        inputs["clusters"], inputs["classes"], inputs["class_edges"])
    write(args.output, result)
    print(f"Generated {len(result.candidates)} candidates and {len(result.recommendations)} accepted recommendations.")
    print(f"Rejected candidates: {sum(bool(row['rejection_reasons']) for row in result.candidates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
