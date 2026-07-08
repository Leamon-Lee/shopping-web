from __future__ import annotations

from typing import TYPE_CHECKING

from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.value_objects.order_values import OrderDate, OrderNumber

if TYPE_CHECKING:
    from online_shopping.domain.entities.item import Item
    from online_shopping.domain.entities.order_log import OrderLog
    from online_shopping.domain.entities.payment import Payment
    from online_shopping.domain.entities.shipment import Shipment


class Order:
    # 创建订单实体，并建立订单与商品项、日志、发货和支付之间的关系。
    def __init__(
        self,
        order_number: OrderNumber,
        status: OrderStatus = OrderStatus.PENDING,
        order_date: OrderDate | None = None,
        items: list[Item] | None = None,
        order_logs: list[OrderLog] | None = None,
        shipments: list[Shipment] | None = None,
        payment: Payment | None = None,
    ):
        self.__order_number = order_number
        self.__status = status
        self.__order_date = order_date
        self.__items = items or []
        self.__order_logs = order_logs or []
        self.__shipments = shipments or []
        self.__payment = payment

    # 返回订单号，后续可用于订单查询和对外展示。
    @property
    def order_number(self) -> OrderNumber:
        return self.__order_number

    # 返回订单状态，后续可用于订单流转和页面展示。
    @property
    def status(self) -> OrderStatus:
        return self.__status

    # 将订单送入发货流程，后续应校验支付状态并创建发货记录。
    def send_for_shipment(self) -> bool:
        pass
