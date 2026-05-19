from typing import Any

from pydantic import BaseModel, Field


class InventoryResponse(BaseModel):
    inventory: dict[str, Any]


class InventoryListResponse(BaseModel):
    count: int
    items: list[dict[str, Any]]


class InventoryMovementRequest(BaseModel):
    sku: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0)


class InventoryUpdateRequest(BaseModel):
    available_quantity: int | None = Field(default=None, ge=0)
    reserved_quantity: int | None = Field(default=None, ge=0)
    sold_quantity: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    warehouse_location: str | None = None


class InventoryMovementResponse(BaseModel):
    success: bool
    message: str
    inventory: dict[str, Any] | None = None
