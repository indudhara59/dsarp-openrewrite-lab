package com.dsarp.shop.ordercore;

import com.dsarp.shop.experimentalpromotions.rules.FlashSaleDiscountPolicy;
import com.dsarp.shop.model.OrderContext;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class OrderStateMachineTest {
    @Test
    void preservesOrderInvariantWhileConsultingDiscountPolicy() {
        OrderContext context = new OrderContext("CORE-14", "C-14", new BigDecimal("75.00"),
                1, "DE", Instant.parse("2026-01-15T10:00:00Z"), Map.of());
        OrderStateMachine service = new OrderStateMachine(new FlashSaleDiscountPolicy());
        assertThat(service.accepts(context)).isTrue();
        assertThat(service.payableAmount(context)).isBetween(BigDecimal.ZERO, context.subtotal());
        assertThat(service.decide(context).evidence()).containsKey("policy");
        assertThat(service.policyDependency()).isEqualTo("FlashSaleDiscountPolicy");
    }
}
