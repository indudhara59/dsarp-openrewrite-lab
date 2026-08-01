package com.dsarp.shop.adapters.repository;

import com.dsarp.shop.megacomponent.validation.OrderValidationCoordinator;
import com.dsarp.shop.model.CapabilityDecision;
import com.dsarp.shop.model.OrderContext;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** In-memory in memory order repository for reproducible local scenarios. */
public final class InMemoryOrderRepository {
    private final OrderValidationCoordinator policy;
    private final List<String> journal = new ArrayList<>();

    public InMemoryOrderRepository(OrderValidationCoordinator policy) {
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
        return "repository";
    }

    public void clear() {
        journal.clear();
    }
}
