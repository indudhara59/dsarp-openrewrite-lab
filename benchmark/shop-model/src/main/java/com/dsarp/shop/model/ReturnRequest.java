package com.dsarp.shop.model;

/** Customer return request; validated at its construction boundary. */
public record ReturnRequest(ReturnId returnId, OrderId orderId, String reason) {
    public ReturnRequest {
        if (returnId == null || orderId == null || reason == null || reason.isBlank()) {
            throw new IllegalArgumentException("Invalid ReturnRequest");
        }
    }
}
