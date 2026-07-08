from __future__ import annotations

from typing import TYPE_CHECKING

from online_shopping.domain.enums.shipment_status import ShipmentStatus
from online_shopping.domain.value_objects.shipment_values import EstimatedArrival, ShipmentDate, ShipmentMethod

if TYPE_CHECKING:
    from online_shopping.domain.entities.shipment_log import ShipmentLog


class Shipment:
    # 创建发货实体，并建立发货信息和发货日志之间的关系。
    def __init__(
        self,
        shipment_date: ShipmentDate,
        estimated_arrival: EstimatedArrival,
        shipment_method: ShipmentMethod,
        shipment_logs: list[ShipmentLog] | None = None,
    ):
        self.__shipment_date = shipment_date
        self.__estimated_arrival = estimated_arrival
        self.__shipment_method = shipment_method
        self.__shipment_logs = shipment_logs or []

    # 添加发货日志，后续应记录发货状态变化和通知信息。
    def add_shipment_log(self) -> bool:
        pass
