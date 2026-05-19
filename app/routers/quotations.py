from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_api_key
from app.models.quotation_models import (
    CustomerQuotationStatusResponse,
    QuotationCreateRequest,
    QuotationResponse,
    QuotationStatusUpdateRequest,
)
from app.services.quotation_service import create_quotation, get_customer, get_quotation_with_items, send_quotation
from app.supabase_client import supabase

router = APIRouter(tags=["quotations"], dependencies=[Depends(verify_api_key)])


@router.post("/api/quotations", response_model=QuotationResponse)
def create(payload: QuotationCreateRequest) -> dict:
    quotation, items = create_quotation(payload)
    return {"quotation": quotation, "items": items}


@router.get("/api/quotations/{quotation_id}", response_model=QuotationResponse)
def get_quotation(quotation_id: str) -> dict:
    quotation, items = get_quotation_with_items(quotation_id)
    return {"quotation": quotation, "items": items}


@router.post("/api/quotations/{quotation_id}/send", response_model=QuotationResponse)
def send(quotation_id: str) -> dict:
    quotation, items = send_quotation(quotation_id)
    return {"quotation": quotation, "items": items}


@router.patch("/api/quotations/{quotation_id}/status", response_model=QuotationResponse)
def update_status(quotation_id: str, payload: QuotationStatusUpdateRequest) -> dict:
    get_quotation_with_items(quotation_id)
    updated = (
        supabase.table("quotations")
        .update({"quotation_status": payload.quotation_status})
        .eq("id", quotation_id)
        .execute()
        .data
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Quotation not found")
    items = supabase.table("quotation_items").select("*").eq("quotation_id", quotation_id).execute().data
    return {"quotation": updated[0], "items": items}


@router.get("/api/customers/{customer_id}/quotation-status", response_model=CustomerQuotationStatusResponse)
def customer_quotation_status(customer_id: str) -> dict:
    get_customer(customer_id)
    quotations = (
        supabase.table("quotations")
        .select("*")
        .eq("customer_id", customer_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
    )
    if not quotations:
        return {"customer_id": customer_id, "latest_quotation": None, "items": []}
    items = (
        supabase.table("quotation_items")
        .select("*")
        .eq("quotation_id", quotations[0]["id"])
        .execute()
        .data
    )
    return {"customer_id": customer_id, "latest_quotation": quotations[0], "items": items}
