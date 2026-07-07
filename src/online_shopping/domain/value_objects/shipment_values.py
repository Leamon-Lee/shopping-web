from dataclasses import dataclass


@dataclass(frozen=True)
# 表示物流追踪号，后续用于查询配送状态。
class TrackingNumber:
    value: str

    # 初始化后校验追踪号，确保追踪号不是空字符串。
    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Tracking number cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
# 表示发货日期。
class ShipmentDate:
    value: object


@dataclass(frozen=True)
# 表示预计送达日期。
class EstimatedArrival:
    value: object


@dataclass(frozen=True)
# 表示配送方式，例如快递、同城配送或自提。
class ShipmentMethod:
    value: str
