from __future__ import annotations

from typing import TYPE_CHECKING

from online_shopping.domain.entities.account import Account

if TYPE_CHECKING:
    from online_shopping.domain.entities.product import Product
    from online_shopping.domain.entities.product_approval import ProductApproval
    from online_shopping.domain.entities.shop import Shop


class Manager:
    def __init__(
        self,
        account: Account,
        managed_shops: list[Shop] | None = None,
    ) -> None:
        self.__account = account
        self.__managed_shops = managed_shops or []

    @property
    def account(self) -> Account:
        return self.__account

    @property
    def managed_shops(self) -> tuple[Shop, ...]:
        return tuple(self.__managed_shops)

    def add_shop(self, shop: Shop) -> Shop:
        self.__managed_shops.append(shop)
        return shop

    def request_product_approval(self, shop: Shop, product: Product) -> ProductApproval:
        from online_shopping.domain.entities.product_approval import ProductApproval

        return ProductApproval(product=product, shop=shop, manager=self)

    def confirm_product_approval(self, approval: ProductApproval) -> bool:
        return approval.confirm(self)

    def list_shop_products(self, shop: Shop) -> tuple[Product, ...]:
        return shop.products
