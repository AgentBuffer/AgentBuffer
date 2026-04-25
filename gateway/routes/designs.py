"""Design Director endpoints — stubbed with mock data."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from gateway.auth import OrgId

router = APIRouter(prefix="/api", tags=["designs"])


class DesignRequestBody(BaseModel):
    task_description: str
    task_type: str = "marketing_header"
    brand_id: str
    platform: str | None = None
    inputs: dict = {}


@router.post("/designs/request", status_code=202)
async def request_design(body: DesignRequestBody, org_id: OrgId) -> dict:
    """Trigger the Design Director for brand asset generation.

    Stub: returns a mock task_id and plan skeleton.
    Real implementation: call handle_request() from
    services/design_director/main.py.
    """
    return {
        "task_id": "dtask-mock-001",
        "plan": {
            "steps": [
                {
                    "step_id": "step-000",
                    "agent": "layout",
                    "action": "render_header",
                }
            ],
            "execution_order": "sequential",
        },
    }
