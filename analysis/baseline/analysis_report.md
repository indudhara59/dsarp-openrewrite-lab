# Blind Baseline Architecture Smell Analysis

This report is generated from semantic analyzer outputs using deterministic formulas. It contains detection only and no refactoring recommendations.

## Ranked findings

| Rank | Finding | Type | Severity | Confidence | Explanation |
|---:|---|---|---:|---:|---|
| 1 | `GC::megacomponent` | GOD_COMPONENT | 67.457100 | 0.796607 | megacomponent scored 0.674571 against the 0.60 threshold; it contains 34.265700% of classes and 50.616500% of LOC, with Ca=2, Ce=2, centrality=0.285714, and 7 measured responsibility clusters. |

## Warnings and missing data

No input warnings or missing required data were reported.

## Unstable Dependency assessment

No component edge satisfies `I(source) + 0.20 < I(target)`. The largest observed increase is `ordercore -> experimentalpromotions` with I(source)=0.666667, I(target)=0.714286, and difference 0.047619, below the required strict margin 0.20.
