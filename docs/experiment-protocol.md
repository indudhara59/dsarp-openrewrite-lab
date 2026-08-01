# Experiment Protocol

## 1. Research objective

The experiment will evaluate whether architecture-smell detection and deterministic recommendation ranking can guide safe, reviewable OpenRewrite refactorings that measurably improve a Java system's architecture. It will preserve a complete evidence chain from the intentionally introduced smells through baseline measurement, recommendation, recipe generation, dry run, application, after-analysis, and visualization.

## 2. Research questions

1. How accurately can the analyzer detect intentionally introduced God Component and Unstable Dependency smells without access to architecture ground truth?
2. How effectively can deterministic ranking identify useful refactoring candidates and recommendations?
3. Which recommended changes can be encoded safely as OpenRewrite recipes, and which require human judgment or manual work?
4. Do applied, reviewed recipes improve the selected architecture metrics without changing the analysis thresholds?
5. Can the full experiment be reproduced from recorded inputs, configuration, commands, and artifacts?

## 3. Meaning of God Component

A God Component is a top-level component that accumulates disproportionate responsibilities, size, or dependencies relative to the rest of the system. Detection criteria and thresholds will be fixed before baseline analysis, stored with the experiment artifacts, and reused unchanged after refactoring. The final implementation must distinguish metric-based detection from explanatory interpretation.

## 4. Meaning of Unstable Dependency

An Unstable Dependency is a dependency in which a more stable component depends on a less stable component, contrary to the Stable Dependencies Principle. Component instability is derived from afferent and efferent coupling. The exact comparison rule, tolerance, exclusions, and thresholds will be declared before baseline analysis and held constant through after-analysis.

## 5. Component granularity

A component is a top-level Java package immediately below `com.dsarp.shop`.

Examples include:

- `com.dsarp.shop.ordercore`
- `com.dsarp.shop.megacomponent`
- `com.dsarp.shop.experimentalpromotions`

Subpackages belong to their top-level component. Therefore, `com.dsarp.shop.megacomponent.payment` belongs to the component `com.dsarp.shop.megacomponent`. Analysis must normalize classes and subpackages to this component boundary before calculating component-level metrics.

## 6. Blind-analysis protocol

Ground truth will be authored and stored separately from detector inputs. During blind detection, the analyzer and the person or agent operating it must not read architecture ground truth. Detector configuration, smell definitions, thresholds, exclusions, and input revision will be frozen before execution. Baseline findings will be written to `analysis/baseline/`; ground-truth comparison will occur only afterward in `analysis/ground-truth-evaluation/`. Any accidental disclosure invalidates the blind run and must be recorded before rerunning from a clean, documented state.

## 7. Refactoring recommendation protocol

Detected candidates will be converted into recommendations by deterministic logic using recorded metrics and stable tie-breaking rules. Each recommendation will identify the smell, affected components, supporting evidence, proposed target state, expected metric effect, confidence or rank rationale, constraints, and validation steps. Ranked results will be stored in `analysis/recommendations/`. LLM-generated explanations may improve readability but must not set ranks, select transformations, or produce machine-control decisions.

## 8. OpenRewrite automation boundaries

Only transformations with explicit, reviewable preconditions and semantics suitable for OpenRewrite will be automated. Declarative recipes are preferred for composable, configuration-driven changes; imperative recipes may be used when source-aware logic is necessary. Every transformation must preserve type attribution and produce a reviewable diff. Recipe plans belong in `analysis/recipe-plan/`, and dry-run output belongs in `analysis/dry-run/`. `rewrite:run` must never execute until a dry run has succeeded and been reviewed. Ambiguous architectural decisions, responsibility allocation, and transformations lacking sufficient semantic evidence remain manual boundaries. LLM text must never directly control recipe execution.

## 9. Validation strategy

Validation will cover repository structure, deterministic analyzer outputs, unit and integration tests, compilation, type attribution, recipe-specific tests, and dry-run diff review. After approved recipes are applied, the same tests and architecture analysis will run again with identical smell thresholds. Results in `analysis/applied/` and `analysis/after/` will be compared with the baseline. Failures must be reported; tests must not be removed, skipped silently, or weakened merely to obtain a passing build.

## 10. Reproducibility requirements

The experiment must record source revision, tool and runtime versions, dependency versions, configuration, random seeds where relevant, thresholds, commands, command results, timestamps, recipe identifiers, and generated artifacts. Algorithms producing data consumed by OpenRewrite must be deterministic, including stable ordering and tie-breaking. Generated artifacts must remain separate from source code. A future automation entry point should recreate each stage without relying on undocumented local state.

## 11. Expected final dashboard

The future Vercel-hosted dashboard is expected to explain the protocol and show the benchmark architecture, baseline metrics and smells, ranked recommendations, ground-truth evaluation, recipe plans, reviewed dry-run diffs, applied changes, and before/after comparisons. It should expose provenance and configuration so that visual summaries remain traceable to versioned artifacts. The dashboard is a presentation layer and must not alter analysis or transformation decisions.

## 12. Threats to validity

Threats include a synthetic benchmark that may not represent industrial systems; definitions and thresholds that favor the constructed smells; limited smell types; coupling measurements that omit runtime or reflective dependencies; errors in ground truth; operator bias during recommendation review; transformations whose apparent metric gains do not improve maintainability; OpenRewrite type-attribution limitations; and results tied to particular Java, build-tool, or library versions. Blind detection, unchanged thresholds, explicit exclusions, negative cases, deterministic outputs, complete command records, and transparent before/after artifacts will mitigate but cannot eliminate these threats.
