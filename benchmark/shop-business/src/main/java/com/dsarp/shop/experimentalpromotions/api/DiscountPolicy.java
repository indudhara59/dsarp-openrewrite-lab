package com.dsarp.shop.experimentalpromotions.api;

import com.dsarp.shop.model.OrderContext;
import java.math.BigDecimal;

/** Volatile promotion contract intentionally consumed directly by the stable order core. */
public interface DiscountPolicy {
    BigDecimal discountFor(OrderContext context);
    String policyName();
}
