# Benchmark Domain

The benchmark models an e-commerce and order-processing platform. Immutable values in `shop-model` describe customers, products, carts, orders, money, inventory, payments, delivery, promotions, notifications, audit events, returns, and sales snapshots. Business behavior covers customer management, catalog browsing and pricing, cart decisions, stable order processing, inventory, payment, delivery, promotions, notifications, reporting, auditing, fraud assessment, returns, configuration, and shared utilities.

All external boundaries are deterministic and in memory. Repositories retain local journals, payment and fraud adapters calculate from supplied facts, notification adapters record messages, and the application composes them without a database, cloud service, Docker daemon, network service, credential, or secret.

`ShopApplication` provides a representative order scenario. An immutable order context moves through stable order submission, validation, reservation, promotion, authorization, confirmation notification, and audit. Capability decisions retain scores, reasons, and ordered evidence so tests can assert behavior and later experiment stages can explain observations.
