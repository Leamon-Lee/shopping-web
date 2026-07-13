"""Comprehensive tests for all domain value objects."""

import re
from datetime import datetime, timezone

import pytest

from online_shopping.domain.value_objects.account_values import Password, Username
from online_shopping.domain.value_objects.address import Address, BillingAddress, ShippingAddress
from online_shopping.domain.value_objects.customer_values import CustomerId, Email, Name, Phone
from online_shopping.domain.value_objects.notification_values import Contact, Message, NotificationContent, NotificationId
from online_shopping.domain.value_objects.order_values import CreationDate, DisplayOrderId, OrderDate, OrderId, OrderItemId, OrderNumber
from online_shopping.domain.value_objects.payment_values import (
    AccountNumber,
    Amount,
    BankName,
    CardNumber,
    PaymentCurrencyCode,
    PaymentId,
    PaymentProvider,
    RoutingNumber,
    SecurityCode,
    TransactionId,
)
from online_shopping.domain.value_objects.product_values import (
    CategoryDescription,
    CategoryId,
    CategoryName,
    CategorySlug,
    CurrencyCode,
    Price,
    ProductCategoryMap,
    ProductCount,
    ProductDescription,
    ProductId,
    ProductImageId,
    ProductImageUrl,
    ProductName,
    ProductNameMap,
    ProductSlug,
    ProductVariantId,
    ProductVariantName,
    Quantity,
    Rating,
    ReviewContent,
    Sku,
)
from online_shopping.domain.value_objects.shipment_values import EstimatedArrival, ShipmentDate, ShipmentMethod, TrackingNumber
from online_shopping.domain.value_objects.store_values import CartId, CartItemId, CustomerEmail, LocaleCode, RegionId, ShopId, ShopName


# ── ProductValueObjects ─────────────────────────────────────────────────

