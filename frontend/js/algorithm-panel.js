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

        Object.entries(categories).forEach(([cat, algos]) => {
            algos.forEach(algo => {
                const card = document.createElement('div');
                card.className = 'algo-card';
                card.dataset.key = `${algo.category}/${algo.name}`;
                card.innerHTML = `
                    <span class="algo-emoji">${algo.emoji}</span>
                    <div class="algo-info">
                        <div class="algo-name">${algo.name}</div>
                        <div class="algo-desc">${algo.description}</div>
                    </div>
                    <span class="algo-badge">${algo.category}</span>
                `;
                card.addEventListener('click', () => this._selectAlgorithm(algo, card));
                container.appendChild(card);
            });
        });
    }

    _selectAlgorithm(algo, card) {
        // Deselect previous
        document.querySelectorAll('.algo-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');

        this.selectedAlgorithm = `${algo.category}/${algo.name}`;

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

                if (param.type === 'node' || (param.name === 'source' || param.name === 'target' || param.name === 'start')) {
                    group.innerHTML = `
                        <label>${param.description || param.name}</label>
                        <select id="param-${param.name}">
                            <option value="">-- Select Node --</option>
                            ${nodeIds.map(id => `<option value="${id}" ${param.default === id ? 'selected' : ''}>${id}</option>`).join('')}
                        </select>
                    `;
                } else {
                    group.innerHTML = `
                        <label>${param.description || param.name}</label>
                        <input type="text" id="param-${param.name}" value="${param.default || ''}" placeholder="${param.description || param.name}">
                    `;
                }
                paramForm.appendChild(group);
            });
        } else {
            paramSection.style.display = 'none';
            paramForm.innerHTML = '';
        }

        document.getElementById('status-badge').textContent = `Selected: ${algo.emoji} ${algo.name}`;
        document.getElementById('status-badge').className = 'status-badge';
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

    _setupControls() {
        document.getElementById('btn-play').addEventListener('click', () => this._play());
        document.getElementById('btn-pause').addEventListener('click', () => this._pause());
        document.getElementById('btn-step').addEventListener('click', () => this._step());
        document.getElementById('btn-reset').addEventListener('click', () => this._reset());

        const slider = document.getElementById('speed-slider');
        const label = document.getElementById('speed-label');
        slider.addEventListener('input', (e) => {
            this.currentSpeed = parseInt(e.target.value);
            label.textContent = `${this.currentSpeed}ms`;
            this.ws.send('speed', { value: this.currentSpeed });
        });
    }

    _play() {
        if (!this.selectedAlgorithm) {
            showToast('Please select an algorithm first', 'error');
            return;
        }

        if (this.isPaused) {
            this.ws.send('resume');
            this.isPaused = false;
            this._setStatus('running', 'Running');
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

        document.getElementById('step-log-content').innerHTML = '';
    }

    _pause() {
        if (this.isRunning && !this.isPaused) {
            this.ws.send('pause');
            this.isPaused = true;
            this._setStatus('paused', 'Paused');
        }
    }

    _step() {
        if (!this.selectedAlgorithm) {
            showToast('Please select an algorithm first', 'error');
            return;
        }

        if (!this.isRunning) {
            // First step - need to start
            const graph = this.editor.toJSON();
            const params = this._collectParams();
            this.visualizer.storeOriginalLabels();
            this.ws.send('step', {
                algorithm_key: this.selectedAlgorithm,
                graph: graph,
                params: params,
                speed: this.currentSpeed
            });
            this.isRunning = true;
            this.isPaused = true;
            this.editor.setMode('run');
            this._setStatus('paused', 'Stepping');
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
        this.editor.setMode('edit');
        this.editor.resetAllStyles();
        this.visualizer.restoreOriginalLabels();
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
        });

        this.ws.on('meta', (data) => {
            console.log('Algorithm meta:', data);
        });

        this.ws.on('finished', () => {
            this.isRunning = false;
            this.isPaused = false;
            this.editor.setMode('view');
            this._setStatus('finished', 'Finished');
            this._updateButtonStates();
            this._appendToLog('Algorithm completed!', 'result');
            showToast('Algorithm finished!', 'success');
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
            this._setStatus('', 'Error');
            this._updateButtonStates();
        });
    }

    _appendToLog(message, phase) {
        const log = document.getElementById('step-log-content');
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.innerHTML = `
            <span class="log-phase ${phase}">${phase}</span>
            <span class="log-msg">${message}</span>
        `;
        log.appendChild(entry);
        log.scrollTop = log.scrollHeight;
    }
}
