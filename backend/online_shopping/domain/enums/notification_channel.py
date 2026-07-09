from enum import Enum


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"

    Email = EMAIL
    Sms = SMS
