from __future__ import annotations

from typing import TYPE_CHECKING

from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.value_objects.order_values import CreationDate

if TYPE_CHECKING:
    from online_shopping.domain.entities.notification import Notification


class OrderLog:
    # 创建订单日志，保存状态变更时间、订单状态和相关通知。
    def __init__(
        self,
        creation_date: CreationDate,
        status: OrderStatus,
        notifications: list[Notification] | None = None,
    ):
        self.__creation_date = creation_date
        self.__status = status
        self.__notifications = notifications or []
