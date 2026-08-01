package com.dsarp.shop.model;

/** Non-negative monetary value; validated at its construction boundary. */
public record Money(java.math.BigDecimal amount, String currency) {
    public Money {
        if (amount == null || amount.signum() < 0 || currency == null || currency.length() != 3) {
            throw new IllegalArgumentException("Invalid Money");
        }
    }
}
