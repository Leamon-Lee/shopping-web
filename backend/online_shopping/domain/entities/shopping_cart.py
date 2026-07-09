from online_shopping.domain.entities.cart_item import CartItem
from online_shopping.domain.value_objects.product_values import CurrencyCode
from online_shopping.domain.value_objects.store_values import (
    CartId,
    CartItemId,
    CustomerEmail,
    LocaleCode,
    RegionId,
)


class ShoppingCart:
    def __init__(
        self,
        items: list[CartItem] | None = None,
        cart_id: CartId | None = None,
        region_id: RegionId | None = None,
        currency_code: CurrencyCode = CurrencyCode("cny"),
        email: CustomerEmail | None = None,
        locale: LocaleCode | None = None,
    ) -> None:
        self.__cart_id = cart_id
        self.__region_id = region_id
        self.__currency_code = currency_code
        self.__email = email
        self.__locale = locale
        self.__items = items or []

    @property
    def cart_id(self) -> CartId | None:
        return self.__cart_id

    @property
    def region_id(self) -> RegionId | None:
        return self.__region_id

    @property
    def currency_code(self) -> CurrencyCode:
        return self.__currency_code

    @property
    def email(self) -> CustomerEmail | None:
        return self.__email

    @property
    def locale(self) -> LocaleCode | None:
        return self.__locale

    @property
    def items(self) -> tuple[CartItem, ...]:
        return tuple(self.__items)

    @property
    def total_quantity(self) -> int:
        return sum(item.quantity.value for item in self.__items)

    @property
    def subtotal(self) -> float:
        return round(sum(item.subtotal for item in self.__items), 2)

    def add_item(self, item: CartItem) -> bool:
        if not item.product_variant.is_available(item.quantity.value):
            return False
        existing_item = next(
            (
                cart_item
                for cart_item in self.__items
                if cart_item.product_variant.variant_id.value
                == item.product_variant.variant_id.value
            ),
            None,
        )
        if existing_item:
            return existing_item.update_quantity(
                type(item.quantity)(existing_item.quantity.value + item.quantity.value)
            )
        self.__items.append(item)
        return True

    def remove_item(self, item_id: CartItemId) -> bool:
        before_count = len(self.__items)
        self.__items = [
            item
            for item in self.__items
            if item.item_id is None or item.item_id.value != item_id.value
        ]
        return len(self.__items) != before_count

    def get_items(self) -> list[CartItem]:
        return list(self.__items)
