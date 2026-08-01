package com.dsarp.shop.experimentalpromotions.adapters;

import com.dsarp.shop.model.OrderContext;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class RemoteCampaignSnapshotAdapterTest {
    @Test
    void calculatesBoundedRepeatableDiscount() {
        OrderContext context = new OrderContext("P-8", "C-8", new BigDecimal("200.00"),
                2, "DE", Instant.parse("2026-01-15T10:00:00Z"), Map.of());
        RemoteCampaignSnapshotAdapter policy = new RemoteCampaignSnapshotAdapter();
        assertThat(policy.discountFor(context)).isEqualByComparingTo(policy.discountFor(context));
        assertThat(policy.discountFor(context)).isBetween(BigDecimal.ZERO, context.subtotal());
        assertThat(policy.policyName()).isEqualTo("RemoteCampaignSnapshotAdapter");
        assertThat(policy.cohortCount()).isEqualTo(3);
    }
}
