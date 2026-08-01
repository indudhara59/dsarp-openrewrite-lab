# Build and Run

## Prerequisites

- A Java 17 JDK available through `JAVA_HOME` or `PATH`.
- `curl` and `unzip` for the Maven Wrapper's first Maven 3.9.9 bootstrap.
- Python 3.9 or newer for the size report.

No database, Docker daemon, cloud account, running network service, credential, or secret is required. The first Maven invocation requires access to Maven Central to obtain Maven and pinned dependencies; subsequent runs may use the local Maven cache.

## Commands from the repository root

```sh
benchmark/mvnw -f benchmark/pom.xml clean verify
java -cp benchmark/shop-model/target/classes:benchmark/shop-business/target/classes:benchmark/shop-adapters/target/classes:benchmark/shop-application/target/classes com.dsarp.shop.application.ShopApplication
python3 scripts/count_benchmark_size.py
```

## Commands from `benchmark/`

```sh
./mvnw clean verify
java -cp shop-model/target/classes:shop-business/target/classes:shop-adapters/target/classes:shop-application/target/classes com.dsarp.shop.application.ShopApplication
../scripts/count_benchmark_size.py
```

`clean verify` compiles all production sources, runs all module tests, and executes the architecture-observation suite. Architecture observations assert that the controlled smells are present; they do not fail merely because those smells exist.
