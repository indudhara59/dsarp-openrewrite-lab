package com.dsarp.shop.model;

/** Payment identifier; validated at its construction boundary. */
public record PaymentId(String value) {
    public PaymentId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Invalid PaymentId");
        }
    }
}
