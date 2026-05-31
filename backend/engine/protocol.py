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
    ADD_NODE = "add_node"
    ADD_EDGE = "add_edge"
    REMOVE_NODE = "remove_node"
    REMOVE_EDGE = "remove_edge"
    UPDATE_NODE_POSITION = "update_node_position"


@dataclass
class Step:
    action: StepAction
    target_type: str  # "node" or "edge"
    target_id: str
    value: str | float | dict | list | None = None
    message: str = ""
    phase: str = "explore"  # "init", "explore", "relax", "finalize", "result"
    state: dict | None = None

    def to_dict(self) -> dict:
        return {
            "action": self.action.value,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "value": self.value,
            "message": self.message,
            "phase": self.phase,
            "state": self.state,
        }


@dataclass
class AlgorithmMeta:
    name: str
    category: str = "graph"
    description: str = ""
    emoji: str = ""
    parameters: list[dict] = field(default_factory=list)
    requires_graph: bool = True
    builds_structure: bool = False
    requires_weighted: bool = False
    requires_directed: bool = False
    requires_dag: bool = False
    allows_negative_weights: bool = True
    time_complexity: str = ""
    space_complexity: str = ""
    use_cases: list[str] = field(default_factory=list)
    pseudocode: str = ""
    layout: str = "force"  # "force" or "hierarchical"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "emoji": self.emoji,
            "parameters": self.parameters,
            "requires_graph": self.requires_graph,
            "builds_structure": self.builds_structure,
            "requires_weighted": self.requires_weighted,
            "requires_directed": self.requires_directed,
            "requires_dag": self.requires_dag,
            "allows_negative_weights": self.allows_negative_weights,
            "time_complexity": self.time_complexity,
            "space_complexity": self.space_complexity,
            "use_cases": self.use_cases,
            "pseudocode": self.pseudocode,
            "layout": self.layout,
        }


class AlgorithmProtocol(ABC):
    @abstractmethod
    def get_meta(self) -> AlgorithmMeta:
        ...

    @abstractmethod
    def run(self, graph: Graph, params: dict) -> Generator[Step, None, None]:
        ...
