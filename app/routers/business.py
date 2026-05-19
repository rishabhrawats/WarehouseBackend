from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import verify_api_key
from app.services.activity_service import latest_activity
from app.services.order_service import get_order_with_items
from app.supabase_client import supabase

router = APIRouter(prefix="/api/business", tags=["business"], dependencies=[Depends(verify_api_key)])


def _money(value: Any, currency: str = "INR") -> str:
    amount = Decimal(str(value))
    return f"{currency} {amount:,.0f}"


@router.get("/product-answer")
def product_answer(
    model: str = Query(...),
    size: str = Query(...),
    color: str = Query(...),
) -> dict:
    products = (
        supabase.table("products")
        .select("*")
        .ilike("product_name", f"%{model}%")
        .eq("size", size)
        .ilike("color", color)
        .limit(1)
        .execute()
        .data
    )
    if not products:
        return {
            "answer": f"No matching product was found for {model} in {size} {color}.",
            "product": None,
            "inventory": None,
        }

    product = products[0]
    inventory_rows = (
        supabase.table("inventory")
        .select("*")
        .eq("sku", product["sku"])
        .limit(1)
        .execute()
        .data
    )
    inventory = inventory_rows[0] if inventory_rows else None
    available = inventory.get("available_quantity", 0) if inventory else 0
    price = product.get("discount_price") or product["base_price"]
    currency = product.get("currency") or "INR"

    if available > 0:
        answer = (
            f"Yes, {product['product_name']} in {product['size']} {product['color']} is available. "
            f"Current available quantity is {available} units. Price is {_money(price, currency)}."
        )
    else:
        answer = (
            f"{product['product_name']} in {product['size']} {product['color']} is currently out of stock. "
            f"Price is {_money(price, currency)}."
        )
    return {"answer": answer, "product": product, "inventory": inventory}


@router.get("/customer-summary/{customer_id}")
def customer_summary(customer_id: str) -> dict:
    customer_rows = supabase.table("customers").select("*").eq("id", customer_id).limit(1).execute().data
    if not customer_rows:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer = customer_rows[0]
    status_rows = (
        supabase.table("customer_status")
        .select("*")
        .eq("customer_id", customer_id)
        .limit(1)
        .execute()
        .data
    )
    status = status_rows[0] if status_rows else None
    activity = latest_activity(customer_id)
    quotation_rows = (
        supabase.table("quotations")
        .select("*")
        .eq("customer_id", customer_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
    )
    quotation = quotation_rows[0] if quotation_rows else None

    update = (status or {}).get("latest_update") or (activity or {}).get("activity_message") or "No update yet"
    stage = (status or {}).get("current_stage") or customer.get("customer_level") or "Unknown"
    next_action = (status or {}).get("next_action") or "no next action is recorded"
    quote_text = f"quotation {quotation['quotation_number']} is {quotation['quotation_status']}" if quotation else "no quotation exists yet"
    answer = (
        f"The latest update for {customer['customer_name']} is: {update}. "
        f"Current customer stage is {stage}. {quote_text}. Next action is {next_action}."
    )
    return {
        "answer": answer,
        "customer": customer,
        "status": status,
        "latest_activity": activity,
        "latest_quotation": quotation,
    }


@router.get("/order-summary/{order_id}")
def order_summary(order_id: str) -> dict:
    order, items = get_order_with_items(order_id)
    customer_rows = (
        supabase.table("customers")
        .select("*")
        .eq("id", order["customer_id"])
        .limit(1)
        .execute()
        .data
    )
    customer = customer_rows[0] if customer_rows else None
    stuck_parts = [
        order.get("order_status"),
        order.get("payment_status"),
        order.get("fulfillment_status"),
        order.get("shipment_status"),
    ]
    answer = (
        f"Order {order['order_number']} is currently {order.get('order_status')}. "
        f"Payment is {order.get('payment_status')}, fulfillment is {order.get('fulfillment_status')}, "
        f"and shipment is {order.get('shipment_status')}. Latest update: {order.get('latest_update') or 'No update yet'}."
    )
    return {
        "answer": answer,
        "order": order,
        "items": items,
        "customer": customer,
        "current_state": " / ".join([part for part in stuck_parts if part]),
    }
