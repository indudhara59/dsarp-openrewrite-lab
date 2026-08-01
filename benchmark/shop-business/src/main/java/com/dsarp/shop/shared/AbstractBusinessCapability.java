package com.dsarp.shop.shared;

import com.dsarp.shop.model.CapabilityDecision;
import com.dsarp.shop.model.OrderContext;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Common mechanics for deterministic benchmark capabilities.
 *
 * <p>The class deliberately limits shared behavior to input validation, bounded scoring, and
 * evidence construction. Concrete services retain ownership of their business thresholds and
 * responsibility-specific decisions. Stable ordering in the evidence map makes demonstrations
 * and future analysis reproducible.</p>
 */
public abstract class AbstractBusinessCapability implements BusinessCapability {
    private final String name;
    private final int threshold;
    private final int weight;

    protected AbstractBusinessCapability(String name, int threshold, int weight) {
        this.name = Objects.requireNonNull(name, "name");
        if (threshold < 0 || threshold > 100) {
            throw new IllegalArgumentException("threshold must be in [0,100]");
        }
        this.threshold = threshold;
        this.weight = weight;
    }

    @Override
    public final String name() {
        return name;
    }

    protected final int threshold() {
        return threshold;
    }

    protected final int weight() {
        return weight;
    }

    protected final int bounded(int value) {
        return Math.max(0, Math.min(100, value));
    }

    protected int baseScore(OrderContext context) {
        int amountSignal = context.subtotal().remainder(java.math.BigDecimal.valueOf(37)).intValue();
        int itemSignal = Math.min(25, context.itemCount() * 3);
        int customerSignal = Math.floorMod(context.customerId().hashCode(), 17);
        return bounded(35 + amountSignal + itemSignal + customerSignal + weight);
    }

    protected abstract List<String> reasons(OrderContext context, int score);

    protected Map<String, String> evidence(OrderContext context, int score) {
        Map<String, String> facts = new LinkedHashMap<>();
        facts.put("orderId", context.orderId());
        facts.put("customerId", context.customerId());
        facts.put("itemCount", Integer.toString(context.itemCount()));
        facts.put("subtotal", context.subtotal().toPlainString());
        facts.put("country", context.destinationCountry());
        facts.put("score", Integer.toString(score));
        facts.put("threshold", Integer.toString(threshold));
        return Map.copyOf(facts);
    }

    @Override
    public CapabilityDecision evaluate(OrderContext context) {
        Objects.requireNonNull(context, "context");
        int score = baseScore(context);
        return new CapabilityDecision(name, score >= threshold, score, reasons(context, score),
                evidence(context, score));
    }
}
