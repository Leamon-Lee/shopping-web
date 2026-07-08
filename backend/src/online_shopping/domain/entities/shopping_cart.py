from online_shopping.domain.entities.item import Item


class ShoppingCart:
    # 创建购物车，并保存购物车中已有的商品项集合。
    def __init__(self, items: list[Item] | None = None) -> None:
        self.__items = items or []

    # 返回购物车项的只读视图，避免外部直接修改内部列表。
    @property
    def items(self) -> tuple[Item, ...]:
        return tuple(self.__items)

    # 添加商品项到购物车，后续应处理重复商品合并和库存校验。
    def add_item(self) -> bool:
        pass

    # 从购物车移除商品项，后续应根据商品或订单项标识进行删除。
    def remove_item(self) -> bool:
        pass

    # 返回购物车中的商品项列表，后续可用于结算和展示。
    def get_items(self) -> list[Item]:
        return self.__items
