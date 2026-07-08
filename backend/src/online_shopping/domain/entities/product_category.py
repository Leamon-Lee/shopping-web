from online_shopping.domain.value_objects.product_values import CategoryDescription, CategoryName


class ProductCategory:
    # 创建商品分类实体，保存分类名称和说明。
    def __init__(self, name: CategoryName, description: CategoryDescription):
        self.__name = name
        self.__description = description
