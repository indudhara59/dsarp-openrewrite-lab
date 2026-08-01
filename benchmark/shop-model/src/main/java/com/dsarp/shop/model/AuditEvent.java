package com.dsarp.shop.model;

/** Auditable business event; validated at its construction boundary. */
public record AuditEvent(String eventType, String aggregateId, java.time.Instant occurredAt) {
    public AuditEvent {
        if (eventType == null || aggregateId == null || occurredAt == null) {
            throw new IllegalArgumentException("Invalid AuditEvent");
        }
    }
}
