# dsarp-openrewrite-lab

`dsarp-openrewrite-lab` is the scaffold for an academic software architecture refactoring experiment. The completed experiment is intended to trace a reproducible path from intentionally introduced architectural smells through automated refactoring and comparative evaluation. This initial phase contains only repository structure, documentation, conventions, and validation entry points; it does not yet contain the benchmark Java application, analyzers, recipes, or dashboard implementation.

## Planned workflow

The experiment is expected to proceed through these stages:

1. Build a Java benchmark with documented, intentionally introduced architectural smells.
2. Analyze the benchmark without consulting its architecture ground truth.
3. Detect God Component and Unstable Dependency candidates using fixed, documented thresholds.
4. Produce deterministic, ranked refactoring recommendations.
5. Evaluate those recommendations against separately maintained ground truth.
6. Translate reviewed recommendations into OpenRewrite recipe plans and recipes.
7. Perform and review an OpenRewrite dry run before applying any transformation.
8. Apply approved recipes and repeat the architectural analysis with unchanged thresholds.
9. Compare baseline and after-analysis results.
10. Present the experiment, evidence, and visual comparisons in a Vercel-hosted dashboard.

LLM-generated prose may explain or summarize recommendations, but it will not directly control transformations. Machine-consumed transformation inputs must be deterministic.

## Repository layout

- `benchmark/`: future intentionally smell-bearing Java benchmark.
- `architecture-analyzer/`: future architecture measurement and smell detection.
- `recommendation-engine/`: future deterministic ranking and recommendation logic.
- `rewrite-recipes/`: future declarative and imperative OpenRewrite recipes.
- `tools/`: future supporting tools and utilities.
- `analysis/`: generated artifacts for each experiment stage, kept outside source code.
- `dashboard/`: future Vercel-hosted results dashboard.
- `docs/`: experiment protocol, terminology, and future supporting documentation.
- `scripts/`: future reproducible experiment and validation commands.
- `tests/`: future cross-module and experiment-level tests.
- `.github/workflows/`: future continuous-integration workflows.

## Current validation

This scaffold can be inspected with standard shell and Git commands:

```sh
find . -path './.git' -prune -o -print | sort
test -f README.md && test -f AGENTS.md && test -f docs/experiment-protocol.md && test -f docs/glossary.md
git status --short
```

Build, test, OpenRewrite, and dashboard commands will be documented only when their implementations are added. No `rewrite:run`, deployment, or push should be performed as part of this scaffolding phase.

## License

This repository is licensed under the MIT License. See [LICENSE](LICENSE).
