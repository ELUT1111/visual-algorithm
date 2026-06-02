/* ===== Visualizer - Applies algorithm steps to graph ===== */

class Visualizer {
    constructor(graphEditor) {
        this.editor = graphEditor;
        this.structureContainer = document.getElementById('structure-container');
        this.structureView = document.getElementById('structure-view');
        this.structureMode = 'graph';
        this.arrayState = null;
        this.matrixState = null;
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

            case 'add_node': {
                let nx = value.x, ny = value.y;
                // If parent_id is provided and no explicit position, place near parent
                if ((nx === undefined || nx === null) && value.parent_id) {
                    try {
                        const parentPos = this.editor.network.getPosition(value.parent_id);
                        if (parentPos) {
                            nx = parentPos.x + (Math.random() - 0.5) * 60;
                            ny = parentPos.y + 80;
                        }
                    } catch (e) { /* parent may not exist yet */ }
                }
                this.editor.addNodeDynamic(value.id, value.label, nx, ny);
                break;
            }

            case 'add_edge':
                this.editor.addEdgeDynamic(value.source, value.target, value.label || '');
                break;

            case 'remove_node':
                this.editor.removeNodeDynamic(targetId);
                break;

            case 'remove_edge':
                this.editor.removeEdgeDynamic(targetId);
                break;

            case 'update_node_position':
                this.editor.updateNodePosition(targetId, value.x, value.y);
                break;

            case 'render_array':
                this._renderArray(value);
                break;

            case 'update_array_item':
                this._updateArrayItem(value);
                break;

            case 'highlight_array_item':
                this._highlightArrayItems(value);
                break;

            case 'swap_array_items':
                this._swapArrayItems(value);
                break;

            case 'clear_array':
                this._clearStructure();
                break;

            case 'render_matrix':
                this._renderMatrix(value);
                break;

            case 'update_matrix_cell':
                this._updateMatrixCell(value);
                break;

            case 'highlight_matrix_cell':
                this._highlightMatrixCells(value);
                break;

            case 'clear_matrix':
                this._clearStructure();
                break;
        }

