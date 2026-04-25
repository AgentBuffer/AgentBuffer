"""JWT verification middleware for Supabase-issued tokens."""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "stub-secret")


def _extract_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    return auth.removeprefix("Bearer ").strip()


def get_org_id(request: Request) -> str:
    """Extract org_id from a Supabase JWT.

    In stub mode (no real secret), returns a fixed demo org_id so the
    frontend can develop against real-shaped responses.
    """
    token = _extract_token(request)

    if SUPABASE_JWT_SECRET == "stub-secret":
        return "org-demo-001"

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        org_id: str | None = (payload.get("app_metadata") or {}).get("org_id")
        if not org_id:
            raise HTTPException(status_code=403, detail="No org_id in token")
        return org_id
    except JWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc


OrgId = Annotated[str, Depends(get_org_id)]
