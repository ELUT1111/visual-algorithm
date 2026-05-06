/* ===== Graph Editor - vis-network wrapper ===== */

class GraphEditor {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.nodes = new vis.DataSet();
        this.edges = new vis.DataSet();
        this.network = null;
        this.mode = 'edit'; // 'edit' | 'view' | 'run'
        this._nextNodeId = 1;
        this._directed = false;
        this._init();
    }

    _init() {
        const options = {
            nodes: {
                shape: 'dot',
                size: 28,
                font: {
                    color: '#e4e7ef',
                    size: 14,
                    face: 'Inter, sans-serif',
                    strokeWidth: 3,
                    strokeColor: '#0f1117'
                },
                color: {
                    background: '#4f8ff7',
                    border: '#4f8ff7',
                    highlight: { background: '#6ba3ff', border: '#6ba3ff' },
                    hover: { background: '#6ba3ff', border: '#6ba3ff' }
                },
                borderWidth: 2,
                shadow: {
                    enabled: true,
                    color: 'rgba(79, 143, 247, 0.3)',
                    size: 12,
                    x: 0,
                    y: 0
                },
                chosen: {
                    node: (values, id, selected, hovering) => {
                        values.shadow = true;
                        values.shadowColor = 'rgba(79, 143, 247, 0.5)';
                        values.shadowSize = 15;
                    }
                }
            },
            edges: {
                color: {
                    color: '#4a4e5e',
                    highlight: '#8b8fa3',
                    hover: '#6b6f83',
                    opacity: 1.0
                },
                font: {
                    color: '#8b8fa3',
                    size: 12,
                    align: 'middle',
                    strokeWidth: 2,
                    strokeColor: '#0f1117'
                },
                width: 2,
                smooth: {
                    type: 'continuous',
                    roundness: 0.5
                },
                arrows: {
                    to: { enabled: false, scaleFactor: 0.8 }
                },
                chosen: {
                    edge: (values, id, selected, hovering) => {
                        values.width = 3;
                    }
                }
            },
            physics: {
                enabled: true,
                solver: 'forceAtlas2Based',
                forceAtlas2Based: {
                    gravitationalConstant: -50,
                    centralGravity: 0.008,
                    springLength: 130,
                    springConstant: 0.06,
                    damping: 0.5,
                    avoidOverlap: 0.8
                },
                stabilization: {
                    enabled: true,
                    iterations: 200,
                    updateInterval: 25
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                multiselect: false,
                navigationButtons: false,
                keyboard: { enabled: false }
            },
            manipulation: {
                enabled: false
            }
        };

        this.network = new vis.Network(
            this.container,
            { nodes: this.nodes, edges: this.edges },
            options
        );

        this.network.on('stabilizationIterationsDone', () => {
            this.network.setOptions({ physics: { enabled: false } });
        });

        this._storedPositions = {};
    }

    loadFromJSON(graphData) {
        this.nodes.clear();
        this.edges.clear();
        this._directed = graphData.directed || false;

        const visNodes = (graphData.nodes || []).map(n => ({
            id: n.id,
            label: n.label || n.id,
            x: n.x,
            y: n.y,
            color: n.color || undefined,
            shape: n.shape || 'dot',
            size: n.size || 28,
            title: n.label || n.id,
            _metadata: n.metadata || {}
        }));

        const visEdges = (graphData.edges || []).map(e => ({
            id: e.id || `${e.source}-${e.target}`,
            from: e.source,
            to: e.target,
            label: e.label || (e.weight !== 1 ? String(e.weight) : ''),
            color: e.color || undefined,
            width: 2,
            arrows: (e.directed || this._directed) ? { to: { enabled: true, scaleFactor: 0.8 } } : undefined,
            _weight: e.weight,
            _metadata: e.metadata || {}
        }));

        this.nodes.add(visNodes);
        this.edges.add(visEdges);

        // Auto-fit after load
        setTimeout(() => {
            this.network.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
        }, 100);
    }

    toJSON() {
        const nodes = this.nodes.get().map(n => ({
            id: String(n.id),
            label: n.label || String(n.id),
            x: n.x,
            y: n.y,
            metadata: n._metadata || {}
        }));

        const edges = this.edges.get().map(e => ({
            id: e.id,
            source: String(e.from),
            target: String(e.to),
            weight: e._weight !== undefined ? e._weight : parseFloat(e.label) || 1,
            label: e.label || '',
            directed: this._directed || (e.arrows && e.arrows.to && e.arrows.to.enabled),
            metadata: e._metadata || {}
        }));

        return {
            name: 'Custom Graph',
            directed: this._directed,
            nodes,
            edges
        };
    }

    addNode(label, x, y) {
        const id = label || `N${this._nextNodeId++}`;
        if (this.nodes.get(id)) {
            showToast(`Node "${id}" already exists`, 'error');
            return null;
        }
        const pos = this.network.getViewPosition();
        const canvasPos = x !== undefined ?
            this.network.canvas.DOMtoCanvas({ x, y }) :
            { x: pos.x + (Math.random() - 0.5) * 100, y: pos.y + (Math.random() - 0.5) * 100 };

        this.nodes.add({
            id: id,
            label: id,
            x: canvasPos.x,
            y: canvasPos.y,
            title: id
        });
        return id;
    }

    addEdge(fromId, toId, weight = 1, directed = false) {
        const edgeId = `${fromId}-${toId}`;
        if (this.edges.get(edgeId)) {
            showToast('Edge already exists', 'error');
            return null;
        }
        this.edges.add({
            id: edgeId,
            from: fromId,
            to: toId,
            label: weight !== 1 ? String(weight) : '',
            width: 2,
            arrows: (directed || this._directed) ? { to: { enabled: true, scaleFactor: 0.8 } } : undefined,
            _weight: weight
        });
        return edgeId;
    }

    deleteSelected() {
        const selection = this.network.getSelection();
        selection.nodes.forEach(id => this.nodes.remove(id));
        selection.edges.forEach(id => this.edges.remove(id));
    }

    highlightNode(nodeId, colors) {
        try {
            this.nodes.update({
                id: nodeId,
                color: {
                    background: colors.bg,
                    border: colors.border,
                    highlight: { background: colors.bg, border: colors.border },
                    hover: { background: colors.bg, border: colors.border }
                },
                shadow: {
                    enabled: true,
                    color: colors.bg + '66',
                    size: 18
                },
                borderWidth: 3
            });
        } catch (e) { /* node may not exist */ }
    }

    highlightEdge(edgeId, colors) {
        try {
            this.edges.update({
                id: edgeId,
                color: {
                    color: colors.bg,
                    highlight: colors.bg,
                    hover: colors.bg,
                    opacity: 1.0
                },
                width: 4
            });
        } catch (e) { /* edge may not exist */ }
    }

    updateNodeLabel(nodeId, label) {
        try {
            this.nodes.update({ id: nodeId, label: String(label) });
        } catch (e) {}
    }

    updateEdgeLabel(edgeId, label) {
        try {
            this.edges.update({ id: edgeId, label: String(label) });
        } catch (e) {}
    }

    resetAllStyles() {
        this.nodes.get().forEach(n => {
            this.nodes.update({
                id: n.id,
                color: { background: '#4f8ff7', border: '#4f8ff7', highlight: { background: '#6ba3ff', border: '#6ba3ff' }, hover: { background: '#6ba3ff', border: '#6ba3ff' } },
                shadow: { enabled: true, color: 'rgba(79, 143, 247, 0.3)', size: 12 },
                borderWidth: 2,
                label: n._originalLabel || n.label
            });
        });
        this.edges.get().forEach(e => {
            this.edges.update({
                id: e.id,
                color: { color: '#4a4e5e', highlight: '#8b8fa3', hover: '#6b6f83', opacity: 1.0 },
                width: 2,
                label: e._originalLabel || e.label
            });
        });
    }

    setMode(mode) {
        this.mode = mode;
        if (mode === 'run') {
            this.network.setOptions({
                interaction: { dragNodes: false, dragView: true, zoomView: true },
                physics: { enabled: false }
            });
        } else {
            this.network.setOptions({
                interaction: { dragNodes: true, dragView: true, zoomView: true }
            });
        }
    }

    togglePhysics() {
        const enabled = this.network.physics.options.enabled;
        this.network.setOptions({ physics: { enabled: !enabled } });
        return !enabled;
    }

    storePositions() {
        const positions = this.network.getPositions();
        this._storedPositions = { ...positions };
    }

    restorePositions() {
        if (Object.keys(this._storedPositions).length > 0) {
            Object.entries(this._storedPositions).forEach(([id, pos]) => {
                try {
                    this.nodes.update({ id, x: pos.x, y: pos.y });
                } catch (e) {}
            });
        }
    }

    getNodeIds() {
        return this.nodes.get().map(n => n.id);
    }
}
