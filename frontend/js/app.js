/* ===== Main Application ===== */

class App {
    constructor() {
        const wsProto = location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.wsClient = new WSClient(`${wsProto}//${location.host}/ws/run`);
        this.graphEditor = new GraphEditor('graph-container');
        this.visualizer = new Visualizer(this.graphEditor);
        this.algorithmPanel = new AlgorithmPanel(this.wsClient, this.visualizer, this.graphEditor);
        this.codeEditor = new CodeEditor();
        this.presetManager = new PresetManager(this.graphEditor);
    }

    async init() {
        // Connect WebSocket
        this.wsClient.connect();

        // Load algorithms and presets
        await Promise.all([
            this.algorithmPanel.init(),
            this.presetManager.init()
        ]);

        // Restore from localStorage, or load default preset
        const restored = this.graphEditor.restoreFromStorage();
        if (!restored && this.presetManager.presets.length > 0) {
            this.graphEditor.loadFromJSON(this.presetManager.presets[0]);
        }

        // Clear undo history after initial load
        this.graphEditor._undoStack = [];
        this.graphEditor._redoStack = [];

        // Setup interactive graph tools
        this._setupGraphTools();

        // Setup undo/redo buttons
        this._setupUndoRedo();

        // Setup keyboard shortcuts
        this._setupKeyboard();

        // Setup resizable bottom panel
        this._setupPanelResize();

        showToast('Visual Algorithm Lab ready!', 'success');
    }

    _setupGraphTools() {
        const btnAddNode = document.getElementById('btn-add-node');
        const btnAddEdge = document.getElementById('btn-add-edge');
        const btnDelete = document.getElementById('btn-delete');
        const btnPhysics = document.getElementById('btn-toggle-physics');

        // Add Node
        btnAddNode.addEventListener('click', async () => {
            const values = await showModal('Add Node', [
                { name: 'id', label: 'Node ID', placeholder: 'e.g. A, B, C...' }
            ]);
            if (values && values.id) {
                this.graphEditor.addNode(values.id.trim());
            }
        });

        // Add Edge
        btnAddEdge.addEventListener('click', async () => {
            const nodeIds = this.graphEditor.getNodeIds();
            if (nodeIds.length < 2) {
                showToast('Need at least 2 nodes', 'error');
                return;
            }
            const values = await showModal('Add Edge', [
                { name: 'from', label: 'From Node', placeholder: nodeIds[0] },
                { name: 'to', label: 'To Node', placeholder: nodeIds[1] },
                { name: 'weight', label: 'Weight', type: 'number', value: '1' }
            ]);
            if (values && values.from && values.to) {
                this.graphEditor.addEdge(
                    values.from.trim(),
                    values.to.trim(),
                    parseFloat(values.weight) || 1
                );
            }
        });

        // Delete
        btnDelete.addEventListener('click', () => {
            this.graphEditor.deleteSelected();
        });

        // Physics toggle
        btnPhysics.addEventListener('click', () => {
            const enabled = this.graphEditor.togglePhysics();
            btnPhysics.classList.toggle('active', enabled);
            showToast(enabled ? 'Physics enabled' : 'Physics disabled', 'info');
        });

        // Fit all nodes in view
        document.getElementById('btn-fit-all').addEventListener('click', () => {
            this.graphEditor.fitAll();
        });

        // Focus on selected nodes
        document.getElementById('btn-focus-selected').addEventListener('click', () => {
            this.graphEditor.focusSelected();
        });

        // Double-click to add node quickly
        this.graphEditor.network.on('doubleClick', async (params) => {
            if (params.nodes.length === 0 && params.edges.length === 0) {
                const values = await showModal('Add Node', [
                    { name: 'id', label: 'Node ID', placeholder: 'e.g. A, B, C...' }
                ]);
                if (values && values.id) {
                    this.graphEditor.addNode(values.id.trim(), params.pointer.canvas.x, params.pointer.canvas.y);
                }
            }
        });
    }

    _setupUndoRedo() {
        const btnUndo = document.getElementById('btn-undo');
        const btnRedo = document.getElementById('btn-redo');

        btnUndo.addEventListener('click', () => this._doUndo());
        btnRedo.addEventListener('click', () => this._doRedo());

        // Update button states when graph changes
        this._updateUndoRedoButtons();

        // Periodically check undo/redo state (simple approach)
        setInterval(() => this._updateUndoRedoButtons(), 500);
    }

