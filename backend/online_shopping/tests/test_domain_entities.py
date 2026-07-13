"""Comprehensive tests for all domain entities."""

from datetime import datetime, timezone

import pytest

from online_shopping.domain.entities.account import Account
from online_shopping.domain.entities.admin import Admin
from online_shopping.domain.entities.cart_item import CartItem
from online_shopping.domain.entities.category import Category
from online_shopping.domain.entities.customer import Customer
from online_shopping.domain.entities.guest import Guest
from online_shopping.domain.entities.manager import Manager
from online_shopping.domain.entities.notification import Notification
from online_shopping.domain.entities.order import Order
from online_shopping.domain.entities.order_item import OrderItem
from online_shopping.domain.entities.order_log import OrderLog
from online_shopping.domain.entities.payment import Payment
from online_shopping.domain.entities.payment_method import PaymentMethod
from online_shopping.domain.entities.payment_transaction import PaymentTransaction
from online_shopping.domain.entities.product import Product
from online_shopping.domain.entities.product_approval import ProductApproval
from online_shopping.domain.entities.product_category import ProductCategory
from online_shopping.domain.entities.product_image import ProductImage
from online_shopping.domain.entities.product_review import ProductReview
from online_shopping.domain.entities.product_variant import ProductVariant
from online_shopping.domain.entities.shipment import Shipment
from online_shopping.domain.entities.shipment_log import ShipmentLog
from online_shopping.domain.entities.shop import Shop
from online_shopping.domain.entities.shopping_cart import ShoppingCart
from online_shopping.domain.entities.credit_card import CreditCard
from online_shopping.domain.entities.electronic_bank_transfer import ElectronicBankTransfer
from online_shopping.domain.enums.account_status import AccountStatus
from online_shopping.domain.enums.notification_channel import NotificationChannel
from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.enums.payment_method_type import PaymentMethodType
from online_shopping.domain.enums.payment_status import PaymentStatus
from online_shopping.domain.enums.shipment_status import ShipmentStatus
from online_shopping.domain.value_objects.account_values import Password, Username
from online_shopping.domain.value_objects.address import Address
from online_shopping.domain.value_objects.customer_values import Email, Name, Phone
from online_shopping.domain.value_objects.notification_values import Contact, NotificationContent, NotificationId
from online_shopping.domain.value_objects.order_values import CreationDate, OrderId, OrderItemId, OrderNumber
from online_shopping.domain.value_objects.payment_values import (
    AccountNumber,
    Amount,
    BankName,
    CardNumber,
    PaymentId,
    PaymentProvider,
    RoutingNumber,
    SecurityCode,
    TransactionId,
)
from online_shopping.domain.value_objects.product_values import (
    CategoryDescription,
    CategoryName,
    Price,
    ProductCount,
    ProductDescription,
    ProductId,
    ProductImageId,
    ProductImageUrl,
    ProductName,
    ProductVariantId,
    ProductVariantName,
    Quantity,
    Rating,
    ReviewContent,
    Sku,
)
from online_shopping.domain.value_objects.shipment_values import EstimatedArrival, ShipmentDate, ShipmentMethod
from online_shopping.domain.value_objects.store_values import CartItemId, RegionId, ShopId, ShopName


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_address() -> Address:
    return Address("123 Main St", "Beijing", "BJ", "100000", "China")


def _make_account() -> Account:
    return Account(
        user_name=Username("johndoe"),
        password=Password("password123"),
        status=AccountStatus.ACTIVE,
        name=Name("John", "Doe"),
        shipping_address=_make_address(),
        email=Email("john@example.com"),
        phone=Phone("+86", "13800138000"),
    )


def _make_category() -> Category:
    return Category(
        name=CategoryName("Bags"),
        description=CategoryDescription("Reusable bags"),
    )


def _make_variant(price: float = 29.0, count: int = 25) -> ProductVariant:
    return ProductVariant(
        variant_id=ProductVariantId("variant_default"),
        name=ProductVariantName("Default"),
        sku=Sku("SKU-DEFAULT"),
        price=Price(price),
        inventory_count=ProductCount(count),
    )


