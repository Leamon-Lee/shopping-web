from online_shopping.domain.entities.payment import Payment


class PaymentService:
    # 处理支付用例入口，后续应调用 Payment 或具体支付渠道完成支付。
    def process_payment(self, payment: Payment) -> Payment:
        return payment
