from fastapi import APIRouter, HTTPException, status

from online_shopping.api import store
from online_shopping.api.schemas import CategoryOut, ProductCreate, ProductOut

router = APIRouter()


@router.get("", response_model=list[ProductOut])
def list_products() -> list[ProductOut]:
    return store.list_products()


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate) -> ProductOut:
    if store.find_product(payload.name) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product with this name already exists.",
        )
    return store.create_product(payload)


@router.get("/categories", response_model=list[CategoryOut])
def list_categories() -> list[CategoryOut]:
    return store.list_categories()


@router.get("/{product_name}", response_model=ProductOut)
def get_product(product_name: str) -> ProductOut:
    product = store.find_product(product_name)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    return product
