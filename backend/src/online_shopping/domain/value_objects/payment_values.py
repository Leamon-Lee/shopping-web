from dataclasses import dataclass

from .address import BillingAddress


@dataclass(frozen=True)
# 表示信用卡号，负责承载支付卡片的号码信息。
class CardNumber:
    value: str

    # 初始化后校验信用卡号，确保只包含合理长度的数字。
    def __post_init__(self) -> None:
        digits = self.value.replace(" ", "")
        if not digits.isdigit() or not 13 <= len(digits) <= 19:
            raise ValueError("Card number must contain 13 to 19 digits.")
        object.__setattr__(self, "value", digits)


@dataclass(frozen=True)
# 表示信用卡安全码，后续用于卡支付验证。
class SecurityCode:
    value: str

    # 初始化后校验安全码，确保是 3 位或 4 位数字。
    def __post_init__(self) -> None:
        if not self.value.isdigit() or len(self.value) not in (3, 4):
            raise ValueError("Security code must contain 3 or 4 digits.")


Code = SecurityCode


@dataclass(frozen=True)
# 表示电子银行转账的银行名称。
class BankName:
    value: str


@dataclass(frozen=True)
# 表示电子银行转账的路由号码。
class RoutingNumber:
    value: str


@dataclass(frozen=True)
# 表示电子银行转账的账户号码。
class AccountNumber:
    value: str


@dataclass(frozen=True)
# 表示支付金额，后续可补充币种和精度规则。
class Amount:
    value: float
