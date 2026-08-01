package com.dsarp.shop.model;

/** Order identifier; validated at its construction boundary. */
public record OrderId(String value) {
    public OrderId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Invalid OrderId");
        }
    }
}
