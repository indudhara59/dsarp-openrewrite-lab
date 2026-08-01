# Intentional Architecture Smells

This benchmark contains exactly two deliberately engineered architecture smells. They must remain intact until a later, explicitly authorized refactoring phase.

## GC-001: God Component

`com.dsarp.shop.megacomponent` contains 49 production classes split into seven internally cohesive subpackages: validation, payment, inventory, notification, reporting, audit, and promotion. Application and adapter behavior depends heavily on these services, while the services consume shared model and capability abstractions. The subpackages create realistic future move boundaries but remain one component under the experiment definition.

The anticipated future destinations are `com.dsarp.shop.validation`, `payment`, `inventory`, `notification`, `reporting`, `audit`, and `promotion`. No move occurs in the benchmark-construction phase.

## UD-001: Unstable Dependency

Stable domain services in `com.dsarp.shop.ordercore` directly import `com.dsarp.shop.experimentalpromotions.api.DiscountPolicy`. The latter contract is owned by a volatile component with replaceable policies and dependencies on catalog, customer, configuration, utilities/time, model, and experimental adapter concepts.

The anticipated future contract location is `com.dsarp.shop.contracts.promotion.DiscountPolicy`, yielding `ordercore -> contracts.promotion <- experimentalpromotions`. The current direct edge is intentional.

The machine-readable ground truth is segregated at `benchmark-ground-truth/architecture-ground-truth.json`; production resources and code do not contain or read it.
