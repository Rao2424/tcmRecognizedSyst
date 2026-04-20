"""Compatibility entrypoint for ``uvicorn app.main:app`` from the repo root."""

from backend.app.main import app

__all__ = ["app"]
