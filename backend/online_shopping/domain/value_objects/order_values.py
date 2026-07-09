from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OrderId:
    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or self.value <= 0:
            raise ValueError("Order ID must be a positive integer.")


@dataclass(frozen=True)
class OrderNumber:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Order number cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
class DisplayOrderId:
    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or self.value <= 0:
            raise ValueError("Display order ID must be a positive integer.")


@dataclass(frozen=True)
class OrderItemId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Order item ID cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
class OrderDate:
    value: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.value, datetime):
            raise TypeError("Order date must be a datetime.")


@dataclass(frozen=True)
class CreationDate:
    value: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.value, datetime):
            raise TypeError("Creation date must be a datetime.")
