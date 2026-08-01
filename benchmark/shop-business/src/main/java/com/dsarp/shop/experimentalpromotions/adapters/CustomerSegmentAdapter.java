package com.dsarp.shop.experimentalpromotions.adapters;

import com.dsarp.shop.catalog.ProductPricingService;
import com.dsarp.shop.configuration.FeatureConfigurationService;
import com.dsarp.shop.customer.CustomerTierService;
import com.dsarp.shop.experimentalpromotions.api.DiscountPolicy;
import com.dsarp.shop.model.OrderContext;
import com.dsarp.shop.utilities.BusinessClockService;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.ZoneOffset;
import java.util.Objects;

/** Replaceable experimental policy with volatile catalog, customer, time and configuration inputs. */
public final class CustomerSegmentAdapter implements DiscountPolicy {
    private static final BigDecimal RATE = new BigDecimal("0.05");
    private final ProductPricingService pricing = new ProductPricingService();
    private final CustomerTierService tiers = new CustomerTierService();
    private final FeatureConfigurationService features = new FeatureConfigurationService();
    private final BusinessClockService clock = new BusinessClockService();

    @Override
    public BigDecimal discountFor(OrderContext context) {
        Objects.requireNonNull(context, "context");
        int variant = Math.floorMod(context.customerId().hashCode() + clock.name().hashCode(), 3);
        boolean eligible = pricing.supports(context) && tiers.supports(context)
                && features.supports(context) && context.subtotal().signum() > 0;
        if (!eligible) {
            return BigDecimal.ZERO;
        }
        BigDecimal variantRate = RATE.add(BigDecimal.valueOf(variant, 2));
        return context.subtotal().multiply(variantRate).setScale(2, RoundingMode.HALF_UP);
    }

    @Override
    public String policyName() {
        return "CustomerSegmentAdapter";
    }

    public ZoneOffset experimentZone() {
        return ZoneOffset.UTC;
    }

    public int cohortCount() {
        return 3;
    }
}
