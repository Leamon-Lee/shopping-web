from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from online_shopping.domain.entities.manager import Manager
    from online_shopping.domain.entities.product import Product
    from online_shopping.domain.entities.shop import Shop


class ProductApproval:
    def __init__(
        self,
        product: Product,
        shop: Shop,
        manager: Manager,
        confirmed: bool = False,
    ) -> None:
        self.__product = product
        self.__shop = shop
        self.__manager = manager
        self.__confirmed = confirmed

    @property
    def product(self) -> Product:
        return self.__product

    @property
    def shop(self) -> Shop:
        return self.__shop

    @property
    def manager(self) -> Manager:
        return self.__manager

    @property
    def confirmed(self) -> bool:
        return self.__confirmed

    def confirm(self, manager: Manager) -> bool:
        if manager is not self.__manager:
            return False
        self.__confirmed = True
        self.__shop.add_approved_product(self.__product)
        return True
