package com.dsarp.shop.application;

import com.dsarp.shop.model.CapabilityDecision;
import com.dsarp.shop.model.OrderContext;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Map;

/** Demonstrates creation through validation, inventory, promotion, payment, notification and audit. */
public final class ShopApplication {
    private ShopApplication() { }

    public static void main(String[] args) {
        OrderContext order = new OrderContext("ORDER-1001", "CUSTOMER-42",
                new BigDecimal("149.90"), 3, "DE", Instant.parse("2026-01-15T10:00:00Z"),
                Map.of("promotion", "flash-sale", "payment", "card", "audit", "required"));
        List<CapabilityDecision> decisions = new OrderWorkflow().execute(order);
        System.out.println("dsarp shop benchmark demonstration");
        decisions.forEach(decision -> System.out.println(decision.summary()));
        if (decisions.size() != 7) {
            throw new IllegalStateException("Workflow did not execute every expected stage");
        }
    }
}
