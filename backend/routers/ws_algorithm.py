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
        try:
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
        except asyncio.CancelledError:
            pass
        except Exception as e:
            try:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"Algorithm error: {e}"},
                })
            except Exception:
                pass

    def _create_runner(algo_key: str, graph_data: dict, params: dict, spd: float):
        """Create and validate a runner. Raises on failure."""
        algo = registry.get(algo_key)
        graph = Graph(**graph_data)

        # Validate required params
        meta = algo.get_meta()
        for p in meta.parameters:
            if p.get("required") and not params.get(p["name"]):
                raise ValueError(f"Parameter '{p['name']}' is required")

        # Validate source/target nodes exist
        node_ids = {n.id for n in graph.nodes}
        for p in meta.parameters:
            val = params.get(p["name"], "")
            if val and val not in node_ids:
                raise ValueError(f"Node '{val}' not found in graph")

        if not graph.nodes:
            raise ValueError("Graph has no nodes")

        r = AlgorithmRunner(algo, graph, params)
        r.speed = spd
        return r

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
                    runner = _create_runner(algo_key, graph_data, params, speed)
                    runner.start()

                    await websocket.send_json({
                        "type": "meta",
                        "data": runner.algorithm.get_meta().to_dict(),
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
                # First step: create runner if needed
                if runner is None:
                    algo_key = msg.get("algorithm_key", "")
                    graph_data = msg.get("graph", {})
                    params = msg.get("params", {})
                    speed = msg.get("speed", 500) / 1000.0
                    if not algo_key:
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": "Please select an algorithm first"},
                        })
                        continue
                    try:
                        runner = _create_runner(algo_key, graph_data, params, speed)
                        runner.start()

                        await websocket.send_json({
                            "type": "meta",
                            "data": runner.algorithm.get_meta().to_dict(),
                        })
                    except Exception as e:
                        runner = None
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": str(e)},
                        })
                        continue

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
