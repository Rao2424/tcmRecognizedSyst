"""Compatibility entrypoint for ``uvicorn vision_adapter.main:app`` from the repo root."""

from backend.vision_adapter.main import app

__all__ = ["app"]
