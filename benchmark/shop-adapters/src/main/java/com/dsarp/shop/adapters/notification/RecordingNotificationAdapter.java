package com.dsarp.shop.adapters.notification;

import com.dsarp.shop.megacomponent.notification.OrderConfirmationNotifier;
import com.dsarp.shop.model.CapabilityDecision;
import com.dsarp.shop.model.OrderContext;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** In-memory recording notification adapter for reproducible local scenarios. */
public final class RecordingNotificationAdapter {
    private final OrderConfirmationNotifier policy;
    private final List<String> journal = new ArrayList<>();

    public RecordingNotificationAdapter(OrderConfirmationNotifier policy) {
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
        return "notification";
    }

    public void clear() {
        journal.clear();
    }
}
