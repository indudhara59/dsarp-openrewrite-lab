package com.dsarp.shop.model;

/** Catalog product snapshot; validated at its construction boundary. */
public record ProductSnapshot(ProductId id, String name, Money price, boolean active) {
    public ProductSnapshot {
        if (id == null || name == null || price == null) {
            throw new IllegalArgumentException("Invalid ProductSnapshot");
        }
    }
}
