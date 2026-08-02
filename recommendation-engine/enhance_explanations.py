#!/usr/bin/env python3
"""Optionally enhance rationales using a local Qwen-family instruction endpoint."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path


def main() -> int:
    endpoint = os.environ.get("LOCAL_LLM_ENDPOINT")
    if not endpoint:
        print("LOCAL_LLM_ENDPOINT is not configured; deterministic recommendations remain complete.")
        return 0
    model = os.environ.get("LOCAL_LLM_MODEL", "qwen2.5:3b-instruct")
    source = Path("analysis/recommendations/recommendations.json")
    recommendations = json.loads(source.read_text(encoding="utf-8"))["recommendations"]
    enhanced = []
    for row in recommendations:
        validated = {
            "recommendation_id": row["recommendation_id"],
            "finding_id": row["finding_id"],
            "refactoring_kind": row["refactoring_kind"],
            "source_symbols": row["source_symbols"],
            "target_package": row["target_package"],
            "evidence": row["evidence"],
            "deterministic_rationale": row["rationale"],
        }
        prompt = ("Explain this validated recommendation evidence in plain academic language. "
                  "Do not propose operations, symbols, packages, recipe kinds, IDs, or ranking changes.\n"
                  + json.dumps(validated, sort_keys=True))
        payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
        request = urllib.request.Request(endpoint, payload, {"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=60) as response:
            answer = json.loads(response.read())
        text = answer.get("response") or answer.get("text") or ""
        enhanced.append({"recommendation_id": row["recommendation_id"],
                         "deterministic_rationale": row["rationale"],
                         "llm_enhanced_explanation": text})
    output = Path("analysis/recommendations/llm_explanations.json")
    output.write_text(json.dumps({"model": model, "explanations": enhanced}, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {len(enhanced)} separate optional explanations to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