        // Handle layout hint from step
        if (step.layout_hint) {
            this.editor.setLayoutMode(step.layout_hint);
        }
    }

    setVisualizationMode(mode = 'graph') {
        this.structureMode = mode || 'graph';
        const useStructure = this.structureMode === 'array' || this.structureMode === 'matrix';
        if (this.editor && this.editor.container) {
            this.editor.container.style.display = useStructure ? 'none' : '';
        }
        if (this.structureContainer) {
            this.structureContainer.style.display = useStructure ? 'block' : 'none';
        }
        if (!useStructure) {
            this._clearStructure();
            setTimeout(() => {
                try {
                    if (this.editor && this.editor.network) this.editor.network.redraw();
                } catch (e) {}
            }, 0);
        }
    }

    clearStructure() {
        this._clearStructure();
    }

    _clearStructure() {
        this.arrayState = null;
        this.matrixState = null;
        if (this.structureView) this.structureView.innerHTML = '';
    }

    _renderArray(value) {
        this.setVisualizationMode('array');
        const rawItems = Array.isArray(value) ? value : (value.items || []);
        this.arrayState = {
            title: value.title || 'Array',
            items: rawItems.map(item => (
                typeof item === 'object' && item !== null
                    ? { value: item.value, state: item.state || '', meta: item.meta || item.detail || '' }
                    : { value: item, state: '', meta: '' }
            ))
        };
        this._drawArray();
    }

    _drawArray() {
        if (!this.structureView || !this.arrayState) return;
        this.structureView.innerHTML = '';

        const shell = document.createElement('div');
        shell.className = 'structure-shell';

        const title = document.createElement('div');
        title.className = 'structure-title';
        title.textContent = this.arrayState.title || 'Array';
        shell.appendChild(title);

        const row = document.createElement('div');
        row.className = 'array-visual';

        this.arrayState.items.forEach((item, idx) => {
            const cell = document.createElement('div');
            cell.className = `array-cell ${item.state || ''}`.trim();
            cell.dataset.index = String(idx);

            const value = document.createElement('div');
            value.className = 'array-value';
            value.textContent = String(item.value);

            const meta = document.createElement('div');
            meta.className = 'array-meta';
            meta.textContent = item.meta || item.state || '';

            const index = document.createElement('div');
            index.className = 'array-index';
            index.textContent = idx;

            cell.appendChild(value);
            cell.appendChild(meta);
            cell.appendChild(index);
            row.appendChild(cell);
        });

        shell.appendChild(row);
        this.structureView.appendChild(shell);
    }

    _updateArrayItem(value) {
        if (!this.arrayState) return;
        const index = value.index;
        if (index < 0 || index >= this.arrayState.items.length) return;
        this.arrayState.items[index] = {
            value: value.value,
            state: value.state || this.arrayState.items[index].state || '',
            meta: value.meta || value.detail || this.arrayState.items[index].meta || ''
        };
        this._drawArray();
    }

    _highlightArrayItems(value) {
        if (!this.arrayState) return;
        const indices = value.indices || (value.index !== undefined ? [value.index] : []);
        const state = value.state || 'current';
        this.arrayState.items.forEach((item, idx) => {
            item.state = indices.includes(idx) ? state : (item.state === 'sorted' ? 'sorted' : '');
        });
        this._drawArray();
    }

    _swapArrayItems(value) {
        if (!this.arrayState) return;
        const i = value.i;
        const j = value.j;
        if (i < 0 || j < 0 || i >= this.arrayState.items.length || j >= this.arrayState.items.length) return;
        const tmp = this.arrayState.items[i];
        this.arrayState.items[i] = this.arrayState.items[j];
        this.arrayState.items[j] = tmp;
        this.arrayState.items[i].state = value.state || 'swapped';
        this.arrayState.items[j].state = value.state || 'swapped';
        this._drawArray();
    }

    _renderMatrix(value) {
        this.setVisualizationMode('matrix');
        this.matrixState = {
            title: value.title || 'Matrix',
            rows: value.rows || [],
            columns: value.columns || [],
            values: (value.values || []).map(row => [...row]),
            highlights: value.highlights || []
        };
        this._drawMatrix();
    }

    _drawMatrix() {
        if (!this.structureView || !this.matrixState) return;
        this.structureView.innerHTML = '';

        const shell = document.createElement('div');
        shell.className = 'structure-shell';

        const title = document.createElement('div');
        title.className = 'structure-title';
        title.textContent = this.matrixState.title || 'Matrix';
        shell.appendChild(title);

        const wrap = document.createElement('div');
        wrap.className = 'matrix-wrap';

        const table = document.createElement('table');
        table.className = 'matrix-visual';

        const thead = document.createElement('thead');
        const headRow = document.createElement('tr');
        headRow.appendChild(document.createElement('th'));
        this.matrixState.columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = String(col);
            headRow.appendChild(th);
        });
        thead.appendChild(headRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        this.matrixState.values.forEach((rowValues, rowIdx) => {
            const row = document.createElement('tr');
            const th = document.createElement('th');
            th.textContent = String(this.matrixState.rows[rowIdx] ?? rowIdx);
            row.appendChild(th);

            rowValues.forEach((cellValue, colIdx) => {
                const td = document.createElement('td');
                td.textContent = String(cellValue);
                const highlight = this.matrixState.highlights.find(h => h.row === rowIdx && h.col === colIdx);
                if (highlight) td.classList.add(highlight.state || 'current');
                row.appendChild(td);
            });
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        wrap.appendChild(table);
        shell.appendChild(wrap);
        this.structureView.appendChild(shell);
    }

    _updateMatrixCell(value) {
        if (!this.matrixState) return;
        const row = value.row;
        const col = value.col;
        if (!this.matrixState.values[row] || col < 0 || col >= this.matrixState.values[row].length) return;
        this.matrixState.values[row][col] = value.value;
        this.matrixState.highlights = [{ row, col, state: value.state || 'updated' }];
        this._drawMatrix();
    }

    _highlightMatrixCells(value) {
        if (!this.matrixState) return;
        const cells = value.cells || (value.row !== undefined ? [value] : []);
        this.matrixState.highlights = cells.map(cell => ({
            row: cell.row,
            col: cell.col,
            state: cell.state || value.state || 'current'
        }));
        this._drawMatrix();
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
            n._originalLabel = n.label || String(n.id);
        });
        this.editor.edges.get().forEach(e => {
            e._originalLabel = e.label || '';
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
