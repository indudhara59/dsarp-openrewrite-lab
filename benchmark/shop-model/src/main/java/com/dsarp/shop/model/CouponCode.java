package com.dsarp.shop.model;

/** Normalized coupon code; validated at its construction boundary. */
public record CouponCode(String value) {
    public CouponCode {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Invalid CouponCode");
        }
    }
}
