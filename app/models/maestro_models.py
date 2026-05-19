from typing import Any, Literal

from pydantic import BaseModel, Field


ProcessStatus = Literal[
    "Running",
    "Waiting for Human Approval",
    "Completed",
    "Failed",
    "Cancelled",
]


class MaestroProcessCreateRequest(BaseModel):
    maestro_instance_id: str = Field(..., min_length=1)
    customer_id: str | None = None
    order_id: str | None = None
    quotation_id: str | None = None
    process_type: str = "Shoe Order Flow"
    current_step: str | None = None
    process_status: ProcessStatus = "Running"


class MaestroProcessUpdateRequest(BaseModel):
    current_step: str | None = None
    process_status: ProcessStatus | None = None
    exception_flag: bool | None = None
    last_error: str | None = None


class MaestroProcessResponse(BaseModel):
    process: dict[str, Any]
