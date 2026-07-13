from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_shopping.api.deps import get_current_user, get_db, get_optional_user
from online_shopping.api.mappers import order_to_out
from online_shopping.api.schemas import OrderCreate, OrderOut
from online_shopping.models.account import Account
from online_shopping.models.order import Order
from online_shopping.services.order_service import OrderService

router = APIRouter()


@router.get("", response_model=list[OrderOut])
async def list_orders(
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[OrderOut]:
    """List orders for the authenticated user."""
    orders = await OrderService(db).list_orders(email=current_user.email)
    return [order_to_out(order) for order in orders]


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> OrderOut:
    """Place a new order. Works for both guests and authenticated users."""
    order = await OrderService(db).place_order(
        payload,
        email=current_user.email if current_user else None,
    )
    return order_to_out(order)


@router.get("/{order_number}", response_model=OrderOut)
async def get_order(
    order_number: str,
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderOut:
    """Get a specific order by number."""
    order = await OrderService(db).get_order(order_number)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return order_to_out(order)


@router.patch("/{order_number}/complete", response_model=OrderOut)
async def complete_order(
    order_number: str,
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderOut:
    """Mark an order as completed (confirm receipt)."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.payments))
        .where(Order.order_number == order_number, Order.account_id == current_user.id)
    )
    order = result.scalars().first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    if order.status == "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order is already completed.")
    order.status = "completed"
    await db.commit()
    await db.refresh(order)
    return order_to_out(order)


@router.delete("/{order_number}", status_code=status.HTTP_200_OK)
async def delete_order(
    order_number: str,
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete an order (completed orders only)."""
    result = await db.execute(
        select(Order).where(
            Order.order_number == order_number,
            Order.account_id == current_user.id,
        )
    )
    order = result.scalars().first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    if order.status != "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only completed orders can be deleted.")
    await db.delete(order)
    await db.commit()
    return {"deleted": True, "order_number": order_number}