def _make_product(name: str = "Everyday Tote", price: float = 29.0) -> Product:
    return Product(
        name=ProductName(name),
        description=ProductDescription("A nice product."),
        price=Price(price),
        category=_make_category(),
        variants=[_make_variant(price=price)],
    )


# ── Product ──────────────────────────────────────────────────────────────

class TestProduct:
    def test_creation(self):
        p = _make_product()
        assert p.name == ProductName("Everyday Tote")
        assert p.slug.value == "everyday-tote"
        assert p.price == Price(29.0)

    def test_default_variant_created(self):
        p = Product(
            name=ProductName("Tote"),
            description=ProductDescription("Desc"),
            price=Price(10),
            category=_make_category(),
        )
        assert len(p.variants) == 1
        assert p.variants[0].name == ProductVariantName("Default Variant")

    def test_get_default_variant(self):
        p = _make_product()
        variant = p.get_default_variant()
        assert variant.variant_id == ProductVariantId("variant_default")

    def test_find_variant(self):
        p = _make_product()
        found = p.find_variant(ProductVariantId("variant_default"))
        assert found is not None
        assert p.find_variant(ProductVariantId("nonexistent")) is None

    def test_is_available(self):
        p = _make_product()
        assert p.is_available(2)
        assert p.is_available(1)
        assert not p.is_available(100)

    def test_get_available_count(self):
        p = _make_product()
        assert p.get_available_count().value == 25

    def test_with_images(self):
        img = ProductImage(ProductImageId("img1"), ProductImageUrl("/img.jpg"), rank=0)
        p = Product(
            name=ProductName("Tote"),
            description=ProductDescription("Desc"),
            price=Price(10),
            category=_make_category(),
            images=[img],
        )
        assert len(p.images) == 1
        assert p.images[0].image_id == ProductImageId("img1")

    def test_with_metadata(self):
        p = Product(
            name=ProductName("Tote"),
            description=ProductDescription("Desc"),
            price=Price(10),
            category=_make_category(),
            metadata={"color": "red"},
        )
        assert p.metadata == {"color": "red"}

    def test_product_id(self):
        p = Product(
            name=ProductName("Tote"),
            description=ProductDescription("Desc"),
            price=Price(10),
            category=_make_category(),
            product_id=ProductId(42),
        )
        assert p.product_id == ProductId(42)


# ── Category ─────────────────────────────────────────────────────────────

class TestCategory:
    def test_creation(self):
        c = _make_category()
        assert c.name == CategoryName("Bags")
        assert c.slug.value == "bags"

    def test_classify_product(self):
        c = _make_category()
        p = _make_product()
        result = c.classify_product(p)
        assert result is p
        assert len(c.products) == 1

    def test_with_id(self):
        from online_shopping.domain.value_objects.product_values import CategoryId
        c = Category(
            name=CategoryName("Home"),
            description=CategoryDescription("Home goods"),
            category_id=CategoryId(1),
        )
        assert c.category_id == CategoryId(1)


# ── ProductVariant ───────────────────────────────────────────────────────

class TestProductVariant:
    def test_creation(self):
        v = _make_variant()
        assert v.sku == Sku("SKU-DEFAULT")
        assert v.price == Price(29.0)
        assert v.manages_inventory is True
        assert v.allows_backorder is False

    def test_is_available_with_stock(self):
        v = _make_variant(count=10)
        assert v.is_available(5)
        assert v.is_available(10)

    def test_is_available_without_stock(self):
        v = _make_variant(count=10)
        assert not v.is_available(11)

    def test_is_available_zero_quantity(self):
        v = _make_variant()
        assert not v.is_available(0)

    def test_backorder_allows_any_quantity(self):
        v = ProductVariant(
            variant_id=ProductVariantId("v1"),
            name=ProductVariantName("Backorder Variant"),
            sku=Sku("SKU-BO"),
            price=Price(10),
            inventory_count=ProductCount(0),
            allows_backorder=True,
        )
        assert v.is_available(9999)

    def test_no_inventory_management_allows_any(self):
        v = ProductVariant(
            variant_id=ProductVariantId("v1"),
            name=ProductVariantName("NoMgmt"),
            sku=Sku("SKU-NM"),
            price=Price(10),
            inventory_count=ProductCount(0),
            manages_inventory=False,
        )
        assert v.is_available(9999)

    def test_currency_code(self):
        v = _make_variant()
        assert v.currency_code.value == "cny"


