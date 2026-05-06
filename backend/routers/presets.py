"""REST endpoints for preset import/export."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from backend.models.graph import Graph
from backend.routers.graphs import _load_preset_graphs

router = APIRouter()

PRESETS_DIR = Path(__file__).parent.parent / "presets" / "graphs"


@router.get("/bundle")
def get_all_presets():
    return {"graphs": _load_preset_graphs()}


@router.get("/export/{graph_id}")
def export_graph(graph_id: str):
    for g in _load_preset_graphs():
        if g.get("id") == graph_id:
            return g
    raise HTTPException(status_code=404, detail="Graph not found")


@router.post("/import")
async def import_graph(file: UploadFile = File(...)):
    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
        # Validate
        Graph(**data)
        # Save
        graph_id = data.get("name", "imported").lower().replace(" ", "_")
        out_file = PRESETS_DIR / f"{graph_id}.json"
        out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"status": "ok", "id": graph_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
