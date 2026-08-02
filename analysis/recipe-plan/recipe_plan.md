# OpenRewrite Automation Plan

Composite recipe: `org.dsarp.architecture.RefactorBenchmarkArchitecture`

This is a non-executing plan. No recipe, dry run, or source refactoring was applied.

## Classification counts

- `DECLARATIVE_BUILT_IN`: **7**
- `CUSTOM_IMPERATIVE_RECIPE`: **0**
- `MANUAL_REFACTORING`: **0**
- `REJECTED_UNSAFE`: **5**

## Ordered operations

| Order | Operation | Recommendation | Class | Recipe | Package mapping | Types | Risk |
|---:|---|---|---|---|---|---:|---|
| 30 | `OP::e5f4488bb0575987` | `REC::c0750f828761f1b8` | `DECLARATIVE_BUILT_IN` | `org.openrewrite.java.ChangePackage` | `com.dsarp.shop.megacomponent.reporting` → `com.dsarp.shop.reporting` | 7 | MEDIUM |
| 31 | `OP::21ef7e62564af116` | `REC::c9924540cef8e8d9` | `DECLARATIVE_BUILT_IN` | `org.openrewrite.java.ChangePackage` | `com.dsarp.shop.megacomponent.promotion` → `com.dsarp.shop.promotion` | 7 | MEDIUM |
| 32 | `OP::74f6005d410bbfdf` | `REC::7460ee4622a5a8ce` | `DECLARATIVE_BUILT_IN` | `org.openrewrite.java.ChangePackage` | `com.dsarp.shop.megacomponent.audit` → `com.dsarp.shop.audit` | 7 | MEDIUM |
| 33 | `OP::a3580c2d7e10f349` | `REC::1b2ed2a730bc0213` | `DECLARATIVE_BUILT_IN` | `org.openrewrite.java.ChangePackage` | `com.dsarp.shop.megacomponent.inventory` → `com.dsarp.shop.inventory` | 7 | MEDIUM |
| 34 | `OP::1c15037279cc9a59` | `REC::6e8aa33dd0e98f53` | `DECLARATIVE_BUILT_IN` | `org.openrewrite.java.ChangePackage` | `com.dsarp.shop.megacomponent.validation` → `com.dsarp.shop.validation` | 7 | MEDIUM |
| 35 | `OP::33520fe2e8208b9c` | `REC::d065451d7c12a381` | `DECLARATIVE_BUILT_IN` | `org.openrewrite.java.ChangePackage` | `com.dsarp.shop.megacomponent.payment` → `com.dsarp.shop.payment` | 7 | MEDIUM |
| 36 | `OP::e25c0ecb47d797ce` | `REC::aa203f303dd39ffa` | `DECLARATIVE_BUILT_IN` | `org.openrewrite.java.ChangePackage` | `com.dsarp.shop.megacomponent.notification` → `com.dsarp.shop.notification` | 7 | MEDIUM |
| 37 | `OP::e80f2952b9ee81da` | `REC::b85da629cd93b795` | `REJECTED_UNSAFE` | `none` | not scheduled | 7 | HIGH |
| 38 | `OP::deee60495b59c81c` | `REC::77fffd4123157d96` | `REJECTED_UNSAFE` | `none` | not scheduled | 7 | HIGH |
| 39 | `OP::5c0580356e55bb06` | `REC::cbc8265e8dc3acc0` | `REJECTED_UNSAFE` | `none` | not scheduled | 7 | HIGH |
| 40 | `OP::5154d9cb685c23a6` | `REC::e48585444f55d1c1` | `REJECTED_UNSAFE` | `none` | not scheduled | 7 | HIGH |
| 41 | `OP::70c7378d610c49d5` | `REC::c045b5a4696a8cdb` | `REJECTED_UNSAFE` | `none` | not scheduled | 7 | HIGH |

## Stable abstraction assessment

The evaluation contains an unmatched expected stable-abstraction unit, but the frozen blind pipeline emitted no accepted recommendation for it. Therefore it is not scheduled in the composite recipe.

The mechanical package mapping from `com.dsarp.shop.experimentalpromotions.api` to `com.dsarp.shop.contracts.promotion` is compatible with the documented `ChangePackage` options. Semantic analysis finds the ordercore callers, experimental implementations, and application wiring, all in `shop-business`. Nevertheless, executing that move would bypass recommendation validation, so it remains a manual planning gap.

If a later authorized recommendation validates it, it must run before responsibility-group moves and must prove:

- `ordercore -> contracts.promotion` exists.
- `experimentalpromotions -> contracts.promotion` exists.
- `ordercore -> experimentalpromotions` no longer exists.
- exactly one `DiscountPolicy` declaration exists.
- application composition still compiles and tests pass.

## Dependency and module assessment

All scheduled package moves remain within `shop-business`; no POM dependency change is scheduled. The ChangeDependency/AddDependency/RemoveDependency recipes were verified but are deliberately unused. Simulating all seven executable moves produced no component cycle and no symbol overlap.

## Safety gate

The five façade-preserving alternatives conflict with higher-ranked direct moves over the same groups and lack a precise facade contract. They are classified `REJECTED_UNSAFE`, are absent from the executable composite, and require a future explicit strategy decision.
