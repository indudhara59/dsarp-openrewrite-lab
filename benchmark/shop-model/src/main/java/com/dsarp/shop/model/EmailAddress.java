package com.dsarp.shop.model;

/** Customer email address; validated at its construction boundary. */
public record EmailAddress(String value) {
    public EmailAddress {
        if (value == null || !value.contains("@")) {
            throw new IllegalArgumentException("Invalid EmailAddress");
        }
    }
}
