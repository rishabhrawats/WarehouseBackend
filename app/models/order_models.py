from typing import Any

from pydantic import BaseModel, Field


class OrderFromQuotationRequest(BaseModel):
    quotation_id: str
    order_number: str = Field(..., min_length=1)
    delivery_city: str | None = None


class OrderStatusUpdateRequest(BaseModel):
    order_status: str | None = None
    payment_status: str | None = None
    fulfillment_status: str | None = None
    shipment_status: str | None = None
    latest_update: str | None = None


class OrderResponse(BaseModel):
    order: dict[str, Any]
    items: list[dict[str, Any]] = []


class OrderStatusResponse(BaseModel):
    order: dict[str, Any]
