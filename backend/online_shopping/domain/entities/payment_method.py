from __future__ import annotations

from typing import TYPE_CHECKING

from online_shopping.domain.enums.payment_method_type import PaymentMethodType

if TYPE_CHECKING:
    from online_shopping.domain.entities.credit_card import CreditCard
    from online_shopping.domain.entities.electronic_bank_transfer import (
        ElectronicBankTransfer,
    )


class PaymentMethod:
    def __init__(
        self,
        method_type: PaymentMethodType,
        credit_card: CreditCard | None = None,
        electronic_bank_transfer: ElectronicBankTransfer | None = None,
    ) -> None:
        self.__method_type = method_type
        self.__credit_card = credit_card
        self.__electronic_bank_transfer = electronic_bank_transfer

    @property
    def method_type(self) -> PaymentMethodType:
        return self.__method_type
