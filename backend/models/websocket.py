"""WebSocket message schemas."""
from __future__ import annotations

from pydantic import BaseModel


class WSCommand(BaseModel):
    command: str
    algorithm_key: str | None = None
    graph: dict | None = None
    params: dict | None = None
    speed: int | None = None
    value: int | None = None


class WSResponse(BaseModel):
    type: str
    data: dict | None = None
