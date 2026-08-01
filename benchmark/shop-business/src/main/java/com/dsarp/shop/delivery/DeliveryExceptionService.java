package com.dsarp.shop.delivery;

import com.dsarp.shop.model.OrderContext;
import com.dsarp.shop.shared.AbstractBusinessCapability;
import java.util.ArrayList;
import java.util.List;

/**
 * Owns the delivery exception service decision within the delivery responsibility.
 *
 * <p>This service is intentionally located in its current top-level component for the academic
 * benchmark. Its decision is deterministic: it combines immutable order facts with explicit
 * thresholds, emits reasons, and never performs network or database access. The small focused
 * API makes this cohesive class suitable for a future package move without performing that move
 * during benchmark construction.</p>
 *
 * <p>Inputs considered are order value, item volume, destination, and responsibility-specific
 * attributes. Output evidence supports behavioral tests and later architecture experiments.</p>
 */
public final class DeliveryExceptionService extends AbstractBusinessCapability {
    private static final int RESPONSIBILITY_THRESHOLD = 51;
    private static final int RESPONSIBILITY_WEIGHT = 5;

    public DeliveryExceptionService() {
        super("DeliveryExceptionService", RESPONSIBILITY_THRESHOLD, RESPONSIBILITY_WEIGHT);
    }

    @Override
    protected int baseScore(OrderContext context) {
        int score = super.baseScore(context);
        int destinationAdjustment = context.isInternational() ? -4 : 3;
        int attributeAdjustment = context.attribute("delivery", "standard").length() % 7;
        return bounded(score + destinationAdjustment + attributeAdjustment);
    }

    @Override
    protected List<String> reasons(OrderContext context, int score) {
        List<String> reasons = new ArrayList<>();
        reasons.add("the delivery policy can make a deterministic decision");
        reasons.add("evaluated " + context.itemCount() + " item(s) for " + context.destinationCountry());
        reasons.add(score >= threshold() ? "responsibility threshold satisfied" : "manual review threshold reached");
        if (context.isInternational()) {
            reasons.add("international handling rules applied");
        }
        return List.copyOf(reasons);
    }

    public boolean supports(OrderContext context) {
        return context.itemCount() > 0 && !context.orderId().isBlank();
    }

    public String responsibility() {
        return "delivery";
    }

    public int configuredThreshold() {
        return RESPONSIBILITY_THRESHOLD;
    }

    /** Returns a human-readable explanation without changing the machine decision. */
    public String explain(OrderContext context) {
        var decision = evaluate(context);
        return "delivery exception service: " + String.join("; ", decision.reasons());
    }

    /** Classifies the deterministic score for application-facing review queues. */
    public String scoreBand(OrderContext context) {
        int score = evaluate(context).score();
        if (score >= 80) {
            return "high";
        }
        if (score >= 55) {
            return "medium";
        }
        return "low";
    }

    /** Identifies the immutable facts required to reproduce this decision. */
    public List<String> requiredEvidence() {
        return List.of("orderId", "customerId", "subtotal", "itemCount", "country", "delivery");
    }

    /** Computes a stable review priority from score distance and order volume. */
    public int reviewPriority(OrderContext context) {
        int distance = Math.abs(evaluate(context).score() - RESPONSIBILITY_THRESHOLD);
        int volume = Math.min(20, context.itemCount() * 2);
        return bounded(100 - distance + volume);
    }

    /** Allows automatic continuation only when support and threshold checks agree. */
    public boolean canContinueAutomatically(OrderContext context) {
        return supports(context) && evaluate(context).accepted() && reviewPriority(context) >= 50;
    }

    /** Documents the operational response expected from a rejected decision. */
    public String reviewInstruction(OrderContext context) {
        if (canContinueAutomatically(context)) {
            return "continue delivery workflow";
        }
        return "review delivery evidence for order " + context.orderId();
    }

    /** Evaluates a batch while preserving caller order for reproducible analysis. */
    public List<com.dsarp.shop.model.CapabilityDecision> evaluateBatch(List<OrderContext> contexts) {
        return contexts.stream().map(this::evaluate).toList();
    }

    /** Produces a compact trace line suitable for the in-memory audit adapters. */
    public String trace(OrderContext context) {
        var decision = evaluate(context);
        return context.orderId() + "|DeliveryExceptionService|" + decision.score() + "|" + decision.accepted();
    }

    /** Reports whether an explicit responsibility attribute influenced evaluation. */
    public boolean hasExplicitConfiguration(OrderContext context) {
        return !"standard".equals(context.attribute("delivery", "standard"));
    }

    /** Exposes a stable capability key for composition and reporting. */
    public String capabilityKey() {
        return "delivery.DeliveryExceptionService";
    }

}
