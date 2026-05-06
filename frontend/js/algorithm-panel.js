/* ===== Algorithm Panel - Selector + Controls ===== */

class AlgorithmPanel {
    constructor(wsClient, visualizer, graphEditor) {
        this.ws = wsClient;
        this.visualizer = visualizer;
        this.editor = graphEditor;
        this.currentSpeed = 500;
        this.isRunning = false;
        this.isPaused = false;
        this.selectedAlgorithm = null;
        this.algorithms = [];
    }

    async init() {
        await this._loadAlgorithms();
        this._setupControls();
        this._setupWSHandlers();
    }

    async _loadAlgorithms() {
        try {
            const response = await fetch('/api/algorithms');
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            this.algorithms = await response.json();
            this._renderAlgorithmCards();
        } catch (e) {
            console.error('Failed to load algorithms:', e);
            showToast('Failed to load algorithms', 'error');
        }
    }

    _renderAlgorithmCards() {
        const container = document.getElementById('algorithm-list');
        container.innerHTML = '';

        const categories = {};
        this.algorithms.forEach(algo => {
            if (!categories[algo.category]) categories[algo.category] = [];
            categories[algo.category].push(algo);
        });

        const categoryOrder = ['graph', 'tree'];
        const categoryLabels = {
            graph: { emoji: '📊', label: 'Graph Algorithms' },
            tree: { emoji: '🌲', label: 'Tree Algorithms' }
        };

        const orderedCats = [
            ...categoryOrder.filter(c => categories[c]),
            ...Object.keys(categories).filter(c => !categoryOrder.includes(c))
        ];

        orderedCats.forEach(cat => {
            const algos = categories[cat];
            const catInfo = categoryLabels[cat] || { emoji: '📋', label: cat };

            // Category header (collapsible)
            const header = document.createElement('div');
            header.className = 'category-header';

            const catEmoji = document.createElement('span');
            catEmoji.className = 'category-emoji';
            catEmoji.textContent = catInfo.emoji;

            const catLabel = document.createElement('span');
            catLabel.className = 'category-label';
            catLabel.textContent = catInfo.label;

            const catCount = document.createElement('span');
            catCount.className = 'category-count';
            catCount.textContent = algos.length;

            const catToggle = document.createElement('span');
            catToggle.className = 'category-toggle';
            catToggle.textContent = '▼';

            header.appendChild(catEmoji);
            header.appendChild(catLabel);
            header.appendChild(catCount);
            header.appendChild(catToggle);

            const algoContainer = document.createElement('div');
            algoContainer.className = 'category-algos';

            header.addEventListener('click', () => {
                const isCollapsed = algoContainer.classList.toggle('collapsed');
                catToggle.textContent = isCollapsed ? '▶' : '▼';
            });

            algos.forEach(algo => {
                const card = document.createElement('div');
                card.className = 'algo-card';
                card.dataset.key = `${algo.category}/${algo.name}`;

                const emojiSpan = document.createElement('span');
                emojiSpan.className = 'algo-emoji';
                emojiSpan.textContent = algo.emoji || '';

                const infoDiv = document.createElement('div');
                infoDiv.className = 'algo-info';

                const nameDiv = document.createElement('div');
                nameDiv.className = 'algo-name';
                nameDiv.textContent = algo.name;

                const descDiv = document.createElement('div');
                descDiv.className = 'algo-desc';
                descDiv.textContent = algo.description;

                infoDiv.appendChild(nameDiv);
                infoDiv.appendChild(descDiv);

                card.appendChild(emojiSpan);
                card.appendChild(infoDiv);

                card.addEventListener('click', () => this._selectAlgorithm(algo, card));
                algoContainer.appendChild(card);
            });

            container.appendChild(header);
            container.appendChild(algoContainer);
        });
    }

    _selectAlgorithm(algo, card) {
        // Deselect previous
        document.querySelectorAll('.algo-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');

        this.selectedAlgorithm = `${algo.category}/${algo.name}`;

        // Switch structure type based on algorithm category
        const isTree = algo.category === 'tree';
        this.editor.setStructureType(isTree ? 'tree' : 'graph');
        document.getElementById('btn-set-root').style.display = isTree ? '' : 'none';

        // Show parameters
        const paramSection = document.getElementById('param-section');
        const paramForm = document.getElementById('param-form');

        if (algo.parameters && algo.parameters.length > 0) {
            paramSection.style.display = 'block';
            paramForm.innerHTML = '';

            // Get current node IDs for dropdowns
            const nodeIds = this.editor.getNodeIds();

            algo.parameters.forEach(param => {
                const group = document.createElement('div');
                group.className = 'param-group';

                const label = document.createElement('label');
                label.textContent = param.description || param.name;
                group.appendChild(label);

                if (param.type === 'node' || (param.name === 'source' || param.name === 'target' || param.name === 'start')) {
                    const select = document.createElement('select');
                    select.id = `param-${param.name}`;

                    const defaultOpt = document.createElement('option');
                    defaultOpt.value = '';
                    defaultOpt.textContent = '-- Select Node --';
                    select.appendChild(defaultOpt);

                    nodeIds.forEach(id => {
                        const opt = document.createElement('option');
                        opt.value = id;
                        opt.textContent = id;
                        if (param.default === id) opt.selected = true;
                        select.appendChild(opt);
                    });

                    group.appendChild(select);
                } else {
                    const input = document.createElement('input');
                    input.type = 'text';
                    input.id = `param-${param.name}`;
                    input.value = param.default || '';
                    input.placeholder = param.description || param.name;
                    group.appendChild(input);
                }
                paramForm.appendChild(group);
            });
        } else {
            paramSection.style.display = 'none';
            paramForm.innerHTML = '';
        }

        document.getElementById('status-badge').textContent = `Selected: ${algo.emoji} ${algo.name}`;
        document.getElementById('status-badge').className = 'status-badge';

        // Populate education panel
        this._renderEduPanel(algo);
    }

