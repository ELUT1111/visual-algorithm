"""Algorithm protocol - the contract every algorithm must implement."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from backend.models.graph import Graph


class StepAction(str, Enum):
    HIGHLIGHT_NODE = "highlight_node"
    HIGHLIGHT_EDGE = "highlight_edge"
    UNHIGHLIGHT_NODE = "unhighlight_node"
    UNHIGHLIGHT_EDGE = "unhighlight_edge"
    UPDATE_NODE_LABEL = "update_node_label"
    UPDATE_EDGE_LABEL = "update_edge_label"
    SET_NODE_COLOR = "set_node_color"
    SET_EDGE_COLOR = "set_edge_color"
    SET_NODE_BORDER = "set_node_border"
    ADD_MESSAGE = "add_message"
    MARK_VISITED = "mark_visited"
    MARK_CURRENT = "mark_current"
    MARK_PATH = "mark_path"
    RESET_ALL = "reset_all"


@dataclass
class Step:
    action: StepAction
    target_type: str  # "node" or "edge"
    target_id: str
    value: str | float | dict | list | None = None
    message: str = ""
    phase: str = "explore"  # "init", "explore", "relax", "finalize", "result"

    def to_dict(self) -> dict:
        return {
            "action": self.action.value,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "value": self.value,
            "message": self.message,
            "phase": self.phase,
        }


@dataclass
class AlgorithmMeta:
    name: str
    category: str = "graph"
    description: str = ""
    emoji: str = ""
    parameters: list[dict] = field(default_factory=list)
    requires_weighted: bool = False
    requires_directed: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "emoji": self.emoji,
            "parameters": self.parameters,
            "requires_weighted": self.requires_weighted,
            "requires_directed": self.requires_directed,
        }


class AlgorithmProtocol(ABC):
    @abstractmethod
    def get_meta(self) -> AlgorithmMeta:
        ...

    @abstractmethod
    def run(self, graph: Graph, params: dict) -> Generator[Step, None, None]:
        ...
