from online_shopping.domain.entities.notification import Notification
from online_shopping.domain.value_objects.customer_values import Email
from online_shopping.domain.value_objects.notification_values import NotificationContent, NotificationId
from online_shopping.domain.value_objects.order_values import CreationDate


class EmailNotification(Notification):
    # 创建邮件通知，并在基础通知信息之外保存接收邮箱。
    def __init__(
        self,
        notification_id: NotificationId,
        created_on: CreationDate,
        content: NotificationContent,
        email: Email,
    ):
        super().__init__(notification_id=notification_id, created_on=created_on, content=content)
        self.__email = email
