# Blind Architectural Smell Detector

This Python 3 standard-library tool consumes only the six semantic analyzer reports in `analysis/raw`. It performs deterministic smell detection; it does not create refactoring recommendations or inspect separately maintained evaluation data.

From the repository root:

```sh
python3 -m unittest discover -s recommendation-engine/tests -p 'test_*.py' -v
python3 recommendation-engine/detect_smells.py --input analysis/raw --output analysis/baseline
```

## God Component formula (`god-component-v1`)

All features are normalized to `[0,1]` by the maximum observed value across components, with zero used when the observed maximum is zero:

```text
0.19 × class share
+ 0.19 × LOC share
+ 0.14 × normalized Ca
+ 0.14 × normalized Ce
+ 0.10 × normalized degree centrality
+ 0.10 × responsibility diversity
+ 0.09 × responsibility cluster count
+ 0.05 × internal dependency concentration
```

Internal dependency concentration is `internal class edges / (internal class edges + weighted outgoing class dependencies)`. Responsibility diversity is the number of distinct cluster subpackages. The fixed detection threshold is `0.60`.

The additional 0.05 dimension is required because the suggested seven weights did not allocate weight to internal dependency concentration. Class share, LOC share, Ca, and Ce were each reduced by 0.01, and cluster count by 0.01, preserving the original emphasis while retaining a total weight of 1.00.

## Unstable Dependency formula (`unstable-dependency-v1`)

An edge `A → B` is a finding only when:

```text
I(A) + 0.20 < I(B)
```

Severity is a percentage calculated as:

```text
100 × (
  0.45 × normalized margin beyond 0.20
  + 0.25 × normalized edge weight
  + 0.20 × source stability
  + 0.10 × source-class coverage
)
```

The excess margin is normalized by the maximum possible excess (`0.80`). Edge weights are normalized by the maximum observed component-edge weight. Source stability is `1 - I(A)`. Source-class coverage is the number of distinct source classes supporting the edge divided by the source component class count.

Finding IDs depend only on smell type and component identity. All lists and rows use stable lexical ordering; ranks use severity descending, detection confidence descending, then finding ID ascending. Only the execution timestamp in `run_metadata.json` may vary between equivalent runs.

## Generate ranked recommendations

Recommendation generation consumes only the documented baseline findings/metrics/clusters and raw class graphs:

```sh
python3 recommendation-engine/generate_recommendations.py --repository . --output analysis/recommendations
```

The ranking formula and limitations are emitted to `analysis/recommendations/ranking_formula.md`. Candidates are generated per finding and exact responsibility cluster or dependency edge. Rejected cycle/package proposals remain visible in `candidates.*` but are excluded from `recommendations.*`.

An optional local Qwen-family explanation layer can be run separately:

```sh
LOCAL_LLM_ENDPOINT=http://127.0.0.1:11434/api/generate \
LOCAL_LLM_MODEL=qwen2.5:3b-instruct \
python3 recommendation-engine/enhance_explanations.py
```

Without those environment variables, the deterministic pipeline is complete. Enhanced text is stored separately and cannot alter IDs, symbols, refactoring kinds, operations, ranking, or machine-consumed transformation data.
