from __future__ import annotations

from typing import TYPE_CHECKING

from online_shopping.domain.value_objects.store_values import ShopId, ShopName

if TYPE_CHECKING:
    from online_shopping.domain.entities.category import Category
    from online_shopping.domain.entities.manager import Manager
    from online_shopping.domain.entities.product import Product


class Shop:
    def __init__(
        self,
        name: ShopName,
        manager: Manager,
        shop_id: ShopId | None = None,
        products: list[Product] | None = None,
    ) -> None:
        self.__shop_id = shop_id
        self.__name = name
        self.__manager = manager
        self.__products = products or []

    @property
    def shop_id(self) -> ShopId | None:
        return self.__shop_id

    @property
    def name(self) -> ShopName:
        return self.__name

    @property
    def manager(self) -> Manager:
        return self.__manager

    @property
    def products(self) -> tuple[Product, ...]:
        return tuple(self.__products)

    def assign_manager(self, manager: Manager) -> Manager:
        self.__manager = manager
        return manager

    def add_approved_product(self, product: Product) -> Product:
        self.__products.append(product)
        return product

    def update_product(self, product: Product) -> Product:
        product_id = product.product_id
        if product_id is None:
            return product
        for index, existing_product in enumerate(self.__products):
            if (
                existing_product.product_id is not None
                and existing_product.product_id.value == product_id.value
            ):
                self.__products[index] = product
                break
        return product

    def remove_product(self, product: Product) -> bool:
        product_id = product.product_id
        before_count = len(self.__products)
        self.__products = [
            existing_product
            for existing_product in self.__products
            if product_id is None
            or existing_product.product_id is None
            or existing_product.product_id.value != product_id.value
        ]
        return len(self.__products) != before_count

    def uses_category(self, category: Category) -> bool:
        return any(product.category.slug.value == category.slug.value for product in self.__products)
