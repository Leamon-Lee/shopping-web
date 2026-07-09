from online_shopping.domain.enums.notification_channel import NotificationChannel
from online_shopping.domain.value_objects.notification_values import (
    Contact,
    NotificationContent,
    NotificationId,
)
from online_shopping.domain.value_objects.order_values import CreationDate


class Notification:
    def __init__(
        self,
        notification_id: NotificationId,
        channel: NotificationChannel,
        receiver: Contact,
        created_on: CreationDate,
        content: NotificationContent,
    ) -> None:
        self.__notification_id = notification_id
        self.__channel = channel
        self.__receiver = receiver
        self.__created_on = created_on
        self.__content = content

    @property
    def channel(self) -> NotificationChannel:
        return self.__channel

    @property
    def receiver(self) -> Contact:
        return self.__receiver

    def send_notification(self) -> bool:
        return True
