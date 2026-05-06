"""REST endpoints for preset import/export."""
from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from backend.models.graph import Graph
from backend.routers.graphs import _load_preset_graphs

router = APIRouter()

PRESETS_DIR = Path(__file__).parent.parent / "presets" / "graphs"
MAX_UPLOAD_SIZE = 1024 * 1024  # 1MB


@router.get("/bundle")
def get_all_presets():
    return {"graphs": _load_preset_graphs()}


@router.get("/export/{graph_id}")
def export_graph(graph_id: str):
    for g in _load_preset_graphs():
        if g.get("id") == graph_id:
            return g
    raise HTTPException(status_code=404, detail="Graph not found")


def _sanitize_filename(name: str) -> str:
    """Sanitize a string to be safe for use as a filename."""
    name = re.sub(r"[^\w\-. ]", "_", name)
    name = name.strip(". ")
    if not name:
        name = "imported"
    return name[:100]


@router.post("/import")
async def import_graph(file: UploadFile = File(...)):
    try:
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 1MB)")

        data = json.loads(content.decode("utf-8"))
        # Validate schema
        Graph(**data)

        # Sanitize filename to prevent path traversal
        raw_name = data.get("name", "imported")
        graph_id = _sanitize_filename(raw_name.lower().replace(" ", "_"))
        out_file = PRESETS_DIR / f"{graph_id}.json"

        # Ensure output path is within presets directory
        if not out_file.resolve().is_relative_to(PRESETS_DIR.resolve()):
            raise HTTPException(status_code=400, detail="Invalid graph name")

        out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"status": "ok", "id": graph_id}
    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
