from __future__ import annotations

from typing import TYPE_CHECKING

from online_shopping.domain.entities.customer import Customer

if TYPE_CHECKING:
    from online_shopping.domain.entities.account import Account


class Member(Customer):
    # 创建注册会员实体，并关联会员账户和客户基础信息。
    def __init__(self, account: Account, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__account = account    
    
    # 提交订单，后续应从购物车生成订单并触发支付或库存校验。
    def place_order(self) -> bool:
        pass
