from fastapi import APIRouter, HTTPException, status

from online_shopping.api import store
from online_shopping.api.schemas import CartItemCreate, CartItemUpdate, ShoppingCartOut

router = APIRouter()


@router.get("", response_model=ShoppingCartOut)
def get_cart() -> ShoppingCartOut:
    return store.get_cart()


@router.post("/items", response_model=ShoppingCartOut, status_code=status.HTTP_201_CREATED)
def add_item(payload: CartItemCreate) -> ShoppingCartOut:
    item = store.add_cart_item(payload)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    return store.get_cart()


@router.patch("/items/{product_name}", response_model=ShoppingCartOut)
def update_item(product_name: str, payload: CartItemUpdate) -> ShoppingCartOut:
    item = store.update_cart_item(product_name, payload.quantity)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found.",
        )
    return store.get_cart()


@router.delete("/items/{product_name}", response_model=ShoppingCartOut)
def remove_item(product_name: str) -> ShoppingCartOut:
    removed = store.remove_cart_item(product_name)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found.",
        )
    return store.get_cart()
