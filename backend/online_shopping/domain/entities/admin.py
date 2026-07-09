from __future__ import annotations

from typing import TYPE_CHECKING

from online_shopping.domain.entities.account import Account

if TYPE_CHECKING:
    from online_shopping.domain.entities.category import Category
    from online_shopping.domain.entities.shop import Shop


class Admin:
    def __init__(
        self,
        account: Account,
        shops: list[Shop] | None = None,
        categories: list[Category] | None = None,
    ) -> None:
        self.__account = account
        self.__shops = shops or []
        self.__categories = categories or []

    @property
    def account(self) -> Account:
        return self.__account

    def block_user(self, account: Account) -> bool:
        account.block()
        return True

    @property
    def shops(self) -> tuple[Shop, ...]:
        return tuple(self.__shops)

    @property
    def categories(self) -> tuple[Category, ...]:
        return tuple(self.__categories)

    def review_shop(self, shop: Shop) -> bool:
        return True

    def add_category(self, category: Category) -> Category:
        self.__categories.append(category)
        return category

    def modify_category(self, category: Category) -> Category:
        return category

    def remove_category(self, category: Category) -> bool:
        category_id = category.category_id
        before_count = len(self.__categories)
        self.__categories = [
            existing_category
            for existing_category in self.__categories
            if category_id is None
            or existing_category.category_id is None
            or existing_category.category_id.value != category_id.value
        ]
        return len(self.__categories) != before_count
