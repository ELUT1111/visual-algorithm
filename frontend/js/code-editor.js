/* ===== Code Editor for Custom Algorithms ===== */

class CodeEditor {
    constructor() {
        this.editor = document.getElementById('code-editor');
        this._initTemplate();
        this._setupSubmit();
    }

    _initTemplate() {
        this.editor.value = `"""
Custom Algorithm Template
========================
Implement your graph algorithm here.

Available:
  - graph.nodes: list of Node objects (id, label, metadata)
  - graph.edges: list of Edge objects (source, target, weight, label)
  - yield Step(action, target_type, target_id, value, message, phase)

Step Actions:
  HIGHLIGHT_NODE, HIGHLIGHT_EDGE, UNHIGHLIGHT_NODE, UNHIGHLIGHT_EDGE,
  UPDATE_NODE_LABEL, UPDATE_EDGE_LABEL, SET_NODE_COLOR, SET_EDGE_COLOR,
  MARK_VISITED, MARK_CURRENT, MARK_PATH, RESET_ALL

Phases: "init", "explore", "relax", "finalize", "result"
"""

from backend.engine.protocol import AlgorithmProtocol, AlgorithmMeta, Step, StepAction
from backend.engine.registry import registry

@registry.register
class MyAlgorithm(AlgorithmProtocol):
    def get_meta(self):
        return AlgorithmMeta(
            name="my_algorithm",
            category="graph",
            description="Describe what your algorithm does",
            emoji="My",
            parameters=[
                {"name": "source", "type": "str", "required": True, "description": "Start node"}
            ]
        )

    def run(self, graph, params):
        source = params.get("source", graph.nodes[0].id)

        yield Step(
            action=StepAction.SET_NODE_COLOR,
            target_type="node",
            target_id=source,
            value="current",
            message=f"Starting from node {source}",
            phase="init"
        )

        visited = set([source])

        for edge in graph.edges:
            neighbor = None
            if edge.source == source and edge.target not in visited:
                neighbor = edge.target
            elif edge.target == source and edge.source not in visited:
                neighbor = edge.source

            if neighbor:
                visited.add(neighbor)
                yield Step(
                    action=StepAction.HIGHLIGHT_EDGE,
                    target_type="edge",
                    target_id=edge.id or f"{edge.source}-{edge.target}",
                    value="exploring",
                    message=f"Exploring edge to {neighbor}",
                    phase="explore"
                )
                yield Step(
                    action=StepAction.SET_NODE_COLOR,
                    target_type="node",
                    target_id=neighbor,
                    value="visited",
                    message=f"Visited node {neighbor}",
                    phase="explore"
                )`;
    }

    _setupSubmit() {
        document.getElementById('btn-submit-code').addEventListener('click', async () => {
            const code = this.editor.value;
            try {
                const response = await fetch('/api/algorithms/custom', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code })
                });
                const result = await response.json();
                if (response.ok) {
                    showToast('Algorithm registered!', 'success');
                    // Reload algorithms
                    if (window.app && window.app.algorithmPanel) {
                        await window.app.algorithmPanel._loadAlgorithms();
                    }
                } else {
                    showToast(result.detail || 'Failed to submit', 'error');
                }
            } catch (e) {
                showToast('Network error', 'error');
            }
        });
    }

    getCode() {
        return this.editor.value;
    }

    setCode(code) {
        this.editor.value = code;
    }
}
