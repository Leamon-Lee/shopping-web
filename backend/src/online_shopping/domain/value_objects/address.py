from dataclasses import dataclass


@dataclass(frozen=True)
# 表示用户收货或账单地址，负责承载完整地址所需的基础字段。
class Address:
    street: str
    city: str
    state: str
    postal_code: str
    country: str

    # 初始化后校验地址字段，确保每个地址组成部分都不是空值。
    def __post_init__(self) -> None:
        for field_name, value in self.__dict__.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} cannot be empty.")
            object.__setattr__(self, field_name, value.strip())


ShippingAddress = Address
BillingAddress = Address
