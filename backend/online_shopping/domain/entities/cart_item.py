from __future__ import annotations

from online_shopping.domain.entities.product_variant import ProductVariant
from online_shopping.domain.value_objects.product_values import Price, Quantity
from online_shopping.domain.value_objects.store_values import CartItemId


class CartItem:
    def __init__(
        self,
        quantity: Quantity,
        product_variant: ProductVariant,
        price: Price | None = None,
        item_id: CartItemId | None = None,
    ) -> None:
        self.__item_id = item_id
        self.__product_variant = product_variant
        self.__quantity = quantity
        self.__price = price or product_variant.price

    @property
    def item_id(self) -> CartItemId | None:
        return self.__item_id

    @property
    def product_variant(self) -> ProductVariant:
        return self.__product_variant

    @property
    def quantity(self) -> Quantity:
        return self.__quantity

    @property
    def price(self) -> Price:
        return self.__price

    @property
    def subtotal(self) -> float:
        return round(self.__price.value * self.__quantity.value, 2)

    def update_quantity(self, quantity: Quantity) -> bool:
        if not self.__product_variant.is_available(quantity.value):
            return False
        self.__quantity = quantity
        return True
