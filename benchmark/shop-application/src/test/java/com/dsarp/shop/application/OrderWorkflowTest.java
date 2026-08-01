package com.dsarp.shop.application;

import com.dsarp.shop.model.OrderContext;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class OrderWorkflowTest {
    @Test
    void executesAllSevenOrderStagesInOrder() {
        OrderContext context = new OrderContext("DEMO", "CUSTOMER", new BigDecimal("99.00"),
                2, "DE", Instant.parse("2026-01-15T10:00:00Z"), Map.of());
        assertThat(new OrderWorkflow().execute(context)).hasSize(7)
                .extracting(decision -> decision.capability())
                .containsExactly("OrderSubmissionService", "OrderValidationCoordinator",
                        "InventoryReservationService", "PromotionEvaluator",
                        "PaymentAuthorizationService", "OrderConfirmationNotifier", "AuditEventWriter");
    }
}
