# Ground-Truth Evaluation

This evaluation compares the frozen blind baseline and frozen recommendations against the subsequently released ground truth. No thresholds or baseline artifacts were changed.

## Matching rules

- **detection exact:** Normalized smell type and affected component set are equal.
- **detection partial:** Normalized smell type is equal and affected component sets overlap but are not equal.
- **false positive:** A detected finding has no exact or partial ground-truth match.
- **false negative:** A ground-truth smell has no exact or partial detected finding.
- **recommendation exact:** Finding matches, expected destination package matches, expected responsibility/type matches, and the operation directly implements the intended boundary.
- **recommendation partial:** Finding and destination match but expected representative symbols or responsibility evidence are incomplete.
- **semantic alternative:** The intended destination and responsibility match, with a behavior-preserving alternative such as retaining a delegating facade.
- **incorrect:** The recommendation does not match an expected destination/responsibility for its finding.
- **unsafe:** The recommendation matches semantically but has a rejection reason or HIGH architecture risk.
- **unautomatable valid:** The recommendation is exact/partial/alternative but is explicitly non-automatable.
- **symbol overlap:** Set overlap of normalized simple names from recommendation source_symbols against all explicit ground-truth affected_symbols.
- **package overlap:** Set overlap of recommendation target_package values against normalized expected destination packages.

## Detection accuracy

- True positives: **1**
- False positives: **0**
- False negatives: **1**
- Precision: **1.000000**
- Recall: **0.500000**
- F1: **0.666667**
- Top-1 accuracy: **0.500000**
- Top-3 accuracy: **0.500000**
- Mean reciprocal rank: **0.500000**

### Matched findings

- `GC::megacomponent` → `GC-001`: **exact match**, rank 1; detected and expected components: `megacomponent`.

### Unmatched findings (false positives)

- None.

### Missed intentional smells (false negatives)

- `UD-001` (Unstable Dependency): Measured instability difference 0.047619 did not satisfy the unchanged condition I(source) + 0.20 < I(target).

### Detected versus expected affected packages

- Matched: `com.dsarp.shop.megacomponent.audit, com.dsarp.shop.megacomponent.inventory, com.dsarp.shop.megacomponent.notification, com.dsarp.shop.megacomponent.payment, com.dsarp.shop.megacomponent.promotion, com.dsarp.shop.megacomponent.reporting, com.dsarp.shop.megacomponent.validation`
- Expected but undetected: `com.dsarp.shop.experimentalpromotions.adapters, com.dsarp.shop.experimentalpromotions.api, com.dsarp.shop.experimentalpromotions.engine, com.dsarp.shop.experimentalpromotions.rules, com.dsarp.shop.ordercore`
- Detected but unexpected: `none`
- Package precision/recall/F1: **1.000000 / 0.583333 / 0.736842**

## Recommendation quality

- Exact matches: **7**
- Partial matches: **0**
- Semantically valid alternatives: **5**
- Incorrect recommendations: **0**
- Unsafe recommendations: **0**
- Unautomatable but valid recommendations: **0**
- Top-1 valid recommendation accuracy: **1.000000**
- Top-3 valid recommendation accuracy: **1.000000**

The seven direct responsibility-group moves exactly match the seven expected God Component destinations. Five façade-preserving variants are semantically valid alternatives at those same measured boundaries. The highest-ranked recommendation targets the reporting responsibility group, which is one of the intentional groups.

No recommendation targets the misplaced abstraction because its Unstable Dependency smell was missed during frozen blind detection.

### Detected versus expected destination packages

- Matched: `com.dsarp.shop.audit, com.dsarp.shop.inventory, com.dsarp.shop.notification, com.dsarp.shop.payment, com.dsarp.shop.promotion, com.dsarp.shop.reporting, com.dsarp.shop.validation`
- Expected but absent: `com.dsarp.shop.contracts.promotion`
- Detected but unexpected: `none`
- Package precision/recall/F1: **1.000000 / 0.875000 / 0.933333**

### Recommendation symbol overlap

- Explicit expected symbols covered: `AuditEventWriter, InventoryReservationService, NotificationComposer, OrderValidationCoordinator, PaymentCoordinator, PromotionEvaluator, SalesReportGenerator`
- Explicit expected symbols missed: `DiscountPolicy, OrderPricingService, OrderSubmissionService`
- Symbol precision/recall/F1/Jaccard: **0.142857 / 0.700000 / 0.237288 / 0.134615**

Symbol precision is deliberately low because recommendations move complete seven-class responsibility groups while ground truth lists representative symbols rather than every class. Package overlap is the more meaningful boundary-level measure.

## Limitations

- The benchmark contains only two intentional smells, so aggregate metrics have high variance.
- Detection top-k accuracy treats each expected smell as one query and assigns zero reciprocal rank to misses.
- Ground-truth affected symbols are representative, so set precision penalizes valid additional group members.
- The semantic analyzer measured the intended unstable edge, but component-level instability did not cross the preconfigured margin.
- Recommendation evaluation cannot credit an abstraction relocation that was never generated.
