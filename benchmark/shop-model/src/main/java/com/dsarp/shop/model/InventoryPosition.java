package com.dsarp.shop.model;

/** Inventory snapshot; validated at its construction boundary. */
public record InventoryPosition(ProductId productId, int available, int reserved) {
    public InventoryPosition {
        if (productId == null || available < 0 || reserved < 0 || reserved > available) {
            throw new IllegalArgumentException("Invalid InventoryPosition");
        }
    }
}