# ── ProductImage ─────────────────────────────────────────────────────────

class TestProductImage:
    def test_creation(self):
        img = ProductImage(ProductImageId("img1"), ProductImageUrl("/img.jpg"))
        assert img.rank == 0

    def test_with_rank(self):
        img = ProductImage(ProductImageId("img1"), ProductImageUrl("http://e.com/a.jpg"), rank=5)
        assert img.rank == 5

    def test_negative_rank_raises(self):
        with pytest.raises(ValueError):
            ProductImage(ProductImageId("img1"), ProductImageUrl("/img.jpg"), rank=-1)


# ── CartItem ─────────────────────────────────────────────────────────────

class TestCartItem:
    def test_creation(self):
        v = _make_variant(price=29.0)
        item = CartItem(quantity=Quantity(2), product_variant=v)
        assert item.quantity == Quantity(2)
        assert item.subtotal == 58.0

    def test_price_defaults_to_variant(self):
        v = _make_variant(price=29.0)
        item = CartItem(quantity=Quantity(1), product_variant=v)
        assert item.price == Price(29.0)

    def test_custom_price(self):
        v = _make_variant(price=29.0)
        item = CartItem(quantity=Quantity(2), product_variant=v, price=Price(25.0))
        assert item.price == Price(25.0)
        assert item.subtotal == 50.0

    def test_update_quantity(self):
        v = _make_variant(count=10)
        item = CartItem(quantity=Quantity(1), product_variant=v)
        assert item.update_quantity(Quantity(5))
        assert item.quantity == Quantity(5)

    def test_update_quantity_exceeds_stock(self):
        v = _make_variant(count=10)
        item = CartItem(quantity=Quantity(1), product_variant=v)
        assert not item.update_quantity(Quantity(20))
        assert item.quantity == Quantity(1)  # unchanged


# ── ShoppingCart ─────────────────────────────────────────────────────────

class TestShoppingCart:
    def test_creation(self):
        cart = ShoppingCart()
        assert len(cart.items) == 0
        assert cart.currency_code.value == "cny"
        assert cart.total_quantity == 0
        assert cart.subtotal == 0.0

    def test_add_item(self):
        cart = ShoppingCart()
        v = _make_variant(count=10)
        item = CartItem(quantity=Quantity(2), product_variant=v)
        assert cart.add_item(item)
        assert cart.total_quantity == 2
        assert cart.subtotal == 58.0

    def test_add_same_variant_merges(self):
        cart = ShoppingCart()
        v = _make_variant(count=10)
        cart.add_item(CartItem(quantity=Quantity(2), product_variant=v))
        cart.add_item(CartItem(quantity=Quantity(3), product_variant=v))
        assert cart.total_quantity == 5

    def test_add_item_not_available(self):
        cart = ShoppingCart()
        v = _make_variant(count=10)
        item = CartItem(quantity=Quantity(20), product_variant=v)
        assert not cart.add_item(item)
        assert cart.total_quantity == 0

    def test_remove_item(self):
        cart = ShoppingCart()
        v = _make_variant()
        item = CartItem(quantity=Quantity(1), product_variant=v, item_id=CartItemId("ci_1"))
        cart.add_item(item)
        assert cart.remove_item(CartItemId("ci_1"))
        assert len(cart.items) == 0

    def test_remove_nonexistent(self):
        cart = ShoppingCart()
        assert not cart.remove_item(CartItemId("nonexistent"))

    def test_get_items(self):
        cart = ShoppingCart()
        v = _make_variant()
        cart.add_item(CartItem(quantity=Quantity(1), product_variant=v))
        items = cart.get_items()
        assert len(items) == 1


