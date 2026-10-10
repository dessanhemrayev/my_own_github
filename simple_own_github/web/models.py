from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    comment: str = ""


class UserValidationRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = ""
    comment: str = ""


class UserValidationResponse(BaseModel):
    username: bool
    comment: bool
    password: bool


class UserCreatedResponse(BaseModel):
    status: Literal["created"]
    username: str


class RepositoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)


class RepositoryResponse(BaseModel):
    username: str
    name: str
    path: str


class RepositoryCreatedResponse(BaseModel):
    status: Literal["created"]
    username: str
    repo: str
    path: str


class RepositoryDeletedResponse(BaseModel):
    status: Literal["deleted"]
    username: str
    repo: str
    path: str
