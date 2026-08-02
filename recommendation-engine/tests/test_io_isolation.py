from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from smell_detector.io import INPUTS, load_inputs


class InputIsolationTest(unittest.TestCase):
    def test_input_loader_reads_exactly_six_allowlisted_files(self):
        self.assertEqual(list(INPUTS.values()), [
            "classes.json", "class_dependencies.json", "component_dependencies.json",
            "component_metrics.json", "responsibility_clusters.json", "analyzer_metadata.json",
        ])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = {
                "classes": [], "class_dependencies": [], "component_dependencies": [],
                "component_metrics": [], "responsibility_clusters": [],
                "analyzer_version": "fixture", "warnings": [],
            }
            for key, filename in INPUTS.items():
                payload_key = key if key != "metadata" else "analyzer_version"
                (root / filename).write_text(json.dumps({payload_key: values[payload_key]}))
            unrelated = root / "unrelated.json"
            unrelated.write_text("not valid json and must never be read")
            loaded, hashes = load_inputs(root)
            self.assertEqual(set(loaded), set(INPUTS))
            self.assertEqual(set(hashes), set(INPUTS.values()))

    def test_production_detector_has_no_component_name_special_case(self):
        production = Path(__file__).resolve().parents[1] / "smell_detector" / "detector.py"
        text = production.read_text(encoding="utf-8").lower()
        self.assertNotIn("mega" + "component", text)


if __name__ == "__main__":
    unittest.main()
