from fastapi import APIRouter, Depends, HTTPException

from app.auth import verify_api_key
from app.models.maestro_models import (
    MaestroProcessCreateRequest,
    MaestroProcessResponse,
    MaestroProcessUpdateRequest,
)
from app.supabase_client import supabase

router = APIRouter(prefix="/api/maestro/processes", tags=["maestro"], dependencies=[Depends(verify_api_key)])


@router.post("", response_model=MaestroProcessResponse)
def create_process(payload: MaestroProcessCreateRequest) -> dict:
    existing = (
        supabase.table("maestro_processes")
        .select("id")
        .eq("maestro_instance_id", payload.maestro_instance_id)
        .limit(1)
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=409, detail="Duplicate maestro_instance_id")
    process = supabase.table("maestro_processes").insert(payload.model_dump(exclude_none=True)).execute().data[0]
    return {"process": process}


@router.get("/{maestro_instance_id}", response_model=MaestroProcessResponse)
def get_process(maestro_instance_id: str) -> dict:
    response = (
        supabase.table("maestro_processes")
        .select("*")
        .eq("maestro_instance_id", maestro_instance_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Maestro process not found")
    return {"process": response.data[0]}


@router.patch("/{maestro_instance_id}", response_model=MaestroProcessResponse)
def update_process(maestro_instance_id: str, payload: MaestroProcessUpdateRequest) -> dict:
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No process fields provided")
    updated = (
        supabase.table("maestro_processes")
        .update(updates)
        .eq("maestro_instance_id", maestro_instance_id)
        .execute()
        .data
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Maestro process not found")
    return {"process": updated[0]}
