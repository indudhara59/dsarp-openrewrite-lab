package com.dsarp.shop.adapters.payment;

import com.dsarp.shop.megacomponent.payment.PaymentRiskAssessor;
import com.dsarp.shop.model.CapabilityDecision;
import com.dsarp.shop.model.OrderContext;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** In-memory deterministic fraud gateway for reproducible local scenarios. */
public final class DeterministicFraudGateway {
    private final PaymentRiskAssessor policy;
    private final List<String> journal = new ArrayList<>();

    public DeterministicFraudGateway(PaymentRiskAssessor policy) {
        this.policy = Objects.requireNonNull(policy, "policy");
    }

    public CapabilityDecision process(OrderContext context) {
        CapabilityDecision decision = policy.evaluate(context);
        journal.add(context.orderId() + ":" + decision.summary());
        return decision;
    }

    public List<String> journal() {
        return List.copyOf(journal);
    }

    public int processedCount() {
        return journal.size();
    }

    public String adapterKind() {
        return "payment";
    }

    public void clear() {
        journal.clear();
    }
}
