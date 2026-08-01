package com.dsarp.shop.architecture;

import com.dsarp.shop.experimentalpromotions.api.DiscountPolicy;
import com.dsarp.shop.megacomponent.payment.PaymentCoordinator;
import com.dsarp.shop.ordercore.OrderSubmissionService;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

/** Observations document the benchmark state; intentional smells are not test failures. */
class IntentionalArchitectureObservationTest {
    @Test
    void orderCoreConstructorExposesIntentionalVolatileContractDependency() {
        assertThat(OrderSubmissionService.class.getConstructors()[0].getParameterTypes())
                .containsExactly(DiscountPolicy.class);
    }

    @Test
    void megacomponentResponsibilityRemainsUnderSingleTopLevelComponent() {
        assertThat(PaymentCoordinator.class.getPackageName())
                .startsWith("com.dsarp.shop.megacomponent.");
    }
}
