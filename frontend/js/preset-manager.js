/* ===== Preset Manager - Import/Export ===== */

class PresetManager {
    constructor(graphEditor) {
        this.editor = graphEditor;
        this.presets = [];
    }

    async init() {
        await this.loadPresets();
        this._setupButtons();
        this._setupGenerator();
    }

    async loadPresets() {
        try {
            const response = await fetch('/api/graphs');
            this.presets = await response.json();
            this._renderPresetList();
        } catch (e) {
            console.error('Failed to load presets:', e);
        }
    }

    _renderPresetList() {
        const container = document.getElementById('preset-list');
        container.innerHTML = '';

        const graphPresets = this.presets.filter(p => p.category !== 'tree');
        const treePresets = this.presets.filter(p => p.category === 'tree');

        if (graphPresets.length > 0) {
            const label = document.createElement('div');
            label.className = 'preset-group-label';
            label.textContent = 'Graph Presets';
            container.appendChild(label);
            graphPresets.forEach(preset => this._renderPresetCard(container, preset, '📊'));
        }

        if (treePresets.length > 0) {
            const label = document.createElement('div');
            label.className = 'preset-group-label';
            label.textContent = 'Tree Presets';
            container.appendChild(label);
            treePresets.forEach(preset => this._renderPresetCard(container, preset, '🌲'));
        }
    }

    _renderPresetCard(container, preset, emoji) {
        const card = document.createElement('div');
        card.className = 'preset-card';

        const emojiSpan = document.createElement('span');
        emojiSpan.textContent = emoji;

        const nameSpan = document.createElement('span');
        nameSpan.textContent = preset.name;

        card.appendChild(emojiSpan);
        card.appendChild(nameSpan);

        card.addEventListener('click', () => {
            document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            if (window.app && window.app.visualizer) {
                window.app.visualizer.setVisualizationMode('graph');
            }
            this.editor.loadFromJSON(preset);
            showToast(`Loaded: ${preset.name}`, 'success');
        });
        container.appendChild(card);
    }

    _setupButtons() {
        // Import
        document.getElementById('btn-import').addEventListener('click', () => {
            const input = document.getElementById('file-input');
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (!file) return;
                try {
                    const text = await file.text();
                    const data = JSON.parse(text);
                    const isRunRecord = this._isRunRecord(data);

                    if (isRunRecord && window.app && window.app.algorithmPanel) {
                        const imported = window.app.algorithmPanel.loadRunRecord(data);
                        if (!imported) {
                            showToast('Unable to import run record', 'error');
                        }
                    } else {
                        if (window.app && window.app.visualizer) {
                            window.app.visualizer.setVisualizationMode('graph');
                        }
                        this.editor.loadFromJSON(data);
                        showToast(`Imported: ${data.name || file.name}`, 'success');
                    }
                } catch (err) {
                    showToast('Invalid JSON file', 'error');
                }
                input.value = '';
            };
            input.click();
        });

