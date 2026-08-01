package com.dsarp.shop.model;

/** Immutable order line; validated at its construction boundary. */
public record OrderLine(ProductId productId, int quantity, Money unitPrice) {
    public OrderLine {
        if (productId == null || quantity <= 0 || unitPrice == null) {
            throw new IllegalArgumentException("Invalid OrderLine");
        }
    }
}