    _renderEduPanel(algo) {
        const section = document.getElementById('edu-section');
        const hasEdu = algo.time_complexity || (algo.use_cases && algo.use_cases.length > 0) || algo.pseudocode;
        if (!hasEdu) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';
        document.getElementById('edu-title').textContent = `${algo.emoji} ${algo.name}`;

        const timeEl = document.getElementById('edu-time');
        const spaceEl = document.getElementById('edu-space');
        timeEl.textContent = algo.time_complexity || '—';
        spaceEl.textContent = algo.space_complexity || '—';

        const listEl = document.getElementById('edu-usecases');
        listEl.innerHTML = '';
        (algo.use_cases || []).forEach(uc => {
            const li = document.createElement('li');
            li.textContent = uc;
            listEl.appendChild(li);
        });

        const codeEl = document.getElementById('edu-pseudocode');
        codeEl.textContent = algo.pseudocode || '';
    }

    _collectParams() {
        const params = {};
        if (!this.selectedAlgorithm) return params;

        const algo = this.algorithms.find(a => `${a.category}/${a.name}` === this.selectedAlgorithm);
        if (!algo) return params;

        (algo.parameters || []).forEach(param => {
            const el = document.getElementById(`param-${param.name}`);
            if (el) {
                params[param.name] = el.value;
            }
        });
        return params;
    }

    _validateParams() {
        if (!this.selectedAlgorithm) {
            showToast('Please select an algorithm first', 'error');
            return false;
        }

        const algo = this.algorithms.find(a => `${a.category}/${a.name}` === this.selectedAlgorithm);
        if (!algo) return false;

        const params = this._collectParams();
        for (const param of (algo.parameters || [])) {
            if (param.required && !params[param.name]) {
                showToast(`Parameter '${param.description || param.name}' is required`, 'error');
                const el = document.getElementById(`param-${param.name}`);
                if (el) el.focus();
                return false;
            }
        }

        const graph = this.editor.toJSON();

        // Skip empty-graph check for tree construction algorithms
        const algo_meta = this.algorithms.find(a => `${a.category}/${a.name}` === this.selectedAlgorithm);
        const isTreeConstruction = algo_meta && algo_meta.layout === 'hierarchical';
        if (!graph.nodes || graph.nodes.length === 0) {
            if (!isTreeConstruction) {
                showToast('Graph has no nodes', 'error');
                return false;
            }
        }

        return true;
    }

    _setupControls() {
        document.getElementById('btn-play').addEventListener('click', () => this._play());
        document.getElementById('btn-pause').addEventListener('click', () => this._pause());
        document.getElementById('btn-step').addEventListener('click', () => this._step());
        document.getElementById('btn-reset').addEventListener('click', () => this._reset());

        document.getElementById('btn-set-root').addEventListener('click', () => {
            const sel = this.editor.network.getSelection();
            if (sel.nodes.length > 0) {
                this.editor.setRoot(sel.nodes[0]);
                showToast(`Root set to node "${sel.nodes[0]}"`, 'success');
            } else {
                showToast('Select a node first, then click Set Root', 'error');
            }
        });

        const slider = document.getElementById('speed-slider');
        const label = document.getElementById('speed-label');
        slider.addEventListener('input', (e) => {
            this.currentSpeed = parseInt(e.target.value);
            label.textContent = `${this.currentSpeed}ms`;
            this.ws.send('speed', { value: this.currentSpeed });
        });
    }

    _play() {
        if (!this._validateParams()) return;

        if (this.isPaused) {
            this.ws.send('resume');
            this.isPaused = false;
            this._setStatus('running', 'Running');
            this._updateButtonStates();
            return;
        }

        const graph = this.editor.toJSON();
        const params = this._collectParams();

        // Store original labels before run
        this.visualizer.storeOriginalLabels();

        this.ws.send('start', {
            algorithm_key: this.selectedAlgorithm,
            graph: graph,
            params: params,
            speed: this.currentSpeed
        });

        this.isRunning = true;
        this.isPaused = false;
        this.editor.setMode('run');
        this._setStatus('running', 'Running');
        this._updateButtonStates();

        // Switch to hierarchical layout for tree algorithms
        if (this.selectedAlgorithm && this.selectedAlgorithm.startsWith('tree/')) {
            this.editor.setLayoutMode('hierarchical');
        }

        document.getElementById('step-log-content').innerHTML = '';
    }

