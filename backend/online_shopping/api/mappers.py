from __future__ import annotations

from online_shopping.api.schemas import (
    CartItemOut,
    CategoryOut,
    ImageOut,
    OrderOut,
    PaymentOut,
    ProductOut,
    ProductVariantOut,
    ShoppingCartOut,
)
from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.enums.payment_status import PaymentStatus
from online_shopping.models.cart import CartItem, ShoppingCart
from online_shopping.models.order import Order
from online_shopping.models.product import Product
from online_shopping.models.product_variant import ProductVariant


def image_to_out(image) -> ImageOut:
    return ImageOut(image_url=image.image_url, url=image.image_url, rank=image.rank)


def variant_to_out(variant: ProductVariant, include_product: bool = False) -> ProductVariantOut:
    product_payload = None
    if include_product:
        product_payload = {
            "id": str(variant.product.id),
            "title": variant.product.name,
            "handle": variant.product.slug,
            "images": [image_to_out(image).model_dump() for image in variant.product.images],
        }

    return ProductVariantOut(
        id=str(variant.id),
        title=variant.name,
        name=variant.name,
        sku=variant.sku,
        price=float(variant.price),
        inventory_quantity=variant.inventory_count,
        inventory_count=variant.inventory_count,
        manage_inventory=variant.manages_inventory,
        allow_backorder=variant.allows_backorder,
        product=product_payload,
    )


def product_to_out(product: Product) -> ProductOut:
    category = product.category
    images = sorted(product.images, key=lambda img: img.rank)
    image_outputs = [image_to_out(img) for img in images]
    return ProductOut(
        id=str(product.id),
        name=product.name,
        title=product.name,
        slug=product.slug,
        handle=product.slug,
        description=product.description,
        price=float(product.price),
        available_item_count=product.available_item_count,
        category=CategoryOut(
            name=category.name if category else "",
            description=category.description if category else "",
        ),
        thumbnail=image_outputs[0].image_url if image_outputs else None,
        images=image_outputs,
        variants=[variant_to_out(variant) for variant in product.variants],
    )


def cart_item_to_out(item: CartItem) -> CartItemOut:
    product = item.variant.product
    product_out = product_to_out(product)
    unit_price = float(item.price)
    total = round(unit_price * item.quantity, 2)
    return CartItemOut(
        id=str(item.id),
        quantity=item.quantity,
        price=unit_price,
        unit_price=unit_price,
        total=total,
        product=product_out,
        product_title=product.name,
        product_handle=product.slug,
        thumbnail=product_out.thumbnail,
        variant=variant_to_out(item.variant, include_product=True),
        created_at=item.created_at.isoformat() if item.created_at else None,
    )


def cart_to_out(cart: ShoppingCart) -> ShoppingCartOut:
    items = [cart_item_to_out(item) for item in cart.items]
    subtotal = round(sum((item.total or 0) for item in items), 2)
    total_quantity = sum(item.quantity for item in items)

    shipping_methods = []
    if cart.shipping_method:
        shipping_methods = [cart.shipping_method]

    payment_collection = None
    if cart.payment_session:
        payment_collection = {
            "id": f"paycol_{cart.id}",
            "payment_sessions": [cart.payment_session],
        }

    return ShoppingCartOut(
        id=str(cart.id),
        email=cart.email,
        items=items,
        total_quantity=total_quantity,
        subtotal=subtotal,
        total=subtotal,
        currency_code=cart.currency_code,
        region={"id": cart.region_id or "reg_cny", "currency_code": cart.currency_code},
        shipping_address=cart.shipping_address,
        billing_address=cart.billing_address,
        shipping_methods=shipping_methods,
        payment_collection=payment_collection,
    )


def order_to_out(order: Order) -> OrderOut:
    items = [
        CartItemOut(
            id=str(item.id),
            quantity=item.quantity,
            price=float(item.price),
            unit_price=float(item.price),
            total=round(float(item.price) * item.quantity, 2),
            product=ProductOut(
                id=str(item.product_id) if item.product_id else None,
                name=item.product_name,
                title=item.product_name,
                description="",
                price=float(item.price),
                available_item_count=0,
                category=CategoryOut(name="", description=""),
            ),
            product_title=item.product_name,
            product_handle=item.product_name.lower().replace(" ", "-"),
        )
        for item in order.items
    ]

    payment = None
    if order.payments:
        p = order.payments[0]
        payment = PaymentOut(status=PaymentStatus(p.status), amount=float(p.amount), currency=p.currency)

    subtotal = round(sum((item.total or 0) for item in items), 2)

    shipments = []
    if order.shipments:
        for s in order.shipments:
            shipments.append({
                "status": s.status,
                "shipment_date": s.shipped_at.isoformat() if s.shipped_at else None,
                "estimated_arrival": s.estimated_arrival.isoformat() if s.estimated_arrival else None,
                "shipment_method": s.carrier,
            })

    # Attach shop info to each item
    for idx, item in enumerate(items):
        if idx < len(order.items):
            oi = order.items[idx]
            if oi.shop_name:
                item.product.shop = {
                    "shop_id": str(oi.shop_id) if oi.shop_id else None,
                    "shop_name": oi.shop_name,
                }

    return OrderOut(
        id=str(order.id),
        order_number=order.order_number,
        status=OrderStatus(order.status),
        order_date=order.order_date.isoformat() if order.order_date else None,
        email=order.email,
        items=items,
        payment=payment,
        shipments=shipments,
        shipping_address=order.shipping_address,
        billing_address=order.billing_address,
        shipping_method=order.shipping_method,
        subtotal=subtotal,
        total=subtotal,
        currency_code="cny",
        access_token=order.order_access_token,
    )
