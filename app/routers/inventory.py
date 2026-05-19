from fastapi import APIRouter, Depends, Query

from app.auth import verify_api_key
from app.models.inventory_models import (
    InventoryListResponse,
    InventoryMovementRequest,
    InventoryMovementResponse,
    InventoryResponse,
    InventoryUpdateRequest,
)
from app.services.inventory_service import (
    get_inventory_by_sku,
    release_inventory,
    reserve_inventory,
    sell_inventory,
    update_inventory_quantities,
)
from app.supabase_client import supabase

router = APIRouter(prefix="/api/inventory", tags=["inventory"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=InventoryListResponse)
def list_inventory(
    available_only: bool = Query(default=True),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    query = (
        supabase.table("inventory")
        .select(
            "sku, available_quantity, reserved_quantity, sold_quantity, reorder_level, "
            "inventory_status, warehouse_location, last_updated_at, "
            "products(product_name, size, color, base_price, discount_price, currency, status)"
        )
        .order("sku")
        .limit(limit)
    )
    if available_only:
        query = query.gt("available_quantity", 0)
    if status:
        query = query.eq("inventory_status", status)

    rows = query.execute().data
    items = []
    for row in rows:
        product = row.get("products") or {}
        price = product.get("discount_price") or product.get("base_price")
        items.append(
            {
                "sku": row["sku"],
                "product_name": product.get("product_name"),
                "size": product.get("size"),
                "color": product.get("color"),
                "available_quantity": row.get("available_quantity", 0),
                "reserved_quantity": row.get("reserved_quantity", 0),
                "sold_quantity": row.get("sold_quantity", 0),
                "reorder_level": row.get("reorder_level", 0),
                "inventory_status": row.get("inventory_status"),
                "warehouse_location": row.get("warehouse_location"),
                "last_updated_at": row.get("last_updated_at"),
                "price": price,
                "currency": product.get("currency") or "INR",
                "product_status": product.get("status"),
            }
        )
    return {"count": len(items), "items": items}


@router.get("/{sku}", response_model=InventoryResponse)
def get_inventory(sku: str) -> dict:
    return {"inventory": get_inventory_by_sku(sku)}


@router.patch("/{sku}", response_model=InventoryMovementResponse)
def update_inventory(sku: str, payload: InventoryUpdateRequest) -> dict:
    return update_inventory_quantities(sku, payload.model_dump(exclude_none=True))


@router.post("/reserve", response_model=InventoryMovementResponse)
def reserve(payload: InventoryMovementRequest) -> dict:
    return reserve_inventory(payload.sku, payload.quantity)


@router.post("/release", response_model=InventoryMovementResponse)
def release(payload: InventoryMovementRequest) -> dict:
    return release_inventory(payload.sku, payload.quantity)


@router.post("/sell", response_model=InventoryMovementResponse)
def sell(payload: InventoryMovementRequest) -> dict:
    return sell_inventory(payload.sku, payload.quantity)