# ── Order ────────────────────────────────────────────────────────────────

class TestOrder:
    def test_default_status(self):
        order = Order(OrderId(1))
        assert order.status == OrderStatus.CREATED

    def test_with_order_number(self):
        order = Order(OrderNumber("ORD-1001"), order_id=OrderId(1001))
        assert order.order_number == OrderNumber("ORD-1001")

    def test_subtotal(self):
        from online_shopping.domain.value_objects.product_values import CurrencyCode
        v = _make_variant(price=30.0)
        oi = OrderItem(unit_price=Price(30.0), quantity=Quantity(2), product_variant=v)
        order = Order(OrderNumber("ORD-1"), items=[oi])
        assert order.subtotal == 60.0

    def test_send_for_shipment_requires_processing(self):
        order = Order(OrderNumber("ORD-1"))
        assert not order.send_for_shipment()
        assert order.status == OrderStatus.CREATED

    def test_send_for_shipment_success(self):
        order = Order(OrderNumber("ORD-1"), status=OrderStatus.PROCESSING)
        assert order.send_for_shipment()
        assert order.status == OrderStatus.SHIPPED

    def test_items_property(self):
        order = Order(OrderNumber("ORD-1"), items=[])
        assert order.items == ()

    def test_with_payment(self):
        payment = Payment(PaymentStatus.PENDING, 100.0, "CNY")
        order = Order(OrderNumber("ORD-1"), payment=payment)
        assert order.payment is payment

    def test_currency_code_default(self):
        order = Order(OrderNumber("ORD-1"))
        assert order.currency_code.value == "cny"


# ── OrderItem ────────────────────────────────────────────────────────────

class TestOrderItem:
    def test_creation(self):
        v = _make_variant(price=29.0)
        oi = OrderItem(unit_price=Price(29.0), quantity=Quantity(3), product_variant=v)
        assert oi.subtotal == 87.0
        assert oi.product_variant_id == v.variant_id

    def test_with_id(self):
        v = _make_variant()
        oi = OrderItem(
            unit_price=Price(10.0),
            quantity=Quantity(1),
            product_variant=v,
            order_item_id=OrderItemId("oi_1"),
        )
        assert oi.order_item_id == OrderItemId("oi_1")


# ── Payment ──────────────────────────────────────────────────────────────

class TestPayment:
    def test_defaults(self):
        p = Payment()
        assert p.status == PaymentStatus.PENDING
        assert p.amount is None

    def test_with_values(self):
        p = Payment(PaymentStatus.PENDING, 20.126, "CNY")
        assert p.amount == Amount(20.13)
        assert p.currency.value == "cny"

    def test_process_payment(self):
        p = Payment(PaymentStatus.PENDING, 100.0, "CNY")
        assert p.process_payment() == PaymentStatus.COMPLETED
        assert p.status == PaymentStatus.COMPLETED

    def test_with_int_status(self):
        p = Payment(status=1)
        assert p.status == PaymentStatus.PENDING  # coerced

    def test_with_method_and_transaction(self):
        method = PaymentMethod(method_type=PaymentMethodType.CREDIT_CARD)
        txn = PaymentTransaction(status=PaymentStatus.PENDING)
        p = Payment(
            PaymentStatus.PENDING, 100.0, "CNY",
            method=method, transaction=txn,
        )
        assert p.method is method
        assert p.transaction is txn


# ── PaymentMethod ────────────────────────────────────────────────────────

