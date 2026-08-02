from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from smell_detector.detector import Detector, GOD_WEIGHTS, normalize


def metric(component, classes=1, loc=10, ca=0, ce=0, instability=0.0, centrality=0.0,
           internal=0, outgoing=0):
    return {
        "component": component, "production_class_count": classes, "production_loc": loc,
        "package_count": 1, "ca": ca, "ce": ce, "instability": instability,
        "incoming_component_edges": [], "outgoing_component_edges": [],
        "weighted_incoming_dependency_count": 0, "weighted_outgoing_dependency_count": outgoing,
        "fan_in": 0, "fan_out": outgoing, "internal_class_dependency_count": internal,
        "internal_dependency_density": 0.0, "percentage_total_production_classes": 50.0,
        "percentage_total_production_loc": 50.0, "degree_centrality": centrality,
    }


def class_row(component, name):
    fqcn = f"com.dsarp.shop.{component}.{name}"
    return {"fully_qualified_class_name": fqcn, "source_file": name + ".java",
            "maven_module": "fixture", "top_level_component": component,
            "package": f"com.dsarp.shop.{component}", "loc": 10,
            "outgoing_class_dependencies": [], "incoming_class_dependencies": [],
            "public_type_count": 1, "method_count": 1}


class DetectorTest(unittest.TestCase):
    def test_formula_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(GOD_WEIGHTS.values()), 1.0)
        self.assertIn("internal_dependency_concentration", GOD_WEIGHTS)

    def test_normalization_is_zero_safe_and_deterministic(self):
        self.assertEqual(normalize({"b": 0, "a": 0}), {"a": 0.0, "b": 0.0})
        self.assertEqual(normalize({"b": 4, "a": 2}), {"a": 0.5, "b": 1.0})

    def test_sdp_boundary_is_strict(self):
        metrics = [metric("stable", instability=0.2), metric("boundary", instability=0.4)]
        result = Detector().detect(
            [class_row("stable", "A"), class_row("boundary", "B")],
            [{"source_class": "com.dsarp.shop.stable.A", "target_class": "com.dsarp.shop.boundary.B"}],
            [{"source_component": "stable", "target_component": "boundary", "weight": 1}],
            metrics, [], "commit", [])
        self.assertFalse(any(row["smell_type"] == "UNSTABLE_DEPENDENCY" for row in result.findings))

    def test_unstable_edge_is_reported_once_even_if_input_repeats(self):
        metrics = [metric("stable", instability=0.0, classes=1),
                   metric("volatile", instability=1.0, classes=1)]
        edge = {"source_component": "stable", "target_component": "volatile", "weight": 2}
        result = Detector().detect(
            [class_row("stable", "A"), class_row("volatile", "B")],
            [{"source_class": "com.dsarp.shop.stable.A", "target_class": "com.dsarp.shop.volatile.B"}],
            [edge, dict(edge)], metrics, [], "commit", [])
        unstable = [row for row in result.findings if row["smell_type"] == "UNSTABLE_DEPENDENCY"]
        self.assertEqual(len(unstable), 1)
        self.assertEqual(unstable[0]["finding_id"], "UD::stable::volatile")

    def test_finding_order_and_ids_are_stable(self):
        metrics = [metric("stable", instability=0.0, classes=1),
                   metric("zeta", instability=1.0, classes=1),
                   metric("alpha", instability=1.0, classes=1)]
        classes = [class_row("stable", "A"), class_row("zeta", "B"), class_row("alpha", "C")]
        dependencies = [
            {"source_class": "com.dsarp.shop.stable.A", "target_class": "com.dsarp.shop.zeta.B"},
            {"source_class": "com.dsarp.shop.stable.A", "target_class": "com.dsarp.shop.alpha.C"},
        ]
        edges = [
            {"source_component": "stable", "target_component": "zeta", "weight": 1},
            {"source_component": "stable", "target_component": "alpha", "weight": 1},
        ]
        first = Detector().detect(classes, dependencies, edges, metrics, [], "commit", [])
        second = Detector().detect(classes, dependencies, list(reversed(edges)), metrics, [], "commit", [])
        self.assertEqual(first.findings, second.findings)
        self.assertEqual([row["finding_id"] for row in first.findings],
                         ["UD::stable::alpha", "UD::stable::zeta"])

    def test_candidate_evidence_contains_all_required_dimensions(self):
        result = Detector().detect([class_row("component", "A")], [], [],
                                   [metric("component", classes=1, loc=10, ca=1, ce=1,
                                           centrality=1.0, internal=1, outgoing=1)],
                                   [{"cluster_id": "cluster:component:root", "component": "component",
                                     "dominant_subpackage": "root"}], "commit", [])
        candidate = result.god_candidates[0]
        self.assertEqual(set(candidate["raw_features"]), set(GOD_WEIGHTS))
        self.assertEqual(set(candidate["normalized_features"]), set(GOD_WEIGHTS))


if __name__ == "__main__":
    unittest.main()
