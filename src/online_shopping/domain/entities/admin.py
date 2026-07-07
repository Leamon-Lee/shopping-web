from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from online_shopping.domain.entities.account import Account
    from online_shopping.domain.entities.product import Product
    from online_shopping.domain.entities.product_category import ProductCategory

class Admin:
    # 创建管理员实体，并记录管理员账户及其可管理的商品和分类。
    def __init__(
        self,
        account: Account,
        products: list[Product] | None = None,
        product_categories: list[ProductCategory] | None = None,
    ):
        self.__account = account
        self.__products = products or []
        self.__product_categories = product_categories or []

    # 封禁或阻止指定用户，后续应实现状态变更和权限校验。
    def block_user(self) -> bool:
        pass

    # 新增商品分类，后续应校验分类名称唯一性并保存分类。
    def add_new_product_category(self) -> bool:
        pass

    # 修改已有商品分类，后续应校验分类存在并更新分类信息。
    def modify_product_category(self) -> bool:
        pass
