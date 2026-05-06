"""Algorithm execution runner with pause/resume/step support."""
from __future__ import annotations

import asyncio
from enum import Enum
from typing import Generator

from backend.engine.protocol import AlgorithmProtocol, Step
from backend.models.graph import Graph


class RunState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STEPPING = "stepping"
    FINISHED = "finished"
    ERROR = "error"


class AlgorithmRunner:
    def __init__(
        self,
        algorithm: AlgorithmProtocol,
        graph: Graph,
        params: dict,
    ) -> None:
        self.algorithm = algorithm
        self.graph = graph
        self.params = params
        self.generator: Generator[Step, None, None] | None = None
        self.state = RunState.IDLE
        self.current_step: Step | None = None
        self.step_history: list[Step] = []
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # not paused initially
        self.speed: float = 0.5  # seconds between steps

    def start(self) -> None:
        self.generator = self.algorithm.run(self.graph, self.params)
        self.state = RunState.RUNNING
        self.step_history.clear()

    def advance(self) -> Step | None:
        if self.generator is None:
            return None
        try:
            step = next(self.generator)
            self.current_step = step
            self.step_history.append(step)
            return step
        except StopIteration:
            self.state = RunState.FINISHED
            return None

    def pause(self) -> None:
        self.state = RunState.PAUSED
        self._pause_event.clear()

    def resume(self) -> None:
        self.state = RunState.RUNNING
        self._pause_event.set()

    def step_forward(self) -> None:
        self.state = RunState.STEPPING
        self._pause_event.set()

    def reset(self) -> None:
        self.generator = None
        self.state = RunState.IDLE
        self.current_step = None
        self.step_history.clear()
        self._pause_event.set()

    async def wait_if_paused(self) -> None:
        await self._pause_event.wait()
