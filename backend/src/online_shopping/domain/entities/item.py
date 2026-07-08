from online_shopping.domain.entities.product import Product
from online_shopping.domain.value_objects.product_values import Price, Quantity

class Item:
    # 创建订单项或购物车项，并关联数量、价格和对应商品。
    def __init__(self, quantity: Quantity, price: Price, product: Product):
        self.__quantity = quantity
        self.__price = price
        self.__product = product

    # 更新商品项数量，后续应校验库存、数量范围和购物车/订单状态。
    def update_quantity(self) -> bool:
        pass
