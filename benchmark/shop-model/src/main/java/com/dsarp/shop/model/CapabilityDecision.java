package com.dsarp.shop.model;

import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Immutable, explainable result from one business capability. */
public record CapabilityDecision(
        String capability,
        boolean accepted,
        int score,
        List<String> reasons,
        Map<String, String> evidence) {
    public CapabilityDecision {
        Objects.requireNonNull(capability, "capability");
        reasons = List.copyOf(reasons);
        evidence = Map.copyOf(evidence);
        if (score < 0 || score > 100) {
            throw new IllegalArgumentException("Score must be between 0 and 100");
        }
    }

    public String summary() {
        return capability + ":" + (accepted ? "accepted" : "rejected") + ":" + score;
    }
}
