from __future__ import annotations

from typing import TYPE_CHECKING

from online_shopping.domain.enums.shipment_status import ShipmentStatus
from online_shopping.domain.value_objects.order_values import CreationDate

if TYPE_CHECKING:
    from online_shopping.domain.entities.notification import Notification


class ShipmentLog:
    # 创建发货日志，保存物流状态、记录时间和相关通知。
    def __init__(
        self,
        status: ShipmentStatus,
        creation_date: CreationDate,
    ):
        self.__status = status
        self.__creation_date = creation_date

    def trigger_notifications(self, notifications: list[Notification]) -> tuple[Notification, ...]:
        for notification in notifications:
            notification.send_notification()
        return tuple(notifications)
