package com.dsarp.shop.model;

/** Applied promotional adjustment; validated at its construction boundary. */
public record PromotionAdjustment(String source, Money discount) {
    public PromotionAdjustment {
        if (source == null || discount == null) {
            throw new IllegalArgumentException("Invalid PromotionAdjustment");
        }
    }
}
