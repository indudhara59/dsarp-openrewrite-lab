package com.dsarp.shop.model;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.Map;
import java.util.Objects;

/** Immutable facts carried through the benchmark order workflow. */
public record OrderContext(
        String orderId,
        String customerId,
        BigDecimal subtotal,
        int itemCount,
        String destinationCountry,
        Instant submittedAt,
        Map<String, String> attributes) {
    public OrderContext {
        Objects.requireNonNull(orderId, "orderId");
        Objects.requireNonNull(customerId, "customerId");
        Objects.requireNonNull(subtotal, "subtotal");
        Objects.requireNonNull(destinationCountry, "destinationCountry");
        Objects.requireNonNull(submittedAt, "submittedAt");
        attributes = Map.copyOf(attributes);
        if (subtotal.signum() < 0 || itemCount < 0) {
            throw new IllegalArgumentException("Order totals cannot be negative");
        }
    }

    public String attribute(String key, String fallback) {
        return attributes.getOrDefault(key, fallback);
    }

    public boolean isInternational() {
        return !"DE".equalsIgnoreCase(destinationCountry);
    }
}
