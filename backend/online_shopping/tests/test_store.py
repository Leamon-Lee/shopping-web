"""Tests for the in-memory store used by native API endpoints."""

from online_shopping.api import store
from online_shopping.api.schemas import (
    CartItemCreate,
    CategoryOut,
    OrderCreate,
    PaymentCreate,
    ProductCreate,
    PaymentOut,
)
from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.enums.payment_status import PaymentStatus


class TestListProducts:
    def test_initial_products(self):
        products = store.list_products()
        assert len(products) >= 3
        names = {p.name for p in products}
        assert "Everyday Tote" in names

    def test_product_has_category(self):
        products = store.list_products()
        tote = next(p for p in products if p.name == "Everyday Tote")
        assert tote.category.name == "Bags"


class TestListCategories:
    def test_deduplicates(self):
        categories = store.list_categories()
        assert len(categories) == 3
        cat_names = {c.name for c in categories}
        assert cat_names == {"Bags", "Home", "Stationery"}


class TestFindProduct:
    def test_by_exact_name(self):
        p = store.find_product("Everyday Tote")
        assert p is not None
        assert p.name == "Everyday Tote"

    def test_case_insensitive(self):
        p = store.find_product("everyday tote")
        assert p is not None
        assert p.name == "Everyday Tote"

    def test_nonexistent(self):
        assert store.find_product("Nonexistent") is None


class TestCreateProduct:
    def test_adds_product(self):
        before = len(store.list_products())
        payload = ProductCreate(
            name="New Product",
            description="Desc",
            price=10.0,
            available_item_count=5,
            category=CategoryOut(name="Test"),
        )
        result = store.create_product(payload)
        assert result.name == "New Product"
        assert len(store.list_products()) == before + 1


class TestCartOperations:
    def setup_method(self):
        store._cart_items.clear()

    def test_empty_cart(self):
        cart = store.get_cart()
        assert cart.total_quantity == 0
        assert cart.subtotal == 0.0

    def test_add_item(self):
        item = store.add_cart_item(CartItemCreate(product_name="Everyday Tote", quantity=2))
        assert item is not None
        assert item.quantity == 2

    def test_add_item_nonexistent_product(self):
        assert store.add_cart_item(CartItemCreate(product_name="NoProduct", quantity=1)) is None

    def test_add_duplicate_merges(self):
        store.add_cart_item(CartItemCreate(product_name="Everyday Tote", quantity=2))
        store.add_cart_item(CartItemCreate(product_name="Everyday Tote", quantity=3))
        cart = store.get_cart()
        assert cart.total_quantity == 5
        assert len(cart.items) == 1

    def test_update_item(self):
        store.add_cart_item(CartItemCreate(product_name="Everyday Tote", quantity=1))
        updated = store.update_cart_item("Everyday Tote", 5)
        assert updated is not None
        assert updated.quantity == 5

    def test_update_nonexistent(self):
        assert store.update_cart_item("NoProduct", 5) is None

    def test_remove_item(self):
        store.add_cart_item(CartItemCreate(product_name="Everyday Tote", quantity=1))
        assert store.remove_cart_item("Everyday Tote")
        assert store.get_cart().total_quantity == 0

    def test_remove_nonexistent(self):
        assert not store.remove_cart_item("NoProduct")


class TestOrderOperations:
    def setup_method(self):
        store._cart_items.clear()
        store._orders.clear()

    def test_create_order(self):
        store.add_cart_item(CartItemCreate(product_name="Everyday Tote", quantity=1))
        order = store.create_order(OrderCreate())
        assert order is not None
        assert order.order_number.startswith("ORD-")
        assert order.status == OrderStatus.CREATED

    def test_create_order_with_items(self):
        order = store.create_order(OrderCreate(
            items=[CartItemCreate(product_name="Everyday Tote", quantity=1)],
            payment=PaymentCreate(amount=29.0),
        ))
        assert order is not None
        assert order.payment is not None
        assert order.payment.status == PaymentStatus.PENDING

    def test_list_orders(self):
        store.add_cart_item(CartItemCreate(product_name="Everyday Tote", quantity=1))
        store.create_order(OrderCreate())
        orders = store.list_orders()
        assert len(orders) == 1

    def test_get_order(self):
        store.add_cart_item(CartItemCreate(product_name="Everyday Tote", quantity=1))
        order = store.create_order(OrderCreate())
        assert order is not None
        found = store.get_order(order.order_number)
        assert found is not None
        assert found.order_number == order.order_number

    def test_get_nonexistent_order(self):
        assert store.get_order("NONEXISTENT") is None

    def test_create_order_with_custom_number(self):
        store.add_cart_item(CartItemCreate(product_name="Everyday Tote", quantity=1))
        order = store.create_order(OrderCreate(order_number="CUSTOM-001"))
        assert order is not None
        assert order.order_number == "CUSTOM-001"


class TestPaymentProcessing:
    def test_process_payment(self):
        payload = PaymentOut(status=PaymentStatus.PENDING, amount=100.0, currency="CNY")
        result = store.process_payment(payload)
        assert result.status == PaymentStatus.COMPLETED
