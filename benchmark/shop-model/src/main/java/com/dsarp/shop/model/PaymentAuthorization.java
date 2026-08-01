package com.dsarp.shop.model;

/** Payment authorization result; validated at its construction boundary. */
public record PaymentAuthorization(PaymentId paymentId, boolean approved, String providerReference) {
    public PaymentAuthorization {
        if (paymentId == null || providerReference == null) {
            throw new IllegalArgumentException("Invalid PaymentAuthorization");
        }
    }
}
