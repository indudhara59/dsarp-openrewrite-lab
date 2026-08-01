package com.dsarp.shop.megacomponent.inventory;

import com.dsarp.shop.model.CapabilityDecision;
import com.dsarp.shop.model.OrderContext;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class ReservationExpiryServiceTest {
    @Test
    void producesExplainableDeterministicDecision() {
        OrderContext context = new OrderContext("O-20", "C-20", new BigDecimal("120.50"),
                1, "DE", Instant.parse("2026-01-15T10:00:00Z"), Map.of());
        ReservationExpiryService service = new ReservationExpiryService();
        CapabilityDecision first = service.evaluate(context);
        CapabilityDecision second = service.evaluate(context);
        assertThat(first).isEqualTo(second);
        assertThat(first.capability()).isEqualTo("ReservationExpiryService");
        assertThat(first.reasons()).isNotEmpty();
        assertThat(first.evidence()).containsKeys("orderId", "threshold");
        assertThat(service.supports(context)).isTrue();
        assertThat(service.configuredThreshold()).isBetween(0, 100);
    }
}
