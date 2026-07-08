from dataclasses import dataclass


@dataclass(frozen=True)
# 表示账户登录用户名，后续应保证用户名格式、长度和唯一性符合业务规则。
class Username:
    value: str

    # 初始化后校验用户名，确保不会创建空用户名对象。
    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Username cannot be empty.")
        if len(self.value.strip()) < 3:
            raise ValueError("Username must contain at least 3 characters.")
        if len(self.value.strip()) > 20:
            raise ValueError("Username cannot exceed 20 characters.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
# 表示账户登录密码，后续可扩展密码强度、加密前格式等规则。
class Password:
    value: str

    # 初始化后校验密码，确保密码满足最基本的长度要求。
    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or len(self.value) < 8:
            raise ValueError("Password must contain at least 8 characters.")
