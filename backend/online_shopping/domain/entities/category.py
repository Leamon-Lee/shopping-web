from __future__ import annotations

from typing import TYPE_CHECKING

from online_shopping.domain.value_objects.product_values import (
    CategoryDescription,
    CategoryId,
    CategoryName,
    CategorySlug,
)

if TYPE_CHECKING:
    from online_shopping.domain.entities.product import Product


class Category:
    def __init__(
        self,
        name: CategoryName,
        description: CategoryDescription,
        category_id: CategoryId | None = None,
        slug: CategorySlug | None = None,
        products: list[Product] | None = None,
    ) -> None:
        self.__category_id = category_id
        self.__name = name
        self.__description = description
        self.__slug = slug or CategorySlug.from_name(name)
        self.__products = products or []

    @property
    def category_id(self) -> CategoryId | None:
        return self.__category_id

    @property
    def name(self) -> CategoryName:
        return self.__name

    @property
    def description(self) -> CategoryDescription:
        return self.__description

    @property
    def slug(self) -> CategorySlug:
        return self.__slug

    @property
    def products(self) -> tuple[Product, ...]:
        return tuple(self.__products)

    def classify_product(self, product: Product) -> Product:
        self.__products.append(product)
        return product
