from dataclasses import dataclass


@dataclass(frozen=True)
# 表示商品编号，后续用于唯一定位一个商品。
class ProductId:
    value: int

    # 初始化后校验商品编号，确保编号是正整数。
    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or self.value <= 0:
            raise ValueError("Product ID must be a positive integer.")


@dataclass(frozen=True)
# 表示商品名称，后续用于商品展示和搜索。
class ProductName:
    value: str

    # 初始化后校验商品名称，确保名称不是空字符串。
    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Product name cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
# 表示商品或订单项价格，后续可扩展币种、精度等规则。
class Price:
    value: float

    # 初始化后校验价格，确保价格是大于零的数字。
    def __post_init__(self) -> None:
        if not isinstance(self.value, (int, float)) or self.value <= 0:
            raise ValueError("Price must be greater than zero.")
        object.__setattr__(self, "value", float(self.value))


@dataclass(frozen=True)
# 表示商品描述，负责限制展示文案的基础长度。
class ProductDescription:
    value: str

    # 初始化后校验商品描述，确保文本类型和长度符合约束。
    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("Description must be a string.")
        if len(self.value) > 500:
            raise ValueError("Description cannot exceed 500 characters.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
# 表示商品可售库存数量，后续可补充非负数校验。
class ProductCount:
    value: int


@dataclass(frozen=True)
# 表示商品分类名称，后续用于分类展示和检索。
class CategoryName:
    value: str


@dataclass(frozen=True)
# 表示商品分类描述，后续用于说明分类用途。
class CategoryDescription:
    value: str


@dataclass(frozen=True)
# 表示购物车或订单中的商品数量。
class Quantity:
    value: int


@dataclass(frozen=True)
# 表示商品评价分数，后续可限制评分范围。
class Rating:
    value: int


@dataclass(frozen=True)
# 表示商品评价正文，后续可限制长度和敏感内容。
class ReviewContent:
    value: str


@dataclass(frozen=True)
# 表示按商品名称建立的商品索引映射。
class ProductNameMap:
    value: dict[str, list[object]]


@dataclass(frozen=True)
# 表示按商品分类建立的商品索引映射。
class ProductCategoryMap:
    value: dict[str, list[object]]
