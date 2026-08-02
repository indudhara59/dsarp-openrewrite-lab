# Recommendation Ranking Formula

Candidate ranking is deterministic and does not use an LLM. Features are bounded to `[0,1]`:

```text
0.30 expected smell reduction
+ 0.20 cohesion (measured cohesion and cluster confidence)
+ 0.10 reference manageability
+ 0.10 low behavior risk
+ 0.10 low package-cycle risk
+ 0.05 low Maven-module-cycle risk
+ 0.10 automation feasibility
+ 0.05 affected-code test coverage
```

No test-coverage table is present in the permitted inputs, so every candidate receives the same neutral `0.50` test-coverage value. This preserves the factor without inventing evidence. Package cycles are checked by remapping the proposed class group in the resolved class graph. Maven cycle risk is zero for package moves that remain in the original module; abstraction relocation candidates check the observed module graph.

Candidates sort by score descending and stable candidate ID ascending. Recommendation IDs are SHA-256-derived from finding ID, refactoring kind, sorted source symbols, target package, and target symbol. Rejected candidates remain in `candidates.*` and are excluded from `recommendations.*`.
