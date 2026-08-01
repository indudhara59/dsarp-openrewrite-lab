package com.dsarp.shop.shared;

import com.dsarp.shop.model.CapabilityDecision;
import com.dsarp.shop.model.OrderContext;

/** Contract shared by the benchmark's independently testable business capabilities. */
public interface BusinessCapability {
    String name();
    CapabilityDecision evaluate(OrderContext context);
}
