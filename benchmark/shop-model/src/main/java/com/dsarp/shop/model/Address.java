package com.dsarp.shop.model;

/** Postal address; validated at its construction boundary. */
public record Address(String line1, String city, String postalCode, String country) {
    public Address {
        if (line1 == null || city == null || postalCode == null || country == null) {
            throw new IllegalArgumentException("Invalid Address");
        }
    }
}
