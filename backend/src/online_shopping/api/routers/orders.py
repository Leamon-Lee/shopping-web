from fastapi import APIRouter, HTTPException, status

from online_shopping.api import store
from online_shopping.api.schemas import OrderCreate, OrderOut

router = APIRouter()


@router.get("", response_model=list[OrderOut])
def list_orders() -> list[OrderOut]:
    return store.list_orders()


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate) -> OrderOut:
    order = store.create_order(payload)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more products were not found.",
        )
    return order


@router.get("/{order_number}", response_model=OrderOut)
def get_order(order_number: str) -> OrderOut:
    order = store.get_order(order_number)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )
    return order
