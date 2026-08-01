package com.dsarp.shop.adapters.delivery;

import com.dsarp.shop.megacomponent.notification.DeliveryUpdateNotifier;
import com.dsarp.shop.model.CapabilityDecision;
import com.dsarp.shop.model.OrderContext;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** In-memory in memory delivery gateway for reproducible local scenarios. */
public final class InMemoryDeliveryGateway {
    private final DeliveryUpdateNotifier policy;
    private final List<String> journal = new ArrayList<>();

    public InMemoryDeliveryGateway(DeliveryUpdateNotifier policy) {
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
        return "delivery";
    }

    public void clear() {
        journal.clear();
    }
}
