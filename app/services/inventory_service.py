from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.supabase_client import supabase


def get_inventory_by_sku(sku: str) -> dict:
    response = supabase.table("inventory").select("*").eq("sku", sku).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Inventory not found for SKU {sku}")
    return response.data[0]


def calculate_inventory_status(available_quantity: int, reorder_level: int) -> str:
    if available_quantity <= 0:
        return "Out of Stock"
    if available_quantity <= reorder_level:
        return "Low Stock"
    return "In Stock"


def update_inventory_quantities(sku: str, updates: dict) -> dict:
    inventory = get_inventory_by_sku(sku)
    if not updates:
        raise HTTPException(status_code=400, detail="No inventory fields provided")

    updated_available = updates.get(
        "available_quantity",
        inventory.get("available_quantity", 0),
    )
    updated_reorder_level = updates.get(
        "reorder_level",
        inventory.get("reorder_level", 5),
    )
    updates["inventory_status"] = calculate_inventory_status(
        updated_available,
        updated_reorder_level,
    )
    updates["last_updated_at"] = datetime.now(timezone.utc).isoformat()

    response = supabase.table("inventory").update(updates).eq("id", inventory["id"]).execute()
    return {
        "success": True,
        "message": f"Inventory updated for SKU {sku}.",
        "inventory": response.data[0],
    }


def reserve_inventory(sku: str, quantity: int) -> dict:
    inventory = get_inventory_by_sku(sku)
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")

    available = inventory.get("available_quantity", 0)
    if available < quantity:
        return {
            "success": False,
            "message": f"Insufficient inventory for SKU {sku}. Available quantity is {available}.",
            "inventory": inventory,
        }

    updated_available = available - quantity
    updated_reserved = inventory.get("reserved_quantity", 0) + quantity
    payload = {
        "available_quantity": updated_available,
        "reserved_quantity": updated_reserved,
        "inventory_status": calculate_inventory_status(
            updated_available,
            inventory.get("reorder_level", 5),
        ),
    }
    response = supabase.table("inventory").update(payload).eq("id", inventory["id"]).execute()
    return {
        "success": True,
        "message": f"Reserved {quantity} units for SKU {sku}.",
        "inventory": response.data[0],
    }


def release_inventory(sku: str, quantity: int) -> dict:
    inventory = get_inventory_by_sku(sku)
    reserved = inventory.get("reserved_quantity", 0)
    if reserved < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot release {quantity} units. Reserved quantity is {reserved}.",
        )

    updated_available = inventory.get("available_quantity", 0) + quantity
    payload = {
        "available_quantity": updated_available,
        "reserved_quantity": reserved - quantity,
        "inventory_status": calculate_inventory_status(
            updated_available,
            inventory.get("reorder_level", 5),
        ),
    }
    response = supabase.table("inventory").update(payload).eq("id", inventory["id"]).execute()
    return {
        "success": True,
        "message": f"Released {quantity} units for SKU {sku}.",
        "inventory": response.data[0],
    }


def sell_inventory(sku: str, quantity: int) -> dict:
    inventory = get_inventory_by_sku(sku)
    reserved = inventory.get("reserved_quantity", 0)
    available = inventory.get("available_quantity", 0)
    sold_from_reserved = min(reserved, quantity)
    remaining_to_sell = quantity - sold_from_reserved

    if remaining_to_sell > available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient inventory to sell {quantity} units for SKU {sku}.",
        )

    updated_reserved = reserved - sold_from_reserved
    updated_available = available - remaining_to_sell
    payload = {
        "reserved_quantity": updated_reserved,
        "available_quantity": updated_available,
        "sold_quantity": inventory.get("sold_quantity", 0) + quantity,
        "inventory_status": calculate_inventory_status(
            updated_available,
            inventory.get("reorder_level", 5),
        ),
    }
    response = supabase.table("inventory").update(payload).eq("id", inventory["id"]).execute()
    return {
        "success": True,
        "message": f"Sold {quantity} units for SKU {sku}.",
        "inventory": response.data[0],
    }
