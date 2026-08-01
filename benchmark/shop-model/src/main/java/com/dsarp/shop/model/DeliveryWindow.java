package com.dsarp.shop.model;

/** Delivery time window; validated at its construction boundary. */
public record DeliveryWindow(java.time.Instant startsAt, java.time.Instant endsAt) {
    public DeliveryWindow {
        if (startsAt == null || endsAt == null || !endsAt.isAfter(startsAt)) {
            throw new IllegalArgumentException("Invalid DeliveryWindow");
        }
    }
}
