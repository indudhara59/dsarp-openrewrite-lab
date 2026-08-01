package com.dsarp.shop.megacomponent.validation;

import com.dsarp.shop.model.CapabilityDecision;
import com.dsarp.shop.model.OrderContext;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class AddressValidatorTest {
    @Test
    void producesExplainableDeterministicDecision() {
        OrderContext context = new OrderContext("O-2", "C-2", new BigDecimal("102.50"),
                3, "DE", Instant.parse("2026-01-15T10:00:00Z"), Map.of());
        AddressValidator service = new AddressValidator();
        CapabilityDecision first = service.evaluate(context);
        CapabilityDecision second = service.evaluate(context);
        assertThat(first).isEqualTo(second);
        assertThat(first.capability()).isEqualTo("AddressValidator");
        assertThat(first.reasons()).isNotEmpty();
        assertThat(first.evidence()).containsKeys("orderId", "threshold");
        assertThat(service.supports(context)).isTrue();
        assertThat(service.configuredThreshold()).isBetween(0, 100);
    }
}
