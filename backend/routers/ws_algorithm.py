"""WebSocket endpoint for algorithm execution."""
from __future__ import annotations

import asyncio
import traceback

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.engine.registry import registry
from backend.engine.runner import AlgorithmRunner, RunState
from backend.models.graph import Graph

router = APIRouter()


@router.websocket("/ws/run")
async def run_algorithm_ws(websocket: WebSocket):
    await websocket.accept()
    runner: AlgorithmRunner | None = None
    speed = 0.5
    exec_task: asyncio.Task | None = None

    async def _execute_loop():
        nonlocal speed
        while runner and runner.state in (RunState.RUNNING, RunState.STEPPING):
            await runner.wait_if_paused()
            if runner.state == RunState.PAUSED:
                break

            step = runner.advance()
            if step is None:
                await websocket.send_json({"type": "finished"})
                break

            await websocket.send_json({"type": "step", "data": step.to_dict()})

            if runner.state == RunState.STEPPING:
                runner.state = RunState.PAUSED
                runner._pause_event.clear()
                await websocket.send_json({"type": "paused"})
                break

            await asyncio.sleep(runner.speed)

    try:
        while True:
            msg = await websocket.receive_json()
            command = msg.get("command", "")

            if command == "start":
                algo_key = msg.get("algorithm_key", "")
                graph_data = msg.get("graph", {})
                params = msg.get("params", {})
                speed = msg.get("speed", 500) / 1000.0

                try:
                    algo = registry.get(algo_key)
                    graph = Graph(**graph_data)
                    runner = AlgorithmRunner(algo, graph, params)
                    runner.speed = speed
                    runner.start()

                    await websocket.send_json({
                        "type": "meta",
                        "data": algo.get_meta().to_dict(),
                    })

                    exec_task = asyncio.create_task(_execute_loop())

                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": str(e)},
                    })

            elif command == "pause":
                if runner:
                    runner.pause()

            elif command == "resume":
                if runner and runner.state == RunState.PAUSED:
                    runner.resume()
                    exec_task = asyncio.create_task(_execute_loop())

            elif command == "step":
                if runner:
                    if runner.state == RunState.IDLE:
                        runner.start()
                    runner.step_forward()
                    exec_task = asyncio.create_task(_execute_loop())

            elif command == "speed":
                new_speed = msg.get("value", 500) / 1000.0
                speed = new_speed
                if runner:
                    runner.speed = new_speed

            elif command == "reset":
                if exec_task and not exec_task.done():
                    exec_task.cancel()
                if runner:
                    runner.reset()
                runner = None
                await websocket.send_json({"type": "reset_done"})

    except WebSocketDisconnect:
        if exec_task and not exec_task.done():
            exec_task.cancel()
    except Exception:
        traceback.print_exc()
        if exec_task and not exec_task.done():
            exec_task.cancel()
