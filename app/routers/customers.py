from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import verify_api_key
from app.models.customer_models import (
    CustomerCreateRequest,
    CustomerLatestUpdateResponse,
    CustomerListResponse,
    CustomerResponse,
    CustomerSearchResponse,
    CustomerStatusResponse,
    CustomerStatusUpdateRequest,
    CustomerTimelineResponse,
)
from app.services.activity_service import add_activity, latest_activity
from app.supabase_client import supabase

router = APIRouter(prefix="/api/customers", tags=["customers"], dependencies=[Depends(verify_api_key)])


def _get_customer(customer_id: str) -> dict:
    response = supabase.table("customers").select("*").eq("id", customer_id).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Customer not found")
    return response.data[0]


def _get_customer_status(customer_id: str) -> dict:
    response = (
        supabase.table("customer_status").select("*").eq("customer_id", customer_id).limit(1).execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Customer status not found")
    return response.data[0]


def _latest_row(table_name: str, customer_id: str, order_column: str = "created_at") -> dict | None:
    response = (
        supabase.table(table_name)
        .select("*")
        .eq("customer_id", customer_id)
        .order(order_column, desc=True)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def _customer_context(customer: dict) -> dict:
    customer_id = customer["id"]
    status_rows = (
        supabase.table("customer_status")
        .select("*")
        .eq("customer_id", customer_id)
        .limit(1)
        .execute()
        .data
    )
    return {
        "customer": customer,
        "status": status_rows[0] if status_rows else None,
        "latest_activity": _latest_row("customer_activities", customer_id),
        "latest_quotation": _latest_row("quotations", customer_id),
        "latest_order": _latest_row("orders", customer_id),
        "latest_maestro_process": _latest_row("maestro_processes", customer_id, "started_at"),
    }


@router.post("", response_model=CustomerResponse)
def create_customer(payload: CustomerCreateRequest) -> dict:
    customer = supabase.table("customers").insert(payload.model_dump(exclude_none=True)).execute().data[0]
    supabase.table("customer_status").insert(
        {
            "customer_id": customer["id"],
            "current_stage": customer.get("customer_level") or "New Lead",
            "latest_update": "Customer created",
        }
    ).execute()
    add_activity(
        customer_id=customer["id"],
        activity_type="Customer Created",
        activity_message=f"Customer {customer['customer_name']} was created.",
    )
    return {"customer": customer}


@router.get("", response_model=CustomerListResponse)
def list_customers(
    stage: Annotated[str | None, Query()] = None,
    city: Annotated[str | None, Query()] = None,
    priority: Annotated[str | None, Query()] = None,
    quotation_requested: Annotated[bool | None, Query()] = None,
    quotation_sent: Annotated[bool | None, Query()] = None,
    owner: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> dict[str, Any]:
    status_filters = any(
        value is not None
        for value in [stage, priority, quotation_requested, quotation_sent]
    )
    allowed_customer_ids: set[str] | None = None

    if status_filters:
        status_query = supabase.table("customer_status").select("customer_id")
        if stage:
            status_query = status_query.eq("current_stage", stage)
        if priority:
            status_query = status_query.eq("priority", priority)
        if quotation_requested is not None:
            status_query = status_query.eq("quotation_requested", quotation_requested)
        if quotation_sent is not None:
            status_query = status_query.eq("quotation_sent", quotation_sent)
        allowed_customer_ids = {
            row["customer_id"] for row in status_query.limit(limit).execute().data
        }
        if not allowed_customer_ids:
            return {"count": 0, "customers": []}

    customer_query = supabase.table("customers").select("*").order("created_at", desc=True).limit(limit)
    if city:
        customer_query = customer_query.ilike("city", city)
    if owner:
        customer_query = customer_query.ilike("assigned_sales_owner", owner)
    if allowed_customer_ids is not None:
        customer_query = customer_query.in_("id", list(allowed_customer_ids))

    customers = customer_query.execute().data
    enriched_customers = [_customer_context(customer) for customer in customers]
    return {"count": len(enriched_customers), "customers": enriched_customers}


@router.get("/search", response_model=CustomerSearchResponse)
def search_customers(
    name: str | None = Query(default=None),
    email: str | None = Query(default=None),
    phone: str | None = Query(default=None),
) -> dict[str, list[dict[str, Any]]]:
    query = supabase.table("customers").select("*")
    if name:
        query = query.ilike("customer_name", f"%{name}%")
    if email:
        query = query.ilike("email", f"%{email}%")
    if phone:
        query = query.ilike("phone", f"%{phone}%")
    return {"customers": query.execute().data}


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str) -> dict:
    return {"customer": _get_customer(customer_id)}


@router.get("/{customer_id}/status", response_model=CustomerStatusResponse)
def get_customer_status(customer_id: str) -> dict:
    _get_customer(customer_id)
    return {"status": _get_customer_status(customer_id)}


@router.patch("/{customer_id}/status", response_model=CustomerStatusResponse)
def update_customer_status(customer_id: str, payload: CustomerStatusUpdateRequest) -> dict:
    _get_customer(customer_id)
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No status fields provided")
    updated = (
        supabase.table("customer_status")
        .update(updates)
        .eq("customer_id", customer_id)
        .execute()
        .data
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Customer status not found")
    if payload.current_stage:
        supabase.table("customers").update({"customer_level": payload.current_stage}).eq(
            "id", customer_id
        ).execute()
    add_activity(
        customer_id=customer_id,
        activity_type="Customer Status Updated",
        activity_message=payload.latest_update or f"Customer status updated to {updates.get('current_stage', 'updated')}.",
    )
    return {"status": updated[0]}


@router.get("/{customer_id}/latest-update", response_model=CustomerLatestUpdateResponse)
def get_latest_update(customer_id: str) -> dict:
    _get_customer(customer_id)
    status = _get_customer_status(customer_id)
    activity = latest_activity(customer_id)
    return {
        "latest_update": status.get("latest_update") or (activity or {}).get("activity_message"),
        "status": status,
        "latest_activity": activity,
    }


@router.get("/{customer_id}/timeline", response_model=CustomerTimelineResponse)
def get_timeline(customer_id: str) -> dict:
    _get_customer(customer_id)
    activities = (
        supabase.table("customer_activities")
        .select("*")
        .eq("customer_id", customer_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )
    return {"customer_id": customer_id, "activities": activities}
