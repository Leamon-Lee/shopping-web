from dataclasses import dataclass


@dataclass(frozen=True)
# 表示订单内部编号，后续用于唯一定位订单。
class OrderId:
    value: int

    # 初始化后校验订单编号，确保编号是正整数。
    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or self.value <= 0:
            raise ValueError("Order ID must be a positive integer.")


@dataclass(frozen=True)
# 表示展示给用户或外部系统使用的订单号。
class OrderNumber:
    value: str


@dataclass(frozen=True)
# 表示订单创建或下单日期。
class OrderDate:
    value: object


@dataclass(frozen=True)
# 表示日志、通知等对象的创建时间。
class CreationDate:
    value: object
