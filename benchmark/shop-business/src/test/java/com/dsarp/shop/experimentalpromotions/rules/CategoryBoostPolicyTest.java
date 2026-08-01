package com.dsarp.shop.experimentalpromotions.rules;

import com.dsarp.shop.model.OrderContext;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class CategoryBoostPolicyTest {
    @Test
    void calculatesBoundedRepeatableDiscount() {
        OrderContext context = new OrderContext("P-6", "C-6", new BigDecimal("200.00"),
                2, "DE", Instant.parse("2026-01-15T10:00:00Z"), Map.of());
        CategoryBoostPolicy policy = new CategoryBoostPolicy();
        assertThat(policy.discountFor(context)).isEqualByComparingTo(policy.discountFor(context));
        assertThat(policy.discountFor(context)).isBetween(BigDecimal.ZERO, context.subtotal());
        assertThat(policy.policyName()).isEqualTo("CategoryBoostPolicy");
        assertThat(policy.cohortCount()).isEqualTo(3);
    }
}
