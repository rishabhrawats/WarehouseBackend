from fastapi import HTTPException

from app.services.activity_service import add_activity
from app.services.quotation_service import get_quotation_with_items
from app.supabase_client import supabase


def get_order_with_items(order_id: str) -> tuple[dict, list[dict]]:
    order_response = supabase.table("orders").select("*").eq("id", order_id).limit(1).execute()
    if not order_response.data:
        raise HTTPException(status_code=404, detail="Order not found")
    items_response = supabase.table("order_items").select("*").eq("order_id", order_id).execute()
    return order_response.data[0], items_response.data


def create_order_from_quotation(payload) -> tuple[dict, list[dict]]:
    existing = (
        supabase.table("orders")
        .select("id")
        .eq("order_number", payload.order_number)
        .limit(1)
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=409, detail="Duplicate order number")

    quotation, quotation_items = get_quotation_with_items(payload.quotation_id)
    order_payload = {
        "customer_id": quotation["customer_id"],
        "quotation_id": quotation["id"],
        "order_number": payload.order_number,
        "order_status": "Confirmed",
        "payment_status": "Pending",
        "fulfillment_status": "Pending",
        "shipment_status": "Not Shipped",
        "total_amount": quotation["final_amount"],
        "delivery_city": payload.delivery_city,
        "latest_update": "Order confirmed from quotation.",
    }
    order = supabase.table("orders").insert(order_payload).execute().data[0]

    order_items = [
        {
            "order_id": order["id"],
            "product_id": item["product_id"],
            "sku": item["sku"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "line_total": item["line_total"],
        }
        for item in quotation_items
    ]
    inserted_items = supabase.table("order_items").insert(order_items).execute().data

    supabase.table("customer_status").update(
        {
            "current_stage": "Order Confirmed",
            "latest_update": f"Order {order['order_number']} confirmed.",
        }
    ).eq("customer_id", quotation["customer_id"]).execute()
    supabase.table("customers").update({"customer_level": "Order Confirmed"}).eq(
        "id", quotation["customer_id"]
    ).execute()
    add_activity(
        customer_id=quotation["customer_id"],
        activity_type="Order Confirmed",
        activity_message=f"Order {order['order_number']} was confirmed from quotation.",
        related_entity_type="order",
        related_entity_id=order["id"],
    )
    return order, inserted_items
