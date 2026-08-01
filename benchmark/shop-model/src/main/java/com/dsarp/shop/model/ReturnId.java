package com.dsarp.shop.model;

/** Return identifier; validated at its construction boundary. */
public record ReturnId(String value) {
    public ReturnId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Invalid ReturnId");
        }
    }
}
