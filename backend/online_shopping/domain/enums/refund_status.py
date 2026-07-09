from enum import Enum


class RefundStatus(str, Enum):
    NONE = "none"
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    REFUNDED = "refunded"

    None_ = NONE
    Requested = REQUESTED
    Approved = APPROVED
    Rejected = REJECTED
    Refunded = REFUNDED
