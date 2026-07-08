from online_shopping.domain.entities.product_category import ProductCategory
from online_shopping.domain.value_objects.product_values import (
    Price,
    ProductCount,
    ProductDescription,
    ProductName,
)


class Product:
    # 创建商品实体，并关联商品名称、描述、价格、库存和所属分类。
    def __init__(
        self,
        name: ProductName,
        description: ProductDescription,
        price: Price,
        available_item_count: ProductCount,
        category: ProductCategory,
    ):
        self.__name = name
        self.__description = description
        self.__price = price
        self.__available_item_count = available_item_count
        self.__category = category

    # 返回当前可售库存数量，后续可接入库存计算或预留库存逻辑。
    def get_available_count(self) -> ProductCount:
        return self.__available_item_count
