from typing import Protocol

from online_shopping.domain.value_objects.product_values import CategoryName, ProductName


class Search(Protocol):
    # 按商品名称查找商品，实现类应返回所有名称匹配的商品。
    def search_products_by_name(self, name: ProductName) -> list[object]:
        pass

    # 按商品分类查找商品，实现类应返回属于该分类的商品。
    def search_products_by_category(self, category: CategoryName) -> list[object]:
        pass
