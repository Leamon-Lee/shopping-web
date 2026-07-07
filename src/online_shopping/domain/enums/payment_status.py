from enum import Enum


class PaymentStatus(str, Enum):
    UNPAID = "unpaid"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    DECLINED = "declined"
    CANCELED = "canceled"
    ABANDONED = "abandoned"
    SETTLING = "settling"
    SETTLED = "settled"
    REFUNDED = "refunded"

    Unpaid = UNPAID
    Pending = PENDING
    Completed = COMPLETED
    Failed = FAILED
    Declined = DECLINED
    Canceled = CANCELED
    Abandoned = ABANDONED
    Settling = SETTLING
    Settled = SETTLED
    Refunded = REFUNDED
