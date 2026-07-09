from __future__ import annotations

from typing import TYPE_CHECKING

from online_shopping.domain.entities.account import Account
from online_shopping.domain.entities.shopping_cart import ShoppingCart

if TYPE_CHECKING:
    from online_shopping.domain.entities.order import Order
    from online_shopping.domain.entities.product import Product
    from online_shopping.domain.entities.product_review import ProductReview


class Customer:
    def __init__(
        self,
        account: Account,
        shopping_cart: ShoppingCart,
        orders: list[Order] | None = None,
        product_reviews: list[ProductReview] | None = None,
    ) -> None:
        self.__account = account
        self.__shopping_cart = shopping_cart
        self.__orders = orders or []
        self.__product_reviews = product_reviews or []

    @property
    def account(self) -> Account:
        return self.__account

    @property
    def orders(self) -> tuple[Order, ...]:
        return tuple(self.__orders)

    @property
    def product_reviews(self) -> tuple[ProductReview, ...]:
        return tuple(self.__product_reviews)

    def get_shopping_cart(self) -> ShoppingCart:
        return self.__shopping_cart

    def place_order(self) -> Order:
        if not self.__orders:
            raise ValueError("No order has been prepared for this customer.")
        return self.__orders[-1]

    def add_product_review(self, product: Product) -> ProductReview:
        from online_shopping.domain.entities.product_review import ProductReview
        from online_shopping.domain.value_objects.product_values import Rating, ReviewContent

        product_review = ProductReview(
            rating=Rating(5),
            review=ReviewContent("Customer review pending content."),
            product=product,
        )
        self.__product_reviews.append(product_review)
        return product_review
