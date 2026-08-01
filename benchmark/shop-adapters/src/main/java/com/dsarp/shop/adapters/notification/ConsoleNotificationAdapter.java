package com.dsarp.shop.adapters.notification;

import com.dsarp.shop.megacomponent.notification.NotificationComposer;
import com.dsarp.shop.model.CapabilityDecision;
import com.dsarp.shop.model.OrderContext;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** In-memory console notification adapter for reproducible local scenarios. */
public final class ConsoleNotificationAdapter {
    private final NotificationComposer policy;
    private final List<String> journal = new ArrayList<>();

    public ConsoleNotificationAdapter(NotificationComposer policy) {
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
