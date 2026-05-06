"""REST endpoints for graph presets."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.models.graph import Graph

router = APIRouter()

PRESETS_DIR = Path(__file__).parent.parent / "presets" / "graphs"


def _load_preset_graphs() -> list[dict]:
    graphs = []
    if PRESETS_DIR.exists():
        for f in sorted(PRESETS_DIR.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                data.setdefault("id", f.stem)
                graphs.append(data)
            except Exception:
                pass
    return graphs


@router.get("")
def list_graphs():
    return _load_preset_graphs()


@router.get("/{graph_id}")
def get_graph(graph_id: str):
    for g in _load_preset_graphs():
        if g.get("id") == graph_id:
            return g
    raise HTTPException(status_code=404, detail="Graph not found")
