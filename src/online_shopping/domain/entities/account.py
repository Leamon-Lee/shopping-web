from __future__ import annotations

from typing import TYPE_CHECKING

from online_shopping.domain.enums.account_status import AccountStatus
from online_shopping.domain.value_objects.account_values import Password, Username
from online_shopping.domain.value_objects.address import Address
from online_shopping.domain.value_objects.customer_values import Email, Name, Phone

if TYPE_CHECKING:
    from online_shopping.domain.entities.admin import Admin
    from online_shopping.domain.entities.credit_card import CreditCard
    from online_shopping.domain.entities.electronic_bank_transfer import ElectronicBankTransfer
    from online_shopping.domain.entities.member import Member


class Account:
    # 创建账户实体，并建立账户与支付方式、会员、管理员之间的关系。
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
        members: list[Member] | None = None,
        admins: list[Admin] | None = None,
    ):
        self.__user_name = user_name
        self.__password = password
        self.__status = status
        self.__name = name
        self.__shipping_address = shipping_address
        self.__email = email
        self.__phone = phone
        self.__credit_card = credit_card
        self.__electronic_bank_transfer = electronic_bank_transfer
        self.__members = members or []
        self.__admins = admins or []

    # 返回账户保存的收货地址，后续可用于下单和配送流程。
    def get_shipping_address(self) -> Address:
        return self.__shipping_address

    # 为账户添加商品评价，后续应校验账户权限、商品是否可评价以及评价内容。
    def add_product_review(self) -> bool:
        pass

    # 通过账户添加新商品，后续应校验账户角色、商品信息和分类关系。
    def add_product(self) -> bool:
        pass
