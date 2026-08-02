"""Strictly allowlisted recommendation input and deterministic artifact output."""

from __future__ import annotations

import csv
import json
from pathlib import Path

INPUTS = {
    "findings": ("analysis/baseline/smell_findings.json", "findings"),
    "metrics": ("analysis/baseline/component_metrics.json", "component_metrics"),
    "component_edges": ("analysis/baseline/component_dependencies.json", "component_dependencies"),
    "clusters": ("analysis/baseline/responsibility_clusters.json", "responsibility_clusters"),
    "classes": ("analysis/raw/classes.json", "classes"),
    "class_edges": ("analysis/raw/class_dependencies.json", "class_dependencies"),
}


def load(repository: Path):
    result = {}
    for name, (relative, root_key) in INPUTS.items():
        path = repository / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        result[name] = json.loads(path.read_text(encoding="utf-8"))[root_key]
    return result


def write(output: Path, result) -> None:
    output.mkdir(parents=True, exist_ok=True)
    dump(output / "candidates.json", {"schema_version": "1.0", "candidates": result.candidates})
    dump(output / "recommendations.json", {"schema_version": "1.0", "recommendations": result.recommendations})
    write_csv(output / "candidates.csv", result.candidates, include_ranking=True)
    write_csv(output / "recommendations.csv", result.recommendations, include_ranking=False)
    (output / "ranking_formula.md").write_text(ranking_formula(), encoding="utf-8")
    (output / "recommendation_report.md").write_text(report(result), encoding="utf-8")


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows, include_ranking: bool) -> None:
    fields = ["recommendation_id", "finding_id", "smell_type", "candidate_rank",
              "detection_confidence", "refactoring_confidence", "source_component",
              "target_component", "source_package", "target_package", "source_symbols",
              "related_symbols", "refactoring_kind", "parameters", "evidence", "rationale",
              "expected_metric_effect", "expected_dependency_changes", "preconditions",
              "postconditions", "behavior_risk", "architecture_risk", "estimated_files_changed",
              "automatable", "automation_notes", "validation_commands", "rejection_reasons"]
    if include_ranking:
        fields = ["candidate_id", "ranking_score", "ranking_features"] + fields
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for item in rows:
            row = dict(item)
            for field in fields:
                if isinstance(row.get(field), (dict, list)):
                    row[field] = json.dumps(row[field], sort_keys=True, separators=(",", ":"))
            writer.writerow(row)


def ranking_formula() -> str:
    return """# Recommendation Ranking Formula

Candidate ranking is deterministic and does not use an LLM. Features are bounded to `[0,1]`:

```text
0.30 expected smell reduction
+ 0.20 cohesion (measured cohesion and cluster confidence)
+ 0.10 reference manageability
+ 0.10 low behavior risk
+ 0.10 low package-cycle risk
+ 0.05 low Maven-module-cycle risk
+ 0.10 automation feasibility
+ 0.05 affected-code test coverage
```

No test-coverage table is present in the permitted inputs, so every candidate receives the same neutral `0.50` test-coverage value. This preserves the factor without inventing evidence. Package cycles are checked by remapping the proposed class group in the resolved class graph. Maven cycle risk is zero for package moves that remain in the original module; abstraction relocation candidates check the observed module graph.

Candidates sort by score descending and stable candidate ID ascending. Recommendation IDs are SHA-256-derived from finding ID, refactoring kind, sorted source symbols, target package, and target symbol. Rejected candidates remain in `candidates.*` and are excluded from `recommendations.*`.
"""


def report(result) -> str:
    lines = ["# Ranked Blind Refactoring Recommendations", "",
             "These recommendations are derived only from validated blind detection and semantic dependency data. They do not claim that a rename fixes a smell and do not move an entire God Component as one unit.", "",
             "## Highest-ranked recommendations", "",
             "| Rank | ID | Finding | Kind | Responsibility/edge | Target | Score basis |", "|---:|---|---|---|---|---|---|"]
    candidates_by_rec = {row["recommendation_id"]: row for row in result.candidates}
    for row in result.recommendations[:10]:
        candidate = candidates_by_rec[row["recommendation_id"]]
        identity = row["parameters"].get("cluster_id", row["parameters"].get("target_symbol", ""))
        lines.append(f"| {row['candidate_rank']} | `{row['recommendation_id']}` | `{row['finding_id']}` | "
                     f"{row['refactoring_kind']} | `{identity}` | `{row['target_package']}` | "
                     f"{candidate['ranking_score']:.6f} |")
    lines.extend(["", "## Why candidates are distinct", ""])
    for row in result.recommendations:
        identity = row["parameters"].get("cluster_id", row["parameters"].get("target_symbol", ""))
        lines.append(f"- `{row['recommendation_id']}` is keyed to `{row['finding_id']}`, "
                     f"`{row['refactoring_kind']}`, `{identity}`, {len(row['source_symbols'])} exact source symbols, "
                     f"and destination `{row['target_package']}`.")
    lines.extend(["", "## Rejected candidates", ""])
    rejected = [row for row in result.candidates if row["rejection_reasons"]]
    if rejected:
        for row in rejected:
            lines.append(f"- `{row['candidate_id']}`: {'; '.join(row['rejection_reasons'])}")
    else:
        lines.append("No generated candidate was rejected by package validity or cycle checks.")
    lines.extend(["", "## Input limitations", "",
                  "- No test-coverage table was provided; ranking uses the documented neutral value.",
                  "- If a smell type has no baseline finding, no real recommendation is generated for that type.",
                  "- Human-readable rationales are deterministic. Optional local-model text is stored separately and cannot alter operations or ranking.", ""])
    return "\n".join(lines)
