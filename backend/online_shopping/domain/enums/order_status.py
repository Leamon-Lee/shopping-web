from enum import Enum


class OrderStatus(str, Enum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELED = "canceled"

    Created = CREATED
    Confirmed = CONFIRMED
    Processing = PROCESSING
    Shipped = SHIPPED
    Completed = COMPLETED
    Canceled = CANCELED
