# Blind Smell Ranking Explanation

Findings are ranked by severity descending, detection confidence descending, then stable finding ID.

## God Component scoring

The `god-component-v1` score uses eight normalized dimensions and a fixed threshold of `0.60`.

| Candidate rank | Component | Score | Threshold | Cluster count | Class share | LOC share |
|---:|---|---:|---:|---:|---:|---:|
| 1 | megacomponent | 0.674571 | 0.60 | 7 | 34.265700% | 50.616500% |
| 2 | model | 0.419022 | 0.60 | 1 | 16.783200% | 2.349200% |
| 3 | experimentalpromotions | 0.389791 | 0.60 | 4 | 8.391600% | 4.390200% |
| 4 | adapters | 0.257284 | 0.60 | 5 | 6.993000% | 3.332200% |
| 5 | shared | 0.237047 | 0.60 | 1 | 1.398600% | 0.724800% |
| 6 | application | 0.204973 | 0.60 | 1 | 4.195800% | 1.166300% |
| 7 | ordercore | 0.192998 | 0.60 | 1 | 8.391600% | 8.497200% |
| 8 | catalog | 0.145592 | 0.60 | 1 | 2.797200% | 4.132000% |
| 9 | customer | 0.145592 | 0.60 | 1 | 2.797200% | 4.132000% |
| 10 | configuration | 0.130082 | 0.60 | 1 | 1.398600% | 2.066000% |
| 11 | utilities | 0.130082 | 0.60 | 1 | 1.398600% | 2.066000% |
| 12 | cart | 0.128449 | 0.60 | 1 | 2.797200% | 4.132000% |
| 13 | delivery | 0.128449 | 0.60 | 1 | 2.797200% | 4.132000% |
| 14 | fraud | 0.128449 | 0.60 | 1 | 2.797200% | 4.132000% |
| 15 | returns | 0.128449 | 0.60 | 1 | 2.797200% | 4.132000% |

## Unstable Dependency scoring

An edge is eligible only when `I(source) + 0.20 < I(target)`. Severity combines excess instability margin, edge weight, source stability, and source-class coverage.

