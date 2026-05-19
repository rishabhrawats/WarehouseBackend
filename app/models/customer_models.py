from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class CustomerCreateRequest(BaseModel):
    customer_name: str = Field(..., min_length=1)
    email: str | None = None
    phone: str | None = None
    city: str | None = None
    customer_type: str = "Retail"
    customer_level: str = "New Lead"
    source: str | None = None
    assigned_sales_owner: str | None = None


class CustomerStatusUpdateRequest(BaseModel):
    current_stage: str | None = None
    latest_update: str | None = None
    next_action: str | None = None
    next_action_date: date | None = None
    quotation_requested: bool | None = None
    quotation_sent: bool | None = None
    status_owner: str | None = None
    priority: str | None = None


class CustomerResponse(BaseModel):
    customer: dict[str, Any]


class CustomerListResponse(BaseModel):
    count: int
    customers: list[dict[str, Any]]


class CustomerSearchResponse(BaseModel):
    customers: list[dict[str, Any]]


class CustomerStatusResponse(BaseModel):
    status: dict[str, Any]


class CustomerLatestUpdateResponse(BaseModel):
    latest_update: str | None
    status: dict[str, Any] | None = None
    latest_activity: dict[str, Any] | None = None


class CustomerTimelineResponse(BaseModel):
    customer_id: str
    activities: list[dict[str, Any]]
