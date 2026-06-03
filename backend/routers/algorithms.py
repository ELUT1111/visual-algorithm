"""REST endpoints for algorithms."""
from __future__ import annotations

import ast
import importlib
import random
import string
import sys
import uuid
import tempfile
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.engine.registry import registry
from backend.models.graph import Graph

router = APIRouter()


class CustomAlgorithmRequest(BaseModel):
    code: str = Field(max_length=50000)


# Names that are forbidden in custom algorithm code
_FORBIDDEN_NAMES = {
    "os", "sys", "subprocess", "shutil", "socket", "http", "urllib",
    "ctypes", "importlib", "pathlib", "io", "tempfile", "glob",
    "signal", "multiprocessing", "threading", "webbrowser",
    "__import__", "exec", "eval", "compile", "open", "breakpoint",
    "globals", "locals", "vars", "dir", "getattr", "setattr", "delattr",
    "__builtins__", "__loader__", "__spec__",
}


def _validate_code_safety(code: str) -> str | None:
    """Validate code safety. Returns error message or None if safe."""
    tree = ast.parse(code)

    for node in ast.walk(tree):
        # Block import statements
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _FORBIDDEN_NAMES:
                    return f"Forbidden import: {alias.name}"

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in _FORBIDDEN_NAMES:
                    return f"Forbidden import: {node.module}"

        # Block calls to dangerous builtins
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in _FORBIDDEN_NAMES:
                return f"Forbidden call: {func.id}()"
            # Block __import__('subprocess') style
            if isinstance(func, ast.Attribute) and func.attr in ("__import__",):
                return f"Forbidden attribute access: {func.attr}"

        # Block attribute access to __builtins__ etc
        elif isinstance(node, ast.Attribute):
            if node.attr in ("__builtins__", "__loader__", "__spec__", "__import__"):
                return f"Forbidden attribute: {node.attr}"

        # Block Name nodes that reference dangerous builtins
        elif isinstance(node, ast.Name):
            if node.id in _FORBIDDEN_NAMES and node.id not in {"open"}:
                # Allow "open" as a string in descriptions etc, only block as calls
                pass

    return None


@router.get("")
def list_algorithms(category: str | None = None):
    metas = registry.list_all(category=category)
    return [m.to_dict() for m in metas]


@router.get("/{category}/{name}")
def get_algorithm(category: str, name: str):
    key = f"{category}/{name}"
    try:
        algo = registry.get(key)
        return algo.get_meta().to_dict()
    except KeyError:
        raise HTTPException(status_code=404, detail="Algorithm not found")


# --- Random parameter generation ---

# Complexity presets: (label, value_range_or_count)
_COMPLEXITY = {
    "simple":  {"count": (5, 8),  "order": 3},
    "medium":  {"count": (8, 15), "order": 4},
    "complex": {"count": (15, 25), "order": 5},
}

_COMMON_WORDS = [
    "apple", "app", "apt", "bat", "bar", "bin", "bit", "cat", "car", "cap",
    "dog", "dot", "dry", "egg", "end", "ear", "fox", "fun", "fog", "gap",
    "get", "got", "hat", "hit", "hot", "ink", "ion", "ice", "jar", "jet",
    "joy", "key", "kid", "kit", "log", "lot", "low", "map", "mix", "mud",
    "net", "new", "nil", "nut", "oak", "odd", "oil", "opt", "pan", "peg",
    "pet", "pin", "pot", "put", "ram", "red", "rig", "rod", "row", "rub",
    "run", "sad", "set", "sip", "sir", "sit", "ski", "sob", "sow", "spy",
    "sub", "sum", "sun", "tab", "tag", "tan", "tap", "tar", "tip", "toe",
    "ton", "top", "try", "tub", "urn", "use", "van", "vet", "vow", "wad",
    "war", "wax", "web", "wed", "wet", "who", "win", "wit", "woe", "wok",
    "won", "woo", "yak", "yam", "yap", "yaw", "yea", "yes", "yet", "yew",
    "zap", "zed", "zen", "zig", "zip", "zoo",
]


def _random_values(count: int, lo: int = 1, hi: int = 999) -> str:
    """Generate comma-separated unique random integers."""
    nums = random.sample(range(lo, hi + 1), min(count, hi - lo + 1))
    return ",".join(str(n) for n in nums)


def _random_words(count: int) -> str:
    """Generate comma-separated random words."""
    words = random.sample(_COMMON_WORDS, min(count, len(_COMMON_WORDS)))
    return ",".join(words)


def _random_text(length: int) -> str:
    """Generate a random lowercase text string."""
    return "".join(random.choices(string.ascii_lowercase, k=length))


