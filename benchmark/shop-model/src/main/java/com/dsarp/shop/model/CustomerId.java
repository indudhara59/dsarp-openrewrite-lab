package com.dsarp.shop.model;

/** Customer identifier; validated at its construction boundary. */
public record CustomerId(String value) {
    public CustomerId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Invalid CustomerId");
        }
    }
}
