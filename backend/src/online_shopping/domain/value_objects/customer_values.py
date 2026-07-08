import re
from dataclasses import dataclass


@dataclass(frozen=True)
# 表示客户编号，后续用于唯一标识一个客户。
class CustomerId:
    value: int

    # 初始化后校验客户编号，确保编号是正整数。
    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or self.value <= 0:
            raise ValueError("Customer ID must be a positive integer.")


@dataclass(frozen=True)
# 表示用户姓名，拆分为名和姓，方便后续展示和检索。
class Name:
    first_name: str
    last_name: str

    # 初始化后校验姓名字段，确保名和姓都不是空字符串。
    def __post_init__(self) -> None:
        if not self.first_name.strip() or not self.last_name.strip():
            raise ValueError("Name fields cannot be empty.")
        object.__setattr__(self, "first_name", self.first_name.strip())
        object.__setattr__(self, "last_name", self.last_name.strip())

    # 将姓名转换为展示文本，后续可根据地区规则调整展示顺序。
    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass(frozen=True)
# 表示邮箱地址，后续用于账号联系、登录或邮件通知。
class Email:
    value: str

    # 初始化后校验邮箱格式，避免无效邮箱进入领域模型。
    def __post_init__(self) -> None:
        email = self.value.strip()
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, email):
            raise ValueError("Invalid email format.")
        object.__setattr__(self, "value", email)


@dataclass(frozen=True)
# 表示电话号码，包含国家/地区代码和本地号码。
class Phone:
    country_code: str
    number: str

    # 初始化后校验电话字段，确保国家代码和号码都有内容。
    def __post_init__(self) -> None:
        if not self.country_code.strip() or not self.number.strip():
            raise ValueError("Phone fields cannot be empty.")
        object.__setattr__(self, "country_code", self.country_code.strip())
        object.__setattr__(self, "number", self.number.strip())
