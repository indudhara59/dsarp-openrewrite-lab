# Ranked Blind Refactoring Recommendations

These recommendations are derived only from validated blind detection and semantic dependency data. They do not claim that a rename fixes a smell and do not move an entire God Component as one unit.

## Highest-ranked recommendations

| Rank | ID | Finding | Kind | Responsibility/edge | Target | Score basis |
|---:|---|---|---|---|---|---|
| 1 | `REC::c0750f828761f1b8` | `GC::megacomponent` | MOVE_RESPONSIBILITY_GROUP | `cluster:megacomponent:reporting` | `com.dsarp.shop.reporting` | 0.501714 |
| 2 | `REC::c9924540cef8e8d9` | `GC::megacomponent` | MOVE_RESPONSIBILITY_GROUP | `cluster:megacomponent:promotion` | `com.dsarp.shop.promotion` | 0.499852 |
| 3 | `REC::7460ee4622a5a8ce` | `GC::megacomponent` | MOVE_RESPONSIBILITY_GROUP | `cluster:megacomponent:audit` | `com.dsarp.shop.audit` | 0.498048 |
| 4 | `REC::1b2ed2a730bc0213` | `GC::megacomponent` | MOVE_RESPONSIBILITY_GROUP | `cluster:megacomponent:inventory` | `com.dsarp.shop.inventory` | 0.496295 |
| 5 | `REC::6e8aa33dd0e98f53` | `GC::megacomponent` | MOVE_RESPONSIBILITY_GROUP | `cluster:megacomponent:validation` | `com.dsarp.shop.validation` | 0.496295 |
| 6 | `REC::d065451d7c12a381` | `GC::megacomponent` | MOVE_RESPONSIBILITY_GROUP | `cluster:megacomponent:payment` | `com.dsarp.shop.payment` | 0.496295 |
| 7 | `REC::aa203f303dd39ffa` | `GC::megacomponent` | MOVE_RESPONSIBILITY_GROUP | `cluster:megacomponent:notification` | `com.dsarp.shop.notification` | 0.494589 |
| 8 | `REC::b85da629cd93b795` | `GC::megacomponent` | PRESERVE_FACADE | `cluster:megacomponent:audit` | `com.dsarp.shop.audit` | 0.493048 |
| 9 | `REC::77fffd4123157d96` | `GC::megacomponent` | PRESERVE_FACADE | `cluster:megacomponent:inventory` | `com.dsarp.shop.inventory` | 0.491295 |
| 10 | `REC::cbc8265e8dc3acc0` | `GC::megacomponent` | PRESERVE_FACADE | `cluster:megacomponent:payment` | `com.dsarp.shop.payment` | 0.491295 |

## Why candidates are distinct

- `REC::c0750f828761f1b8` is keyed to `GC::megacomponent`, `MOVE_RESPONSIBILITY_GROUP`, `cluster:megacomponent:reporting`, 7 exact source symbols, and destination `com.dsarp.shop.reporting`.
- `REC::c9924540cef8e8d9` is keyed to `GC::megacomponent`, `MOVE_RESPONSIBILITY_GROUP`, `cluster:megacomponent:promotion`, 7 exact source symbols, and destination `com.dsarp.shop.promotion`.
- `REC::7460ee4622a5a8ce` is keyed to `GC::megacomponent`, `MOVE_RESPONSIBILITY_GROUP`, `cluster:megacomponent:audit`, 7 exact source symbols, and destination `com.dsarp.shop.audit`.
- `REC::1b2ed2a730bc0213` is keyed to `GC::megacomponent`, `MOVE_RESPONSIBILITY_GROUP`, `cluster:megacomponent:inventory`, 7 exact source symbols, and destination `com.dsarp.shop.inventory`.
- `REC::6e8aa33dd0e98f53` is keyed to `GC::megacomponent`, `MOVE_RESPONSIBILITY_GROUP`, `cluster:megacomponent:validation`, 7 exact source symbols, and destination `com.dsarp.shop.validation`.
- `REC::d065451d7c12a381` is keyed to `GC::megacomponent`, `MOVE_RESPONSIBILITY_GROUP`, `cluster:megacomponent:payment`, 7 exact source symbols, and destination `com.dsarp.shop.payment`.
- `REC::aa203f303dd39ffa` is keyed to `GC::megacomponent`, `MOVE_RESPONSIBILITY_GROUP`, `cluster:megacomponent:notification`, 7 exact source symbols, and destination `com.dsarp.shop.notification`.
- `REC::b85da629cd93b795` is keyed to `GC::megacomponent`, `PRESERVE_FACADE`, `cluster:megacomponent:audit`, 7 exact source symbols, and destination `com.dsarp.shop.audit`.
- `REC::77fffd4123157d96` is keyed to `GC::megacomponent`, `PRESERVE_FACADE`, `cluster:megacomponent:inventory`, 7 exact source symbols, and destination `com.dsarp.shop.inventory`.
- `REC::cbc8265e8dc3acc0` is keyed to `GC::megacomponent`, `PRESERVE_FACADE`, `cluster:megacomponent:payment`, 7 exact source symbols, and destination `com.dsarp.shop.payment`.
- `REC::e48585444f55d1c1` is keyed to `GC::megacomponent`, `PRESERVE_FACADE`, `cluster:megacomponent:validation`, 7 exact source symbols, and destination `com.dsarp.shop.validation`.
- `REC::c045b5a4696a8cdb` is keyed to `GC::megacomponent`, `PRESERVE_FACADE`, `cluster:megacomponent:notification`, 7 exact source symbols, and destination `com.dsarp.shop.notification`.

## Rejected candidates

No generated candidate was rejected by package validity or cycle checks.

## Input limitations

- No test-coverage table was provided; ranking uses the documented neutral value.
- If a smell type has no baseline finding, no real recommendation is generated for that type.
- Human-readable rationales are deterministic. Optional local-model text is stored separately and cannot alter operations or ranking.
