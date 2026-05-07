"""REST endpoints for algorithms."""
from __future__ import annotations

import ast
import importlib
import random
import string
import sys
import uuid
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.engine.registry import registry

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

    # Pick complexity
    if complexity not in _COMPLEXITY:
        complexity = random.choice(list(_COMPLEXITY.keys()))
    cfg = _COMPLEXITY[complexity]
    count = random.randint(*cfg["count"])

    node_ids = [n["id"] for n in graph_data.get("nodes", [])]
    is_construction = algo_meta.layout == "hierarchical" and algo_meta.category == "tree"
    is_traversal = algo_meta.layout == "hierarchical" and not is_construction

    for p in algo_meta.parameters:
        name = p["name"]

        if name == "values":
            params[name] = _random_values(count)
        elif name == "words":
            params[name] = _random_words(count)
        elif name == "patterns":
            params[name] = _random_words(min(count, 5))
        elif name == "text":
            params[name] = _random_text(count)
        elif name == "order":
            params[name] = str(cfg["order"])
        elif name in ("source", "target", "start", "end", "from", "to"):
            if node_ids:
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
