package com.dsarp.shop.model;

/** Outbound notification; validated at its construction boundary. */
public record NotificationMessage(String recipient, String subject, String body) {
    public NotificationMessage {
        if (recipient == null || subject == null || body == null) {
            throw new IllegalArgumentException("Invalid NotificationMessage");
        }
    }
}
