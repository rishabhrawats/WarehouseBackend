from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import verify_api_key
from app.models.product_models import ProductPriceResponse, ProductSearchResponse
from app.supabase_client import supabase

router = APIRouter(prefix="/api/products", tags=["products"], dependencies=[Depends(verify_api_key)])


@router.get("/search", response_model=ProductSearchResponse)
def search_products(
    model: str | None = Query(default=None),
    size: str | None = Query(default=None),
    color: str | None = Query(default=None),
) -> dict[str, list[dict[str, Any]]]:
    query = supabase.table("products").select("*")
    if model:
        query = query.ilike("product_name", f"%{model}%")
    if size:
        query = query.eq("size", size)
    if color:
        query = query.ilike("color", color)
    return {"products": query.execute().data}


@router.get("/{sku}/price", response_model=ProductPriceResponse)
def get_product_price(sku: str) -> dict:
    response = supabase.table("products").select("*").eq("sku", sku).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Product not found")
    product = response.data[0]
    effective_price = Decimal(str(product.get("discount_price") or product["base_price"]))
    return {
        "sku": product["sku"],
        "product_name": product["product_name"],
        "base_price": product["base_price"],
        "discount_price": product.get("discount_price"),
        "effective_price": effective_price,
        "currency": product.get("currency") or "INR",
    }
