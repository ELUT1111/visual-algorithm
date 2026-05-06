/* ===== Visualizer - Applies algorithm steps to graph ===== */

class Visualizer {
    constructor(graphEditor) {
        this.editor = graphEditor;
        this.colorScheme = {
            default:   { bg: '#4f8ff7', border: '#4f8ff7' },
            current:   { bg: '#fbbf24', border: '#f59e0b' },
            visited:   { bg: '#34d399', border: '#10b981' },
            exploring: { bg: '#a78bfa', border: '#8b5cf6' },
            path:      { bg: '#f87171', border: '#ef4444' },
            settled:   { bg: '#6b7280', border: '#4b5563' },
            mst:       { bg: '#34d399', border: '#10b981' },
            skipped:   { bg: '#f87171', border: '#ef4444' },
        };
        this._originalLabels = {};
    }

    applyStep(step) {
        const action = step.action;
        const targetType = step.target_type;
        const targetId = step.target_id;
        const value = step.value;

        switch (action) {
            case 'highlight_node':
                this.editor.highlightNode(targetId, this._getColor(value || 'current'));
                break;

            case 'unhighlight_node':
                this.editor.highlightNode(targetId, this.colorScheme.default);
                break;

            case 'highlight_edge':
                this.editor.highlightEdge(targetId, this._getColor(value || 'current'));
                break;

            case 'unhighlight_edge':
                this.editor.highlightEdge(targetId, { bg: '#4a4e5e', border: '#4a4e5e' });
                break;

            case 'set_node_color':
                this.editor.highlightNode(targetId, this._getColor(value));
                break;

            case 'set_edge_color':
                this.editor.highlightEdge(targetId, this._getColor(value));
                break;

            case 'update_node_label':
                this.editor.updateNodeLabel(targetId, value);
                break;

            case 'update_edge_label':
                this.editor.updateEdgeLabel(targetId, value);
                break;

            case 'set_node_border':
                try {
                    this.editor.nodes.update({
                        id: targetId,
                        borderWidth: value.width || 3,
                        color: { border: value.color || '#fff' }
                    });
                } catch (e) {}
                break;

            case 'mark_visited':
                this.editor.highlightNode(targetId, this.colorScheme.visited);
                break;

            case 'mark_current':
                this.editor.highlightNode(targetId, this.colorScheme.current);
                break;

            case 'mark_path':
                this._highlightPath(value);
                break;

            case 'reset_all':
                this.editor.resetAllStyles();
                break;

            case 'add_message':
                // Messages are handled by the algorithm panel
                break;
        }
    }

    _getColor(value) {
        if (typeof value === 'object' && value.bg) return value;
        if (typeof value === 'string' && this.colorScheme[value]) {
            return this.colorScheme[value];
        }
        if (typeof value === 'string' && value.startsWith('#')) {
            return { bg: value, border: value };
        }
        return this.colorScheme.current;
    }

    _highlightPath(pathData) {
        if (!pathData) return;

        // pathData can be a list of node IDs or { nodes: [], edges: [] }
        if (Array.isArray(pathData)) {
            pathData.forEach(nodeId => {
                this.editor.highlightNode(nodeId, this.colorScheme.path);
            });
            // Highlight edges between consecutive nodes
            for (let i = 0; i < pathData.length - 1; i++) {
                const edgeId = `${pathData[i]}-${pathData[i + 1]}`;
                const reverseEdgeId = `${pathData[i + 1]}-${pathData[i]}`;
                if (this.editor.edges.get(edgeId)) {
                    this.editor.highlightEdge(edgeId, this.colorScheme.path);
                } else if (this.editor.edges.get(reverseEdgeId)) {
                    this.editor.highlightEdge(reverseEdgeId, this.colorScheme.path);
                }
            }
        } else if (pathData.nodes) {
            pathData.nodes.forEach(id => this.editor.highlightNode(id, this.colorScheme.path));
            (pathData.edges || []).forEach(id => this.editor.highlightEdge(id, this.colorScheme.path));
        }
    }

    storeOriginalLabels() {
        this.editor.nodes.get().forEach(n => {
            n._originalLabel = n.label;
        });
        this.editor.edges.get().forEach(e => {
            e._originalLabel = e.label;
        });
    }

    restoreOriginalLabels() {
        this.editor.nodes.get().forEach(n => {
            if (n._originalLabel !== undefined) {
                this.editor.updateNodeLabel(n.id, n._originalLabel);
            }
        });
        this.editor.edges.get().forEach(e => {
            if (e._originalLabel !== undefined) {
                this.editor.updateEdgeLabel(e.id, e._originalLabel);
            }
        });
    }
}
