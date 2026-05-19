from decimal import Decimal
from datetime import datetime, timezone

from fastapi import HTTPException

from app.services.activity_service import add_activity
from app.supabase_client import supabase


def get_customer(customer_id: str) -> dict:
    response = supabase.table("customers").select("*").eq("id", customer_id).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Customer not found")
    return response.data[0]


def get_product_by_sku(sku: str) -> dict:
    response = supabase.table("products").select("*").eq("sku", sku).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail=f"Product not found for SKU {sku}")
    return response.data[0]


def get_quotation_with_items(quotation_id: str) -> tuple[dict, list[dict]]:
    quotation_response = (
        supabase.table("quotations").select("*").eq("id", quotation_id).limit(1).execute()
    )
    if not quotation_response.data:
        raise HTTPException(status_code=404, detail="Quotation not found")
    items_response = (
        supabase.table("quotation_items")
        .select("*")
        .eq("quotation_id", quotation_id)
        .execute()
    )
    return quotation_response.data[0], items_response.data


def create_quotation(payload) -> tuple[dict, list[dict]]:
    customer = get_customer(payload.customer_id)
    existing = (
        supabase.table("quotations")
        .select("id")
        .eq("quotation_number", payload.quotation_number)
        .limit(1)
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=409, detail="Duplicate quotation number")

    item_rows = []
    total_amount = Decimal("0")
    final_amount = Decimal("0")

    for item in payload.items:
        product = get_product_by_sku(item.sku)
        base_price = Decimal(str(product["base_price"]))
        effective_price = Decimal(str(product.get("discount_price") or product["base_price"]))
        quantity = Decimal(item.quantity)
        total_amount += base_price * quantity
        final_amount += effective_price * quantity
        item_rows.append(
            {
                "product_id": product["id"],
                "sku": product["sku"],
                "product_name": product["product_name"],
                "size": product["size"],
                "color": product["color"],
                "quantity": item.quantity,
                "unit_price": str(effective_price),
                "line_total": str(effective_price * quantity),
            }
        )

    quotation_payload = {
        "customer_id": customer["id"],
        "quotation_number": payload.quotation_number,
        "quotation_status": "Draft",
        "total_amount": str(total_amount),
        "discount_amount": str(total_amount - final_amount),
        "final_amount": str(final_amount),
        "valid_until": payload.valid_until.isoformat() if payload.valid_until else None,
        "created_by": payload.created_by,
    }
    quotation = supabase.table("quotations").insert(quotation_payload).execute().data[0]

    for row in item_rows:
        row["quotation_id"] = quotation["id"]
    items = supabase.table("quotation_items").insert(item_rows).execute().data

    supabase.table("customer_status").update(
        {
            "current_stage": "Quotation Generated",
            "quotation_requested": True,
            "latest_update": "Quotation generated",
        }
    ).eq("customer_id", customer["id"]).execute()
    supabase.table("customers").update({"customer_level": "Quotation Generated"}).eq(
        "id", customer["id"]
    ).execute()
    add_activity(
        customer_id=customer["id"],
        activity_type="Quotation Generated",
        activity_message=f"Quotation {quotation['quotation_number']} was generated.",
        related_entity_type="quotation",
        related_entity_id=quotation["id"],
        created_by=payload.created_by or "System",
    )
    return quotation, items


def send_quotation(quotation_id: str) -> tuple[dict, list[dict]]:
    quotation, items = get_quotation_with_items(quotation_id)
    updated = (
        supabase.table("quotations")
        .update(
            {
                "quotation_status": "Sent",
                "sent_to_customer": True,
                "sent_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", quotation_id)
        .execute()
        .data[0]
    )
    customer_id = quotation["customer_id"]
    supabase.table("customers").update({"customer_level": "Quotation Sent"}).eq(
        "id", customer_id
    ).execute()
    supabase.table("customer_status").update(
        {
            "current_stage": "Quotation Sent",
            "quotation_requested": True,
            "quotation_sent": True,
            "quotation_sent_at": datetime.now(timezone.utc).isoformat(),
            "latest_update": f"Quotation {quotation['quotation_number']} was sent to customer.",
        }
    ).eq("customer_id", customer_id).execute()
    add_activity(
        customer_id=customer_id,
        activity_type="Quotation Sent",
        activity_message=f"Quotation {quotation['quotation_number']} was sent to customer.",
        related_entity_type="quotation",
        related_entity_id=quotation_id,
    )
    return updated, items
