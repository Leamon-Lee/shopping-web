from __future__ import annotations

from typing import TYPE_CHECKING

from online_shopping.domain.enums.account_status import AccountStatus
from online_shopping.domain.value_objects.account_values import Password, Username
from online_shopping.domain.value_objects.address import Address
from online_shopping.domain.value_objects.customer_values import Email, Name, Phone

if TYPE_CHECKING:
    from online_shopping.domain.entities.credit_card import CreditCard
    from online_shopping.domain.entities.electronic_bank_transfer import (
        ElectronicBankTransfer,
    )


class Account:
    def __init__(
        self,
        user_name: Username,
        password: Password,
        status: AccountStatus,
        name: Name,
        shipping_address: Address,
        email: Email,
        phone: Phone,
        credit_card: CreditCard | None = None,
        electronic_bank_transfer: ElectronicBankTransfer | None = None,
    ) -> None:
        self.__user_name = user_name
        self.__password = password
        self.__status = status
        self.__name = name
        self.__shipping_address = shipping_address
        self.__email = email
        self.__phone = phone
        self.__credit_card = credit_card
        self.__electronic_bank_transfer = electronic_bank_transfer

    def __repr__(self) -> str:
        return f"Account(user_name={self.__user_name}, status={self.__status}, name={self.__name})"

    @property
    def status(self) -> AccountStatus:
        return self.__status

    def block(self) -> None:
        self.__status = AccountStatus.BLOCKED

    def get_shipping_address(self) -> Address:
        return self.__shipping_address
