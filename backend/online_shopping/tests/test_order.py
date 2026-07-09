from online_shopping.domain.entities.order import Order
from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.value_objects.order_values import OrderId, OrderNumber


def test_order_defaults_to_pending() -> None:
    assert Order(OrderId(1)).status == OrderStatus.CREATED


def test_order_accepts_backend_order_number() -> None:
    order = Order(OrderNumber("ORD-1001"), order_id=OrderId(1001))

    assert order.order_number.value == "ORD-1001"
    assert order.order_id == OrderId(1001)
