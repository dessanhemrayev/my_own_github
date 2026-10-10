from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Request

from ..dependencies import repository_service
from ..models import (
    RepositoryCreateRequest,
    RepositoryCreatedResponse,
    RepositoryDeletedResponse,
    RepositoryResponse,
)
from .common import require_existing_user

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


@router.get("/users/{username}/repos", response_model=list[RepositoryResponse])
def list_repositories(username: str, request: Request) -> list[dict[str, str]]:
    _require_api_key(request)
    require_existing_user(username)
    return [
        {"name": repo["name"], "path": repo["path"], "username": repo["username"]}
        for repo in repository_service.list_repositories(username)
    ]


@router.get("/users/{username}/repos/{repo}", response_model=RepositoryResponse)
def get_repository(username: str, repo: str, request: Request) -> dict[str, str]:
    _require_api_key(request)
    require_existing_user(username)
    try:
        result = repository_service.get_repository(username, repo)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"username": result["username"], "name": result["name"], "path": result["path"]}


@router.post("/users/{username}/repos", response_model=RepositoryCreatedResponse)
def create_repository(username: str, payload: RepositoryCreateRequest, request: Request) -> dict[str, str]:
    _require_api_key(request)
    require_existing_user(username)
    if not repository_service.is_valid_repo_name(payload.name):
        raise HTTPException(status_code=400, detail="Repository name may contain only letters, numbers, dots, underscores, hyphens.")

    try:
        result = repository_service.create_repository(username, payload.name)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"status": "created", "username": result["username"], "repo": result["repo"], "path": result["path"]}


@router.delete("/users/{username}/repos/{repo}", response_model=RepositoryDeletedResponse)
def delete_repository(username: str, repo: str, request: Request) -> dict[str, str]:
    _require_api_key(request)
    require_existing_user(username)
    try:
        result = repository_service.delete_repository(username, repo)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"status": "deleted", "username": result["username"], "repo": result["repo"], "path": result["path"]}
