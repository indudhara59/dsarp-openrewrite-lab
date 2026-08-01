package com.dsarp.shop.megacomponent.reporting;

import com.dsarp.shop.model.CapabilityDecision;
import com.dsarp.shop.model.OrderContext;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class DeliveryPerformanceReporterTest {
    @Test
    void producesExplainableDeterministicDecision() {
        OrderContext context = new OrderContext("O-35", "C-35", new BigDecimal("135.50"),
                1, "DE", Instant.parse("2026-01-15T10:00:00Z"), Map.of());
        DeliveryPerformanceReporter service = new DeliveryPerformanceReporter();
        CapabilityDecision first = service.evaluate(context);
        CapabilityDecision second = service.evaluate(context);
        assertThat(first).isEqualTo(second);
        assertThat(first.capability()).isEqualTo("DeliveryPerformanceReporter");
        assertThat(first.reasons()).isNotEmpty();
        assertThat(first.evidence()).containsKeys("orderId", "threshold");
        assertThat(service.supports(context)).isTrue();
        assertThat(service.configuredThreshold()).isBetween(0, 100);
    }
}
