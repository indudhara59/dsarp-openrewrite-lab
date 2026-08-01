package com.dsarp.shop.model;

/** Customer profile; validated at its construction boundary. */
public record CustomerProfile(CustomerId id, EmailAddress email, String tier) {
    public CustomerProfile {
        if (id == null || email == null || tier == null) {
            throw new IllegalArgumentException("Invalid CustomerProfile");
        }
    }
}
