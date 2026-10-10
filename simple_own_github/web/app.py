from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routes.repositories import router as repositories_router
from .routes.users import router as users_router

app = FastAPI(title="My Own GitHub User Service", version="0.1.0")

WEB_ROOT = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(WEB_ROOT)), name="static")
app.include_router(users_router)
app.include_router(repositories_router)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_ROOT / "index.html")
