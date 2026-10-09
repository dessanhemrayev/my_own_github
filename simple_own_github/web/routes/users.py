from __future__ import annotations

from fastapi import APIRouter, HTTPException

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


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/users/validate", response_model=UserValidationResponse)
def validate_user(payload: UserValidationRequest) -> dict[str, bool]:
    return {
        "username": user_service.is_valid_username(payload.username),
        "comment": user_service.is_valid_comment(payload.comment),
        "password": user_service.is_valid_password(payload.password),
    }


@router.post("/users", response_model=UserCreatedResponse)
def create_user(payload: UserCreateRequest) -> dict[str, str]:
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

    user_service.create_user(payload.username, payload.comment, payload.password)
    return {"status": "created", "username": payload.username}
