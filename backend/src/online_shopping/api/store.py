from itertools import count

from online_shopping.api.schemas import (
    CartItemCreate,
    CartItemOut,
    CategoryOut,
    OrderCreate,
    OrderOut,
    PaymentOut,
    ProductCreate,
    ProductOut,
    ShoppingCartOut,
)
from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.enums.payment_status import PaymentStatus


_order_numbers = count(1001)

_products: list[ProductOut] = [
    ProductOut(
        name="Everyday Tote",
        description="Durable cotton tote for daily shopping.",
        price=29.0,
        available_item_count=25,
        category=CategoryOut(name="Bags", description="Reusable shopping bags"),
    ),
    ProductOut(
        name="Ceramic Mug",
        description="Simple glazed mug for coffee or tea.",
        price=18.0,
        available_item_count=40,
        category=CategoryOut(name="Home", description="Useful home goods"),
    ),
    ProductOut(
        name="Notebook Set",
        description="Three ruled notebooks for work and study.",
        price=12.5,
        available_item_count=60,
        category=CategoryOut(name="Stationery", description="Paper and desk items"),
    ),
]
_cart_items: list[CartItemOut] = []
_orders: dict[str, OrderOut] = {}


def list_products() -> list[ProductOut]:
    return _products


def list_categories() -> list[CategoryOut]:
    categories: dict[str, CategoryOut] = {}
    for product in _products:
        categories[product.category.name.lower()] = product.category
    return list(categories.values())


def find_product(product_name: str) -> ProductOut | None:
    normalized_name = product_name.casefold()
    return next(
        (product for product in _products if product.name.casefold() == normalized_name),
        None,
    )


def create_product(payload: ProductCreate) -> ProductOut:
    product = ProductOut(**payload.model_dump())
    _products.append(product)
    return product


def get_cart() -> ShoppingCartOut:
    subtotal = sum(item.price * item.quantity for item in _cart_items)
    total_quantity = sum(item.quantity for item in _cart_items)
    return ShoppingCartOut(
        items=_cart_items,
        subtotal=round(subtotal, 2),
        total_quantity=total_quantity,
    )


def add_cart_item(payload: CartItemCreate) -> CartItemOut | None:
    product = find_product(payload.product_name)
    if product is None:
        return None

    existing_item = next(
        (
            item
            for item in _cart_items
            if item.product.name.casefold() == product.name.casefold()
        ),
        None,
    )
    if existing_item:
        existing_item.quantity += payload.quantity
        return existing_item

    item = CartItemOut(quantity=payload.quantity, price=product.price, product=product)
    _cart_items.append(item)
    return item


def update_cart_item(product_name: str, quantity: int) -> CartItemOut | None:
    item = next(
        (
            cart_item
            for cart_item in _cart_items
            if cart_item.product.name.casefold() == product_name.casefold()
        ),
        None,
    )
    if item is None:
        return None
    item.quantity = quantity
    return item


def remove_cart_item(product_name: str) -> bool:
    before_count = len(_cart_items)
    _cart_items[:] = [
        item
        for item in _cart_items
        if item.product.name.casefold() != product_name.casefold()
    ]
    return len(_cart_items) != before_count


def list_orders() -> list[OrderOut]:
    return list(_orders.values())


def get_order(order_number: str) -> OrderOut | None:
    return _orders.get(order_number)


def create_order(payload: OrderCreate) -> OrderOut | None:
    items = [add_cart_item(item) for item in payload.items] if payload.items else _cart_items
    if any(item is None for item in items):
        return None

    order_number = payload.order_number or f"ORD-{next(_order_numbers)}"
    payment = None
    if payload.payment is not None:
        payment = PaymentOut(
            status=PaymentStatus.PENDING,
            amount=payload.payment.amount,
            currency=payload.payment.currency,
        )
    order = OrderOut(
        order_number=order_number,
        status=OrderStatus.PENDING,
        items=[item for item in items if item is not None],
        payment=payment,
    )
    _orders[order.order_number] = order
    return order


def process_payment(payload: PaymentOut) -> PaymentOut:
    payload.status = PaymentStatus.COMPLETED
    return payload
