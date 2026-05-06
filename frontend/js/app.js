/* ===== Main Application ===== */

class App {
    constructor() {
        this.wsClient = new WSClient(`ws://${location.host}/ws/run`);
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

        // Load default graph if available
        if (this.presetManager.presets.length > 0) {
            this.graphEditor.loadFromJSON(this.presetManager.presets[0]);
        }

        // Setup interactive graph tools
        this._setupGraphTools();

        // Setup keyboard shortcuts
        this._setupKeyboard();

        showToast('Visual Algorithm Lab ready!', 'success');
    }

    _setupGraphTools() {
        let addNodeMode = false;
        let addEdgeMode = false;

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

    _setupKeyboard() {
        document.addEventListener('keydown', (e) => {
            // Don't trigger shortcuts when typing in inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
                return;
            }

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
            }
        });
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
    window.app.init();
});
