# Java Architecture-Smell Benchmark

This Maven reactor is an intentionally poorly architected, fully local e-commerce benchmark for architecture detection and automated-refactoring research. The smells are controlled experimental fixtures, not unfinished cleanup work. Do not refactor them while establishing or measuring the baseline.

The reactor uses Java 17, JUnit 5, AssertJ, pinned Maven plugin/dependency versions, and in-memory adapters. Its five modules are `shop-model`, `shop-business`, `shop-adapters`, `shop-application`, and `shop-architecture-tests`.

From this directory, build and test with:

```sh
./mvnw clean verify
```

Run the deterministic demonstration with:

```sh
java -cp shop-model/target/classes:shop-business/target/classes:shop-adapters/target/classes:shop-application/target/classes com.dsarp.shop.application.ShopApplication
```

The demonstration exercises order creation, validation, inventory reservation, promotion evaluation, payment authorization, notification, and auditing. See `../docs/build-and-run.md` for prerequisites and root-directory equivalents.

Ground truth is deliberately outside this reactor at `../benchmark-ground-truth/architecture-ground-truth.json`. Production code must never read it.
