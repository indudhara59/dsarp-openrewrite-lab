package com.dsarp.shop.model;

/** Delivery identifier; validated at its construction boundary. */
public record DeliveryId(String value) {
    public DeliveryId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Invalid DeliveryId");
        }
    }
}
