"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from online_shopping.api.schemas import (
    AccountOut,
    AccountUpdate,
    AddressCreate,
    AddressOut,
    AddressUpdate,
    CartItemCreate,
    CartItemUpdate,
    CartItemOut,
    CategoryOut,
    LoginPayload,
    NameOut,
    OrderCreate,
    OrderOut,
    PaymentCreate,
    PaymentOut,
    PhoneOut,
    ProductCreate,
    ProductOut,
    RegisterPayload,
    ShoppingCartOut,
    TokenResponse,
    AccountRole,
    ProductVariantOut,
    ImageOut,
    ShipmentOut,
)
from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.enums.payment_status import PaymentStatus
from online_shopping.domain.enums.shipment_status import ShipmentStatus


class TestCategoryBase:
    def test_valid(self):
        cat = CategoryOut(name="Bags", description="Reusable bags")
        assert cat.name == "Bags"
        assert cat.description == "Reusable bags"

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            CategoryOut(name="", description="")

    def test_default_description(self):
        cat = CategoryOut(name="Bags")
        assert cat.description == ""


class TestProductBase:
    def test_valid(self):
        p = ProductOut(
            name="Tote",
            description="A bag",
            price=29.0,
            available_item_count=25,
            category=CategoryOut(name="Bags", description="Bags"),
        )
        assert p.name == "Tote"
        assert p.price == 29.0

    def test_zero_price_raises(self):
        with pytest.raises(ValidationError):
            ProductOut(
                name="Tote",
                description="A bag",
                price=0,
                available_item_count=25,
                category=CategoryOut(name="Bags"),
            )

    def test_negative_count_raises(self):
        with pytest.raises(ValidationError):
            ProductOut(
                name="Tote",
                description="A bag",
                price=10,
                available_item_count=-1,
                category=CategoryOut(name="Bags"),
            )


class TestCartItemCreate:
    def test_valid(self):
        c = CartItemCreate(product_name="Tote", quantity=2)
        assert c.product_name == "Tote"
        assert c.quantity == 2

    def test_zero_quantity_raises(self):
        with pytest.raises(ValidationError):
            CartItemCreate(product_name="Tote", quantity=0)

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            CartItemCreate(product_name="", quantity=1)


class TestCartItemUpdate:
    def test_valid(self):
        c = CartItemUpdate(quantity=3)
        assert c.quantity == 3

    def test_zero_quantity_raises(self):
        with pytest.raises(ValidationError):
            CartItemUpdate(quantity=0)


class TestCartItemOut:
    def test_minimal(self):
        product = ProductOut(
            name="Tote", description="A bag", price=29.0,
            available_item_count=25,
            category=CategoryOut(name="Bags"),
        )
        item = CartItemOut(
            quantity=2, price=29.0, product=product,
            product_title="Tote", product_handle="tote",
        )
        assert item.quantity == 2
        assert item.price == 29.0


class TestShoppingCartOut:
    def test_valid(self):
        product = ProductOut(
            name="Tote", description="A bag", price=29.0,
            available_item_count=25,
            category=CategoryOut(name="Bags"),
        )
        item = CartItemOut(
            quantity=2, price=29.0, product=product,
            product_title="Tote", product_handle="tote",
        )
        cart = ShoppingCartOut(items=[item], total_quantity=2, subtotal=58.0)
        assert cart.total_quantity == 2
        assert cart.subtotal == 58.0
        assert cart.currency_code == "cny"


class TestPaymentCreate:
    def test_valid(self):
        p = PaymentCreate(amount=100.0, currency="CNY")
        assert p.amount == 100.0

    def test_zero_amount_raises(self):
        with pytest.raises(ValidationError):
            PaymentCreate(amount=0)


class TestPaymentOut:
    def test_default(self):
        p = PaymentOut()
        assert p.status == PaymentStatus.PENDING

    def test_with_values(self):
        p = PaymentOut(status=PaymentStatus.COMPLETED, amount=100.0, currency="CNY")
        assert p.status == PaymentStatus.COMPLETED


class TestShipmentOut:
    def test_default(self):
        s = ShipmentOut()
        assert s.status == ShipmentStatus.PENDING


class TestOrderCreate:
    def test_valid(self):
        o = OrderCreate(order_number="ORD-1001")
        assert o.order_number == "ORD-1001"

    def test_with_items(self):
        o = OrderCreate(
            items=[CartItemCreate(product_name="Tote", quantity=1)],
            payment=PaymentCreate(amount=29.0),
        )
        assert len(o.items) == 1
        assert o.payment.amount == 29.0

    def test_default_items(self):
        o = OrderCreate()
        assert o.items == []