class TestProductId:
    def test_valid_product_id(self):
        pid = ProductId(1)
        assert pid.value == 1

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            ProductId(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            ProductId(-5)

    def test_non_int_raises(self):
        with pytest.raises(ValueError):
            ProductId("abc")  # type: ignore[arg-type]


class TestProductName:
    def test_valid(self):
        assert ProductName("Tote").value == "Tote"

    def test_strips_whitespace(self):
        assert ProductName("  Bag  ").value == "Bag"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            ProductName("")

    def test_too_long_raises(self):
        with pytest.raises(ValueError):
            ProductName("x" * 161)


class TestProductSlug:
    def test_valid(self):
        assert ProductSlug("everyday-tote").value == "everyday-tote"

    def test_uppercase_lowered(self):
        assert ProductSlug("My-Product").value == "my-product"

    def test_from_name(self):
        slug = ProductSlug.from_name(ProductName("Everyday Tote"))
        assert slug.value == "everyday-tote"

    def test_from_name_chinese_strips(self):
        slug = ProductSlug.from_name(ProductName("测试 Product"))
        assert "product" in slug.value

    def test_invalid_chars_raises(self):
        with pytest.raises(ValueError):
            ProductSlug("hello world")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            ProductSlug("")


class TestPrice:
    def test_valid(self):
        assert Price(10).value == 10.0

    def test_rounds_cents(self):
        assert Price(10.256).value == 10.26

    def test_rounds_down(self):
        assert Price(10.254).value == 10.25

    def test_minor_units(self):
        assert Price(10.25).minor_units == 1025
        assert Price(10).minor_units == 1000

    def test_decimal_input(self):
        from decimal import Decimal
        assert Price(Decimal("19.99")).value == 19.99

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            Price(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            Price(-5)


class TestCurrencyCode:
    def test_valid(self):
        assert CurrencyCode("CNY").value == "cny"

    def test_strips_and_lowers(self):
        assert CurrencyCode("  UsD  ").value == "usd"

    def test_non_alpha_raises(self):
        with pytest.raises(ValueError):
            CurrencyCode("CN1")

    def test_too_short_raises(self):
        with pytest.raises(ValueError):
            CurrencyCode("CN")

    def test_too_long_raises(self):
        with pytest.raises(ValueError):
            CurrencyCode("CNYY")


class TestProductDescription:
    def test_valid(self):
        assert ProductDescription("A nice bag.").value == "A nice bag."

    def test_empty_allowed(self):
        assert ProductDescription("").value == ""

    def test_too_long_raises(self):
        with pytest.raises(ValueError):
            ProductDescription("x" * 501)


class TestProductCount:
    def test_valid(self):
        assert ProductCount(0).value == 0
        assert ProductCount(100).value == 100

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            ProductCount(-1)


class TestCategoryId:
    def test_valid(self):
        assert CategoryId(1).value == 1

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            CategoryId(0)


class TestCategoryName:
    def test_valid(self):
        assert CategoryName("Bags").value == "Bags"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            CategoryName("")

    def test_too_long_raises(self):
        with pytest.raises(ValueError):
            CategoryName("x" * 121)


class TestCategorySlug:
    def test_valid(self):
        assert CategorySlug("reusable-bags").value == "reusable-bags"

    def test_from_name(self):
        slug = CategorySlug.from_name(CategoryName("Reusable Bags"))
        assert slug.value == "reusable-bags"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            CategorySlug("hello world")


class TestCategoryDescription:
    def test_valid(self):
        assert CategoryDescription("Bags category.").value == "Bags category."

    def test_strips(self):
        assert CategoryDescription("  desc  ").value == "desc"

    def test_too_long_raises(self):
        with pytest.raises(ValueError):
            CategoryDescription("x" * 501)


class TestQuantity:
    def test_valid(self):
        assert Quantity(1).value == 1

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            Quantity(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            Quantity(-1)


class TestProductVariantId:
    def test_valid(self):
        assert ProductVariantId("variant_tote").value == "variant_tote"

    def test_strips(self):
        assert ProductVariantId("  v1  ").value == "v1"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            ProductVariantId("")


class TestProductVariantName:
    def test_valid(self):
        assert ProductVariantName("Large").value == "Large"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            ProductVariantName("")


class TestSku:
    def test_valid(self):
        assert Sku("SKU-001").value == "SKU-001"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            Sku("")

    def test_too_long_raises(self):
        with pytest.raises(ValueError):
            Sku("x" * 65)


class TestProductImageId:
    def test_valid(self):
        assert ProductImageId("img_001").value == "img_001"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            ProductImageId("")


class TestProductImageUrl:
    def test_absolute_url(self):
        assert ProductImageUrl("http://example.com/img.jpg").value == "http://example.com/img.jpg"

    def test_https_url(self):
        assert ProductImageUrl("https://example.com/img.jpg").value == "https://example.com/img.jpg"

    def test_root_relative(self):
        assert ProductImageUrl("/images/img.jpg").value == "/images/img.jpg"

    def test_relative_raises(self):
        with pytest.raises(ValueError):
            ProductImageUrl("images/img.jpg")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            ProductImageUrl("")


class TestRating:
    def test_valid(self):
        assert Rating(1).value == 1
        assert Rating(5).value == 5
        assert Rating(3).value == 3

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            Rating(0)

    def test_six_raises(self):
        with pytest.raises(ValueError):
            Rating(6)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            Rating(-1)


class TestReviewContent:
    def test_valid(self):
        assert ReviewContent("Good product!").value == "Good product!"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            ReviewContent("")

    def test_too_long_raises(self):
        with pytest.raises(ValueError):
            ReviewContent("x" * 1001)


# ── OrderValueObjects ────────────────────────────────────────────────────

class TestOrderId:
    def test_valid(self):
        assert OrderId(1001).value == 1001

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            OrderId(0)


class TestOrderNumber:
    def test_valid(self):
        assert OrderNumber("ORD-1001").value == "ORD-1001"

    def test_strips(self):
        assert OrderNumber("  ORD-1001  ").value == "ORD-1001"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            OrderNumber("")


class TestDisplayOrderId:
    def test_valid(self):
        assert DisplayOrderId(1).value == 1

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            DisplayOrderId(0)


class TestOrderItemId:
    def test_valid(self):
        assert OrderItemId("oi_001").value == "oi_001"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            OrderItemId("")


class TestOrderDate:
    def test_valid(self):
        now = datetime.now(timezone.utc)
        od = OrderDate(now)
        assert od.value == now

    def test_non_datetime_raises(self):
        with pytest.raises(TypeError):
            OrderDate("2024-01-01")  # type: ignore[arg-type]


class TestCreationDate:
    def test_valid(self):
        now = datetime.now(timezone.utc)
        cd = CreationDate(now)
        assert cd.value == now


# ── PaymentValueObjects ──────────────────────────────────────────────────

class TestCardNumber:
    def test_valid(self):
        assert CardNumber("1234567890123456").value == "1234567890123456"

    def test_with_spaces(self):
        assert CardNumber("1234 5678 9012 3456").value == "1234567890123456"

    def test_too_short_raises(self):
        with pytest.raises(ValueError):
            CardNumber("123456789012")

    def test_too_long_raises(self):
        with pytest.raises(ValueError):
            CardNumber("1" * 20)

    def test_non_digit_raises(self):
        with pytest.raises(ValueError):
            CardNumber("abcdabcdabcdabcd")


class TestSecurityCode:
    def test_valid_3(self):
        assert SecurityCode("123").value == "123"

    def test_valid_4(self):
        assert SecurityCode("1234").value == "1234"

    def test_invalid_length_raises(self):
        with pytest.raises(ValueError):
            SecurityCode("12")


class TestBankName:
    def test_valid(self):
        assert BankName("Bank of China").value == "Bank of China"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            BankName("")


class TestRoutingNumber:
    def test_valid(self):
        assert RoutingNumber("123456789").value == "123456789"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            RoutingNumber("")


class TestAccountNumber:
    def test_valid(self):
        assert AccountNumber("987654321").value == "987654321"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            AccountNumber("")


class TestAmount:
    def test_valid(self):
        assert Amount(100).value == 100.0

    def test_rounds(self):
        assert Amount(20.126).value == 20.13

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            Amount(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            Amount(-10)


class TestPaymentCurrencyCode:
    def test_valid(self):
        assert PaymentCurrencyCode("CNY").value == "cny"


class TestPaymentId:
    def test_valid(self):
        assert PaymentId("pay_001").value == "pay_001"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            PaymentId("")


class TestTransactionId:
    def test_valid(self):
        assert TransactionId("txn_001").value == "txn_001"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            TransactionId("")


class TestPaymentProvider:
    def test_valid(self):
        assert PaymentProvider("Alipay").value == "Alipay"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            PaymentProvider("")


# ── AccountValueObjects ──────────────────────────────────────────────────

class TestUsername:
    def test_valid(self):
        assert Username("john_doe").value == "john_doe"

    def test_strips(self):
        assert Username("  john  ").value == "john"

    def test_too_short_raises(self):
        with pytest.raises(ValueError):
            Username("ab")

    def test_too_long_raises(self):
        with pytest.raises(ValueError):
            Username("x" * 21)

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            Username("")


class TestPassword:
    def test_valid(self):
        assert Password("password123").value == "password123"

    def test_min_length(self):
        assert Password("12345678").value == "12345678"

    def test_too_short_raises(self):
        with pytest.raises(ValueError):
            Password("1234567")


# ── CustomerValueObjects ──────────────────────────────────────────────────

class TestCustomerId:
    def test_valid(self):
        assert CustomerId(1).value == 1

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            CustomerId(0)


class TestName:
    def test_valid(self):
        n = Name("John", "Doe")
        assert n.first_name == "John"
        assert n.last_name == "Doe"

    def test_str(self):
        assert str(Name("John", "Doe")) == "John Doe"

    def test_strips(self):
        n = Name(" John ", " Doe ")
        assert n.first_name == "John"
        assert n.last_name == "Doe"

    def test_empty_first_raises(self):
        with pytest.raises(ValueError):
            Name("", "Doe")

    def test_empty_last_raises(self):
        with pytest.raises(ValueError):
            Name("John", "")


class TestEmail:
    def test_valid(self):
        assert Email("test@example.com").value == "test@example.com"

    def test_strips_and_lowers(self):
        assert Email("  Test@Example.COM  ").value == "test@example.com"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            Email("not-an-email")

    def test_no_at_raises(self):
        with pytest.raises(ValueError):
            Email("testexample.com")


class TestPhone:
    def test_valid(self):
        p = Phone("+86", "13800138000")
        assert p.country_code == "+86"
        assert p.number == "13800138000"

    def test_empty_country_raises(self):
        with pytest.raises(ValueError):
            Phone("", "123")

    def test_empty_number_raises(self):
        with pytest.raises(ValueError):
            Phone("+86", "")


# ── Address ───────────────────────────────────────────────────────────────

class TestAddress:
    def test_valid(self):
        addr = Address("123 St", "Beijing", "BJ", "100000", "China")
        assert addr.street == "123 St"

    def test_empty_field_raises(self):
        with pytest.raises(ValueError):
            Address("", "City", "State", "Zip", "Country")

    def test_strips(self):
        addr = Address("  123 St  ", " Beijing ", "BJ", "100000", "China")
        assert addr.street == "123 St"
        assert addr.city == "Beijing"

    def test_shipping_address_alias(self):
        addr = ShippingAddress("123 St", "City", "ST", "00000", "US")
        assert isinstance(addr, Address)

    def test_billing_address_alias(self):
        addr = BillingAddress("456 Ave", "City", "ST", "00000", "US")
        assert isinstance(addr, Address)


# ── NotificationValueObjects ──────────────────────────────────────────────

class TestMessage:
    def test_valid(self):
        assert Message("Hello").value == "Hello"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            Message("")


class TestNotificationId:
    def test_valid(self):
        assert NotificationId(1).value == 1


class TestNotificationContent:
    def test_valid(self):
        assert NotificationContent("Content").value == "Content"


class TestContact:
    def test_valid(self):
        assert Contact("user@example.com").value == "user@example.com"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            Contact("")


# ── ShipmentValueObjects ──────────────────────────────────────────────────

class TestTrackingNumber:
    def test_valid(self):
        assert TrackingNumber("TN123456").value == "TN123456"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            TrackingNumber("")


class TestShipmentDate:
    def test_valid(self):
        sd = ShipmentDate("2024-01-01")
        assert sd.value == "2024-01-01"


class TestEstimatedArrival:
    def test_valid(self):
        ea = EstimatedArrival("2024-01-05")
        assert ea.value == "2024-01-05"


class TestShipmentMethod:
    def test_valid(self):
        assert ShipmentMethod("Express").value == "Express"


# ── StoreValueObjects ─────────────────────────────────────────────────────

class TestShopId:
    def test_valid(self):
        assert ShopId("shop_001").value == "shop_001"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            ShopId("")


class TestShopName:
    def test_valid(self):
        assert ShopName("My Shop").value == "My Shop"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            ShopName("")


class TestCartId:
    def test_valid(self):
        assert CartId("cart_001").value == "cart_001"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            CartId("")


class TestCartItemId:
    def test_valid(self):
        assert CartItemId("ci_001").value == "ci_001"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            CartItemId("")


class TestRegionId:
    def test_valid(self):
        assert RegionId("reg_cny").value == "reg_cny"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            RegionId("")


class TestCustomerEmail:
    def test_valid(self):
        assert CustomerEmail("user@example.com").value == "user@example.com"

    def test_uppercase_lowered(self):
        assert CustomerEmail("USER@EXAMPLE.COM").value == "user@example.com"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            CustomerEmail("not-valid")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            CustomerEmail("")


class TestLocaleCode:
    def test_valid(self):
        assert LocaleCode("zh-CN").value == "zh-cn"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            LocaleCode("")


# ── Edge cases ────────────────────────────────────────────────────────────

class TestFrozenDataclasses:
    """Verify that value objects are immutable."""
    def test_price_immutable(self):
        p = Price(10)
        with pytest.raises(Exception):
            p.value = 20  # type: ignore[misc]

    def test_product_name_immutable(self):
        n = ProductName("Test")
        with pytest.raises(Exception):
            n.value = "Other"  # type: ignore[misc]


class TestProductNameMap:
    def test_creation(self):
        pm = ProductNameMap({"test": []})
        assert pm.value == {"test": []}


class TestProductCategoryMap:
    def test_creation(self):
        pcm = ProductCategoryMap({"bags": []})
        assert pcm.value == {"bags": []}
