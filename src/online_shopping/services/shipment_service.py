from online_shopping.domain.entities.shipment import Shipment


class ShipmentService:
    # 发货用例入口，后续应创建发货记录并更新物流状态。
    def ship(self, shipment: Shipment) -> Shipment:
        return shipment
