from __future__ import annotations

from online_shopping.domain.entities.shopping_cart import ShoppingCart

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from online_shopping.domain.entities.order import Order
    from online_shopping.domain.interfaces.search import Search


class Customer:
    # 创建客户实体，并建立客户与购物车、订单、搜索能力之间的关系。
    def __init__(
        self,
        shopping_cart: ShoppingCart,
        orders: list[Order] | None = None,
        search: Search | None = None,
    ):
        self.__shopping_cart = shopping_cart
        self.__orders = orders or []
        self.__search = search

    # 返回客户当前购物车，后续可用于购物车查看和结算。
    def get_shopping_cart(self) -> ShoppingCart:
        return self.__shopping_cart
