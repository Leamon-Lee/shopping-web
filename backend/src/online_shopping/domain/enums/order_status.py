from enum import Enum


class OrderStatus(str, Enum):
    UNSHIPPED = "unshipped"
    PENDING = "pending"
    SHIPPED = "shipped"
    COMPLETE = "complete"
    CANCELED = "canceled"
    REFUND_APPLIED = "refund_applied"

    Unshipped = UNSHIPPED
    Pending = PENDING
    Shipped = SHIPPED
    Complete = COMPLETE
    Canceled = CANCELED
    RefundApplied = REFUND_APPLIED
