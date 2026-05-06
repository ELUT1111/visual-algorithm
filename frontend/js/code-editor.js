/* ===== Code Editor for Custom Algorithms ===== */

class CodeEditor {
    constructor() {
        this.editor = document.getElementById('code-editor');
        this._storageKey = 'val_custom_algos';
        this._draftKey = 'val_custom_draft';
        this._initTemplate();
        this._setupSubmit();
        this._setupAutoSave();
        this._renderSavedList();
    }

    _getSavedAlgorithms() {
        try {
            const raw = localStorage.getItem(this._storageKey);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            return [];
        }
    }

    _saveAlgorithms(algos) {
        try {
            localStorage.setItem(this._storageKey, JSON.stringify(algos));
        } catch (e) {}
    }

    _initTemplate() {
        // Restore draft if exists
        try {
            const draft = localStorage.getItem(this._draftKey);
            if (draft) {
                this.editor.value = draft;
                return;
            }
        } catch (e) {}

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
                )

        yield Step(
            action=StepAction.ADD_MESSAGE,
            target_type="node",
            target_id="",
            message=f"Done! Visited {len(visited)} nodes",
            phase="result"
        )`;
    }

    _setupSubmit() {
        document.getElementById('btn-submit-code').addEventListener('click', async () => {
            const code = this.editor.value;

            // Extract algorithm name from code
            const nameMatch = code.match(/name\s*=\s*["']([^"']+)["']/);
            const algoName = nameMatch ? nameMatch[1] : 'unnamed';

            try {
                const response = await fetch('/api/algorithms/custom', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code })
                });
                const result = await response.json();
                if (response.ok) {
                    showToast('Algorithm registered!', 'success');

                    // Save to localStorage
                    this._saveCustomAlgorithm(algoName, code);

                    // Clear draft
                    localStorage.removeItem(this._draftKey);

                    // Reload algorithms in the panel
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

    _setupAutoSave() {
        // Auto-save draft as user types (debounced)
        let timer = null;
        this.editor.addEventListener('input', () => {
            clearTimeout(timer);
            timer = setTimeout(() => {
                try {
                    localStorage.setItem(this._draftKey, this.editor.value);
                } catch (e) {}
            }, 1000);
        });
    }

    _saveCustomAlgorithm(name, code) {
        const algos = this._getSavedAlgorithms();
        const existing = algos.findIndex(a => a.name === name);
        const entry = { name, code, savedAt: Date.now() };
        if (existing >= 0) {
            algos[existing] = entry;
        } else {
            algos.push(entry);
        }
        this._saveAlgorithms(algos);
        this._renderSavedList();
    }

    _renderSavedList() {
        const algos = this._getSavedAlgorithms();
        const container = document.getElementById('custom-section');

        // Remove existing saved list if any
        const existing = document.getElementById('saved-algos-list');
        if (existing) existing.remove();

        if (algos.length === 0) return;

        const listDiv = document.createElement('div');
        listDiv.id = 'saved-algos-list';
        listDiv.className = 'saved-algos';

        const label = document.createElement('div');
        label.className = 'saved-algos-label';
        label.textContent = `Saved (${algos.length})`;
        listDiv.appendChild(label);

        algos.forEach((algo, idx) => {
            const item = document.createElement('div');
            item.className = 'saved-algo-item';

            const nameSpan = document.createElement('span');
            nameSpan.className = 'saved-algo-name';
            nameSpan.textContent = algo.name;
            nameSpan.title = 'Click to load';
            nameSpan.addEventListener('click', () => {
                this.editor.value = algo.code;
                showToast(`Loaded: ${algo.name}`, 'info');
            });

            const timeSpan = document.createElement('span');
            timeSpan.className = 'saved-algo-time';
            timeSpan.textContent = this._formatTime(algo.savedAt);

            const delBtn = document.createElement('button');
            delBtn.className = 'saved-algo-del';
            delBtn.textContent = 'x';
            delBtn.title = 'Delete';
            delBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this._deleteCustomAlgorithm(algo.name);
            });

            item.appendChild(nameSpan);
            item.appendChild(timeSpan);
            item.appendChild(delBtn);
            listDiv.appendChild(item);
        });

        // Insert before the submit button
        const submitBtn = document.getElementById('btn-submit-code');
        container.insertBefore(listDiv, submitBtn);
    }

    _deleteCustomAlgorithm(name) {
        const algos = this._getSavedAlgorithms().filter(a => a.name !== name);
        this._saveAlgorithms(algos);
        this._renderSavedList();
        showToast(`Deleted: ${name}`, 'info');
    }

    _formatTime(timestamp) {
        const d = new Date(timestamp);
        const now = new Date();
        const diff = now - d;
        if (diff < 60000) return 'just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return d.toLocaleDateString();
    }

    getCode() {
        return this.editor.value;
    }

    setCode(code) {
        this.editor.value = code;
    }
}
