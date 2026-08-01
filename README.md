# dsarp-openrewrite-lab

`dsarp-openrewrite-lab` is an academic software architecture refactoring experiment. It is intended to trace a reproducible path from intentionally introduced architectural smells through automated refactoring and comparative evaluation. The Java benchmark is implemented; analyzers, recommendation logic, OpenRewrite recipes, and the dashboard remain future phases.

## Planned workflow

The experiment is expected to proceed through these stages:

1. Build a Java benchmark with documented, intentionally introduced architectural smells. *(Current phase complete.)*
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

## Benchmark validation

With Java 17 available, build and exercise the benchmark from the repository root:

```sh
benchmark/mvnw -f benchmark/pom.xml clean verify
java -cp benchmark/shop-model/target/classes:benchmark/shop-business/target/classes:benchmark/shop-adapters/target/classes:benchmark/shop-application/target/classes com.dsarp.shop.application.ShopApplication
python3 scripts/count_benchmark_size.py
```

See [the build and run guide](docs/build-and-run.md) and [benchmark README](benchmark/README.md). No OpenRewrite execution, architecture analysis, refactoring, deployment, or push is part of the benchmark-construction phase.

## License

This repository is licensed under the MIT License. See [LICENSE](LICENSE).
