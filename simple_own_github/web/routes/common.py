from __future__ import annotations

import pwd

from fastapi import HTTPException

from ..dependencies import user_service


def require_existing_user(username: str) -> None:
    if not user_service.is_valid_username(username):
        raise HTTPException(status_code=400, detail="Username must contain only lowercase letters.")

    try:
        pwd.getpwnam(username)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"User '{username}' does not exist.") from exc
