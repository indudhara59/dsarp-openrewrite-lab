# Repository-wide agent instructions

These instructions apply to every future Codex task in this repository.

- Inspect the repository before modifying files.
- Never claim a command passed unless it was actually executed.
- Do not silently bypass failing tests.
- Do not delete tests to make a build pass.
- Do not change smell thresholds between baseline and after-analysis.
- Do not read architecture ground truth during blind detection.
- Use deterministic algorithms for data consumed by OpenRewrite.
- LLM-generated explanations must never directly control code transformations.
- Never run OpenRewrite `rewrite:run` without a successful, reviewed dry run.
- Never push or deploy unless explicitly requested.
- Preserve existing user changes.
- Keep generated analysis artifacts separate from source code.
- Record all relevant commands and results.
