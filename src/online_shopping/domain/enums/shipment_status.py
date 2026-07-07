from enum import Enum


class ShipmentStatus(str, Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    ON_HOLD = "on_hold"

    Pending = PENDING
    Shipped = SHIPPED
    Delivered = DELIVERED
    OnHold = ON_HOLD
