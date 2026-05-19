from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class QuotationItemRequest(BaseModel):
    sku: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0)


class QuotationCreateRequest(BaseModel):
    customer_id: str
    quotation_number: str = Field(..., min_length=1)
    items: list[QuotationItemRequest] = Field(..., min_length=1)
    valid_until: date | None = None
    created_by: str | None = None


class QuotationStatusUpdateRequest(BaseModel):
    quotation_status: str = Field(..., min_length=1)


class QuotationResponse(BaseModel):
    quotation: dict[str, Any]
    items: list[dict[str, Any]] = []


class CustomerQuotationStatusResponse(BaseModel):
    customer_id: str
    latest_quotation: dict[str, Any] | None = None
    items: list[dict[str, Any]] = []
