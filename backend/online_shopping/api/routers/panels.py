"""Admin and Manager panel endpoints — protected, role-scoped."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from online_shopping.api.deps import get_db, require_admin, require_manager
from online_shopping.models.account import Account
from online_shopping.repositories.shop_repository import ShopRepository
from online_shopping.services.admin_service import AdminService
from online_shopping.services.manager_service import ManagerService

router = APIRouter()


# ── Request schemas ────────────────────────────────────────────────


class ShopCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    category: str | None = None


class ShopApprovalRequest(BaseModel):
    status: str = Field(pattern="^(active|rejected)$")


# ── Admin endpoints (require admin role) ──────────────────────────


@router.get("/admin/dashboard")
async def admin_dashboard(
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Platform dashboard — admin only."""
    return await AdminService(db).dashboard()


@router.get("/admin/users")
async def admin_users(
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List platform users — admin only."""
    users = await AdminService(db).list_users()
    return {"users": users, "total": len(users)}


@router.get("/admin/products")
async def admin_products(
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List platform products — admin only."""
    products = await AdminService(db).list_products()
    return {"products": products, "total": len(products)}


@router.get("/admin/orders")
async def admin_orders(
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List platform orders — admin only."""
    orders = await AdminService(db).list_orders()
    return {"orders": orders, "total": len(orders)}


# ── Manager endpoints (require manager or admin role) ─────────────


@router.get("/manager/dashboard")
async def manager_dashboard(
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manager dashboard — manager or admin."""
    return await ManagerService(db).dashboard(current_user)


@router.get("/manager/products")
async def manager_products(
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manager's products — manager or admin."""
    products = await ManagerService(db).list_products(current_user)
    return {"products": products, "total": len(products)}


@router.get("/manager/orders")
async def manager_orders(
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manager's orders — manager or admin."""
    orders = await ManagerService(db).list_orders(current_user)
    return {"orders": orders, "total": len(orders)}


# ── Legacy simple endpoints (maintain backward compat) ────────────


@router.get("/admin")
async def admin_legacy(
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Legacy admin panel summary."""
    return await AdminService(db).dashboard()


@router.get("/manager")
async def manager_legacy(
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Legacy manager panel summary."""
    return await ManagerService(db).dashboard(current_user)


@router.get("/customer")
async def customer_legacy(db: AsyncSession = Depends(get_db)) -> dict:
    """Legacy customer panel summary (public)."""
    from online_shopping.repositories.cart_repository import CartRepository
    from online_shopping.repositories.order_repository import OrderRepository
    cart = await CartRepository(db).get_default_cart()
    orders = await OrderRepository(db).list_orders()
    return {
        "route": "/customer",
        "title": "Customer Panel",
        "stats": {
            "cart_items": sum(item.quantity for item in cart.items),
            "orders": len(orders),
        },
    }


# ── Inventory management (manager) ──────────────────────────────────


class InventoryUpdateRequest(BaseModel):
    inventory_count: int = Field(ge=0)


@router.patch("/manager/inventory/{variant_id}")
async def manager_update_inventory(
    variant_id: UUID,
    payload: InventoryUpdateRequest,
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update inventory count for a product variant."""
    from online_shopping.models.product_variant import ProductVariant
    from sqlalchemy import select as _sel

    result = await db.execute(_sel(ProductVariant).where(ProductVariant.id == variant_id))
    variant = result.scalars().first()
    if variant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found.")

    variant.inventory_count = payload.inventory_count
    await db.commit()
    return {
        "id": str(variant.id),
        "name": variant.name,
        "sku": variant.sku,
        "inventory_count": variant.inventory_count,
    }


# ── Shop management (manager + admin) ──────────────────────────────


@router.get("/manager/shops")
async def manager_shops(
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List shops owned by this manager."""
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
    """Create a new shop (pending admin approval)."""
    shop = await ManagerService(db).create_shop(current_user, payload.model_dump())
    return shop


@router.get("/admin/shops")
async def admin_shops(
    current_user: Account = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all shops (admin view)."""
    shops = await ShopRepository(db).list_all()
    return {
        "shops": [
            {
                "id": str(s.id), "name": s.name, "slug": s.slug,
                "status": s.status, "category": s.category,
                "owner_email": s.owner.email if s.owner else None,
            }
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
    """Approve or reject a shop."""
    shop = await ShopRepository(db).get_by_id(shop_id)
    if shop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found.")
    await ShopRepository(db).update_status(shop, payload.status)
    await db.commit()
    return {"id": str(shop.id), "name": shop.name, "status": shop.status}


# ── Shipment endpoints (manager) ────────────────────────────────────


class ShipmentCreateRequest(BaseModel):
    carrier: str | None = None
    tracking_number: str | None = None


@router.post("/manager/orders/{order_number}/shipments", status_code=status.HTTP_201_CREATED)
async def manager_create_shipment(
    order_number: str,
    payload: ShipmentCreateRequest,
    current_user: Account = Depends(require_manager),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a shipment for an order."""
    from online_shopping.models.shipment import Shipment
    from online_shopping.models.order import Order as OrderModel
    from sqlalchemy import select as _sel2

    order_result = await db.execute(
        _sel2(OrderModel).where(OrderModel.order_number == order_number)
    )
    order = order_result.scalars().first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    shipment = Shipment(
        order_id=order.id,
        status="pending",
        carrier=payload.carrier,
        tracking_number=payload.tracking_number,
    )
    db.add(shipment)
    await db.commit()
    await db.refresh(shipment)
    return {
        "id": str(shipment.id),
        "status": shipment.status,
        "carrier": shipment.carrier,
        "tracking_number": shipment.tracking_number,
    }


@router.get("/orders/{order_number}/shipments")
async def get_order_shipments(
    order_number: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get shipments for an order."""
    from online_shopping.models.shipment import Shipment as ShipmentModel
    from online_shopping.models.order import Order as OrderModel
    from sqlalchemy import select as _sel3

    order_result = await db.execute(
        _sel3(OrderModel).where(OrderModel.order_number == order_number)
    )
    order = order_result.scalars().first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    shipments_result = await db.execute(
        _sel3(ShipmentModel).where(ShipmentModel.order_id == order.id)
    )
    shipments = list(shipments_result.scalars().all())
    return {
        "shipments": [
            {
                "id": str(s.id),
                "status": s.status,
                "carrier": s.carrier,
                "tracking_number": s.tracking_number,
                "tracking_url": s.tracking_url,
                "estimated_arrival": s.estimated_arrival.isoformat() if s.estimated_arrival else None,
            }
            for s in shipments
        ]
    }
