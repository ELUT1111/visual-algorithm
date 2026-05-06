"""Graph data models for the Visual Algorithm Lab."""
from __future__ import annotations

import uuid
from pydantic import BaseModel, Field


class Node(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    label: str = ""
    x: float | None = None
    y: float | None = None
    color: str | None = None
    shape: str = "dot"
    size: int = 25
    metadata: dict = Field(default_factory=dict)


class Edge(BaseModel):
    id: str | None = None
    source: str
    target: str
    weight: float = 1.0
    label: str | None = None
    directed: bool = False
    color: str | None = None
    metadata: dict = Field(default_factory=dict)

    def model_post_init(self, __context) -> None:
        if self.id is None:
            self.id = f"{self.source}-{self.target}"


class Graph(BaseModel):
    id: str | None = None
    name: str = "Untitled Graph"
    description: str = ""
    directed: bool = False
    root_id: str | None = None
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