        // Export
        document.getElementById('btn-export').addEventListener('click', () => {
            const data = this.editor.toJSON();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `graph-${(data.name || 'export').replace(/\s+/g, '_')}.json`;
            a.click();
            URL.revokeObjectURL(url);
            showToast('Graph exported!', 'success');
        });
    }

    _isRunRecord(data) {
        return Boolean(
            data &&
            typeof data === 'object' &&
            (data.schema === 'visual-algorithm-run-v1' ||
                (Array.isArray(data.steps) && data.steps.length > 0 && (data.algorithm_key || data.algorithmKey) && (data.base_graph || data.baseGraph)))
        );
    }

    _setupGenerator() {
        const btn = document.getElementById('btn-generate-graph');
        if (!btn) return;

        btn.addEventListener('click', () => {
            const type = document.getElementById('generator-type').value;
            const count = this._readNodeCount();
            const density = parseFloat(document.getElementById('generator-density').value) || 0.45;
            const weighted = document.getElementById('generator-weighted').checked || type === 'negative';

            const graph = this.generateGraph(type, count, density, weighted);
            document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('selected'));
            if (window.app && window.app.visualizer) {
                window.app.visualizer.setVisualizationMode('graph');
            }
            this.editor.loadFromJSON(graph);
            showToast(`Generated: ${graph.name}`, 'success');
        });
    }

    _readNodeCount() {
        const input = document.getElementById('generator-nodes');
        const raw = parseInt(input.value, 10);
        const count = Math.max(4, Math.min(raw || 10, 40));
        input.value = String(count);
        return count;
    }

    generateGraph(type, count, density, weighted) {
        switch (type) {
            case 'connected':
                return this._generateConnectedGraph(count, density, weighted);
            case 'dag':
                return this._generateDag(count, density, weighted, false);
            case 'bipartite':
                return this._generateBipartiteGraph(count, density, weighted);
            case 'grid':
                return this._generateGridGraph(count, weighted);
            case 'negative':
                return this._generateDag(count, density, true, true);
            case 'disconnected':
                return this._generateDisconnectedGraph(count, density, weighted);
            case 'random':
            default:
                return this._generateRandomGraph(count, density, weighted);
        }
    }

    _makeNodes(count, layout = 'circle') {
        if (layout === 'grid') {
            const cols = Math.ceil(Math.sqrt(count));
            const spacing = 110;
            return Array.from({ length: count }, (_, i) => ({
                id: this._nodeId(i),
                label: this._nodeId(i),
                x: (i % cols) * spacing - ((cols - 1) * spacing) / 2,
                y: Math.floor(i / cols) * spacing - ((Math.ceil(count / cols) - 1) * spacing) / 2
            }));
        }

        const radius = Math.max(160, count * 15);
        return Array.from({ length: count }, (_, i) => {
            const angle = (Math.PI * 2 * i) / count - Math.PI / 2;
            return {
                id: this._nodeId(i),
                label: this._nodeId(i),
                x: Math.cos(angle) * radius,
                y: Math.sin(angle) * radius
            };
        });
    }

    _nodeId(index) {
        return `N${index + 1}`;
    }

    _makeEdge(source, target, weight, directed) {
        return {
            id: `${source}-${target}`,
            source,
            target,
            weight,
            label: weight !== 1 ? String(weight) : '',
            directed
        };
    }

    _edgeWeight(weighted, allowNegative = false) {
        if (!weighted) return 1;
        if (allowNegative) {
            let w = this._randInt(-5, 12);
            if (w === 0) w = 1;
            return w;
        }
        return this._randInt(1, 12);
    }

    _randInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    _addEdge(edges, seen, source, target, weighted, directed, allowNegative = false) {
        if (source === target) return false;
        const key = directed
            ? `${source}->${target}`
            : [source, target].sort().join('--');
        if (seen.has(key)) return false;
        seen.add(key);
        edges.push(this._makeEdge(source, target, this._edgeWeight(weighted, allowNegative), directed));
        return true;
    }

    _graph(name, description, directed, nodes, edges) {
        return { name, description, directed, nodes, edges };
    }

    _generateRandomGraph(count, density, weighted) {
        const nodes = this._makeNodes(count);
        const edges = [];
        const seen = new Set();

        for (let i = 0; i < count; i++) {
            for (let j = i + 1; j < count; j++) {
                if (Math.random() <= density) {
                    this._addEdge(edges, seen, this._nodeId(i), this._nodeId(j), weighted, false);
                }
            }
        }

        return this._graph(
            'Generated Random Graph',
            'Undirected random graph generated in the browser',
            false,
            nodes,
            edges
        );
    }

    _generateConnectedGraph(count, density, weighted) {
        const nodes = this._makeNodes(count);
        const edges = [];
        const seen = new Set();

        // First add a random spanning tree so the graph is connected.
        for (let i = 1; i < count; i++) {
            const parent = this._randInt(0, i - 1);
            this._addEdge(edges, seen, this._nodeId(parent), this._nodeId(i), weighted, false);
        }

        for (let i = 0; i < count; i++) {
            for (let j = i + 1; j < count; j++) {
                if (Math.random() <= density) {
                    this._addEdge(edges, seen, this._nodeId(i), this._nodeId(j), weighted, false);
                }
            }
        }

        return this._graph(
            'Generated Connected Graph',
            'Undirected connected graph with a spanning tree and extra random edges',
            false,
            nodes,
            edges
        );
    }

    _generateDag(count, density, weighted, allowNegative) {
        const nodes = this._makeNodes(count);
        const edges = [];
        const seen = new Set();

        // A forward chain guarantees reachability while preserving acyclicity.
        for (let i = 0; i < count - 1; i++) {
            this._addEdge(edges, seen, this._nodeId(i), this._nodeId(i + 1), weighted, true, allowNegative);
        }

        for (let i = 0; i < count; i++) {
            for (let j = i + 2; j < count; j++) {
                if (Math.random() <= density) {
                    this._addEdge(edges, seen, this._nodeId(i), this._nodeId(j), weighted, true, allowNegative);
                }
            }
        }

        return this._graph(
            allowNegative ? 'Generated Negative Weighted DAG' : 'Generated DAG',
            allowNegative
                ? 'Directed acyclic graph with negative weights for Bellman-Ford'
                : 'Directed acyclic graph for topological sorting and DAG checks',
            true,
            nodes,
            edges
        );
    }

    _generateBipartiteGraph(count, density, weighted) {
        const nodes = this._makeNodes(count);
        const edges = [];
        const seen = new Set();
        const leftCount = Math.floor(count / 2);

        for (let i = 0; i < leftCount; i++) {
            for (let j = leftCount; j < count; j++) {
                if (Math.random() <= density) {
                    this._addEdge(edges, seen, this._nodeId(i), this._nodeId(j), weighted, false);
                }
            }
        }

        // Ensure every node has at least one cross edge when possible.
        for (let i = 0; i < leftCount; i++) {
            this._addEdge(edges, seen, this._nodeId(i), this._nodeId(this._randInt(leftCount, count - 1)), weighted, false);
        }
        for (let j = leftCount; j < count; j++) {
            this._addEdge(edges, seen, this._nodeId(this._randInt(0, leftCount - 1)), this._nodeId(j), weighted, false);
        }

        return this._graph(
            'Generated Bipartite Graph',
            'Undirected graph with edges only between two partitions',
            false,
            nodes,
            edges
        );
    }

    _generateGridGraph(requestedCount, weighted) {
        const cols = Math.ceil(Math.sqrt(requestedCount));
        const rows = Math.ceil(requestedCount / cols);
        const count = requestedCount;
        const nodes = this._makeNodes(count, 'grid');
        const edges = [];
        const seen = new Set();

        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const idx = r * cols + c;
                if (idx >= count) continue;
                if (c + 1 < cols) {
                    const right = idx + 1;
                    if (right < count && Math.floor(right / cols) === r) {
                        this._addEdge(edges, seen, this._nodeId(idx), this._nodeId(right), weighted, false);
                    }
                }
                if (r + 1 < rows) {
                    const down = idx + cols;
                    if (down < count) {
                        this._addEdge(edges, seen, this._nodeId(idx), this._nodeId(down), weighted, false);
                    }
                }
            }
        }

        return this._graph(
            'Generated Grid Graph',
            'Rectangular grid graph for pathfinding and traversal algorithms',
            false,
            nodes,
            edges
        );
    }

    _generateDisconnectedGraph(count, density, weighted) {
        const nodes = this._makeNodes(count);
        const edges = [];
        const seen = new Set();
        const splitA = Math.max(1, Math.floor(count / 3));
        let splitB = Math.max(splitA + 1, Math.floor((count * 2) / 3));
        if (splitB >= count) splitB = count - 1;
        const groups = [
            [0, splitA],
            [splitA, splitB],
            [splitB, count]
        ].filter(([start, end]) => end - start > 0);

        groups.forEach(([start, end]) => {
            for (let i = start; i < end - 1; i++) {
                this._addEdge(edges, seen, this._nodeId(i), this._nodeId(i + 1), weighted, false);
            }
            for (let i = start; i < end; i++) {
                for (let j = i + 1; j < end; j++) {
                    if (Math.random() <= density) {
                        this._addEdge(edges, seen, this._nodeId(i), this._nodeId(j), weighted, false);
                    }
                }
            }
        });

        return this._graph(
            'Generated Disconnected Graph',
            'Undirected graph split into multiple connected components',
            false,
            nodes,
            edges
        );
    }
}
