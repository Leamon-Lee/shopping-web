from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_shopping.api.deps import get_db
from online_shopping.api.schemas import OrderCreate, OrderOut, CartItemOut, ProductOut, CategoryOut, PaymentOut, ShipmentOut
from online_shopping.models.order import Order, OrderItem
from online_shopping.models.payment import Payment
from online_shopping.models.product import Product
from online_shopping.domain.enums.order_status import OrderStatus
from online_shopping.domain.enums.payment_status import PaymentStatus
from online_shopping.domain.enums.shipment_status import ShipmentStatus
from itertools import count

_order_numbers = count(1001)

router = APIRouter()


def _product_to_out(product: Product) -> ProductOut:
    category = product.category
    return ProductOut(
        name=product.name,
        description=product.description,
        price=float(product.price),
        available_item_count=product.available_item_count,
        category=CategoryOut(
            name=category.name if category else "",
            description=category.description if category else "",
        ),
    )


def _order_to_out(order: Order) -> OrderOut:
    items = [
        CartItemOut(
            quantity=item.quantity,
            price=float(item.price),
            product=ProductOut(
                name=item.product_name,
                description="",
                price=float(item.price),
                available_item_count=0,
                category=CategoryOut(name="", description=""),
            ),
        )
        for item in order.items
    ]
    subtotal = sum(item.price * item.quantity for item in items)
    total_quantity = sum(item.quantity for item in items)

    payment = None
    if order.payments:
        p = order.payments[0]
        payment = PaymentOut(status=PaymentStatus(p.status), amount=float(p.amount), currency=p.currency)

    return OrderOut(
        order_number=order.order_number,
        status=OrderStatus(order.status),
        order_date=order.order_date.isoformat() if order.order_date else None,
        items=items,
        payment=payment,
        shipments=[],
    )


@router.get("", response_model=list[OrderOut])
async def list_orders(db: AsyncSession = Depends(get_db)) -> list[OrderOut]:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.payments))
        .order_by(Order.created_at.desc())
    )
    return [_order_to_out(o) for o in result.scalars().all()]


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(payload: OrderCreate, db: AsyncSession = Depends(get_db)) -> OrderOut:
    if not payload.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order must have at least one item.")

    order_number = payload.order_number or f"ORD-{next(_order_numbers)}"

    # Validate all products exist
    validated_items = []
    for item in payload.items:
        result = await db.execute(
            select(Product).where(Product.name.ilike(item.product_name))
        )
        product = result.scalars().first()
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product '{item.product_name}' not found.")
        validated_items.append((product, item.quantity))

    order = Order(order_number=order_number, status=OrderStatus.PENDING.value)
    db.add(order)
    await db.flush()

    for product, quantity in validated_items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            quantity=quantity,
            price=product.price,
        ))

    if payload.payment:
        db.add(Payment(
            order_id=order.id,
            status=PaymentStatus.PENDING.value,
            amount=payload.payment.amount,
            currency=payload.payment.currency,
        ))

    await db.commit()
    await db.refresh(order)

    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.payments))
        .where(Order.id == order.id)
    )
    return _order_to_out(result.scalars().one())


@router.get("/{order_number}", response_model=OrderOut)
async def get_order(order_number: str, db: AsyncSession = Depends(get_db)) -> OrderOut:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.payments))
        .where(Order.order_number == order_number)
    )
    order = result.scalars().first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return _order_to_out(order)