class TestPaymentMethod:
    def test_credit_card(self):
        pm = PaymentMethod(method_type=PaymentMethodType.CREDIT_CARD)
        assert pm.method_type == PaymentMethodType.CREDIT_CARD

    def test_bank_transfer(self):
        pm = PaymentMethod(method_type=PaymentMethodType.ELECTRONIC_BANK_TRANSFER)
        assert pm.method_type == PaymentMethodType.ELECTRONIC_BANK_TRANSFER

    def test_with_card(self):
        card = CreditCard(
            name_on_card=Name("John", "Doe"),
            card_number=CardNumber("1234567890123456"),
            code=SecurityCode("123"),
            billing_address=Address("123 St", "City", "ST", "00000", "US"),
        )
        pm = PaymentMethod(PaymentMethodType.CREDIT_CARD, credit_card=card)
        assert pm.method_type == PaymentMethodType.CREDIT_CARD


# ── PaymentTransaction ───────────────────────────────────────────────────

class TestPaymentTransaction:
    def test_creation(self):
        txn = PaymentTransaction(
            status=PaymentStatus.COMPLETED,
            transaction_id=TransactionId("txn_1"),
            provider=PaymentProvider("Alipay"),
        )
        assert txn.status == PaymentStatus.COMPLETED

    def test_defaults(self):
        txn = PaymentTransaction(status=PaymentStatus.PENDING)
        assert txn.status == PaymentStatus.PENDING


# ── CreditCard ───────────────────────────────────────────────────────────

class TestCreditCard:
    def test_creation(self):
        card = CreditCard(
            name_on_card=Name("John", "Doe"),
            card_number=CardNumber("1234567890123456"),
            code=SecurityCode("123"),
            billing_address=Address("123 St", "City", "ST", "00000", "US"),
        )
        assert card is not None


# ── ElectronicBankTransfer ───────────────────────────────────────────────

class TestElectronicBankTransfer:
    def test_creation(self):
        ebt = ElectronicBankTransfer(
            bank_name=BankName("Bank of China"),
            routing_number=RoutingNumber("123456789"),
            account_number=AccountNumber("987654321"),
        )
        assert ebt.bank_name == BankName("Bank of China")
        assert ebt.routing_number == RoutingNumber("123456789")
        assert ebt.account_number == AccountNumber("987654321")


# ── Account ──────────────────────────────────────────────────────────────

class TestAccount:
    def test_creation(self):
        account = _make_account()
        assert account.status == AccountStatus.ACTIVE

    def test_block(self):
        account = _make_account()
        account.block()
        assert account.status == AccountStatus.BLOCKED

    def test_repr(self):
        account = _make_account()
        r = repr(account)
        assert "johndoe" in r

    def test_get_shipping_address(self):
        account = _make_account()
        addr = account.get_shipping_address()
        assert addr.city == "Beijing"


# ── Shop ─────────────────────────────────────────────────────────────────

class TestShop:
    def test_creation(self):
        account = _make_account()
        manager = Manager(account=account)
        shop = Shop(name=ShopName("My Shop"), manager=manager)
        assert shop.name == ShopName("My Shop")
        assert shop.manager is manager
        assert len(shop.products) == 0

    def test_add_approved_product(self):
        account = _make_account()
        manager = Manager(account=account)
        shop = Shop(name=ShopName("Shop"), manager=manager)
        product = _make_product()
        shop.add_approved_product(product)
        assert len(shop.products) == 1

    def test_update_product(self):
        account = _make_account()
        manager = Manager(account=account)
        shop = Shop(name=ShopName("Shop"), manager=manager)
        product = _make_product()
        product._Product__product_id = ProductId(1)
        shop.add_approved_product(product)
        updated = Product(
            name=ProductName("Updated"),
            description=ProductDescription("New"),
            price=Price(50),
            category=_make_category(),
            product_id=ProductId(1),
        )
        shop.update_product(updated)
        assert shop.products[0].name == ProductName("Updated")

    def test_remove_product(self):
        account = _make_account()
        manager = Manager(account=account)
        shop = Shop(name=ShopName("Shop"), manager=manager)
        product = _make_product()
        product._Product__product_id = ProductId(1)
        shop.add_approved_product(product)
        assert shop.remove_product(product)
        assert len(shop.products) == 0

    def test_uses_category(self):
        account = _make_account()
        manager = Manager(account=account)
        shop = Shop(name=ShopName("Shop"), manager=manager)
        shop.add_approved_product(_make_product())
        assert shop.uses_category(_make_category())

    def test_assign_manager(self):
        account = _make_account()
        m1 = Manager(account=account)
        shop = Shop(name=ShopName("Shop"), manager=m1)
        m2 = Manager(account=_make_account())
        result = shop.assign_manager(m2)
        assert result is m2
        assert shop.manager is m2


