package com.dsarp.shop.application;

import com.dsarp.shop.experimentalpromotions.rules.FlashSaleDiscountPolicy;
import com.dsarp.shop.megacomponent.audit.AuditEventWriter;
import com.dsarp.shop.megacomponent.inventory.InventoryReservationService;
import com.dsarp.shop.megacomponent.notification.OrderConfirmationNotifier;
import com.dsarp.shop.megacomponent.payment.PaymentAuthorizationService;
import com.dsarp.shop.megacomponent.promotion.PromotionEvaluator;
import com.dsarp.shop.megacomponent.validation.OrderValidationCoordinator;
import com.dsarp.shop.model.CapabilityDecision;
import com.dsarp.shop.model.OrderContext;
import com.dsarp.shop.ordercore.OrderSubmissionService;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Composes the deliberately broad benchmark workflow without hiding component dependencies. */
public final class OrderWorkflow {
    private final OrderValidationCoordinator validation = new OrderValidationCoordinator();
    private final InventoryReservationService inventory = new InventoryReservationService();
    private final PromotionEvaluator promotion = new PromotionEvaluator();
    private final PaymentAuthorizationService payment = new PaymentAuthorizationService();
    private final OrderConfirmationNotifier notification = new OrderConfirmationNotifier();
    private final AuditEventWriter audit = new AuditEventWriter();
    private final OrderSubmissionService orderCore = new OrderSubmissionService(new FlashSaleDiscountPolicy());

    public List<CapabilityDecision> execute(OrderContext context) {
        Objects.requireNonNull(context, "context");
        List<CapabilityDecision> decisions = new ArrayList<>();
        decisions.add(orderCore.decide(context));
        decisions.add(validation.evaluate(context));
        decisions.add(inventory.evaluate(context));
        decisions.add(promotion.evaluate(context));
        decisions.add(payment.evaluate(context));
        decisions.add(notification.evaluate(context));
        decisions.add(audit.evaluate(context));
        return List.copyOf(decisions);
    }
}
