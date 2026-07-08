from online_shopping.domain.value_objects.notification_values import NotificationContent, NotificationId
from online_shopping.domain.value_objects.order_values import CreationDate


class Notification:
    # 创建通知实体，保存通知编号、创建时间和通知内容。
    def __init__(self, notification_id: NotificationId, created_on: CreationDate, content: NotificationContent):
        self.__notification_id = notification_id
        self.__created_on = created_on
        self.__content = content

    # 发送通知，后续应由具体通知渠道实现实际发送动作。
    def send_notification(self) -> bool:
        pass
