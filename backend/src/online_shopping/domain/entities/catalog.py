from online_shopping.domain.entities.product import Product
from online_shopping.domain.interfaces.search import Search
from online_shopping.domain.value_objects.customer_values import Name
from online_shopping.domain.value_objects.order_values import CreationDate
from online_shopping.domain.value_objects.product_values import (
    CategoryName,
    ProductCategoryMap,
    ProductName,
    ProductNameMap,
)


class Catalog(Search):
    # 创建商品目录，并维护商品名称、分类索引以及目录中的商品集合。
    def __init__(
        self,
        last_updated: CreationDate,
        product_names: ProductNameMap,
        product_categories: ProductCategoryMap,
        name: Name,
        products: list[Product] | None = None,
    ):
        self.__last_updated = last_updated
        self.__product_names = product_names
        self.__product_categories = product_categories
        self.__name = name
        self.__products = products or []

    # 按商品名称搜索商品，后续应使用名称索引或商品仓储返回匹配商品。
    def search_products_by_name(self, name: ProductName) -> list[Product]:
        pass

    # 按商品分类搜索商品，后续应使用分类索引或商品仓储返回匹配商品。
    def search_products_by_category(self, category: CategoryName) -> list[Product]:
        pass
