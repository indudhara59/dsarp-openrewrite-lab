package com.dsarp.shop.model;

/** Catalog product identifier; validated at its construction boundary. */
public record ProductId(String value) {
    public ProductId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Invalid ProductId");
        }
    }
}
