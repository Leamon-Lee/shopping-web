"""Admin and Manager panel endpoints — role-scoped, shop-ownership-aware."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_db, require_admin, require_manager
from online_shopping.models.account import Account
from online_shopping.models.category import ProductCategory
from online_shopping.models.product import Product
from online_shopping.repositories.shop_repository import ShopRepository
from online_shopping.services.admin_service import AdminService
from online_shopping.services.manager_service import ManagerService

router = APIRouter()


# ── Request schemas ────────────────────────────────────────────────

class ShopCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    category: str | None = None

class ShopUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None

class ShopApprovalRequest(BaseModel):
    status: str = Field(pattern="^(active|rejected)$")

class InventoryUpdateRequest(BaseModel):
    inventory_count: int = Field(ge=0)

class ShipmentCreateRequest(BaseModel):
    carrier: str | None = None
    tracking_number: str | None = None
    tracking_url: str | None = None

class ProductCreateByManagerRequest(BaseModel):
    shop_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    price: float = Field(gt=0)
    available_item_count: int = Field(ge=0, default=0)
    category: dict | None = None

class ProductUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    available_item_count: int | None = None
    status: str | None = None

class UserStatusRequest(BaseModel):
    status: str = Field(pattern="^(active|blocked|banned)$")

class UserRoleRequest(BaseModel):
    role: str = Field(pattern="^(customer|manager|admin)$")

class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""

class ProductStatusRequest(BaseModel):
    status: str = Field(pattern="^(active|hidden|rejected)$")

class OrderStatusUpdateRequest(BaseModel):
    status: str = Field(pattern="^(confirmed|processing|shipped)$")


# ── Manager endpoints ──────────────────────────────────────────────

@router.get("/manager/dashboard")
async def manager_dashboard(
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await ManagerService(db).dashboard(current_user)

@router.get("/manager/shops")
async def manager_shops(
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    shops = await ShopRepository(db).list_by_owner(current_user.id)
    return {
        "shops": [
            {"id": str(s.id), "name": s.name, "slug": s.slug, "status": s.status, "category": s.category}
            for s in shops
        ]
    }

@router.post("/manager/shops", status_code=status.HTTP_201_CREATED)
async def manager_create_shop(
    payload: ShopCreateRequest,
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await ManagerService(db).create_shop(current_user, payload.model_dump())

@router.patch("/manager/shops/{shop_id}")
async def manager_update_shop(
    shop_id: UUID,
    payload: ShopUpdateRequest,
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await ManagerService(db).update_shop(current_user, shop_id, payload.model_dump(exclude_none=True))

@router.get("/manager/products")
async def manager_products(
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    products = await ManagerService(db).list_products(current_user)
    return {"products": products, "total": len(products)}

@router.post("/manager/products", status_code=status.HTTP_201_CREATED)
async def manager_create_product(
    payload: ProductCreateByManagerRequest,
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await ManagerService(db).create_product(current_user, payload.model_dump())

@router.patch("/manager/products/{product_id}")
async def manager_update_product(
    product_id: UUID,
    payload: ProductUpdateRequest,
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await ManagerService(db).update_product(current_user, product_id, payload.model_dump(exclude_none=True))

@router.patch("/manager/inventory/{variant_id}")
async def manager_update_inventory(
    variant_id: UUID,
    payload: InventoryUpdateRequest,
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await ManagerService(db).update_inventory(current_user, variant_id, payload.inventory_count)

@router.get("/manager/orders")
async def manager_orders(
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    orders = await ManagerService(db).list_orders(current_user)
    return {"orders": orders, "total": len(orders)}

@router.get("/manager/orders/{order_number}")
async def manager_order_detail(
    order_number: str,
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await ManagerService(db).get_manager_order_detail(current_user, order_number)

@router.patch("/manager/orders/{order_number}/status")
async def manager_update_order_status(
    order_number: str,
    payload: OrderStatusUpdateRequest,
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manager updates fulfillment_status for their shop's shipments only.
    Does NOT change the whole order.status — that is computed from all shipments."""
    from online_shopping.models.order import Order, OrderItem
    from online_shopping.models.shipment import Shipment

    shop_ids = await ManagerService(db)._get_shop_ids(current_user.id)
    order_result = await db.execute(
        select(Order).options(
            __import__("sqlalchemy.orm", fromlist=["selectinload"]).selectinload(Order.items)
        ).where(Order.order_number == order_number)
    )
    order = order_result.scalars().first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    if not any(oi.shop_id in shop_ids for oi in order.items if oi.shop_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No items from your shops in this order.")

    # Update only this manager's shipments
    shipments_result = await db.execute(
        select(Shipment).where(Shipment.order_id == order.id, Shipment.shop_id.in_(shop_ids))
    )
    updated = 0
    for shipment in shipments_result.scalars().all():
        shipment.fulfillment_status = payload.status
        if payload.status == "shipped":
            shipment.status = "shipped"
        updated += 1

    await db.commit()
    return {"order_number": order.order_number, "updated_shipments": updated, "fulfillment_status": payload.status}

@router.post("/manager/orders/{order_number}/shipments", status_code=status.HTTP_201_CREATED)
async def manager_create_shipment(
    order_number: str,
    payload: ShipmentCreateRequest,
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await ManagerService(db).create_shipment(current_user, order_number, payload.model_dump())

@router.get("/manager/shipments")
async def manager_shipments(
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    shipments = await ManagerService(db).list_shipments(current_user)
    return {"shipments": shipments}

@router.get("/manager/income")
async def manager_income(
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await ManagerService(db).income(current_user)

@router.get("/manager/reports")
async def manager_reports(
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await ManagerService(db).reports(current_user)

# ── Admin endpoints ────────────────────────────────────────────────

@router.get("/admin/dashboard")
async def admin_dashboard(
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await AdminService(db).dashboard()

@router.get("/admin/users")
async def admin_users(
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    users = await AdminService(db).list_users()
    return {"users": users, "total": len(users)}

@router.patch("/admin/users/{user_id}/status")
async def admin_update_user_status(
    user_id: UUID,
    payload: UserStatusRequest,
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user = await db.get(Account, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.status = payload.status
    await db.commit()
    return {"id": str(user.id), "status": user.status}

@router.patch("/admin/users/{user_id}/role")
async def admin_update_user_role(
    user_id: UUID,
    payload: UserRoleRequest,
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user = await db.get(Account, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.role = payload.role
    await db.commit()
    return {"id": str(user.id), "role": user.role}

@router.get("/admin/products")
async def admin_products(
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    products = await AdminService(db).list_products()
    return {"products": products, "total": len(products)}

@router.patch("/admin/products/{product_id}/status")
async def admin_update_product_status(
    product_id: UUID,
    payload: ProductStatusRequest,
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    product.status = payload.status
    await db.commit()
    return {"id": str(product.id), "status": product.status}

@router.get("/admin/orders")
async def admin_orders(
    current_user: Account = Depends(require_admin),
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    orders = await AdminService(db).list_orders(status_filter=status_filter)
    return {"orders": orders, "total": len(orders)}

@router.get("/admin/shops")
async def admin_shops(
    current_user: Account = Depends(require_admin),
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    shops = await ShopRepository(db).list_all()
    if status_filter:
        shops = [s for s in shops if s.status == status_filter]
    return {
        "shops": [
            {"id": str(s.id), "name": s.name, "slug": s.slug,
             "status": s.status, "category": s.category,
             "owner_email": s.owner.email if s.owner else None}
            for s in shops
        ]
    }

@router.patch("/admin/shops/{shop_id}/approval")
async def admin_approve_shop(
    shop_id: UUID,
    payload: ShopApprovalRequest,
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    shop = await ShopRepository(db).get_by_id(shop_id)
    if shop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found.")
    await ShopRepository(db).update_status(shop, payload.status)
    await db.commit()
    return {"id": str(shop.id), "name": shop.name, "status": shop.status}

@router.get("/admin/categories")
async def admin_categories(
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(ProductCategory).order_by(ProductCategory.name))
    categories = list(result.scalars().all())
    return {
        "categories": [
            {"id": str(c.id), "name": c.name, "description": c.description}
            for c in categories
        ]
    }

@router.post("/admin/categories", status_code=status.HTTP_201_CREATED)
async def admin_create_category(
    payload: CategoryCreateRequest,
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    existing = (await db.execute(
        select(ProductCategory).where(ProductCategory.name == payload.name)
    )).scalars().first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already exists.")
    cat = ProductCategory(name=payload.name, description=payload.description)
    db.add(cat)
    await db.commit()
    return {"id": str(cat.id), "name": cat.name, "description": cat.description}

@router.patch("/admin/categories/{category_id}")
async def admin_update_category(
    category_id: UUID,
    payload: CategoryCreateRequest,
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    cat = await db.get(ProductCategory, category_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    cat.name = payload.name
    cat.description = payload.description
    await db.commit()
    return {"id": str(cat.id), "name": cat.name, "description": cat.description}

@router.delete("/admin/categories/{category_id}")
async def admin_delete_category(
    category_id: UUID,
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    cat = await db.get(ProductCategory, category_id)
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    await db.delete(cat)
    await db.commit()
    return {"deleted": True}

# ── Legacy endpoints ───────────────────────────────────────────────

@router.get("/admin")
async def admin_legacy(
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await AdminService(db).dashboard()

@router.get("/manager")
async def manager_legacy(
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await ManagerService(db).dashboard(current_user)

@router.get("/customer")
async def customer_legacy(db: AsyncSession = Depends(get_db)) -> dict:
    from online_shopping.repositories.cart_repository import CartRepository
    from online_shopping.repositories.order_repository import OrderRepository
    cart = await CartRepository(db).get_default_cart()
    orders = await OrderRepository(db).list_orders()
    return {
        "route": "/customer",
        "title": "Customer Panel",
        "stats": {"cart_items": sum(item.quantity for item in cart.items), "orders": len(orders)},
    }