def _generate_params(algo_meta, graph_data: dict, complexity: str | None) -> dict:
    """Generate random parameters for an algorithm."""
    params = {}
    generated_values: list[int | str] = []
    generated_text = ""

    # Pick complexity
    if complexity not in _COMPLEXITY:
        complexity = random.choice(list(_COMPLEXITY.keys()))
    cfg = _COMPLEXITY[complexity]
    count = random.randint(*cfg["count"])

    node_ids = [n["id"] for n in graph_data.get("nodes", [])]
    for p in algo_meta.parameters:
        name = p["name"]

        if name == "values":
            if algo_meta.name == "binary_search":
                values = sorted(random.sample(range(1, 999), min(count, 999)))
                generated_values = values
                params[name] = ",".join(str(v) for v in values)
            elif algo_meta.name == "kadane":
                values = [random.randint(-30, 40) for _ in range(count)]
                generated_values = values
                params[name] = ",".join(str(v) for v in values)
            else:
                values = [int(v) for v in _random_values(count).split(",")]
                generated_values = values
                params[name] = ",".join(str(v) for v in values)
        elif name == "coins":
            coins = sorted(random.sample(range(1, 15), min(4, count)))
            generated_values = coins
            params[name] = ",".join(str(v) for v in coins)
        elif name == "amount":
            if generated_values:
                params[name] = str(random.randint(max(1, int(max(generated_values))), max(8, int(sum(generated_values)) * 2)))
            else:
                params[name] = str(random.randint(8, 40))
        elif name == "weights":
            weights = [random.randint(1, 9) for _ in range(count)]
            generated_values = weights
            params[name] = ",".join(str(v) for v in weights)
        elif name == "capacity":
            if generated_values:
                params[name] = str(max(1, sum(int(v) for v in generated_values) // 2))
            else:
                params[name] = str(random.randint(5, 30))
        elif name == "dimensions":
            dims = [random.randint(5, 80) for _ in range(max(4, min(count, 7)))]
            params[name] = ",".join(str(v) for v in dims)
        elif name == "n":
            params[name] = str(random.randint(5, min(20, max(5, count + 5))))
        elif name == "query_index":
            params[name] = str(random.randint(1, max(1, count)))
        elif name == "words":
            params[name] = _random_words(count)
        elif name == "patterns":
            params[name] = _random_words(min(count, 5))
        elif name == "text":
            if algo_meta.name == "kmp":
                seed = random.choice(_COMMON_WORDS)
                generated_text = f"{_random_text(4)}{seed}{_random_text(3)}{seed}"
            else:
                generated_text = _random_text(count)
            params[name] = generated_text
        elif name == "pattern":
            if generated_text and len(generated_text) >= 4:
                start = random.randint(0, max(0, len(generated_text) - 3))
                params[name] = generated_text[start:start + 3]
            else:
                params[name] = random.choice(_COMMON_WORDS)
        elif name in ("text_a", "text_b"):
            params[name] = _random_text(max(4, min(count, 12)))
        elif name == "order":
            params[name] = str(cfg["order"])
        elif name in ("source", "target", "start", "end", "from", "to"):
            if name == "target" and algo_meta.name == "subset_sum" and generated_values:
                sample_size = random.randint(1, min(4, len(generated_values)))
                params[name] = str(sum(int(v) for v in random.sample(generated_values, sample_size)))
            elif name == "target" and algo_meta.name in {"edmonds_karp", "dinic", "push_relabel"} and node_ids:
                choices = [node_id for node_id in node_ids if node_id != params.get("source")]
                params[name] = random.choice(choices or node_ids)
            elif name == "target" and generated_values:
                params[name] = str(random.choice(generated_values))
            elif node_ids:
                params[name] = random.choice(node_ids)
            else:
                params[name] = p.get("default", "")
        else:
            params[name] = p.get("default", "")

    return params


class RandomParamsRequest(BaseModel):
    algorithm_key: str
    graph: dict = Field(default_factory=dict)
    complexity: str | None = None  # "simple" | "medium" | "complex" | None=random


class CompareAlgorithmsRequest(BaseModel):
    algorithm_keys: list[str] = Field(min_length=1, max_length=8)
    graph: dict = Field(default_factory=dict)
    params: dict = Field(default_factory=dict)


@router.post("/random-params")
def generate_random_params(req: RandomParamsRequest):
    """Generate random parameters for a given algorithm."""
    try:
        algo = registry.get(req.algorithm_key)
    except KeyError:
        raise HTTPException(status_code=404, detail="Algorithm not found")

    meta = algo.get_meta()
    params = _generate_params(meta, req.graph, req.complexity)
    return {"params": params, "complexity": req.complexity or "random"}


def _summarize_final_state(state: dict | None) -> dict:
    if not state:
        return {}

    preferred_keys = [
        "found",
        "index",
        "distance",
        "distances",
        "negative_cycle",
        "max_flow",
        "matches",
        "length",
        "lcs",
        "min_cost",
        "fib_n",
        "subset_found",
        "selected_sum",
        "min_coins",
        "max_value",
        "max_sum",
        "sorted",
        "array",
        "components",
        "cycle",
        "topological_order",
        "mst_weight",
    ]
    summary = {key: state[key] for key in preferred_keys if key in state}
    if summary:
        return summary
    return {key: value for key, value in list(state.items())[:5]}


def _collect_step_metrics(steps: list[dict]) -> dict:
    phases: dict[str, int] = {}
    actions: dict[str, int] = {}
    visited_nodes: set[str] = set()
    highlighted_edges: set[str] = set()

    for step in steps:
        phase = step.get("phase") or "unknown"
        action = step.get("action") or "unknown"
        phases[phase] = phases.get(phase, 0) + 1
        actions[action] = actions.get(action, 0) + 1

        if step.get("target_type") == "node":
            target_id = step.get("target_id")
            if target_id:
                visited_nodes.add(str(target_id))
        if step.get("target_type") == "edge":
            target_id = step.get("target_id")
            if target_id:
                highlighted_edges.add(str(target_id))

    return {
        "phase_counts": dict(sorted(phases.items())),
        "action_counts": dict(sorted(actions.items())),
        "visited_node_count": len(visited_nodes),
        "touched_edge_count": len(highlighted_edges),
    }


@router.post("/compare")
def compare_algorithms(req: CompareAlgorithmsRequest):
    """Run multiple algorithms on the same input and return a compact comparison."""
    graph = Graph(**req.graph)
    results = []

    # Local import avoids coupling router module import order.
    from backend.routers.ws_algorithm import _validate_runner_inputs

    for key in req.algorithm_keys:
        started = time.perf_counter()
        try:
            algo = registry.get(key)
            meta = algo.get_meta()
            params = dict(req.params)
            _validate_runner_inputs(key, meta, graph, params)

            steps = [step.to_dict() for step in algo.run(graph, params)]
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            final_state = steps[-1].get("state") if steps else None
            metrics = _collect_step_metrics(steps)

            results.append({
                "algorithm_key": key,
                "name": meta.name,
                "category": meta.category,
                "status": "ok",
                "step_count": len(steps),
                "duration_ms": elapsed_ms,
                "visited_node_count": metrics["visited_node_count"],
                "touched_edge_count": metrics["touched_edge_count"],
                "phase_counts": metrics["phase_counts"],
                "action_counts": metrics["action_counts"],
                "summary": _summarize_final_state(final_state),
            })
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            results.append({
                "algorithm_key": key,
                "name": key.split("/")[-1],
                "category": key.split("/")[0] if "/" in key else "",
                "status": "error",
                "step_count": 0,
                "duration_ms": elapsed_ms,
                "visited_node_count": 0,
                "touched_edge_count": 0,
                "phase_counts": {},
                "action_counts": {},
                "summary": {},
                "error": str(e),
            })

    return {
        "algorithm_count": len(results),
        "params": req.params,
        "results": results,
    }


@router.post("/custom")
def submit_custom_algorithm(req: CustomAlgorithmRequest):
    """Validate and register a user-submitted algorithm."""
    code = req.code

    # Basic syntax check
    try:
        ast.parse(code)
    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Syntax error: {e}")

    # Security validation
    error = _validate_code_safety(code)
    if error:
        raise HTTPException(status_code=400, detail=error)

    # Write to temp file with unique name
    tmp_dir = Path(tempfile.gettempdir()) / "visual_algo_custom"
    tmp_dir.mkdir(exist_ok=True)
    module_name = f"custom_{uuid.uuid4().hex[:8]}"
    tmp_file = tmp_dir / f"{module_name}.py"
    tmp_file.write_text(code, encoding="utf-8")

    # Add to sys.path and import
    tmp_dir_str = str(tmp_dir)
    if tmp_dir_str not in sys.path:
        sys.path.insert(0, tmp_dir_str)

    try:
        if module_name in sys.modules:
            del sys.modules[module_name]
        mod = importlib.import_module(module_name)

        # Find AlgorithmProtocol subclass
        from backend.engine.protocol import AlgorithmProtocol

        found = False
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, AlgorithmProtocol)
                and attr is not AlgorithmProtocol
            ):
                registry.register(attr)
                found = True

        if not found:
            raise HTTPException(
                status_code=400,
                detail="No AlgorithmProtocol subclass found in code",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading algorithm: {e}")
    finally:
        # Clean up temp file
        try:
            tmp_file.unlink(missing_ok=True)
        except Exception:
            pass

    return {"status": "ok", "message": "Algorithm registered successfully"}
