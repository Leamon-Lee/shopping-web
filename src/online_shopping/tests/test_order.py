from online_shopping.domain.entities.order import Order
from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.value_objects.order_values import OrderId


def test_order_defaults_to_pending() -> None:
    assert Order(OrderId(1)).status == OrderStatus.PENDING
