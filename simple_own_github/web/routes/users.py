from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Request

try:
    from simple_own_github.service.adduser import root_check
except ImportError:  # pragma: no cover
    from service.adduser import root_check

from ..dependencies import user_service
from ..models import (
    UserCreateRequest,
    UserCreatedResponse,
    UserValidationRequest,
    UserValidationResponse,
)

router = APIRouter()


def _require_api_key(request: Request) -> None:
    expected_key = os.environ.get("SIMPLE_OWN_GITHUB_API_KEY")
    if not expected_key:
        return

    provided_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
    if provided_key and provided_key.lower().startswith("bearer "):
        provided_key = provided_key.split(None, 1)[1]
    if provided_key != expected_key:
        raise HTTPException(status_code=401, detail="Authentication required.")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/users/validate", response_model=UserValidationResponse)
def validate_user(payload: UserValidationRequest, request: Request) -> dict[str, bool]:
    _require_api_key(request)
    return {
        "username": user_service.is_valid_username(payload.username),
        "comment": user_service.is_valid_comment(payload.comment),
        "password": user_service.is_valid_password(payload.password),
    }


@router.post("/users", response_model=UserCreatedResponse)
def create_user(payload: UserCreateRequest, request: Request) -> dict[str, str]:
    _require_api_key(request)
    if not user_service.is_valid_username(payload.username):
        raise HTTPException(status_code=400, detail="Username must contain only lowercase letters.")
    if not user_service.is_valid_comment(payload.comment):
        raise HTTPException(status_code=400, detail="Comment may contain only lowercase letters and commas.")
    if not user_service.is_valid_password(payload.password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 chars and include letters, digits, and symbols.")

    try:
        root_check()
    except SystemExit as exc:
        raise HTTPException(status_code=403, detail="Root privileges are required to create a system user.") from exc

    try:
        user_service.create_user(payload.username, payload.comment, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "created", "username": payload.username}