# ── Customer ─────────────────────────────────────────────────────────────

class TestCustomer:
    def test_creation(self):
        account = _make_account()
        cart = ShoppingCart()
        customer = Customer(account=account, shopping_cart=cart)
        assert customer.account is account
        assert customer.get_shopping_cart() is cart
        assert len(customer.orders) == 0

    def test_place_order_raises_without_order(self):
        account = _make_account()
        customer = Customer(account=account, shopping_cart=ShoppingCart())
        with pytest.raises(ValueError, match="No order"):
            customer.place_order()

    def test_add_product_review(self):
        account = _make_account()
        customer = Customer(account=account, shopping_cart=ShoppingCart())
        review = customer.add_product_review(_make_product())
        assert review.get_rating() == Rating(5)
        assert len(customer.product_reviews) == 1


# ── Admin ────────────────────────────────────────────────────────────────

class TestAdmin:
    def test_creation(self):
        admin = Admin(account=_make_account())
        assert admin.account.status == AccountStatus.ACTIVE
        assert len(admin.shops) == 0
        assert len(admin.categories) == 0

    def test_block_user(self):
        admin = Admin(account=_make_account())
        target = _make_account()
        assert admin.block_user(target)
        assert target.status == AccountStatus.BLOCKED

    def test_review_shop(self):
        admin = Admin(account=_make_account())
        manager = Manager(account=_make_account())
        shop = Shop(name=ShopName("Shop"), manager=manager)
        assert admin.review_shop(shop)

    def test_add_category(self):
        admin = Admin(account=_make_account())
        cat = _make_category()
        assert admin.add_category(cat) is cat
        assert len(admin.categories) == 1

    def test_remove_category(self):
        admin = Admin(account=_make_account())
        from online_shopping.domain.value_objects.product_values import CategoryId
        cat = Category(
            name=CategoryName("Test"),
            description=CategoryDescription("Test"),
            category_id=CategoryId(1),
        )
        admin.add_category(cat)
        assert admin.remove_category(cat)
        assert len(admin.categories) == 0

    def test_modify_category(self):
        admin = Admin(account=_make_account())
        cat = _make_category()
        assert admin.modify_category(cat) is cat


# ── Manager ──────────────────────────────────────────────────────────────

class TestManager:
    def test_creation(self):
        mgr = Manager(account=_make_account())
        assert mgr.account.status == AccountStatus.ACTIVE
        assert len(mgr.managed_shops) == 0

    def test_add_shop(self):
        mgr = Manager(account=_make_account())
        shop = Shop(name=ShopName("Shop"), manager=mgr)
        assert mgr.add_shop(shop) is shop
        assert len(mgr.managed_shops) == 1

    def test_request_product_approval(self):
        mgr = Manager(account=_make_account())
        shop = Shop(name=ShopName("Shop"), manager=mgr)
        product = _make_product()
        approval = mgr.request_product_approval(shop, product)
        assert approval.product is product
        assert approval.shop is shop

    def test_confirm_product_approval(self):
        mgr = Manager(account=_make_account())
        shop = Shop(name=ShopName("Shop"), manager=mgr)
        product = _make_product()
        approval = ProductApproval(product=product, shop=shop, manager=mgr)
        assert mgr.confirm_product_approval(approval)
        assert approval.confirmed

    def test_confirm_by_wrong_manager(self):
        mgr = Manager(account=_make_account())
        shop = Shop(name=ShopName("Shop"), manager=mgr)
        product = _make_product()
        approval = ProductApproval(product=product, shop=shop, manager=mgr)
        other_mgr = Manager(account=_make_account())
        assert not other_mgr.confirm_product_approval(approval)
        assert not approval.confirmed

    def test_list_shop_products(self):
        mgr = Manager(account=_make_account())
        shop = Shop(name=ShopName("Shop"), manager=mgr)
        shop.add_approved_product(_make_product())
        products = mgr.list_shop_products(shop)
        assert len(products) == 1


