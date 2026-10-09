from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..dependencies import repository_service
from ..models import (
    RepositoryCreateRequest,
    RepositoryCreatedResponse,
    RepositoryDeletedResponse,
    RepositoryResponse,
)
from .common import require_existing_user

router = APIRouter()


@router.get("/users/{username}/repos", response_model=list[RepositoryResponse])
def list_repositories(username: str) -> list[dict[str, str]]:
    require_existing_user(username)
    return [
        {"name": repo["name"], "path": repo["path"], "username": repo["username"]}
        for repo in repository_service.list_repositories(username)
    ]


@router.get("/users/{username}/repos/{repo}", response_model=RepositoryResponse)
def get_repository(username: str, repo: str) -> dict[str, str]:
    require_existing_user(username)
    try:
        result = repository_service.get_repository(username, repo)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"username": result["username"], "name": result["name"], "path": result["path"]}


@router.post("/users/{username}/repos", response_model=RepositoryCreatedResponse)
def create_repository(username: str, payload: RepositoryCreateRequest) -> dict[str, str]:
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
def delete_repository(username: str, repo: str) -> dict[str, str]:
    require_existing_user(username)
    try:
        result = repository_service.delete_repository(username, repo)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"status": "deleted", "username": result["username"], "repo": result["repo"], "path": result["path"]}
