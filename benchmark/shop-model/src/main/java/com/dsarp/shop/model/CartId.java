package com.dsarp.shop.model;

/** Shopping cart identifier; validated at its construction boundary. */
public record CartId(String value) {
    public CartId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Invalid CartId");
        }
    }
}