# ── Guest ────────────────────────────────────────────────────────────────

class TestGuest:
    def test_register_account(self):
        guest = Guest()
        account = _make_account()
        assert guest.register_account(account) is account


# ── ProductApproval ──────────────────────────────────────────────────────

class TestProductApproval:
    def test_creation(self):
        mgr = Manager(account=_make_account())
        shop = Shop(name=ShopName("Shop"), manager=mgr)
        product = _make_product()
        approval = ProductApproval(product=product, shop=shop, manager=mgr)
        assert not approval.confirmed

    def test_confirm_adds_product_to_shop(self):
        mgr = Manager(account=_make_account())
        shop = Shop(name=ShopName("Shop"), manager=mgr)
        product = _make_product()
        approval = ProductApproval(product=product, shop=shop, manager=mgr)
        assert approval.confirm(mgr)
        assert len(shop.products) == 1


# ── Notification ─────────────────────────────────────────────────────────

class TestNotification:
    def test_creation(self):
        n = Notification(
            notification_id=NotificationId(1),
            channel=NotificationChannel.EMAIL,
            receiver=Contact("user@example.com"),
            created_on=CreationDate(datetime.now(timezone.utc)),
            content=NotificationContent("Hello"),
        )
        assert n.channel == NotificationChannel.EMAIL
        assert n.receiver == Contact("user@example.com")
        assert n.send_notification()


# ── OrderLog ─────────────────────────────────────────────────────────────

class TestOrderLog:
    def test_creation(self):
        now = datetime.now(timezone.utc)
        log = OrderLog(creation_date=CreationDate(now), status=OrderStatus.CREATED)

    def test_trigger_notifications(self):
        now = datetime.now(timezone.utc)
        log = OrderLog(creation_date=CreationDate(now), status=OrderStatus.SHIPPED)
        notif = Notification(
            NotificationId(1), NotificationChannel.EMAIL,
            Contact("u@e.com"), CreationDate(now), NotificationContent("Shipped!"),
        )
        result = log.trigger_notifications([notif])
        assert len(result) == 1


# ── ShipmentLog ──────────────────────────────────────────────────────────

class TestShipmentLog:
    def test_creation(self):
        now = datetime.now(timezone.utc)
        log = ShipmentLog(status=ShipmentStatus.PENDING, creation_date=CreationDate(now))

    def test_trigger_notifications(self):
        now = datetime.now(timezone.utc)
        log = ShipmentLog(status=ShipmentStatus.SHIPPED, creation_date=CreationDate(now))
        notif = Notification(
            NotificationId(1), NotificationChannel.SMS,
            Contact("+8613800138000"), CreationDate(now), NotificationContent("Shipped"),
        )
        result = log.trigger_notifications([notif])
        assert len(result) == 1


# ── Shipment ─────────────────────────────────────────────────────────────

class TestShipment:
    def test_creation(self):
        s = Shipment(
            shipment_date=ShipmentDate("2024-01-01"),
            estimated_arrival=EstimatedArrival("2024-01-05"),
            shipment_method=ShipmentMethod("Express"),
        )


# ── ProductCategory ──────────────────────────────────────────────────────

class TestProductCategory:
    def test_is_category(self):
        assert ProductCategory is Category


# ── ProductReview ────────────────────────────────────────────────────────

class TestProductReview:
    def test_creation(self):
        review = ProductReview(
            rating=Rating(4),
            review=ReviewContent("Great product!"),
            product=_make_product(),
        )
        assert review.get_rating() == Rating(4)
