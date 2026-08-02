from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from smell_detector.recommender import Recommender, PACKAGE, RANKING_WEIGHTS


def clazz(component, simple, package=None, module="business"):
    package = package or f"com.dsarp.shop.{component}"
    name = package + "." + simple
    return {"fully_qualified_class_name": name, "top_level_component": component,
            "package": package, "maven_module": module, "loc": 10,
            "public_type_count": 1, "method_count": 1,
            "incoming_class_dependencies": [], "outgoing_class_dependencies": [],
            "source_file": simple + ".java"}


def metric(component, count):
    return {"component": component, "production_class_count": count,
            "production_loc": count * 10, "package_count": 1, "ca": 1, "ce": 1,
            "instability": 0.5, "incoming_component_edges": [], "outgoing_component_edges": [],
            "weighted_incoming_dependency_count": 1, "weighted_outgoing_dependency_count": 1,
            "fan_in": 1, "fan_out": 1, "internal_class_dependency_count": 1,
            "internal_dependency_density": 0.5, "percentage_total_production_classes": 50,
            "percentage_total_production_loc": 50, "degree_centrality": 0.5}


def cluster(component, subpackage, member):
    return {"cluster_id": f"cluster:{component}:{subpackage}", "component": component,
            "member_classes": [member], "dominant_name_tokens": [subpackage],
            "dominant_subpackage": subpackage, "internal_edge_count": 0,
            "outgoing_edge_count": 0, "cohesion_score": 1.0,
            "confidence": 1.0, "evidence": []}


class RecommenderTest(unittest.TestCase):
    def test_ranking_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(RANKING_WEIGHTS.values()), 1.0)

    def test_god_candidates_are_specific_to_clusters(self):
        classes = [clazz("large", "Pay", "com.dsarp.shop.large.payment"),
                   clazz("large", "Notify", "com.dsarp.shop.large.notification")]
        finding = {"finding_id": "GC::large", "smell_type": "GOD_COMPONENT",
                   "primary_component": "large", "related_component": None,
                   "detection_confidence": 0.9}
        clusters = [cluster("large", "payment", classes[0]["fully_qualified_class_name"]),
                    cluster("large", "notification", classes[1]["fully_qualified_class_name"])]
        result = Recommender().generate([finding], [metric("large", 2)], [], clusters, classes, [])
        self.assertEqual({row["target_package"] for row in result.recommendations},
                         {"com.dsarp.shop.payment", "com.dsarp.shop.notification"})
        self.assertEqual(len({tuple(row["source_symbols"]) for row in result.recommendations}), 2)

    def test_different_smells_produce_different_candidate_sets(self):
        large = clazz("large", "PaymentService", "com.dsarp.shop.large.payment")
        stable = clazz("stable", "OrderService")
        volatile = clazz("volatile", "DiscountPolicy")
        findings = [
            {"finding_id": "GC::large", "smell_type": "GOD_COMPONENT", "primary_component": "large",
             "related_component": None, "detection_confidence": 0.9},
            {"finding_id": "UD::stable::volatile", "smell_type": "UNSTABLE_DEPENDENCY",
             "primary_component": "stable", "related_component": "volatile", "detection_confidence": 0.8},
        ]
        edge = {"source_class": stable["fully_qualified_class_name"],
                "target_class": volatile["fully_qualified_class_name"]}
        result = Recommender().generate(findings,
            [metric("large", 1), metric("stable", 1), metric("volatile", 1)], [],
            [cluster("large", "payment", large["fully_qualified_class_name"])],
            [large, stable, volatile], [edge])
        sets = {finding: {tuple(row["source_symbols"]) for row in result.candidates
                          if row["finding_id"] == finding} for finding in ("GC::large", "UD::stable::volatile")}
        self.assertTrue(sets["GC::large"].isdisjoint(sets["UD::stable::volatile"]))
        self.assertEqual({row["refactoring_kind"] for row in result.candidates
                          if row["finding_id"].startswith("UD::")}, {"INTRODUCE_STABLE_ABSTRACTION"})

    def test_ids_and_deduplication_are_deterministic(self):
        service = clazz("large", "PaymentService", "com.dsarp.shop.large.payment")
        finding = {"finding_id": "GC::large", "smell_type": "GOD_COMPONENT", "primary_component": "large",
                   "related_component": None, "detection_confidence": 0.9}
        item = cluster("large", "payment", service["fully_qualified_class_name"])
        first = Recommender().generate([finding], [metric("large", 1)], [], [item, dict(item)], [service], [])
        second = Recommender().generate([finding], [metric("large", 1)], [], [item], [service], [])
        self.assertEqual(first.recommendations, second.recommendations)
        self.assertEqual(len(first.recommendations), 1)

    def test_destination_packages_are_valid(self):
        self.assertIsNotNone(PACKAGE.fullmatch("com.dsarp.shop.payment"))
        self.assertIsNone(PACKAGE.fullmatch("com.dsarp.shop.Bad-Package"))


if __name__ == "__main__":
    unittest.main()
