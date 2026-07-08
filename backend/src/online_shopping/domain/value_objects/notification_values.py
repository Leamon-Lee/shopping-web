from dataclasses import dataclass


@dataclass(frozen=True)
# 表示通用消息文本，后续可用于通知正文或系统消息。
class Message:
    value: str

    # 初始化后校验消息内容，确保消息不是空字符串。
    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("Message cannot be empty.")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
# 表示通知编号，后续用于唯一定位一条通知。
class NotificationId:
    value: int


@dataclass(frozen=True)
# 表示通知正文内容，后续由不同通知渠道发送。
class NotificationContent:
    value: str
