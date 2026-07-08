from online_shopping.domain.entities.order import Order


class OrderService:
    # 提交订单用例入口，后续应编排订单校验、库存扣减和支付流程。
    def place_order(self, order: Order) -> Order:
        return order
