from dataclasses import dataclass

from .address import BillingAddress
from .product_values import CurrencyCode


@dataclass(frozen=True)
class CardNumber:
    value: str

    def __post_init__(self) -> None:
        digits = self.value.replace(" ", "")
        if not digits.isdigit() or not 13 <= len(digits) <= 19:
            raise ValueError("Card number must contain 13 to 19 digits.")
        object.__setattr__(self, "value", digits)


@dataclass(frozen=True)
class SecurityCode:
    value: str

    def __post_init__(self) -> None:
        if not self.value.isdigit() or len(self.value) not in (3, 4):
            raise ValueError("Security code must contain 3 or 4 digits.")


Code = SecurityCode


@dataclass(frozen=True)
class BankName:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Bank name cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
class RoutingNumber:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Routing number cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
class AccountNumber:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Account number cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
class Amount:
    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.value, (int, float)) or self.value <= 0:
            raise ValueError("Amount must be greater than zero.")
        object.__setattr__(self, "value", float(round(self.value, 2)))


PaymentCurrencyCode = CurrencyCode


@dataclass(frozen=True)
class PaymentId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Payment ID cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
class TransactionId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Transaction ID cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
class PaymentProvider:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Payment provider cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())

__all__ = [
    "AccountNumber",
    "Amount",
    "BankName",
    "BillingAddress",
    "CardNumber",
    "Code",
    "PaymentCurrencyCode",
    "PaymentId",
    "PaymentProvider",
    "RoutingNumber",
    "SecurityCode",
    "TransactionId",
]