    _pause() {
        if (this.isRunning && !this.isPaused) {
            this.ws.send('pause');
            this.isPaused = true;
            this._setStatus('paused', 'Paused');
            this._updateButtonStates();
        }
    }

    _step() {
        if (!this._validateParams()) return;

        if (!this.isRunning) {
            // First step: send 'start' command so backend creates the runner
            const graph = this.editor.toJSON();
            const params = this._collectParams();
            this.visualizer.storeOriginalLabels();

            this.ws.send('start', {
                algorithm_key: this.selectedAlgorithm,
                graph: graph,
                params: params,
                speed: this.currentSpeed
            });

            // Then immediately pause — the backend will start and we'll pause on first step
            this.isRunning = true;
            this.isPaused = false;
            this.editor.setMode('run');
            this._setStatus('running', 'Running');
            document.getElementById('step-log-content').innerHTML = '';

            // After start, immediately pause so we only get one step
            // We'll pause after the first step arrives
            this._pendingStepPause = true;
        } else {
            this.ws.send('step');
            this._setStatus('paused', 'Stepping');
        }
        this._updateButtonStates();
    }

    _reset() {
        this.ws.send('reset');
        this.isRunning = false;
        this.isPaused = false;
        this._pendingStepPause = false;
        this.editor.setMode('edit');
        this.editor.resetAllStyles();
        this.visualizer.restoreOriginalLabels();

        // Restore layout mode based on current structure type
        if (this.editor.getStructureType() === 'tree') {
            this.editor.setLayoutMode('hierarchical');
        } else {
            const graphData = this.editor.toJSON();
            if (graphData.directed && graphData.root_id) {
                this.editor.setLayoutMode('hierarchical');
            } else {
                this.editor.setLayoutMode('force');
            }
        }

        this._setStatus('', 'Ready');
        this._updateButtonStates();
        document.getElementById('step-log-content').innerHTML = '';
    }

    _setStatus(className, text) {
        const badge = document.getElementById('status-badge');
        badge.className = `status-badge ${className}`;
        badge.textContent = text;
    }

    _updateButtonStates() {
        document.getElementById('btn-play').disabled = this.isRunning && !this.isPaused;
        document.getElementById('btn-pause').disabled = !this.isRunning || this.isPaused;
        document.getElementById('btn-step').disabled = this.isRunning && !this.isPaused;
    }

    _setupWSHandlers() {
        this.ws.on('step', (data) => {
            this.visualizer.applyStep(data);
            if (data.message) {
                this._appendToLog(data.message, data.phase || 'explore');
            }
            // If we started via step button, pause after first step
            if (this._pendingStepPause) {
                this._pendingStepPause = false;
                this.ws.send('pause');
                this.isPaused = true;
                this._setStatus('paused', 'Stepping');
                this._updateButtonStates();
            }
        });

        this.ws.on('meta', (data) => {
            console.log('Algorithm meta:', data);
            if (data.layout === 'hierarchical') {
                this.editor.setLayoutMode('hierarchical');
            }
        });

        this.ws.on('finished', () => {
            this.isRunning = false;
            this.isPaused = false;
            this._pendingStepPause = false;
            this.editor.setMode('view');
            this._setStatus('finished', 'Finished');
            this._updateButtonStates();
            this._appendToLog('Algorithm completed!', 'result');
            showToast('Algorithm finished!', 'success');
            // Auto-fit to show all nodes (important for tree construction algorithms)
            setTimeout(() => this.editor.fitAll(), 200);
        });

        this.ws.on('paused', () => {
            this.isPaused = true;
            this._setStatus('paused', 'Paused');
            this._updateButtonStates();
        });

        this.ws.on('reset_done', () => {
            this.isRunning = false;
            this.isPaused = false;
            this.editor.setMode('edit');
            this._setStatus('', 'Ready');
            this._updateButtonStates();
        });

        this.ws.on('error', (data) => {
            showToast(data.message || 'Algorithm error', 'error');
            this._appendToLog(`Error: ${data.message}`, 'result');
            this.isRunning = false;
            this.isPaused = false;
            this._pendingStepPause = false;
            this._setStatus('', 'Error');
            this._updateButtonStates();
        });
    }

    _appendToLog(message, phase) {
        const log = document.getElementById('step-log-content');
        const entry = document.createElement('div');
        entry.className = 'log-entry';

        const phaseSpan = document.createElement('span');
        phaseSpan.className = `log-phase ${phase}`;
        phaseSpan.textContent = phase;

        const msgSpan = document.createElement('span');
        msgSpan.className = 'log-msg';
        msgSpan.textContent = message;

        entry.appendChild(phaseSpan);
        entry.appendChild(msgSpan);
        log.appendChild(entry);
        log.scrollTop = log.scrollHeight;
    }
}
