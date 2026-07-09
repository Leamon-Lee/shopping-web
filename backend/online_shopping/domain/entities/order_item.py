from online_shopping.domain.entities.product_variant import ProductVariant
from online_shopping.domain.value_objects.order_values import OrderItemId
from online_shopping.domain.value_objects.product_values import (
    Price,
    ProductVariantId,
    Quantity,
)


class OrderItem:
    def __init__(
        self,
        unit_price: Price,
        quantity: Quantity,
        product_variant: ProductVariant,
        order_item_id: OrderItemId | None = None,
    ) -> None:
        self.__order_item_id = order_item_id
        self.__product_variant = product_variant
        self.__unit_price = unit_price
        self.__quantity = quantity

    @property
    def order_item_id(self) -> OrderItemId | None:
        return self.__order_item_id

    @property
    def product_variant_id(self) -> ProductVariantId:
        return self.__product_variant.variant_id

    @property
    def product_variant(self) -> ProductVariant:
        return self.__product_variant

    @property
    def unit_price(self) -> Price:
        return self.__unit_price

    @property
    def quantity(self) -> Quantity:
        return self.__quantity

    @property
    def subtotal(self) -> float:
        return round(self.__unit_price.value * self.__quantity.value, 2)
