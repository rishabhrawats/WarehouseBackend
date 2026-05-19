from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_api_key
from app.models.order_models import (
    OrderFromQuotationRequest,
    OrderResponse,
    OrderStatusResponse,
    OrderStatusUpdateRequest,
)
from app.services.order_service import create_order_from_quotation, get_order_with_items
from app.supabase_client import supabase

router = APIRouter(prefix="/api/orders", tags=["orders"], dependencies=[Depends(verify_api_key)])


@router.post("/from-quotation", response_model=OrderResponse)
def create_from_quotation(payload: OrderFromQuotationRequest) -> dict:
    order, items = create_order_from_quotation(payload)
    return {"order": order, "items": items}


@router.get("/{order_id}/status", response_model=OrderStatusResponse)
def get_status(order_id: str) -> dict:
    order, _ = get_order_with_items(order_id)
    return {"order": order}


@router.patch("/{order_id}/status", response_model=OrderStatusResponse)
def update_status(order_id: str, payload: OrderStatusUpdateRequest) -> dict:
    get_order_with_items(order_id)
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No order status fields provided")
    updated = supabase.table("orders").update(updates).eq("id", order_id).execute().data
    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order": updated[0]}
