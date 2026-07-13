"""Comprehensive tests for all domain enums."""

import pytest

from online_shopping.domain.enums.account_status import AccountStatus
from online_shopping.domain.enums.notification_channel import NotificationChannel
from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.enums.payment_method_type import PaymentMethodType
from online_shopping.domain.enums.payment_status import PaymentStatus
from online_shopping.domain.enums.refund_status import RefundStatus
from online_shopping.domain.enums.shipment_status import ShipmentStatus


class TestAccountStatus:
    def test_values(self):
        assert AccountStatus.ACTIVE == "active"
        assert AccountStatus.BLOCKED == "blocked"
        assert AccountStatus.BANNED == "banned"
        assert AccountStatus.COMPROMISED == "compromised"
        assert AccountStatus.ARCHIVED == "archived"
        assert AccountStatus.UNKNOWN == "unknown"

    def test_capitalized_aliases(self):
        assert AccountStatus.Active == "active"
        assert AccountStatus.Blocked == "blocked"
        assert AccountStatus.Banned == "banned"

    def test_is_string(self):
        assert isinstance(AccountStatus.ACTIVE, str)

    def test_from_string(self):
        assert AccountStatus("active") == AccountStatus.ACTIVE
        assert AccountStatus("blocked") == AccountStatus.BLOCKED


class TestOrderStatus:
    def test_values(self):
        assert OrderStatus.CREATED == "created"
        assert OrderStatus.CONFIRMED == "confirmed"
        assert OrderStatus.PROCESSING == "processing"
        assert OrderStatus.SHIPPED == "shipped"
        assert OrderStatus.COMPLETED == "completed"
        assert OrderStatus.CANCELED == "canceled"

    def test_capitalized_aliases(self):
        assert OrderStatus.Created == "created"
        assert OrderStatus.Confirmed == "confirmed"
        assert OrderStatus.Completed == "completed"
        assert OrderStatus.Canceled == "canceled"

    def test_from_string(self):
        assert OrderStatus("created") == OrderStatus.CREATED
        assert OrderStatus("shipped") == OrderStatus.SHIPPED

    def test_len(self):
        assert len(OrderStatus) == 6


class TestPaymentStatus:
    def test_values(self):
        assert PaymentStatus.PENDING == "pending"
        assert PaymentStatus.COMPLETED == "completed"
        assert PaymentStatus.FAILED == "failed"
        assert PaymentStatus.REFUNDED == "refunded"

    def test_capitalized_aliases(self):
        assert PaymentStatus.Pending == "pending"
        assert PaymentStatus.Completed == "completed"

    def test_from_string(self):
        assert PaymentStatus("pending") == PaymentStatus.PENDING
        assert PaymentStatus("settled") == PaymentStatus.SETTLED

    def test_all_values_count(self):
        assert len(PaymentStatus) == 10


class TestPaymentMethodType:
    def test_values(self):
        assert PaymentMethodType.CREDIT_CARD == "credit_card"
        assert PaymentMethodType.ELECTRONIC_BANK_TRANSFER == "electronic_bank_transfer"

    def test_capitalized_aliases(self):
        assert PaymentMethodType.CreditCard == "credit_card"


class TestRefundStatus:
    def test_values(self):
        assert RefundStatus.NONE == "none"
        assert RefundStatus.REQUESTED == "requested"
        assert RefundStatus.APPROVED == "approved"
        assert RefundStatus.REJECTED == "rejected"
        assert RefundStatus.REFUNDED == "refunded"

    def test_capitalized_aliases(self):
        assert RefundStatus.Requested == "requested"
        assert RefundStatus.Approved == "approved"

    def test_none_alias(self):
        assert RefundStatus.None_ == "none"


class TestShipmentStatus:
    def test_values(self):
        assert ShipmentStatus.PENDING == "pending"
        assert ShipmentStatus.SHIPPED == "shipped"
        assert ShipmentStatus.DELIVERED == "delivered"
        assert ShipmentStatus.ON_HOLD == "on_hold"

    def test_capitalized_aliases(self):
        assert ShipmentStatus.Pending == "pending"
        assert ShipmentStatus.Delivered == "delivered"


class TestNotificationChannel:
    def test_values(self):
        assert NotificationChannel.EMAIL == "email"
        assert NotificationChannel.SMS == "sms"

    def test_capitalized_aliases(self):
        assert NotificationChannel.Email == "email"
        assert NotificationChannel.Sms == "sms"


class TestEnumImports:
    """Verify the __init__ re-exports work."""
    def test_from_init(self):
        from online_shopping.domain.enums import (
            AccountStatus,
            NotificationChannel,
            OrderStatus,
            PaymentMethodType,
            PaymentStatus,
            RefundStatus,
            ShipmentStatus,
        )
        assert AccountStatus.ACTIVE == "active"
        assert OrderStatus.CREATED == "created"
        assert PaymentStatus.PENDING == "pending"
        assert PaymentMethodType.CREDIT_CARD == "credit_card"
        assert RefundStatus.NONE == "none"
        assert ShipmentStatus.PENDING == "pending"
        assert NotificationChannel.EMAIL == "email"
