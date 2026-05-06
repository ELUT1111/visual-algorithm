"""REST endpoints for algorithms."""
from __future__ import annotations

import ast
import importlib
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