class TestOrderOut:
    def test_minimal(self):
        product = ProductOut(
            name="Tote", description="A bag", price=29.0,
            available_item_count=25,
            category=CategoryOut(name="Bags"),
        )
        item = CartItemOut(
            quantity=1, price=29.0, product=product,
            product_title="Tote", product_handle="tote",
        )
        o = OrderOut(order_number="ORD-1", items=[item])
        assert o.status == OrderStatus.CREATED
        assert o.payment is None


class TestLoginPayload:
    def test_valid(self):
        p = LoginPayload(email="a@b.com", password="secret123")
        assert p.email == "a@b.com"

    def test_empty_email_raises(self):
        with pytest.raises(ValidationError):
            LoginPayload(email="", password="secret123")

    def test_empty_password_raises(self):
        with pytest.raises(ValidationError):
            LoginPayload(email="a@b.com", password="")


class TestRegisterPayload:
    def test_valid(self):
        p = RegisterPayload(email="a@b.com", password="password123")
        assert p.first_name == ""

    def test_short_password_raises(self):
        with pytest.raises(ValidationError):
            RegisterPayload(email="a@b.com", password="short")

    def test_empty_email_raises(self):
        with pytest.raises(ValidationError):
            RegisterPayload(email="", password="password123")


class TestAddressCreate:
    def test_valid(self):
        a = AddressCreate(street="123 St", city="Beijing")
        assert a.is_default_shipping is False

    def test_empty_street_raises(self):
        with pytest.raises(ValidationError):
            AddressCreate(street="", city="Beijing")

    def test_empty_city_raises(self):
        with pytest.raises(ValidationError):
            AddressCreate(street="123 St", city="")


class TestAddressUpdate:
    def test_all_none(self):
        a = AddressUpdate()
        assert a.street is None

    def test_partial(self):
        a = AddressUpdate(street="New St")
        assert a.street == "New St"
        assert a.city is None


class TestAddressOut:
    def test_valid(self):
        a = AddressOut(street="123", city="BJ", state="BJ", postal_code="100", country="CN")
        assert a.country == "CN"


class TestNameOut:
    def test_valid(self):
        n = NameOut(first_name="John", last_name="Doe")
        assert n.first_name == "John"


class TestPhoneOut:
    def test_valid(self):
        p = PhoneOut(country_code="+86", number="13800138000")
        assert p.country_code == "+86"


class TestAccountOut:
    def test_valid(self):
        a = AccountOut(
            user_name="johndoe",
            status="active",
            name=NameOut(first_name="John", last_name="Doe"),
            shipping_address=AddressOut(street="123", city="BJ", state="", postal_code="", country="CN"),
            email="john@example.com",
            phone=PhoneOut(country_code="+86", number="138"),
        )
        assert a.user_name == "johndoe"
        assert a.email == "john@example.com"


class TestTokenResponse:
    def test_valid(self):
        user = AccountOut(
            user_name="test", status="active",
            name=NameOut(first_name="T", last_name="U"),
            shipping_address=AddressOut(street="", city="", state="", postal_code="", country=""),
            email="t@u.com",
            phone=PhoneOut(country_code="", number=""),
        )
        t = TokenResponse(access_token="abc.def.ghi", token_type="bearer", user=user)
        assert t.access_token == "abc.def.ghi"


class TestAccountUpdate:
    def test_all_none(self):
        a = AccountUpdate()
        assert a.first_name is None

    def test_partial(self):
        a = AccountUpdate(first_name="New")
        assert a.first_name == "New"


class TestAccountRole:
    def test_default(self):
        r = AccountRole()
        assert r.role == "customer"

    def test_admin(self):
        r = AccountRole(role="admin")
        assert r.role == "admin"


class TestProductVariantOut:
    def test_minimal(self):
        v = ProductVariantOut(
            id="v1", title="Default", name="Default",
            sku="SKU-1", price=10.0,
            inventory_quantity=100, inventory_count=100,
        )
        assert v.id == "v1"
        assert v.manage_inventory is True
        assert v.allow_backorder is False
        assert v.options == []
        assert v.product is None


class TestImageOut:
    def test_valid(self):
        img = ImageOut(image_url="/img.jpg")
        assert img.image_url == "/img.jpg"
        assert img.url is None
        assert img.rank == 0

    def test_with_rank(self):
        img = ImageOut(image_url="/img.jpg", url="/img.jpg", rank=2)
        assert img.rank == 2


class TestProductCreate:
    def test_valid(self):
        p = ProductCreate(
            name="Tote", description="Bag", price=29.0,
            available_item_count=25,
            category=CategoryOut(name="Bags"),
        )
        assert p.name == "Tote"
