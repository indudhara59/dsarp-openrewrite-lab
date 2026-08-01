package com.dsarp.shop.ordercore;

import com.dsarp.shop.experimentalpromotions.api.DiscountPolicy;
import com.dsarp.shop.model.CapabilityDecision;
import com.dsarp.shop.model.OrderContext;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Stable order-domain service that deliberately imports the volatile DiscountPolicy contract. */
public final class OrderLifecycleService {
    private final DiscountPolicy discountPolicy;

    public OrderLifecycleService(DiscountPolicy discountPolicy) {
        this.discountPolicy = Objects.requireNonNull(discountPolicy, "discountPolicy");
    }

    public CapabilityDecision decide(OrderContext context) {
        Objects.requireNonNull(context, "context");
        BigDecimal discount = discountPolicy.discountFor(context);
        BigDecimal payable = context.subtotal().subtract(discount).max(BigDecimal.ZERO);
        int score = Math.max(0, Math.min(100, 100 - payable.remainder(BigDecimal.valueOf(39)).intValue()));
        return new CapabilityDecision("OrderLifecycleService", context.itemCount() > 0, score,
                List.of("stable order invariant evaluated", "volatile discount policy consulted"),
                Map.of("policy", discountPolicy.policyName(), "discount", discount.toPlainString(),
                        "payable", payable.toPlainString()));
    }

    public BigDecimal payableAmount(OrderContext context) {
        return context.subtotal().subtract(discountPolicy.discountFor(context)).max(BigDecimal.ZERO);
    }

    public String policyDependency() {
        return discountPolicy.policyName();
    }

    public boolean accepts(OrderContext context) {
        return context.itemCount() > 0 && payableAmount(context).signum() >= 0;
    }

    /** Produces a stable receipt for downstream components using this order-core behavior. */
    public Map<String, String> receipt(OrderContext context) {
        CapabilityDecision decision = decide(context);
        return Map.of(
                "service", "OrderLifecycleService",
                "order", context.orderId(),
                "policy", policyDependency(),
                "payable", payableAmount(context).toPlainString(),
                "accepted", Boolean.toString(decision.accepted()));
    }

    /** Explains stable invariants separately from volatile policy details. */
    public List<String> invariantEvidence(OrderContext context) {
        return List.of(
                "order identifier present=" + !context.orderId().isBlank(),
                "positive item count=" + (context.itemCount() > 0),
                "non-negative payable=" + (payableAmount(context).signum() >= 0));
    }

    /** Applies the same deterministic decision to an ordered batch. */
    public List<CapabilityDecision> decideAll(List<OrderContext> contexts) {
        return contexts.stream().map(this::decide).toList();
    }

    /** Signals cases close enough to the boundary to merit human review. */
    public boolean requiresReview(OrderContext context) {
        CapabilityDecision decision = decide(context);
        return !decision.accepted() || decision.score() < 55;
    }

    /** Creates an application-facing status without leaking implementation objects. */
    public String status(OrderContext context) {
        if (!accepts(context)) {
            return "rejected";
        }
        return requiresReview(context) ? "review" : "ready";
    }

    /** Stable key used by reporting and audit components. */
    public String capabilityKey() {
        return "ordercore.OrderLifecycleService";
    }

}
