package com.dsarp.shop.model;

/** Daily sales summary; validated at its construction boundary. */
public record SalesSnapshot(java.time.LocalDate date, int orders, Money revenue) {
    public SalesSnapshot {
        if (date == null || orders < 0 || revenue == null) {
            throw new IllegalArgumentException("Invalid SalesSnapshot");
        }
    }
}
