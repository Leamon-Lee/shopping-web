from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_current_user, get_db, get_optional_user
from online_shopping.api.mappers import order_to_out
from online_shopping.api.schemas import OrderCreate, OrderOut
from online_shopping.models.account import Account
from online_shopping.services.order_service import OrderService

router = APIRouter()


def _cart_id_from_header(x_cart_id: str | None = Header(None)) -> str | None:
    return x_cart_id


def _access_token_from_query(token: str | None = Query(None, alias="token")) -> str | None:
    return token


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
    cart_id: str | None = Depends(_cart_id_from_header),
) -> OrderOut:
    """Place a new order. Guest orders receive an access_token for secure retrieval."""
    order = await OrderService(db).place_order(
        payload,
        email=current_user.email if current_user else None,
        cart_id=cart_id,
    )
    return order_to_out(order)


@router.get("/{order_number}", response_model=OrderOut)
async def get_order(
    order_number: str,
    current_user: Account | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    token: str | None = Depends(_access_token_from_query),
) -> OrderOut:
    """Get a specific order by number.

    - Authenticated users: can only see their own orders.
    - Guest users: MUST provide the order_access_token returned at creation.
    """
    order = await OrderService(db).get_order(order_number)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    # Authenticated user: must own the order
    if current_user:
        if order.account_id is not None and order.account_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Order does not belong to you.",
            )
        return order_to_out(order)

    # Guest: must provide matching access token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token required for guest orders. Use ?token=... parameter.",
        )
    if order.order_access_token != token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid access token for this order.",
        )

    return order_to_out(order)
