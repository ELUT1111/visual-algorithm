"""Algorithm-related models."""
from __future__ import annotations

from pydantic import BaseModel, Field


class AlgorithmParam(BaseModel):
    name: str
    type: str = "str"
    required: bool = False
    default: str | None = None
    description: str = ""


class AlgorithmMeta(BaseModel):
    name: str
    category: str = "graph"
    description: str = ""
    emoji: str = ""
    parameters: list[AlgorithmParam] = Field(default_factory=list)
    requires_weighted: bool = False
    requires_directed: bool = False
