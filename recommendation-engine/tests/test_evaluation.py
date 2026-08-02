from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from smell_detector.evaluation import overlap_metrics, prf, safe_divide


ROOT = Path(__file__).resolve().parents[2]


def read(relative, key):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))[key]


class IndependentEvaluationTest(unittest.TestCase):
    def test_precision_recall_f1_recalculation(self):
        self.assertEqual(prf(1, 0, 1), {
            "true_positives": 1, "false_positives": 0, "false_negatives": 1,
            "precision": 1.0, "recall": 0.5, "f1": 0.666667})

    def test_detection_counts_recalculated_from_frozen_files(self):
        truth = read("benchmark-ground-truth/architecture-ground-truth.json", "smells")
        findings = read("analysis/baseline/smell_findings.json", "findings")
        expected = {(row["smell_type"].lower().replace(" ", "_"), tuple(sorted(row["affected_components"])))
                    for row in truth}
        detected = {(row["smell_type"].lower(), tuple(sorted(
                    [row["primary_component"]] + ([row["related_component"]] if row["related_component"] else []))))
                    for row in findings}
        self.assertEqual(len(expected & detected), 1)
        self.assertEqual(len(detected - expected), 0)
        self.assertEqual(len(expected - detected), 1)

    def test_ranking_metrics_recalculated_independently(self):
        truth = read("benchmark-ground-truth/architecture-ground-truth.json", "smells")
        findings = read("analysis/baseline/smell_findings.json", "findings")
        matched_ranks = []
        for expected in truth:
            expected_type = expected["smell_type"].upper().replace(" ", "_")
            rank = next((row["rank"] for row in findings if row["smell_type"] == expected_type
                         and row["primary_component"] in expected["affected_components"]), 0)
            matched_ranks.append(rank)
        self.assertEqual(safe_divide(sum(0 < rank <= 1 for rank in matched_ranks), len(truth)), 0.5)
        self.assertEqual(safe_divide(sum(0 < rank <= 3 for rank in matched_ranks), len(truth)), 0.5)
        self.assertEqual(safe_divide(sum(1 / rank for rank in matched_ranks if rank), len(truth)), 0.5)

    def test_overlap_metrics_recalculated_independently(self):
        truth = read("benchmark-ground-truth/architecture-ground-truth.json", "smells")
        recommendations = read("analysis/recommendations/recommendations.json", "recommendations")
        expected_symbols = {symbol.rsplit(".", 1)[-1] for smell in truth for symbol in smell["affected_symbols"]}
        predicted_symbols = {symbol.rsplit(".", 1)[-1] for row in recommendations for symbol in row["source_symbols"]}
        overlap = overlap_metrics(predicted_symbols, expected_symbols)
        self.assertEqual(overlap["intersection_count"], 7)
        self.assertEqual(overlap["expected_count"], 10)
        self.assertEqual(overlap["recall"], 0.7)

    def test_generated_json_is_valid_and_metrics_match(self):
        detection = json.loads((ROOT / "analysis/ground-truth-evaluation/detection_evaluation.json").read_text())
        recommendation = json.loads((ROOT / "analysis/ground-truth-evaluation/recommendation_evaluation.json").read_text())
        self.assertEqual(detection["overall"], prf(1, 0, 1))
        self.assertEqual(recommendation["summary"]["exact match"], 7)
        self.assertEqual(recommendation["summary"]["semantically valid alternative"], 5)


if __name__ == "__main__":
    unittest.main()
