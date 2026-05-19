from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class ProductResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    sku: str
    product_name: str
    category: str | None = None
    brand_name: str | None = None
    gender: str | None = None
    size: str
    color: str
    base_price: Decimal
    discount_price: Decimal | None = None
    currency: str | None = None
    status: str | None = None


class ProductSearchResponse(BaseModel):
    products: list[dict[str, Any]]


class ProductPriceResponse(BaseModel):
    sku: str
    product_name: str
    base_price: Decimal
    discount_price: Decimal | None = None
    effective_price: Decimal
    currency: str
