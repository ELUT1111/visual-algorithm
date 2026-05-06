"""REST endpoints for algorithms."""
from __future__ import annotations

import ast
import importlib
import sys
import textwrap
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.engine.registry import registry

router = APIRouter()


class CustomAlgorithmRequest(BaseModel):
    code: str


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

    # Check for forbidden imports
    tree = ast.parse(code)
    forbidden = {"os", "sys", "subprocess", "shutil", "socket", "http", "urllib"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in forbidden:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Forbidden import: {alias.name}",
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in forbidden:
                raise HTTPException(
                    status_code=400,
                    detail=f"Forbidden import: {node.module}",
                )

    # Write to temp file and import
    tmp_dir = Path(tempfile.gettempdir()) / "visual_algo_custom"
    tmp_dir.mkdir(exist_ok=True)
    counter = len(list(tmp_dir.glob("*.py")))
    tmp_file = tmp_dir / f"custom_{counter}.py"
    tmp_file.write_text(code, encoding="utf-8")

    # Add to sys.path and import
    if str(tmp_dir) not in sys.path:
        sys.path.insert(0, str(tmp_dir))

    try:
        module_name = f"custom_{counter}"
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

    return {"status": "ok", "message": "Algorithm registered successfully"}
