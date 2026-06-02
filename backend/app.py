"""FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.engine.registry import registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Discover and register all algorithms on startup
    registry.discover()
    print(f"Registered {len(registry.list_keys())} algorithms")
    yield


app = FastAPI(title="Visual Algorithm Lab", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from backend.routers import graphs, algorithms, presets, ws_algorithm  # noqa: E402

app.include_router(graphs.router, prefix="/api/graphs", tags=["graphs"])
app.include_router(algorithms.router, prefix="/api/algorithms", tags=["algorithms"])
app.include_router(presets.router, prefix="/api/presets", tags=["presets"])
app.include_router(ws_algorithm.router, tags=["websocket"])

# Serve frontend static files
frontend_dir = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


def _build_health_payload() -> dict:
    metas = registry.list_all()
    category_counts: dict[str, int] = {}
    visualization_counts: dict[str, int] = {}

    for meta in metas:
        category_counts[meta.category] = category_counts.get(meta.category, 0) + 1
        visualization_counts[meta.visualization] = visualization_counts.get(meta.visualization, 0) + 1

    return {
        "status": "ok",
        "algorithm_count": len(registry.list_keys()),
        "categories": dict(sorted(category_counts.items())),
        "visualizations": dict(sorted(visualization_counts.items())),
    }


@app.get("/health")
async def health():
    return _build_health_payload()


@app.get("/")
async def root():
    index_file = frontend_dir / "index.html"
    from fastapi.responses import HTMLResponse

    return HTMLResponse(index_file.read_text(encoding="utf-8"))
