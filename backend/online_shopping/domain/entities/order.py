from __future__ import annotations

from typing import TYPE_CHECKING

from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.enums.refund_status import RefundStatus
from online_shopping.domain.value_objects.order_values import (
    DisplayOrderId,
    OrderDate,
    OrderId,
    OrderNumber,
)
from online_shopping.domain.value_objects.product_values import CurrencyCode
from online_shopping.domain.value_objects.store_values import CustomerEmail, RegionId

if TYPE_CHECKING:
    from online_shopping.domain.entities.order_item import OrderItem
    from online_shopping.domain.entities.order_log import OrderLog
    from online_shopping.domain.entities.payment import Payment
    from online_shopping.domain.entities.shipment import Shipment


class Order:
    def __init__(
        self,
        order_number: OrderNumber | OrderId,
        status: OrderStatus = OrderStatus.CREATED,
        refund_status: RefundStatus = RefundStatus.NONE,
        order_date: OrderDate | None = None,
        items: list[OrderItem] | None = None,
        order_logs: list[OrderLog] | None = None,
        shipments: list[Shipment] | None = None,
        payment: Payment | None = None,
        order_id: OrderId | None = None,
        display_order_id: DisplayOrderId | None = None,
        email: CustomerEmail | None = None,
        region_id: RegionId | None = None,
        currency_code: CurrencyCode = CurrencyCode("cny"),
    ) -> None:
        if isinstance(order_number, OrderId):
            order_id = order_number
            order_number = OrderNumber(f"ORD-{order_number.value}")
        self.__order_id = order_id
        self.__display_order_id = display_order_id
        self.__order_number = order_number
        self.__status = status
        self.__refund_status = refund_status
        self.__order_date = order_date
        self.__items = items or []
        self.__order_logs = order_logs or []
        self.__shipments = shipments or []
        self.__payment = payment
        self.__email = email
        self.__region_id = region_id
        self.__currency_code = currency_code

    @property
    def order_id(self) -> OrderId | None:
        return self.__order_id

    @property
    def display_order_id(self) -> DisplayOrderId | None:
        return self.__display_order_id

    @property
    def order_number(self) -> OrderNumber:
        return self.__order_number

    @property
    def status(self) -> OrderStatus:
        return self.__status

    @property
    def refund_status(self) -> RefundStatus:
        return self.__refund_status

    @property
    def order_date(self) -> OrderDate | None:
        return self.__order_date

    @property
    def items(self) -> tuple[OrderItem, ...]:
        return tuple(self.__items)

    @property
    def payment(self) -> Payment | None:
        return self.__payment

    @property
    def email(self) -> CustomerEmail | None:
        return self.__email

    @property
    def region_id(self) -> RegionId | None:
        return self.__region_id

    @property
    def currency_code(self) -> CurrencyCode:
        return self.__currency_code

    @property
    def subtotal(self) -> float:
        return round(sum(item.subtotal for item in self.__items), 2)

    def send_for_shipment(self) -> bool:
        if self.__status != OrderStatus.PROCESSING:
            return False
        self.__status = OrderStatus.SHIPPED
        return True