    _doUndo() {
        if (this.graphEditor.undo()) {
            showToast('Undo', 'info');
        }
        this._updateUndoRedoButtons();
    }

    _doRedo() {
        if (this.graphEditor.redo()) {
            showToast('Redo', 'info');
        }
        this._updateUndoRedoButtons();
    }

    _updateUndoRedoButtons() {
        const btnUndo = document.getElementById('btn-undo');
        const btnRedo = document.getElementById('btn-redo');
        if (btnUndo) btnUndo.disabled = !this.graphEditor.canUndo();
        if (btnRedo) btnRedo.disabled = !this.graphEditor.canRedo();
    }

    _setupPanelResize() {
        const handle = document.getElementById('panel-resize-handle');
        const bottomPanel = document.getElementById('bottom-panel');
        const mainContent = document.getElementById('main-content');
        if (!handle || !bottomPanel || !mainContent) return;

        const STORAGE_KEY = 'val_bottomPanelHeight';
        const MIN_HEIGHT = 180;  // control bar (56) + timeline (38) + state/log minimum
        const MAX_RATIO = 0.6;

        // Restore saved height
        const saved = parseInt(localStorage.getItem(STORAGE_KEY), 10);
        if (!isNaN(saved)) {
            const maxH = mainContent.clientHeight * MAX_RATIO;
            const h = Math.max(MIN_HEIGHT, Math.min(saved, maxH));
            bottomPanel.style.height = h + 'px';
        }

        let dragging = false;
        let startY = 0;
        let startH = 0;

        const onMouseMove = (e) => {
            if (!dragging) return;
            const maxH = mainContent.clientHeight * MAX_RATIO;
            const delta = startY - e.clientY;  // drag up = increase log height
            const newH = Math.max(MIN_HEIGHT, Math.min(startH + delta, maxH));
            bottomPanel.style.height = newH + 'px';
            // Trigger vis-network resize so it redraws correctly
            if (this.graphEditor && this.graphEditor.network) {
                this.graphEditor.network.redraw();
            }
        };

        const onMouseUp = () => {
            if (!dragging) return;
            dragging = false;
            handle.classList.remove('dragging');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            localStorage.setItem(STORAGE_KEY, parseInt(bottomPanel.style.height, 10));
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        };

        handle.addEventListener('mousedown', (e) => {
            e.preventDefault();
            dragging = true;
            startY = e.clientY;
            startH = bottomPanel.offsetHeight;
            handle.classList.add('dragging');
            document.body.style.cursor = 'ns-resize';
            document.body.style.userSelect = 'none';
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        });

        // Double-click to reset to default
        handle.addEventListener('dblclick', () => {
            bottomPanel.style.height = '';
            localStorage.removeItem(STORAGE_KEY);
            if (this.graphEditor && this.graphEditor.network) {
                this.graphEditor.network.redraw();
            }
        });
    }

    _setupKeyboard() {
        document.addEventListener('keydown', (e) => {
            const isInput = e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT';

            // Ctrl+Z / Ctrl+Y work even in inputs (standard behavior)
            if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
                e.preventDefault();
                this._doUndo();
                return;
            }
            if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.shiftKey && e.key === 'Z'))) {
                e.preventDefault();
                this._doRedo();
                return;
            }

            // Ctrl+A select all nodes
            if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
                if (!isInput) {
                    e.preventDefault();
                    this.graphEditor.selectAll();
                    return;
                }
            }

            // Don't trigger other shortcuts when typing in inputs
            if (isInput) return;

            switch (e.key) {
                case ' ':
                    e.preventDefault();
                    if (this.algorithmPanel.isRunning && !this.algorithmPanel.isPaused) {
                        this.algorithmPanel._pause();
                    } else {
                        this.algorithmPanel._play();
                    }
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.algorithmPanel._step();
                    break;
                case 'r':
                case 'R':
                    e.preventDefault();
                    this.algorithmPanel._reset();
                    break;
                case 'f':
                case 'F':
                    e.preventDefault();
                    this.graphEditor.fitAll();
                    break;
                case 'Delete':
                case 'Backspace':
                    e.preventDefault();
                    this.graphEditor.deleteSelected();
                    break;
                case 'Escape':
                    e.preventDefault();
                    this.graphEditor.network.unselectAll();
                    if (this.graphEditor._applySelectionContrast) this.graphEditor._applySelectionContrast();
                    break;
            }
        });
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
    window.app.init();
});
