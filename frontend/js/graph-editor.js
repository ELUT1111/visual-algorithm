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
        this._saveTimer = null;
        this._undoStack = [];
        this._redoStack = [];
        this._maxHistory = 50;
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
                multiselect: true,
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
        this._rootId = null;
        this._structureType = 'graph'; // 'graph' or 'tree'
        this._setupSelectionContrast();
        this._setupRubberBand();
    }

    _setupSelectionContrast() {
        const self = this;
        const dimBg = '#2a2d3a';
        const dimBorder = '#3a3d4e';
        const selectedBg = '#00e5ff';
        const selectedBorder = '#00e5ff';

        const dimStyle = {
            color: { background: dimBg, border: dimBorder, highlight: { background: dimBg, border: dimBorder }, hover: { background: '#353849', border: '#4a4e5e' } },
            font: { color: '#555a6e' },
            shadow: { enabled: false },
            borderWidth: 2,
            opacity: 0.4
        };
        const selectedStyle = {
            color: { background: selectedBg, border: selectedBorder, highlight: { background: selectedBg, border: selectedBorder }, hover: { background: selectedBg, border: selectedBorder } },
            font: { color: '#ffffff' },
            shadow: { enabled: true, color: 'rgba(0, 229, 255, 0.6)', size: 20 },
            borderWidth: 3,
            opacity: 1
        };
        const normalStyle = {
            color: { background: '#4f8ff7', border: '#4f8ff7', highlight: { background: '#6ba3ff', border: '#6ba3ff' }, hover: { background: '#6ba3ff', border: '#6ba3ff' } },
            font: { color: '#e4e7ef' },
            shadow: { enabled: true, color: 'rgba(79, 143, 247, 0.3)', size: 12 },
            borderWidth: 2,
            opacity: 1
        };

        function applyContrast() {
            if (self.mode === 'run') return; // Don't interfere during algorithm execution

            const selectedIds = new Set(self.network.getSelectedNodes());
            const hasSelection = selectedIds.size > 0;

            // Batch node updates
            const nodeUpdates = [];
            self.nodes.forEach(n => {
                const style = hasSelection
                    ? (selectedIds.has(n.id) ? selectedStyle : dimStyle)
                    : normalStyle;
                nodeUpdates.push({ id: n.id, ...style });
            });
            if (nodeUpdates.length) self.nodes.update(nodeUpdates);

            // Batch edge updates
            const edgeUpdates = [];
            self.edges.forEach(e => {
                if (hasSelection) {
                    const connected = selectedIds.has(e.from) || selectedIds.has(e.to);
                    edgeUpdates.push({
                        id: e.id,
                        color: connected
                            ? { color: '#00e5ff', highlight: '#00e5ff', hover: '#00e5ff', opacity: 0.8 }
                            : { color: '#2a2d3a', highlight: '#3a3d4e', hover: '#3a3d4e', opacity: 0.3 },
                        width: connected ? 3 : 1
                    });
                } else {
                    edgeUpdates.push({
                        id: e.id,
                        color: { color: '#4a4e5e', highlight: '#8b8fa3', hover: '#6b6f83', opacity: 1.0 },
                        width: 2
                    });
                }
            });
            if (edgeUpdates.length) self.edges.update(edgeUpdates);
        }

        this.network.on('selectNode', applyContrast);
        this.network.on('deselectNode', applyContrast);
        this._applySelectionContrast = applyContrast;
    }

    _setupRubberBand() {
        const self = this;
        const LONG_PRESS_MS = 180;
        const canvas = this.container;

        // Create selection rectangle overlay
        const rect = document.createElement('div');
        rect.id = 'rubber-band-rect';
        Object.assign(rect.style, {
            position: 'absolute',
            border: '1.5px dashed #00e5ff',
            background: 'rgba(0, 229, 255, 0.08)',
            pointerEvents: 'none',
            display: 'none',
            zIndex: 10,
            borderRadius: '2px'
        });
        canvas.style.position = 'relative';
        canvas.appendChild(rect);

        let startX = 0, startY = 0;
        let timer = null;
        let active = false;
        let moved = false;

        function onDown(e) {
            // Only left button, only in edit mode
            if (e.button !== 0 || self.mode === 'run') return;
            // Don't start if clicking on a node
            const nodeAtPointer = self.network.getNodeAt(e);
            if (nodeAtPointer !== undefined) return;

            startX = e.offsetX;
            startY = e.offsetY;
            moved = false;

            timer = setTimeout(() => {
                active = true;
                rect.style.display = 'block';
                updateRect(e.offsetX, e.offsetY);
                // Disable drag-view while rubber banding
                self.network.setOptions({ interaction: { dragView: false, zoomView: false } });
            }, LONG_PRESS_MS);
        }

        function onMove(e) {
            if (!active) {
                // If mouse moved before timer fires, cancel long press
                if (timer && (Math.abs(e.offsetX - startX) > 5 || Math.abs(e.offsetY - startY) > 5)) {
                    clearTimeout(timer);
                    timer = null;
                }
                return;
            }
            moved = true;
            updateRect(e.offsetX, e.offsetY);
        }

        function updateRect(curX, curY) {
            const x = Math.min(startX, curX);
            const y = Math.min(startY, curY);
            const w = Math.abs(curX - startX);
            const h = Math.abs(curY - startY);
            rect.style.left = x + 'px';
            rect.style.top = y + 'px';
            rect.style.width = w + 'px';
            rect.style.height = h + 'px';
        }

        function onUp(e) {
            clearTimeout(timer);
            timer = null;

            if (active && moved) {
                // Find nodes within the rubber band rectangle
                const x1 = Math.min(startX, e.offsetX);
                const y1 = Math.min(startY, e.offsetY);
                const x2 = Math.max(startX, e.offsetX);
                const y2 = Math.max(startY, e.offsetY);

                // Convert rectangle corners to canvas coordinates
                const topLeft = self.network.canvas.DOMtoCanvas({ x: x1, y: y1 });
                const bottomRight = self.network.canvas.DOMtoCanvas({ x: x2, y: y2 });
                const cx1 = Math.min(topLeft.x, bottomRight.x);
                const cy1 = Math.min(topLeft.y, bottomRight.y);
                const cx2 = Math.max(topLeft.x, bottomRight.x);
                const cy2 = Math.max(topLeft.y, bottomRight.y);

                // Collect nodes inside the rectangle
                const hits = [];
                self.nodes.forEach(n => {
                    const pos = self.network.getPosition(n.id);
                    if (pos.x >= cx1 && pos.x <= cx2 && pos.y >= cy1 && pos.y <= cy2) {
                        hits.push(n.id);
                    }
                });

                // Select with Ctrl: add to existing selection; without: replace
                if (hits.length > 0) {
                    if (e.ctrlKey || e.metaKey) {
                        // Toggle: add unselected hits, remove already-selected hits
                        const current = new Set(self.network.getSelectedNodes());
                        hits.forEach(id => {
                            if (current.has(id)) current.delete(id);
                            else current.add(id);
                        });
                        self.network.selectNodes([...current]);
                    } else {
                        self.network.selectNodes(hits);
                    }
                    if (self._applySelectionContrast) self._applySelectionContrast();
                }

                e.preventDefault();
                e.stopPropagation();
            }

            // Reset
            active = false;
            moved = false;
            rect.style.display = 'none';
            rect.style.width = '0';
            rect.style.height = '0';
            self.network.setOptions({ interaction: { dragView: true, zoomView: true } });
        }

        canvas.addEventListener('mousedown', onDown);
        window.addEventListener('mousemove', onMove);
        window.addEventListener('mouseup', onUp);

        // Prevent context menu interference
        canvas.addEventListener('contextmenu', () => {
            clearTimeout(timer);
            timer = null;
        });
    }

    selectAll() {
        const ids = this.nodes.getIds();
        this.network.selectNodes(ids);
        if (this._applySelectionContrast) this._applySelectionContrast();
    }

    fitAll() {
        this.network.fit({ animation: { duration: 400, easingFunction: 'easeInOutQuad' } });
    }

    focusSelected() {
        const selectedIds = this.network.getSelectedNodes();
        if (selectedIds.length > 0) {
            this.network.fit({
                nodes: selectedIds,
                animation: { duration: 400, easingFunction: 'easeInOutQuad' }
            });
        } else {
            this.fitAll();
        }
    }

    loadFromJSON(graphData) {
        if (this.nodes.length > 0 || this.edges.length > 0) {
            this._pushUndo();
        }
        this.nodes.clear();
        this.edges.clear();
        this._directed = graphData.directed || false;
        this._rootId = graphData.root_id || null;

        const visNodes = (graphData.nodes || []).map(n => ({
            id: n.id,
            label: n.label || n.id,
            x: n.x,
            y: n.y,
            color: n.color || undefined,
            shape: n.shape || 'dot',
            size: n.size || 28,
            title: n.label || n.id,
            _metadata: n.metadata || {},
            _originalLabel: n.label || n.id
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

        this._scheduleSave();

        // Auto-detect tree layout and structure type
        if (this._directed && this._rootId) {
            this._structureType = 'tree';
            setTimeout(() => this.setLayoutMode('hierarchical'), 150);
        } else {
            this._structureType = 'graph';
            setTimeout(() => this.setLayoutMode('force'), 150);
        }
    }

    toJSON() {
        let positions = {};
        try {
            positions = this.network ? this.network.getPositions() : {};
        } catch (e) {
            positions = {};
        }

        const nodes = this.nodes.get().map(n => ({
            id: String(n.id),
            label: n.label || String(n.id),
            x: positions[n.id] ? positions[n.id].x : n.x,
            y: positions[n.id] ? positions[n.id].y : n.y,
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

        const result = {
            name: 'Custom Graph',
            directed: this._directed,
            nodes,
            edges
        };
        if (this._rootId) {
            result.root_id = this._rootId;
        }
        return result;
    }

    addNode(label, x, y) {
        const id = label || `N${this._nextNodeId++}`;
        if (this.nodes.get(id)) {
            showToast(`Node "${id}" already exists`, 'error');
            return null;
        }
        this._pushUndo();
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
        this._scheduleSave();
        return id;
    }

    addEdge(fromId, toId, weight = 1, directed = false) {
        const edgeId = `${fromId}-${toId}`;
        if (this.edges.get(edgeId)) {
            showToast('Edge already exists', 'error');
            return null;
        }
        this._pushUndo();
        const isDirected = directed || this._directed || this._structureType === 'tree';
        this.edges.add({
            id: edgeId,
            from: fromId,
            to: toId,
            label: weight !== 1 ? String(weight) : '',
            width: 2,
            arrows: isDirected ? { to: { enabled: true, scaleFactor: 0.8 } } : undefined,
            _weight: weight
        });
        this._scheduleSave();
        return edgeId;
    }

    deleteSelected() {
        const selection = this.network.getSelection();
        if (selection.nodes.length === 0 && selection.edges.length === 0) return;
        this._pushUndo();
        selection.nodes.forEach(id => this.nodes.remove(id));
        selection.edges.forEach(id => this.edges.remove(id));
        this.network.unselectAll();
        if (this._applySelectionContrast) this._applySelectionContrast();
        this._scheduleSave();
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
        this.network.unselectAll();
        this.nodes.get().forEach(n => {
            this.nodes.update({
                id: n.id,
                color: { background: '#4f8ff7', border: '#4f8ff7', highlight: { background: '#6ba3ff', border: '#6ba3ff' }, hover: { background: '#6ba3ff', border: '#6ba3ff' } },
                font: { color: '#e4e7ef' },
                shadow: { enabled: true, color: 'rgba(79, 143, 247, 0.3)', size: 12 },
                borderWidth: 2,
                opacity: 1,
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
            // Disable layout engine so it doesn't override algorithm-computed positions
            this.network.setOptions({
                interaction: { dragNodes: false, dragView: true, zoomView: true },
                physics: { enabled: false },
                layout: { hierarchical: { enabled: false } }
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

    setLayoutMode(mode) {
        if (mode === 'hierarchical') {
            this.network.setOptions({
                layout: {
                    hierarchical: {
                        enabled: true,
                        direction: 'UD',
                        sortMethod: 'directed',
                        levelSeparation: 100,
                        nodeSpacing: 120,
                        treeSpacing: 200,
                        blockShifting: true,
                        edgeMinimization: true,
                        parentCentralization: true
                    }
                },
                physics: { enabled: false }
            });
            setTimeout(() => {
                this.network.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
            }, 300);
        } else {
            this.network.setOptions({
                layout: { hierarchical: { enabled: false } },
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
                }
            });
        }
    }

    setStructureType(type) {
        this._structureType = type;
        if (type === 'tree') {
            // Tree mode: directed edges, hierarchical layout
            this._directed = true;
            this.setLayoutMode('hierarchical');
            // Update all existing edges to be directed
            this.edges.get().forEach(e => {
                this.edges.update({
                    id: e.id,
                    arrows: { to: { enabled: true, scaleFactor: 0.8 } }
                });
            });
            // Auto-set root to first node if not set
            if (!this._rootId && this.nodes.length > 0) {
                this._rootId = this.nodes.get()[0].id;
            }
            showToast('Switched to Tree mode', 'info');
        } else {
            // Graph mode: force layout, undirected by default
            this._directed = false;
            this._rootId = null;
            this.setLayoutMode('force');
            // Remove arrows from all edges
            this.edges.get().forEach(e => {
                this.edges.update({
                    id: e.id,
                    arrows: undefined
                });
            });
            showToast('Switched to Graph mode', 'info');
        }
        this._scheduleSave();
    }

    getStructureType() {
        return this._structureType;
    }

    setRoot(nodeId) {
        this._rootId = nodeId;
        this._scheduleSave();
    }

    getRoot() {
        return this._rootId;
    }

    addNodeDynamic(id, label, x, y) {
        if (this.nodes.get(id)) return;
        const node = {
            id: id,
            label: label || id,
            title: label || id,
            _metadata: {},
            _originalLabel: label || id
        };
        // Only set position if explicitly provided; let vis-network layout handle otherwise
        if (x !== undefined && x !== null) node.x = x;
        if (y !== undefined && y !== null) node.y = y;
        this.nodes.add(node);
    }

    addEdgeDynamic(fromId, toId, label) {
        const edgeId = `${fromId}-${toId}`;
        if (this.edges.get(edgeId)) return;
        this.edges.add({
            id: edgeId,
            from: fromId,
            to: toId,
            label: label || '',
            width: 2,
            arrows: { to: { enabled: true, scaleFactor: 0.8 } },
            _weight: 1,
            _metadata: {}
        });
    }

    removeNodeDynamic(id) {
        try { this.nodes.remove(id); } catch (e) {}
    }

    removeEdgeDynamic(id) {
        try { this.edges.remove(id); } catch (e) {}
    }

    updateNodePosition(id, x, y) {
        try { this.nodes.update({ id, x, y }); } catch (e) {}
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

    _scheduleSave() {
        clearTimeout(this._saveTimer);
        this._saveTimer = setTimeout(() => {
            try {
                const data = this.toJSON();
                localStorage.setItem('val_graph', JSON.stringify(data));
            } catch (e) { /* quota exceeded etc */ }
        }, 500);
    }

    // --- Undo / Redo ---

    _pushUndo() {
        const snapshot = JSON.stringify(this.toJSON());
        this._undoStack.push(snapshot);
        if (this._undoStack.length > this._maxHistory) {
            this._undoStack.shift();
        }
        this._redoStack = [];
    }

    canUndo() {
        return this._undoStack.length > 0;
    }

    canRedo() {
        return this._redoStack.length > 0;
    }

    undo() {
        if (!this.canUndo()) return false;
        // Save current state to redo stack
        this._redoStack.push(JSON.stringify(this.toJSON()));
        // Restore previous state
        const snapshot = this._undoStack.pop();
        const data = JSON.parse(snapshot);
        this._restoreSnapshot(data);
        this._scheduleSave();
        return true;
    }

    redo() {
        if (!this.canRedo()) return false;
        // Save current state to undo stack
        this._undoStack.push(JSON.stringify(this.toJSON()));
        // Restore next state
        const snapshot = this._redoStack.pop();
        const data = JSON.parse(snapshot);
        this._restoreSnapshot(data);
        this._scheduleSave();
        return true;
    }

    _restoreSnapshot(data) {
        this.nodes.clear();
        this.edges.clear();
        this._directed = data.directed || false;
        this._rootId = data.root_id || null;

        const visNodes = (data.nodes || []).map(n => ({
            id: n.id,
            label: n.label || n.id,
            x: n.x,
            y: n.y,
            title: n.label || n.id,
            _metadata: n.metadata || {},
            _originalLabel: n.label || n.id
        }));

        const visEdges = (data.edges || []).map(e => ({
            id: e.id || `${e.source}-${e.target}`,
            from: e.source,
            to: e.target,
            label: e.label || (e.weight !== 1 ? String(e.weight) : ''),
            width: 2,
            arrows: (e.directed || this._directed) ? { to: { enabled: true, scaleFactor: 0.8 } } : undefined,
            _weight: e.weight,
            _metadata: e.metadata || {},
            _originalLabel: e.label || (e.weight !== 1 ? String(e.weight) : '')
        }));

        this.nodes.add(visNodes);
        this.edges.add(visEdges);
    }

    restoreSnapshot(data, options = {}) {
        this._restoreSnapshot(data);
        if (options.save) this._scheduleSave();
        if (options.fit) {
            setTimeout(() => {
                try {
                    this.fitAll();
                } catch (e) {}
            }, 0);
        }
    }

    restoreFromStorage() {
        try {
            const saved = localStorage.getItem('val_graph');
            if (saved) {
                const data = JSON.parse(saved);
                if (data && data.nodes && data.nodes.length > 0) {
                    this.loadFromJSON(data);
                    return true;
                }
            }
        } catch (e) {}
        return false;
    }
}
