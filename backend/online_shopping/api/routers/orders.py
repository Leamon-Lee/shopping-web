from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_current_user, get_db
from online_shopping.api.mappers import order_to_out
from online_shopping.api.schemas import OrderCreate, OrderOut
from online_shopping.models.account import Account
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
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderOut:
    """Place a new order for the authenticated user."""
    order = await OrderService(db).place_order(payload, email=current_user.email)
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
