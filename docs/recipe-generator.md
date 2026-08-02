# OpenRewrite recipe generator

`tools/generate_openrewrite_recipes.py` is a data-only compiler from the validated recipe plan to an OpenRewrite declarative YAML recipe. It requires Python 3.10 or newer and does not inspect or modify Java source, invoke Maven, or run OpenRewrite.

## Setup

Create an isolated environment and install the pinned runtime dependencies:

```text
python3 -m venv .venv-recipe-generator
.venv-recipe-generator/bin/python -m pip install -r tools/requirements-recipe-generator.txt
```

## Usage

```text
python tools/generate_openrewrite_recipes.py \
  --input analysis/recipe-plan/recipe_plan.json \
  --output rewrite-generated.yml \
  --report analysis/recipe-plan/recipe_generation_report.json \
  --strict
```

The complete JSON document is validated before YAML generation. JSON Schema rejects unexpected plan and operation fields. A second validation layer rejects duplicate IDs, conflicting package moves, invalid package and recipe names, unknown recipes, missing parameters, extra parameters, and values of the wrong type.

The allow-list is defined in `SUPPORTED_RECIPES`. Parameters are emitted in its canonical order, after operations are sorted by `(execution_order, operation_id)`. YAML is serialized with `yaml.safe_dump`, UTF-8, Unix newlines, explicit document start, and stable formatting. Only structured `options` values enter `recipeList`; rationale, evidence, rollback descriptions, and validation commands never do.

`MANUAL_REFACTORING` and `REJECTED_UNSAFE` entries are excluded and recorded in the report. A `CUSTOM_IMPERATIVE_RECIPE` is emitted only as its fully qualified recipe class name, only when `verified_recipe_source` names an existing local `.jar` or `.class` artifact relative to the input plan. The generator never creates that implementation.

Strict mode exits non-zero and does not write YAML when validation fails or when any unsupported, ambiguous, unverified, manual, or rejected operation exists. The report is still written. Without `--strict`, explicitly manual/rejected operations and custom recipes with missing artifacts are skipped and reported; structural or allow-list violations remain fatal.

The current validated plan deliberately retains rejected alternatives and an unsupported manual operation. Consequently, strict validation is expected to fail. A non-strict invocation can produce the seven validated declarative package moves while retaining all exclusions in the generation report.

## Tests

```text
python -m unittest discover -s tests/python -p 'test_*.py' -v
```

The input and output digests in the report are SHA-256 hashes of the exact bytes read and emitted. The generation timestamp is the sole time-dependent report field; recipe YAML is byte-for-byte deterministic.
