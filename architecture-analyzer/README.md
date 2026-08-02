# Semantic Architecture Analyzer

This deterministic Java 17 CLI analyzes compiled production bytecode under `com.dsarp.shop`. It does not read benchmark ground truth. Class-file constant-pool entries and JVM descriptors/signatures provide resolved class-to-class dependencies; source is consulted only for module, file, package, and LOC attribution.

## Build and test

```sh
architecture-analyzer/mvnw -f architecture-analyzer/pom.xml clean verify
```

## Analyze the benchmark

Compile the benchmark first, then run from the repository root:

```sh
benchmark/mvnw -f benchmark/pom.xml clean package
java -jar architecture-analyzer/target/architecture-analyzer-1.0.0.jar analyze --project benchmark --output analysis/raw --strict
java -jar architecture-analyzer/target/architecture-analyzer-1.0.0.jar validate --output analysis/raw --schemas architecture-analyzer/schemas
```

Strict mode exits nonzero when unresolved internal symbols exceed 1% of all internal symbol references. Output rows, dependency sets, cluster members, tokens, evidence, and identifiers are sorted deterministically. Timestamps and environment metadata naturally vary between executions.

Generated JSON and CSV artifacts are written only to the requested analysis directory. Schema files are versioned under `schemas/`.
