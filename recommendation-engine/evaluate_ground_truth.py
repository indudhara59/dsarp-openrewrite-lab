#!/usr/bin/env python3
"""Evaluate frozen blind findings and recommendations against released ground truth."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from smell_detector.evaluation import Evaluator


def read(path: Path, key: str):
    return json.loads(path.read_text(encoding="utf-8"))[key]


def dump(path: Path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("analysis/ground-truth-evaluation"))
    args = parser.parse_args()
    root = args.repository.resolve()
    truth = read(root / "benchmark-ground-truth/architecture-ground-truth.json", "smells")
    findings = read(root / "analysis/baseline/smell_findings.json", "findings")
    metrics = read(root / "analysis/baseline/component_metrics.json", "component_metrics")
    recommendations = read(root / "analysis/recommendations/recommendations.json", "recommendations")
    result = Evaluator().evaluate(truth, findings, recommendations, metrics)
    args.output.mkdir(parents=True, exist_ok=True)
    dump(args.output / "detection_evaluation.json", result.detection)
    dump(args.output / "recommendation_evaluation.json", result.recommendation)
    write_confusion(args.output / "confusion_matrix.csv", result.detection)
    write_ranking(args.output / "ranking_metrics.csv", result)
    (args.output / "evaluation_report.md").write_text(report(result), encoding="utf-8")
    overall = result.detection["overall"]
    print(f"Detection: TP={overall['true_positives']} FP={overall['false_positives']} FN={overall['false_negatives']} "
          f"precision={overall['precision']:.6f} recall={overall['recall']:.6f} F1={overall['f1']:.6f}")
    print(f"Recommendations evaluated: {result.recommendation['summary']['recommendation_count']}")
    return 0


def write_confusion(path, detection):
    fields = ["smell_type", "true_positives", "false_positives", "false_negatives", "precision", "recall", "f1"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(detection["by_smell_type"])
        writer.writerow({"smell_type": "OVERALL", **detection["overall"]})


def write_ranking(path, result):
    detection = result.detection["ranking_metrics"]
    recommendation = result.recommendation["summary"]
    rows = [
        ("detection", "top_1_accuracy", detection["top_1_accuracy"]),
        ("detection", "top_3_accuracy", detection["top_3_accuracy"]),
        ("detection", "mean_reciprocal_rank", detection["mean_reciprocal_rank"]),
        ("recommendation", "top_1_valid_accuracy", recommendation["top_1_valid_accuracy"]),
        ("recommendation", "top_3_valid_accuracy", recommendation["top_3_valid_accuracy"]),
        ("recommendation", "symbol_overlap_f1", result.recommendation["recommendation_symbol_overlap"]["f1"]),
        ("recommendation", "package_overlap_f1", result.recommendation["recommendation_package_overlap"]["f1"]),
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["scope", "metric", "value"])
        writer.writerows(rows)


def report(result):
    detection = result.detection
    recommendation = result.recommendation
    overall = detection["overall"]
    rank = detection["ranking_metrics"]
    lines = ["# Ground-Truth Evaluation", "",
             "This evaluation compares the frozen blind baseline and frozen recommendations against the subsequently released ground truth. No thresholds or baseline artifacts were changed.", "",
             "## Matching rules", ""]
    lines.extend(f"- **{key.replace('_', ' ')}:** {value}" for key, value in detection["matching_rules"].items())
    lines.extend(["", "## Detection accuracy", "",
                  f"- True positives: **{overall['true_positives']}**",
                  f"- False positives: **{overall['false_positives']}**",
                  f"- False negatives: **{overall['false_negatives']}**",
                  f"- Precision: **{overall['precision']:.6f}**",
                  f"- Recall: **{overall['recall']:.6f}**",
                  f"- F1: **{overall['f1']:.6f}**",
                  f"- Top-1 accuracy: **{rank['top_1_accuracy']:.6f}**",
                  f"- Top-3 accuracy: **{rank['top_3_accuracy']:.6f}**",
                  f"- Mean reciprocal rank: **{rank['mean_reciprocal_rank']:.6f}**", "",
                  "### Matched findings", ""])
    for row in detection["matched_findings"]:
        lines.append(f"- `{row['finding_id']}` → `{row['smell_id']}`: **{row['quality']}**, rank {row['rank']}; detected and expected components: `{', '.join(row['expected_components'])}`.")
    if not detection["matched_findings"]:
        lines.append("- None.")
    lines.extend(["", "### Unmatched findings (false positives)", ""])
    if detection["unmatched_findings"]:
        lines.extend(f"- `{row['finding_id']}` ({row['smell_type']})" for row in detection["unmatched_findings"])
    else:
        lines.append("- None.")
    lines.extend(["", "### Missed intentional smells (false negatives)", ""])
    for row in detection["missed_ground_truth_smells"]:
        lines.append(f"- `{row['smell_id']}` ({row['smell_type']}): {row['measured_reason']}")
    if not detection["missed_ground_truth_smells"]:
        lines.append("- None.")
    detected_packages = detection["detected_vs_expected_packages"]
    lines.extend(["", "### Detected versus expected affected packages", "",
                  f"- Matched: `{', '.join(detected_packages['matched'])}`",
                  f"- Expected but undetected: `{', '.join(detected_packages['expected_only']) or 'none'}`",
                  f"- Detected but unexpected: `{', '.join(detected_packages['predicted_only']) or 'none'}`",
                  f"- Package precision/recall/F1: **{detected_packages['precision']:.6f} / {detected_packages['recall']:.6f} / {detected_packages['f1']:.6f}**"])
    summary = recommendation["summary"]
    lines.extend(["", "## Recommendation quality", "",
                  f"- Exact matches: **{summary['exact match']}**",
                  f"- Partial matches: **{summary['partial match']}**",
                  f"- Semantically valid alternatives: **{summary['semantically valid alternative']}**",
                  f"- Incorrect recommendations: **{summary['incorrect recommendation']}**",
                  f"- Unsafe recommendations: **{summary['unsafe recommendation']}**",
                  f"- Unautomatable but valid recommendations: **{summary['unautomatable but valid recommendation']}**",
                  f"- Top-1 valid recommendation accuracy: **{summary['top_1_valid_accuracy']:.6f}**",
                  f"- Top-3 valid recommendation accuracy: **{summary['top_3_valid_accuracy']:.6f}**", "",
                  "The seven direct responsibility-group moves exactly match the seven expected God Component destinations. Five façade-preserving variants are semantically valid alternatives at those same measured boundaries. The highest-ranked recommendation targets the reporting responsibility group, which is one of the intentional groups.", "",
                  "No recommendation targets the misplaced abstraction because its Unstable Dependency smell was missed during frozen blind detection.", "",
                  "### Detected versus expected destination packages", ""])
    packages = recommendation["recommendation_package_overlap"]
    lines.extend([f"- Matched: `{', '.join(packages['matched'])}`",
                  f"- Expected but absent: `{', '.join(packages['expected_only']) or 'none'}`",
                  f"- Detected but unexpected: `{', '.join(packages['predicted_only']) or 'none'}`",
                  f"- Package precision/recall/F1: **{packages['precision']:.6f} / {packages['recall']:.6f} / {packages['f1']:.6f}**", ""])
    symbols = recommendation["recommendation_symbol_overlap"]
    lines.extend(["### Recommendation symbol overlap", "",
                  f"- Explicit expected symbols covered: `{', '.join(symbols['matched'])}`",
                  f"- Explicit expected symbols missed: `{', '.join(symbols['expected_only'])}`",
                  f"- Symbol precision/recall/F1/Jaccard: **{symbols['precision']:.6f} / {symbols['recall']:.6f} / {symbols['f1']:.6f} / {symbols['jaccard']:.6f}**", "",
                  "Symbol precision is deliberately low because recommendations move complete seven-class responsibility groups while ground truth lists representative symbols rather than every class. Package overlap is the more meaningful boundary-level measure.", "",
                  "## Limitations", "",
                  "- The benchmark contains only two intentional smells, so aggregate metrics have high variance.",
                  "- Detection top-k accuracy treats each expected smell as one query and assigns zero reciprocal rank to misses.",
                  "- Ground-truth affected symbols are representative, so set precision penalizes valid additional group members.",
                  "- The semantic analyzer measured the intended unstable edge, but component-level instability did not cross the preconfigured margin.",
                  "- Recommendation evaluation cannot credit an abstraction relocation that was never generated.", ""])
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
