from __future__ import annotations

from typing import TYPE_CHECKING

from online_shopping.domain.enums.payment_status import PaymentStatus
from online_shopping.domain.value_objects.payment_values import (
    Amount,
    PaymentCurrencyCode,
    PaymentId,
)

if TYPE_CHECKING:
    from online_shopping.domain.entities.payment_method import PaymentMethod
    from online_shopping.domain.entities.payment_transaction import PaymentTransaction


class Payment:
    def __init__(
        self,
        status: PaymentStatus | int = PaymentStatus.PENDING,
        amount: Amount | float | None = None,
        currency: PaymentCurrencyCode | str | None = None,
        payment_id: PaymentId | None = None,
        method: PaymentMethod | None = None,
        transaction: PaymentTransaction | None = None,
    ) -> None:
        if not isinstance(status, PaymentStatus):
            status = PaymentStatus.PENDING
        if isinstance(amount, (int, float)):
            amount = Amount(amount)
        if isinstance(currency, str):
            currency = PaymentCurrencyCode(currency)
        self.__payment_id = payment_id
        self.__status = status
        self.__amount = amount
        self.__currency = currency
        self.__method = method
        self.__transaction = transaction

    @property
    def payment_id(self) -> PaymentId | None:
        return self.__payment_id

    @property
    def amount(self) -> Amount | None:
        return self.__amount

    @property
    def currency(self) -> PaymentCurrencyCode | None:
        return self.__currency

    @property
    def method(self) -> PaymentMethod | None:
        return self.__method

    @property
    def transaction(self) -> PaymentTransaction | None:
        return self.__transaction

    @property
    def status(self) -> PaymentStatus:
        return self.__status

    def process_payment(self) -> PaymentStatus:
        self.__status = PaymentStatus.COMPLETED
        return self.__status
