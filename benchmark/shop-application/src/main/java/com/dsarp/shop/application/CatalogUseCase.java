package com.dsarp.shop.application;

import com.dsarp.shop.model.CapabilityDecision;
import com.dsarp.shop.model.OrderContext;
import java.util.List;
import java.util.Objects;

/** Application boundary for the catalog scenario. */
public final class CatalogUseCase {
    private final OrderWorkflow workflow;

    public CatalogUseCase(OrderWorkflow workflow) {
        this.workflow = Objects.requireNonNull(workflow, "workflow");
    }

    public List<CapabilityDecision> execute(OrderContext context) {
        return workflow.execute(context);
    }
}
