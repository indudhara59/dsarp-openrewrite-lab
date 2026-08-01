# Benchmark Module Structure

The Maven reactor has five modules and no module cycle:

- `shop-model` owns immutable domain values and has no reactor dependency.
- `shop-business` depends on model and contains business components, including both intentional smells.
- `shop-adapters` depends on model and business and supplies in-memory boundaries.
- `shop-application` depends on model, business, and adapters and composes use cases.
- `shop-architecture-tests` depends on all four application modules and records architecture observations without failing merely because intentional smells exist.

Maven modules are build boundaries, not architecture-analysis components. A component is the first package segment immediately below `com.dsarp.shop`, irrespective of module. For example, every `com.dsarp.shop.megacomponent.*` package belongs to `megacomponent`.

This layout permits `ordercore` and `experimentalpromotions` to coexist in `shop-business`. Their deliberate Java-package dependency is observable without creating a Maven dependency cycle.
