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
        this.selectedVisualization = 'graph';
        this.algorithms = [];
        this.searchQuery = '';
        this.selectedLearningPath = 'all';
        this.selectedAlgorithmTag = 'all';
        this.categoryCollapsed = new Set();
        this.exampleInputs = this._buildExampleInputs();
        this.learningPaths = this._buildLearningPaths();
        this.algorithmTags = this._buildAlgorithmTags();
        this.favoriteAlgorithms = new Set(this._loadStoredList('val_favoriteAlgorithms'));
        this.recentAlgorithms = this._loadStoredList('val_recentAlgorithms');
        this.savedRunRecords = this._loadSavedRunRecords();
        this.lastRenderedState = null;
        this.logFilter = {
            query: '',
            phase: 'all'
        };
        this.collapsedPanels = new Set();
        this.timeline = {
            baseGraph: null,
            algorithmKey: null,
            params: {},
            startedAt: null,
            finishedAt: null,
            steps: [],
            currentIndex: 0,
            completed: false,
            playbackTimer: null,
            playbackActive: false,
            keyOnly: false,
            bookmarkOnly: false,
            bookmarks: new Set()
        };
        this.runMetrics = this._createEmptyRunMetrics();
    }

    async init() {
        await this._loadAlgorithms();
        this._setupAlgorithmSearch();
        this._setupControls();
        this._setupTimelineControls();
        this._setupLogFilters();
        this._setupRunHistory();
        this._setupPanelToggles();
        this._setupWSHandlers();
        this._renderRunHistory();
    }

    async _loadAlgorithms() {
        try {
            const response = await fetch('/api/algorithms');
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            this.algorithms = await response.json();
            this._renderAlgorithmOverview();
            this._renderLearningPaths();
            this._renderAlgorithmTags();
            this._renderQuickAccess();
            this._renderAlgorithmCards();
        } catch (e) {
            console.error('Failed to load algorithms:', e);
            showToast('Failed to load algorithms', 'error');
        }
    }

    _renderAlgorithmOverview() {
        const container = document.getElementById('algorithm-overview');
        if (!container) return;

        const categoryCounts = this.algorithms.reduce((counts, algo) => {
            counts[algo.category] = (counts[algo.category] || 0) + 1;
            return counts;
        }, {});
        const visualizationCounts = this.algorithms.reduce((counts, algo) => {
            const mode = algo.visualization || 'graph';
            counts[mode] = (counts[mode] || 0) + 1;
            return counts;
        }, {});

        const stats = [
            ['Total', this.algorithms.length],
            ['Graph', categoryCounts.graph || 0],
            ['Tree', categoryCounts.tree || 0],
            ['Array', categoryCounts.array || 0],
            ['DP', categoryCounts.dp || 0],
            ['String', categoryCounts.string || 0],
            ['Views', Object.keys(visualizationCounts).length]
        ];

        container.innerHTML = '';
        stats.forEach(([label, value]) => {
            const item = document.createElement('div');
            item.className = 'overview-stat';

            const valueEl = document.createElement('div');
            valueEl.className = 'overview-value';
            valueEl.textContent = value;

            const labelEl = document.createElement('div');
            labelEl.className = 'overview-label';
            labelEl.textContent = label;

            item.appendChild(valueEl);
            item.appendChild(labelEl);
            container.appendChild(item);
        });
    }

    _renderLearningPaths() {
        const container = document.getElementById('learning-paths');
        if (!container) return;

        container.innerHTML = '';

        const header = document.createElement('div');
        header.className = 'learning-paths-title';
        header.textContent = 'Learning paths';
        container.appendChild(header);

        const list = document.createElement('div');
        list.className = 'learning-path-list';

        const allPath = {
            id: 'all',
            label: 'All',
            description: 'Show every registered algorithm.',
            keys: this.algorithms.map(algo => `${algo.category}/${algo.name}`)
        };
        [allPath, ...this.learningPaths].forEach(path => {
            const availableKeys = path.keys.filter(key => this._findAlgorithmByKey(key));
            if (path.id !== 'all' && availableKeys.length === 0) return;

            const button = document.createElement('button');
            button.className = path.id === this.selectedLearningPath ? 'learning-path active' : 'learning-path';
            button.type = 'button';
            button.dataset.path = path.id;
            button.title = path.description;

            const label = document.createElement('span');
            label.className = 'learning-path-label';
            label.textContent = path.label;

            const count = document.createElement('span');
            count.className = 'learning-path-count';
            count.textContent = availableKeys.length;

            button.appendChild(label);
            button.appendChild(count);
            button.addEventListener('click', () => {
                this.selectedLearningPath = path.id;
                this._renderLearningPaths();
                this._renderAlgorithmCards();
            });
            list.appendChild(button);
        });

        container.appendChild(list);
    }

    _renderQuickAccess() {
        const container = document.getElementById('algorithm-quick-access');
        if (!container) return;

        container.innerHTML = '';

        const favorites = [...this.favoriteAlgorithms]
            .map(key => this._findAlgorithmByKey(key))
            .filter(Boolean);
        const recent = this.recentAlgorithms
            .filter(key => !this.favoriteAlgorithms.has(key))
            .map(key => this._findAlgorithmByKey(key))
            .filter(Boolean)
            .slice(0, 5);

        if (favorites.length === 0 && recent.length === 0) {
            const empty = document.createElement('div');
            empty.className = 'quick-access-empty';
            empty.textContent = 'Star algorithms to pin them here.';
            container.appendChild(empty);
            return;
        }

        const sections = [
            ['Favorites', favorites],
            ['Recent', recent]
        ];

        sections.forEach(([label, algos]) => {
            if (algos.length === 0) return;

            const section = document.createElement('div');
            section.className = 'quick-access-section';

            const title = document.createElement('div');
            title.className = 'quick-access-title';
            title.textContent = label;
            section.appendChild(title);

            const list = document.createElement('div');
            list.className = 'quick-access-list';

            algos.forEach(algo => {
                const key = `${algo.category}/${algo.name}`;
                const button = document.createElement('button');
                button.className = key === this.selectedAlgorithm ? 'quick-access-item active' : 'quick-access-item';
                button.type = 'button';
                button.dataset.key = key;
                button.title = `${algo.category}/${algo.name}`;

                const emoji = document.createElement('span');
                emoji.className = 'quick-access-emoji';
                emoji.textContent = algo.emoji || '';

                const name = document.createElement('span');
                name.className = 'quick-access-name';
                name.textContent = algo.name;

                button.appendChild(emoji);
                button.appendChild(name);
                button.addEventListener('click', () => this._selectAlgorithmByKey(key));
                list.appendChild(button);
            });

            section.appendChild(list);
            container.appendChild(section);
        });
    }

    _toggleFavorite(key) {
        if (this.favoriteAlgorithms.has(key)) {
            this.favoriteAlgorithms.delete(key);
        } else {
            this.favoriteAlgorithms.add(key);
        }
        this._storeList('val_favoriteAlgorithms', [...this.favoriteAlgorithms]);
        this._renderQuickAccess();
        this._renderAlgorithmCards();
    }

    _recordRecentAlgorithm(key) {
        this.recentAlgorithms = [key, ...this.recentAlgorithms.filter(item => item !== key)].slice(0, 8);
        this._storeList('val_recentAlgorithms', this.recentAlgorithms);
        this._renderQuickAccess();
    }

    _selectAlgorithmByKey(key) {
        const algo = this._findAlgorithmByKey(key);
        if (!algo) return;

        const searchInput = document.getElementById('algorithm-search');
        this.searchQuery = '';
        if (searchInput) searchInput.value = '';
        this.selectedLearningPath = 'all';
        this.selectedAlgorithmTag = 'all';
        this.categoryCollapsed.clear();
        this._renderLearningPaths();
        this._renderAlgorithmTags();
        this._renderAlgorithmCards();

        const card = document.querySelector(`.algo-card[data-key="${key}"]`);
        this._selectAlgorithm(algo, card);
    }

    _loadStoredList(key) {
        try {
            const value = JSON.parse(localStorage.getItem(key) || '[]');
            return Array.isArray(value) ? value.filter(item => typeof item === 'string') : [];
        } catch (e) {
            return [];
        }
    }

    _storeList(key, values) {
        try {
            localStorage.setItem(key, JSON.stringify(values));
        } catch (e) {
            // Ignore storage failures; quick access is a non-critical convenience.
        }
    }

    _loadSavedRunRecords() {
        try {
            const value = JSON.parse(localStorage.getItem('val_savedRunRecords') || '[]');
            if (!Array.isArray(value)) return [];
            return value
                .filter(item => item && typeof item === 'object' && item.record)
                .slice(0, 10);
        } catch (e) {
            return [];
        }
    }

    _storeSavedRunRecords() {
        try {
            localStorage.setItem('val_savedRunRecords', JSON.stringify(this.savedRunRecords.slice(0, 10)));
        } catch (e) {
            showToast('Could not save run record locally', 'error');
        }
    }

    _renderAlgorithmTags() {
        const container = document.getElementById('algorithm-tags');
        if (!container) return;

        container.innerHTML = '';

        const title = document.createElement('div');
        title.className = 'algorithm-tags-title';
        title.textContent = 'Tags';

        const list = document.createElement('div');
        list.className = 'algorithm-tag-list';

        const allTag = {
            id: 'all',
            label: 'All',
            description: 'Show all algorithm tags.'
        };

        [allTag, ...this.algorithmTags].forEach(tag => {
            const count = tag.id === 'all'
                ? this.algorithms.length
                : this.algorithms.filter(algo => this._getAlgorithmTagIds(algo).includes(tag.id)).length;
            if (tag.id !== 'all' && count === 0) return;

            const button = document.createElement('button');
            button.className = tag.id === this.selectedAlgorithmTag ? 'algorithm-tag active' : 'algorithm-tag';
            button.type = 'button';
            button.dataset.tag = tag.id;
            button.title = tag.description;

            const label = document.createElement('span');
            label.textContent = tag.label;

            const countEl = document.createElement('span');
            countEl.className = 'algorithm-tag-count';
            countEl.textContent = count;

            button.appendChild(label);
            button.appendChild(countEl);
            button.addEventListener('click', () => {
                this.selectedAlgorithmTag = tag.id;
                this.categoryCollapsed.clear();
                this._renderAlgorithmTags();
                this._renderAlgorithmCards();
            });
            list.appendChild(button);
        });

        container.appendChild(title);
        container.appendChild(list);
    }

    _getActiveAlgorithmTag() {
        if (this.selectedAlgorithmTag === 'all') return null;
        return this.algorithmTags.find(tag => tag.id === this.selectedAlgorithmTag) || null;
    }

    _getAlgorithmTagIds(algo) {
        const key = `${algo.category}/${algo.name}`;
        const name = String(algo.name || '').toLowerCase();
        const category = String(algo.category || '').toLowerCase();
        const text = [
            name,
            category,
            algo.description,
            ...(algo.use_cases || [])
        ].join(' ').toLowerCase();
        const tags = new Set();

        if (category === 'graph') tags.add('graph');
        if (category === 'tree') tags.add('tree');
        if (category === 'array') tags.add('array');
        if (category === 'dp') tags.add('dp');
        if (category === 'string') tags.add('string');

        if (/(bfs|dfs|search|traversal|level_order|binary_search)/.test(text)) tags.add('search');
        if (/(dijkstra|bellman|spfa|floyd|johnson|a\*|shortest|longest|critical|path)/.test(text)) tags.add('shortest-path');
        if (/(flow|edmonds|dinic|capacity|augment|min-cost)/.test(text)) tags.add('flow');
        if (/(sort|quick|merge|heap_sort|bubble|topological)/.test(text)) tags.add('sorting');
        if (/(mst|minimum spanning|prim|kruskal)/.test(text)) tags.add('mst');
        if (/(scc|component|cycle|bridge|articulation|union_find|bipartite|matching)/.test(text)) tags.add('graph-structure');
        if (/(match|matching|assignment|pattern|kmp|rabin|boyer|z_algorithm|suffix|aho|palindrome|manacher)/.test(text)) tags.add('matching');
        if (/(knapsack|coin|lcs|edit|subset|word|matrix|fibonacci|lis|dynamic|hungarian|assignment)/.test(text)) tags.add('dp-table');
        if (/(heap|treap|trie|bst|tree|avl|black|btree|fenwick|segment|huffman)/.test(text)) tags.add('data-structure');

        const overrides = {
            'graph/topological_sort': ['graph', 'sorting', 'graph-structure'],
            'graph/dag_longest_path': ['graph', 'dp', 'shortest-path', 'graph-structure'],
            'graph/dominator_tree': ['graph', 'graph-structure', 'data-structure'],
            'graph/directed_mst': ['graph', 'mst', 'graph-structure'],
            'graph/yen_k_shortest_paths': ['graph', 'shortest-path', 'graph-structure'],
            'graph/suurballe_disjoint_paths': ['graph', 'shortest-path', 'graph-structure'],
            'graph/karp_minimum_mean_cycle': ['graph', 'graph-structure', 'dp'],
            'graph/minimum_cycle_basis': ['graph', 'graph-structure', 'data-structure'],
            'graph/euler_path': ['graph', 'graph-structure'],
            'array/kadane': ['array', 'dp', 'dp-table'],
            'array/sparse_table': ['array', 'data-structure'],
            'graph/blossom_matching': ['graph', 'graph-structure', 'matching'],
            'graph/hopcroft_karp': ['graph', 'graph-structure', 'matching'],
            'graph/min_cost_max_flow': ['graph', 'flow', 'shortest-path'],
            'graph/push_relabel': ['graph', 'flow'],
            'graph/gomory_hu_tree': ['graph', 'graph-structure', 'flow'],
            'graph/stoer_wagner': ['graph', 'graph-structure'],
            'dp/hungarian': ['dp', 'matching', 'dp-table'],
            'string/suffix_array': ['string', 'matching', 'data-structure'],
            'string/suffix_automaton': ['string', 'matching', 'data-structure'],
            'tree/lca': ['tree', 'search', 'data-structure'],
            'tree/heavy_light_decomposition': ['tree', 'data-structure'],
            'tree/aho_corasick': ['tree', 'string', 'matching', 'data-structure'],
            'tree/fenwick_tree': ['tree', 'array', 'data-structure'],
            'tree/segment_tree': ['tree', 'array', 'data-structure']
        };
        (overrides[key] || []).forEach(tag => tags.add(tag));

        return [...tags];
    }

    _renderAlgorithmCards() {
        const container = document.getElementById('algorithm-list');
        container.innerHTML = '';

        const categories = {};
        this.algorithms.forEach(algo => {
            if (!categories[algo.category]) categories[algo.category] = [];
            categories[algo.category].push(algo);
        });

        const query = this.searchQuery.trim().toLowerCase();
        const activePath = this._getActiveLearningPath();
        const activePathKeys = activePath ? new Set(activePath.keys) : null;
        const activeTag = this._getActiveAlgorithmTag();
        const matchesSearch = (algo) => {
            if (!query) return true;
            const fields = [
                algo.name,
                algo.category,
                algo.description,
                algo.time_complexity,
                algo.space_complexity,
                ...(algo.use_cases || []),
                ...this._getAlgorithmTagIds(algo)
            ];
            return fields.some(field => String(field || '').toLowerCase().includes(query));
        };
        const matchesLearningPath = (algo) => {
            if (!activePathKeys) return true;
            return activePathKeys.has(`${algo.category}/${algo.name}`);
        };
        const matchesTag = (algo) => {
            if (!activeTag) return true;
            return this._getAlgorithmTagIds(algo).includes(activeTag.id);
        };

        const categoryOrder = ['graph', 'tree', 'array', 'dp', 'string'];
        const categoryLabels = {
            graph: { emoji: '📊', label: 'Graph Algorithms' },
            tree: { emoji: '🌲', label: 'Tree Algorithms' },
            array: { emoji: '🔢', label: 'Array Algorithms' },
            dp: { emoji: '🧮', label: 'Dynamic Programming' },
            string: { emoji: '🔤', label: 'String Algorithms' }
        };

        const orderedCats = [
            ...categoryOrder.filter(c => categories[c]),
            ...Object.keys(categories).filter(c => !categoryOrder.includes(c))
        ];

        orderedCats.forEach(cat => {
            const totalCount = categories[cat].length;
            const algos = categories[cat].filter(algo => matchesLearningPath(algo) && matchesTag(algo) && matchesSearch(algo));
            if (algos.length === 0) return;

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
            catCount.textContent = query ? `${algos.length}/${totalCount}` : algos.length;

            const catToggle = document.createElement('span');
            catToggle.className = 'category-toggle';

            header.appendChild(catEmoji);
            header.appendChild(catLabel);
            header.appendChild(catCount);
            header.appendChild(catToggle);

            const algoContainer = document.createElement('div');
            algoContainer.className = 'category-algos';
            const isCollapsed = !query && this.categoryCollapsed.has(cat);
            if (isCollapsed) algoContainer.classList.add('collapsed');
            catToggle.textContent = isCollapsed ? '▶' : '▼';

            header.addEventListener('click', () => {
                const nextCollapsed = algoContainer.classList.toggle('collapsed');
                catToggle.textContent = nextCollapsed ? '▶' : '▼';
                if (nextCollapsed) {
                    this.categoryCollapsed.add(cat);
                } else {
                    this.categoryCollapsed.delete(cat);
                }
            });

            algos.forEach(algo => {
                const key = `${algo.category}/${algo.name}`;
                const card = document.createElement('div');
                card.className = key === this.selectedAlgorithm ? 'algo-card selected' : 'algo-card';
                card.dataset.key = key;

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

                const favoriteBtn = document.createElement('button');
                favoriteBtn.className = this.favoriteAlgorithms.has(key) ? 'algo-favorite active' : 'algo-favorite';
                favoriteBtn.type = 'button';
                favoriteBtn.title = this.favoriteAlgorithms.has(key) ? 'Remove favorite' : 'Add favorite';
                favoriteBtn.setAttribute('aria-label', `${this.favoriteAlgorithms.has(key) ? 'Remove' : 'Add'} ${algo.name} favorite`);
                favoriteBtn.textContent = '★';
                favoriteBtn.addEventListener('click', (event) => {
                    event.stopPropagation();
                    this._toggleFavorite(key);
                });

                infoDiv.appendChild(nameDiv);
                infoDiv.appendChild(descDiv);

                card.appendChild(emojiSpan);
                card.appendChild(infoDiv);
                card.appendChild(favoriteBtn);

                card.addEventListener('click', () => this._selectAlgorithm(algo, card));
                algoContainer.appendChild(card);
            });

            container.appendChild(header);
            container.appendChild(algoContainer);
        });

        if (!container.children.length) {
            const empty = document.createElement('div');
            empty.className = 'algorithm-empty';
            const pathText = activePath ? ` in ${activePath.label}` : '';
            const tagText = activeTag ? ` tagged ${activeTag.label}` : '';
            empty.textContent = `No algorithms match "${this.searchQuery.trim()}"${pathText}${tagText}`;
            container.appendChild(empty);
        }
    }

    _setupAlgorithmSearch() {
        const input = document.getElementById('algorithm-search');
        const clearBtn = document.getElementById('btn-clear-algo-search');
        if (!input) return;

        input.addEventListener('input', () => {
            this.searchQuery = input.value;
            this._renderAlgorithmCards();
        });

        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                input.value = '';
                this.searchQuery = '';
                this._renderAlgorithmCards();
                input.focus();
            });
        }
    }

    _selectAlgorithm(algo, card) {
        // Deselect previous
        document.querySelectorAll('.algo-card').forEach(c => c.classList.remove('selected'));
        if (card) card.classList.add('selected');

        this.selectedAlgorithm = `${algo.category}/${algo.name}`;
        this._recordRecentAlgorithm(this.selectedAlgorithm);

        const visualization = algo.visualization || 'graph';
        this.selectedVisualization = visualization;
        if (this.visualizer && this.visualizer.setVisualizationMode) {
            this.visualizer.setVisualizationMode(visualization);
            if (visualization !== 'graph' && this.visualizer.clearStructure) {
                this.visualizer.clearStructure();
            }
        }

        // Switch structure type based on algorithm category
        const isTree = algo.category === 'tree';
        if (visualization === 'graph') {
            this.editor.setStructureType(isTree ? 'tree' : 'graph');
        }
        document.getElementById('btn-set-root').style.display = isTree ? '' : 'none';

        this._renderParamSection(algo);

        document.getElementById('status-badge').textContent = `Selected: ${algo.emoji} ${algo.name}`;
        document.getElementById('status-badge').className = 'status-badge';

        // Populate education panel
        this._renderEduPanel(algo);
    }

    _renderParamSection(algo) {
        const paramSection = document.getElementById('param-section');
        const paramForm = document.getElementById('param-form');
        const examples = this._getExampleInputs(algo);
        const hasParams = algo.parameters && algo.parameters.length > 0;

        if (!hasParams && examples.length === 0) {
            paramSection.style.display = 'none';
            paramForm.innerHTML = '';
            return;
        }

        paramSection.style.display = 'block';
        paramForm.innerHTML = '';

        const errorPanel = document.createElement('div');
        errorPanel.className = 'param-error-panel';
        errorPanel.style.display = 'none';
        paramForm.appendChild(errorPanel);

        if (examples.length > 0) {
            this._renderExampleControls(algo, paramForm, examples);
        }

        if (!hasParams) return;

        const nodeIds = this.editor.getNodeIds();

        algo.parameters.forEach(param => {
            const group = document.createElement('div');
            group.className = 'param-group';
            group.dataset.paramName = param.name;

            const label = document.createElement('label');
            label.textContent = param.description || param.name;
            group.appendChild(label);

            const nodeParamNames = ['source', 'target', 'start', 'end', 'from', 'to'];
            const isNodeParam = param.type === 'node' || (
                nodeParamNames.includes(param.name) &&
                algo.requires_graph !== false &&
                (algo.visualization || 'graph') === 'graph'
            );

            if (isNodeParam) {
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

        const randomBtn = document.createElement('button');
        randomBtn.className = 'btn btn-sm btn-random';
        randomBtn.innerHTML = '<span class="emoji-icon">🎲</span> Random';
        randomBtn.type = 'button';
        randomBtn.addEventListener('click', () => this._generateRandomParams(algo));
        paramForm.appendChild(randomBtn);

        this._renderCompareControls(algo, paramForm);
    }

    _clearParamErrors() {
        const panel = document.querySelector('.param-error-panel');
        if (panel) {
            panel.textContent = '';
            panel.style.display = 'none';
        }
        document.querySelectorAll('.param-group.error').forEach(group => group.classList.remove('error'));
    }

    _showParamError(message, fields = []) {
        const panel = document.querySelector('.param-error-panel');
        if (panel) {
            panel.textContent = message || 'Input validation failed';
            panel.style.display = 'block';
        }

        fields.forEach(name => {
            const group = document.querySelector(`.param-group[data-param-name="${name}"]`);
            if (group) group.classList.add('error');
        });
    }

    _inferErrorFields(message) {
        const text = String(message || '').toLowerCase();
        const fields = [];
        if (text.includes("parameter '")) {
            const match = text.match(/parameter '([^']+)'/);
            if (match) fields.push(match[1]);
        }
        if (text.includes('source')) fields.push('source');
        if (text.includes('target')) fields.push('target');
        if (text.includes('start')) fields.push('start');
        if (text.includes('end')) fields.push('end');
        if (text.includes('node')) {
            ['source', 'target', 'start', 'end', 'from', 'to'].forEach(name => fields.push(name));
        }
        return [...new Set(fields)];
    }

    _renderExampleControls(algo, paramForm, examples) {
        const panel = document.createElement('div');
        panel.className = 'example-panel';

        const label = document.createElement('label');
        label.className = 'example-label';
        label.textContent = 'Example input';

        const row = document.createElement('div');
        row.className = 'example-row';

        const select = document.createElement('select');
        select.className = 'example-select';

        examples.forEach((example, index) => {
            const opt = document.createElement('option');
            opt.value = String(index);
            opt.textContent = example.label;
            select.appendChild(opt);
        });

        const loadBtn = document.createElement('button');
        loadBtn.className = 'btn btn-sm btn-example';
        loadBtn.type = 'button';
        loadBtn.textContent = 'Load';

        const desc = document.createElement('div');
        desc.className = 'example-description';
        const updateDescription = () => {
            const selected = examples[parseInt(select.value, 10)] || examples[0];
            desc.textContent = selected.description || '';
        };

        select.addEventListener('change', updateDescription);
        loadBtn.addEventListener('click', () => {
            const selected = examples[parseInt(select.value, 10)] || examples[0];
            this._applyExampleInput(algo, selected);
        });

        row.appendChild(select);
        row.appendChild(loadBtn);
        panel.appendChild(label);
        panel.appendChild(row);
        panel.appendChild(desc);
        paramForm.appendChild(panel);
        updateDescription();
    }

    _renderCompareControls(algo, paramForm) {
        const selectedKey = `${algo.category}/${algo.name}`;
        const candidates = this._getCompareCandidates(selectedKey);
        if (candidates.length < 2) return;

        const panel = document.createElement('div');
        panel.className = 'compare-panel';

        const label = document.createElement('label');
        label.className = 'compare-label';
        label.textContent = 'Compare algorithms';

        const list = document.createElement('div');
        list.className = 'compare-options';

        candidates.forEach(key => {
            const candidate = this._findAlgorithmByKey(key);
            if (!candidate) return;

            const option = document.createElement('label');
            option.className = 'compare-option';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = key;
            checkbox.checked = true;
            checkbox.disabled = key === selectedKey;

            const name = document.createElement('span');
            name.textContent = candidate.name;

            option.appendChild(checkbox);
            option.appendChild(name);
            list.appendChild(option);
        });

        const runBtn = document.createElement('button');
        runBtn.className = 'btn btn-sm btn-compare';
        runBtn.type = 'button';
        runBtn.textContent = 'Compare';
        runBtn.addEventListener('click', () => this._runComparison(panel));

        const output = document.createElement('div');
        output.className = 'compare-results';

        panel.appendChild(label);
        panel.appendChild(list);
        panel.appendChild(runBtn);
        panel.appendChild(output);
        paramForm.appendChild(panel);
    }

    _getCompareCandidates(selectedKey) {
        const groups = [
            ['graph/dijkstra', 'graph/bellman_ford', 'graph/spfa'],
            ['graph/edmonds_karp', 'graph/dinic'],
            ['string/kmp', 'string/rabin_karp', 'string/boyer_moore', 'string/z_algorithm'],
            ['array/bubble_sort', 'array/quick_sort', 'array/merge_sort', 'array/heap_sort']
        ];
        const group = groups.find(items => items.includes(selectedKey)) || [];
        return group.filter(key => this._findAlgorithmByKey(key));
    }

    async _runComparison(panel) {
        if (!this._validateParams()) return;
        this._clearParamErrors();

        const output = panel.querySelector('.compare-results');
        const selectedKeys = [...panel.querySelectorAll('.compare-option input:checked')]
            .map(input => input.value);

        if (selectedKeys.length < 2) {
            showToast('Select at least two algorithms to compare', 'error');
            return;
        }

        output.textContent = 'Comparing...';
        const graph = this.editor.toJSON();
        const params = this._collectParams();

        try {
            const response = await fetch('/api/algorithms/compare', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    algorithm_keys: selectedKeys,
                    graph,
                    params
                })
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Comparison failed');
            }
            this._renderComparisonResults(output, data.results || []);
            showToast('Comparison complete', 'success');
        } catch (e) {
            output.textContent = '';
            this._showParamError(e.message || 'Comparison failed', this._inferErrorFields(e.message));
            showToast(e.message || 'Comparison failed', 'error');
        }
    }

    _renderComparisonResults(output, results) {
        output.innerHTML = '';
        if (!results.length) {
            output.textContent = 'No comparison results';
            return;
        }

        const table = document.createElement('table');
        table.className = 'compare-table';

        const thead = document.createElement('thead');
        const header = document.createElement('tr');
        ['Algorithm', 'Status', 'Steps', 'Duration', 'Nodes', 'Edges', 'Phases', 'Actions', 'Result'].forEach(text => {
            const th = document.createElement('th');
            th.textContent = text;
            header.appendChild(th);
        });
        thead.appendChild(header);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        results.forEach(result => {
            const row = document.createElement('tr');
            const cells = [
                result.name || result.algorithm_key,
                result.status,
                result.step_count,
                result.duration_ms !== undefined && result.duration_ms !== null ? `${result.duration_ms}ms` : '',
                result.visited_node_count,
                result.touched_edge_count,
                this._formatCountBreakdown(result.phase_counts || {}, 2),
                this._formatCountBreakdown(result.action_counts || {}, 2),
                result.status === 'ok'
                    ? this._formatComparisonSummary(result.summary || {})
                    : (result.error || 'error')
            ];

            cells.forEach(value => {
                const td = document.createElement('td');
                td.textContent = this._formatStateValue(value);
                td.title = td.textContent;
                row.appendChild(td);
            });
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        output.appendChild(table);
    }

    _formatComparisonSummary(summary) {
        if (!summary || Object.keys(summary).length === 0) return '';
        const preferred = [
            'max_flow',
            'distance',
            'distances',
            'matches',
            'found',
            'index',
            'sorted',
            'array',
            'negative_cycle'
        ];
        const keys = preferred.filter(key => Object.prototype.hasOwnProperty.call(summary, key));
        const shown = keys.length ? keys : Object.keys(summary).slice(0, 2);
        return shown
            .map(key => `${this._formatStateKey(key)}: ${this._formatInlineStateValue(summary[key])}`)
            .join(', ');
    }

    _applyExampleInput(algo, example) {
        if (!example) return;

        if (example.graph) {
            const graphData = JSON.parse(JSON.stringify(example.graph));
            if (this.visualizer && this.visualizer.setVisualizationMode) {
                this.visualizer.setVisualizationMode('graph');
            }
            this.editor.loadFromJSON(graphData);
            document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('selected'));
        } else if (example.presetId) {
            const preset = this._findPresetById(example.presetId);
            if (!preset) {
                showToast(`Preset '${example.presetId}' is not loaded yet`, 'error');
                return;
            }
            if (this.visualizer && this.visualizer.setVisualizationMode) {
                this.visualizer.setVisualizationMode('graph');
            }
            this.editor.loadFromJSON(JSON.parse(JSON.stringify(preset)));
            document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('selected'));
        }

        this._renderParamSection(algo);
        this._fillParamFields(example.params || {});
        showToast(`Loaded example: ${example.label}`, 'success');
    }

    _fillParamFields(params) {
        Object.entries(params || {}).forEach(([name, value]) => {
            const el = document.getElementById(`param-${name}`);
            if (el) {
                el.value = value;
                el.dispatchEvent(new Event('change'));
            }
        });
    }

    _findPresetById(id) {
        const manager = window.app && window.app.presetManager;
        const presets = manager && Array.isArray(manager.presets) ? manager.presets : [];
        return presets.find(preset => preset.id === id || preset.name === id) || null;
    }

    _getExampleInputs(algo) {
        const key = `${algo.category}/${algo.name}`;
        return this.exampleInputs[key] || [];
    }

    _getActiveLearningPath() {
        if (this.selectedLearningPath === 'all') return null;
        return this.learningPaths.find(path => path.id === this.selectedLearningPath) || null;
    }

    _buildLearningPaths() {
        return [
            {
                id: 'graph-core',
                label: 'Graph Core',
                description: 'Traversal, shortest paths, MST, and graph structure basics.',
                keys: [
                    'graph/bfs',
                    'graph/dfs',
                    'graph/dijkstra',
                    'graph/bellman_ford',
                    'graph/prim',
                    'graph/kruskal',
                    'graph/topological_sort',
                    'graph/dag_longest_path',
                    'graph/euler_path',
                    'graph/connected_components'
                ]
            },
            {
                id: 'graph-advanced',
                label: 'Graph Advanced',
                description: 'SCCs, low-link analysis, all-pairs paths, and max flow.',
                keys: [
                    'graph/cycle_detection',
                    'graph/tarjan_scc',
                    'graph/kosaraju_scc',
                    'graph/bridges_articulation',
                    'graph/floyd_warshall',
                    'graph/spfa',
                    'graph/johnson',
                    'graph/dominator_tree',
                    'graph/directed_mst',
                    'graph/yen_k_shortest_paths',
                    'graph/suurballe_disjoint_paths',
                    'graph/karp_minimum_mean_cycle',
                    'graph/minimum_cycle_basis',
                    'graph/edmonds_karp',
                    'graph/dinic',
                    'graph/push_relabel',
                    'graph/min_cost_max_flow',
                    'graph/hopcroft_karp',
                    'graph/blossom_matching',
                    'graph/stoer_wagner',
                    'graph/gomory_hu_tree'
                ]
            },
            {
                id: 'dp-foundations',
                label: 'DP Foundations',
                description: 'Classic table, sequence, and subset dynamic programming.',
                keys: [
                    'dp/fibonacci_dp',
                    'dp/lcs',
                    'dp/edit_distance',
                    'dp/knapsack',
                    'dp/coin_change',
                    'dp/lis',
                    'dp/matrix_chain_multiplication',
                    'dp/subset_sum',
                    'dp/word_break',
                    'dp/hungarian'
                ]
            },
            {
                id: 'strings',
                label: 'String Matching',
                description: 'Pattern matching and palindrome preprocessing algorithms.',
                keys: [
                    'string/kmp',
                    'string/rabin_karp',
                    'string/boyer_moore',
                    'string/z_algorithm',
                    'string/manacher',
                    'string/suffix_array',
                    'string/suffix_automaton'
                ]
            },
            {
                id: 'data-structures',
                label: 'Data Structures',
                description: 'Trees, heaps, tries, automata, and prefix-sum structures.',
                keys: [
                    'tree/bst',
                    'tree/avl',
                    'tree/red_black',
                    'tree/treap',
                    'tree/btree',
                    'tree/bplus',
                    'tree/heap',
                    'tree/fenwick_tree',
                    'tree/segment_tree',
                    'tree/lca',
                    'tree/heavy_light_decomposition',
                    'tree/trie',
                    'tree/aho_corasick',
                    'tree/huffman'
                ]
            },
            {
                id: 'arrays',
                label: 'Arrays',
                description: 'Sorting, searching, and linear array scans.',
                keys: [
                    'array/bubble_sort',
                    'array/quick_sort',
                    'array/merge_sort',
                    'array/heap_sort',
                    'array/binary_search',
                    'array/kadane',
                    'array/sparse_table'
                ]
            }
        ];
    }

    _buildAlgorithmTags() {
        return [
            { id: 'search', label: 'Search', description: 'Traversal and lookup algorithms.' },
            { id: 'shortest-path', label: 'Shortest Path', description: 'Single-source and all-pairs shortest paths.' },
            { id: 'flow', label: 'Flow', description: 'Maximum-flow and augmenting-path algorithms.' },
            { id: 'sorting', label: 'Sorting', description: 'Ordering, partitioning, and topological ordering.' },
            { id: 'mst', label: 'MST', description: 'Minimum spanning tree algorithms.' },
            { id: 'graph-structure', label: 'Structure', description: 'Connectivity, cycles, SCCs, and low-link analysis.' },
            { id: 'matching', label: 'Matching', description: 'Pattern matching and palindrome algorithms.' },
            { id: 'dp-table', label: 'DP Table', description: 'Dynamic programming tables and sequence states.' },
            { id: 'data-structure', label: 'Data Structure', description: 'Trees, heaps, tries, and indexed structures.' }
        ];
    }

    _buildExampleInputs() {
        const ex = (label, description, params = {}, presetId = null, graph = null) => ({
            label,
            description,
            params,
            presetId,
            graph
        });

        const astarGrid = {
            name: 'A* Grid Route',
            description: 'Small positioned graph for heuristic pathfinding',
            directed: false,
            nodes: [
                { id: 'A', label: 'A', x: -220, y: -80 },
                { id: 'B', label: 'B', x: -80, y: -140 },
                { id: 'C', label: 'C', x: -60, y: 20 },
                { id: 'D', label: 'D', x: 80, y: -120 },
                { id: 'E', label: 'E', x: 100, y: 40 },
                { id: 'F', label: 'F', x: 240, y: -20 }
            ],
            edges: [
                { source: 'A', target: 'B', weight: 2, label: '2' },
                { source: 'A', target: 'C', weight: 4, label: '4' },
                { source: 'B', target: 'D', weight: 3, label: '3' },
                { source: 'C', target: 'E', weight: 2, label: '2' },
                { source: 'D', target: 'F', weight: 4, label: '4' },
                { source: 'E', target: 'F', weight: 2, label: '2' },
                { source: 'B', target: 'C', weight: 1, label: '1' },
                { source: 'D', target: 'E', weight: 1, label: '1' }
            ]
        };

        const negativeGraph = {
            name: 'Negative Edge DAG',
            description: 'Directed graph with negative edges and no negative cycle',
            directed: true,
            nodes: [
                { id: 'S', label: 'S' },
                { id: 'A', label: 'A' },
                { id: 'B', label: 'B' },
                { id: 'C', label: 'C' },
                { id: 'T', label: 'T' }
            ],
            edges: [
                { source: 'S', target: 'A', weight: 6, label: '6', directed: true },
                { source: 'S', target: 'B', weight: 7, label: '7', directed: true },
                { source: 'A', target: 'C', weight: 5, label: '5', directed: true },
                { source: 'B', target: 'A', weight: -2, label: '-2', directed: true },
                { source: 'B', target: 'C', weight: 4, label: '4', directed: true },
                { source: 'C', target: 'T', weight: -1, label: '-1', directed: true }
            ]
        };

        const flowNetwork = {
            name: 'Flow Network',
            description: 'Directed capacity network for max-flow algorithms',
            directed: true,
            nodes: [
                { id: 'S', label: 'S', x: -260, y: 0 },
                { id: 'A', label: 'A', x: -90, y: -90 },
                { id: 'B', label: 'B', x: -90, y: 90 },
                { id: 'C', label: 'C', x: 90, y: -90 },
                { id: 'D', label: 'D', x: 90, y: 90 },
                { id: 'T', label: 'T', x: 260, y: 0 }
            ],
            edges: [
                { source: 'S', target: 'A', weight: 10, label: '10', directed: true },
                { source: 'S', target: 'B', weight: 10, label: '10', directed: true },
                { source: 'A', target: 'B', weight: 2, label: '2', directed: true },
                { source: 'A', target: 'C', weight: 4, label: '4', directed: true },
                { source: 'A', target: 'D', weight: 8, label: '8', directed: true },
                { source: 'B', target: 'D', weight: 9, label: '9', directed: true },
                { source: 'D', target: 'C', weight: 6, label: '6', directed: true },
                { source: 'C', target: 'T', weight: 10, label: '10', directed: true },
                { source: 'D', target: 'T', weight: 10, label: '10', directed: true }
            ]
        };

        const matchingGraph = {
            name: 'Bipartite Matching',
            description: 'Worker-task graph for maximum bipartite matching',
            directed: false,
            nodes: [
                { id: 'L1', label: 'L1', x: -180, y: -120, metadata: { partition: 'L' } },
                { id: 'L2', label: 'L2', x: -180, y: 0, metadata: { partition: 'L' } },
                { id: 'L3', label: 'L3', x: -180, y: 120, metadata: { partition: 'L' } },
                { id: 'R1', label: 'R1', x: 180, y: -120, metadata: { partition: 'R' } },
                { id: 'R2', label: 'R2', x: 180, y: 0, metadata: { partition: 'R' } },
                { id: 'R3', label: 'R3', x: 180, y: 120, metadata: { partition: 'R' } }
            ],
            edges: [
                { source: 'L1', target: 'R1', weight: 1, label: '' },
                { source: 'L1', target: 'R2', weight: 1, label: '' },
                { source: 'L2', target: 'R1', weight: 1, label: '' },
                { source: 'L2', target: 'R3', weight: 1, label: '' },
                { source: 'L3', target: 'R2', weight: 1, label: '' },
                { source: 'L3', target: 'R3', weight: 1, label: '' }
            ]
        };

        const blossomGraph = {
            name: 'General Matching Blossom',
            description: 'Non-bipartite graph where an odd cycle is contracted as a blossom',
            directed: false,
            nodes: [
                { id: 'A', label: 'A', x: -120, y: -120 },
                { id: 'B', label: 'B', x: 80, y: -120 },
                { id: 'C', label: 'C', x: -20, y: 20 },
                { id: 'D', label: 'D', x: -240, y: 70 },
                { id: 'E', label: 'E', x: 200, y: 70 }
            ],
            edges: [
                { source: 'A', target: 'B', weight: 1, label: '' },
                { source: 'B', target: 'C', weight: 1, label: '' },
                { source: 'C', target: 'A', weight: 1, label: '' },
                { source: 'A', target: 'D', weight: 1, label: '' },
                { source: 'B', target: 'E', weight: 1, label: '' }
            ]
        };

        const costFlowNetwork = {
            name: 'Costed Flow Network',
            description: 'Directed network with capacity and cost metadata',
            directed: true,
            nodes: [
                { id: 'S', label: 'S', x: -260, y: 0 },
                { id: 'A', label: 'A', x: -80, y: -90 },
                { id: 'B', label: 'B', x: -80, y: 90 },
                { id: 'T', label: 'T', x: 220, y: 0 }
            ],
            edges: [
                { source: 'S', target: 'A', weight: 2, label: 'c1', directed: true, metadata: { capacity: 2, cost: 1 } },
                { source: 'S', target: 'B', weight: 1, label: 'c2', directed: true, metadata: { capacity: 1, cost: 2 } },
                { source: 'A', target: 'B', weight: 1, label: 'c1', directed: true, metadata: { capacity: 1, cost: 1 } },
                { source: 'A', target: 'T', weight: 1, label: 'c3', directed: true, metadata: { capacity: 1, cost: 3 } },
                { source: 'B', target: 'T', weight: 2, label: 'c1', directed: true, metadata: { capacity: 2, cost: 1 } }
            ]
        };

        const minCutGraph = {
            name: 'Global Min Cut',
            description: 'Undirected weighted graph with a clear sparse cut',
            directed: false,
            nodes: [
                { id: 'A', label: 'A', x: -220, y: -90 },
                { id: 'B', label: 'B', x: -220, y: 90 },
                { id: 'C', label: 'C', x: 0, y: -90 },
                { id: 'D', label: 'D', x: 0, y: 90 },
                { id: 'E', label: 'E', x: 220, y: -90 },
                { id: 'F', label: 'F', x: 220, y: 90 }
            ],
            edges: [
                { source: 'A', target: 'B', weight: 4, label: '4' },
                { source: 'A', target: 'C', weight: 3, label: '3' },
                { source: 'B', target: 'D', weight: 3, label: '3' },
                { source: 'C', target: 'D', weight: 4, label: '4' },
                { source: 'C', target: 'E', weight: 1, label: '1' },
                { source: 'D', target: 'F', weight: 1, label: '1' },
                { source: 'E', target: 'F', weight: 5, label: '5' }
            ]
        };

        const controlFlowGraph = {
            name: 'Control Flow Graph',
            description: 'Directed CFG with joins for dominator and dominance-frontier analysis',
            directed: true,
            root_id: 'S',
            nodes: [
                { id: 'S', label: 'S', x: -260, y: 0 },
                { id: 'A', label: 'A', x: -120, y: -100 },
                { id: 'B', label: 'B', x: -120, y: 100 },
                { id: 'C', label: 'C', x: 40, y: 0 },
                { id: 'D', label: 'D', x: 180, y: -90 },
                { id: 'E', label: 'E', x: 180, y: 90 },
                { id: 'T', label: 'T', x: 320, y: 0 }
            ],
            edges: [
                { source: 'S', target: 'A', weight: 1, label: '', directed: true },
                { source: 'S', target: 'B', weight: 1, label: '', directed: true },
                { source: 'A', target: 'C', weight: 1, label: '', directed: true },
                { source: 'B', target: 'C', weight: 1, label: '', directed: true },
                { source: 'C', target: 'D', weight: 1, label: '', directed: true },
                { source: 'C', target: 'E', weight: 1, label: '', directed: true },
                { source: 'D', target: 'T', weight: 1, label: '', directed: true },
                { source: 'E', target: 'T', weight: 1, label: '', directed: true }
            ]
        };

        const directedMstGraph = {
            name: 'Directed Arborescence',
            description: 'Rooted directed graph where Edmonds contracts a selected incoming-edge cycle',
            directed: true,
            root_id: 'R',
            nodes: [
                { id: 'R', label: 'R', x: -260, y: 0 },
                { id: 'A', label: 'A', x: -90, y: -120 },
                { id: 'B', label: 'B', x: 70, y: -20 },
                { id: 'C', label: 'C', x: -20, y: 130 },
                { id: 'D', label: 'D', x: 240, y: 70 }
            ],
            edges: [
                { source: 'R', target: 'A', weight: 4, label: '4', directed: true },
                { source: 'R', target: 'B', weight: 6, label: '6', directed: true },
                { source: 'R', target: 'D', weight: 10, label: '10', directed: true },
                { source: 'A', target: 'B', weight: 1, label: '1', directed: true },
                { source: 'B', target: 'C', weight: 1, label: '1', directed: true },
                { source: 'C', target: 'A', weight: 1, label: '1', directed: true },
                { source: 'C', target: 'D', weight: 1, label: '1', directed: true },
                { source: 'A', target: 'D', weight: 4, label: '4', directed: true }
            ]
        };

        const kShortestGraph = {
            name: 'Alternative Routes',
            description: 'Directed weighted graph with several near-shortest simple paths',
            directed: true,
            nodes: [
                { id: 'S', label: 'S', x: -260, y: 0 },
                { id: 'A', label: 'A', x: -100, y: -120 },
                { id: 'B', label: 'B', x: -100, y: 120 },
                { id: 'C', label: 'C', x: 80, y: -40 },
                { id: 'D', label: 'D', x: 80, y: 120 },
                { id: 'T', label: 'T', x: 260, y: 0 }
            ],
            edges: [
                { source: 'S', target: 'A', weight: 1, label: '1', directed: true },
                { source: 'S', target: 'B', weight: 1, label: '1', directed: true },
                { source: 'A', target: 'C', weight: 1, label: '1', directed: true },
                { source: 'B', target: 'C', weight: 1, label: '1', directed: true },
                { source: 'A', target: 'D', weight: 2, label: '2', directed: true },
                { source: 'B', target: 'D', weight: 2, label: '2', directed: true },
                { source: 'C', target: 'T', weight: 1, label: '1', directed: true },
                { source: 'D', target: 'T', weight: 1, label: '1', directed: true },
                { source: 'C', target: 'D', weight: 1, label: '1', directed: true }
            ]
        };

        const meanCycleGraph = {
            name: 'Minimum Mean Cycle',
            description: 'Directed weighted graph where a short low-cost cycle has the smallest average weight',
            directed: true,
            nodes: [
                { id: 'A', label: 'A', x: -180, y: -100 },
                { id: 'B', label: 'B', x: 20, y: -140 },
                { id: 'C', label: 'C', x: 120, y: 10 },
                { id: 'D', label: 'D', x: -40, y: 120 }
            ],
            edges: [
                { source: 'A', target: 'B', weight: 4, label: '4', directed: true },
                { source: 'B', target: 'C', weight: 4, label: '4', directed: true },
                { source: 'C', target: 'A', weight: 4, label: '4', directed: true },
                { source: 'C', target: 'D', weight: 1, label: '1', directed: true },
                { source: 'D', target: 'C', weight: 1, label: '1', directed: true },
                { source: 'A', target: 'D', weight: 6, label: '6', directed: true }
            ]
        };

        const cycleBasisGraph = {
            name: 'Cycle Basis Grid',
            description: 'Undirected weighted square with a diagonal, producing two independent light cycles',
            directed: false,
            nodes: [
                { id: 'A', label: 'A', x: -160, y: -120 },
                { id: 'B', label: 'B', x: 120, y: -120 },
                { id: 'C', label: 'C', x: 120, y: 120 },
                { id: 'D', label: 'D', x: -160, y: 120 }
            ],
            edges: [
                { source: 'A', target: 'B', weight: 1, label: '1' },
                { source: 'B', target: 'C', weight: 1, label: '1' },
                { source: 'C', target: 'D', weight: 1, label: '1' },
                { source: 'D', target: 'A', weight: 1, label: '1' },
                { source: 'A', target: 'C', weight: 1, label: '1' }
            ]
        };

        const eulerGraph = {
            name: 'Euler Trail',
            description: 'Undirected graph with exactly two odd-degree vertices',
            directed: false,
            nodes: [
                { id: 'A', label: 'A', x: -180, y: 0 },
                { id: 'B', label: 'B', x: -60, y: -100 },
                { id: 'C', label: 'C', x: 100, y: -80 },
                { id: 'D', label: 'D', x: 120, y: 80 },
                { id: 'E', label: 'E', x: -40, y: 100 }
            ],
            edges: [
                { source: 'A', target: 'B', weight: 1, label: '' },
                { source: 'B', target: 'C', weight: 1, label: '' },
                { source: 'C', target: 'D', weight: 1, label: '' },
                { source: 'D', target: 'A', weight: 1, label: '' },
                { source: 'A', target: 'E', weight: 1, label: '' },
                { source: 'E', target: 'C', weight: 1, label: '' }
            ]
        };

        return {
            'graph/bfs': [
                ex('Social path', 'Loads the social network and searches Alice to Grace.', { source: 'Alice', target: 'Grace' }, 'social_network'),
                ex('Unreachable target', 'Loads disconnected components and searches across components.', { source: 'A', target: 'G' }, 'disconnected_components')
            ],
            'graph/dfs': [
                ex('Directed reachability', 'Loads the directed SCC graph and searches A to F.', { source: 'A', target: 'F' }, 'directed_cycle_scc'),
                ex('Social traversal', 'Loads the social network and traverses from Alice.', { source: 'Alice', target: '' }, 'social_network')
            ],
            'graph/dijkstra': [
                ex('City distances', 'Loads weighted city roads and starts from A.', { source: 'A' }, 'city_road_network'),
                ex('DAG shortest paths', 'Loads the weighted DAG and starts from S.', { source: 'S' }, 'weighted_dag')
            ],
            'graph/astar': [
                ex('Heuristic route', 'Loads a positioned graph so the A* heuristic is visible.', { source: 'A', target: 'F' }, null, astarGrid)
            ],
            'graph/bellman_ford': [
                ex('Negative edges', 'Loads a DAG with negative edges and starts from S.', { source: 'S' }, null, negativeGraph),
                ex('Weighted DAG', 'Loads the weighted DAG and starts from S.', { source: 'S' }, 'weighted_dag')
            ],
            'graph/spfa': [
                ex('Negative edges', 'Queue-based relaxation on a graph with negative edges.', { source: 'S' }, null, negativeGraph),
                ex('Weighted DAG', 'Shortest paths from S on a DAG.', { source: 'S' }, 'weighted_dag')
            ],
            'graph/johnson': [
                ex('Negative all-pairs', 'All-pairs shortest paths with Johnson reweighting.', {}, null, negativeGraph),
                ex('Sparse weighted DAG', 'All-pairs shortest paths on the weighted DAG.', {}, 'weighted_dag')
            ],
            'graph/edmonds_karp': [
                ex('Capacity network', 'BFS augmenting paths from S to T.', { source: 'S', target: 'T' }, null, flowNetwork)
            ],
            'graph/dinic': [
                ex('Level graph flow', 'Blocking flows on the same capacity network.', { source: 'S', target: 'T' }, null, flowNetwork)
            ],
            'graph/push_relabel': [
                ex('Preflow network', 'Saturates source edges, then pushes excess through admissible residual edges.', { source: 'S', target: 'T' }, null, flowNetwork)
            ],
            'graph/min_cost_max_flow': [
                ex('Costed network', 'Tracks shortest residual paths while minimizing flow cost.', { source: 'S', target: 'T' }, null, costFlowNetwork)
            ],
            'graph/hopcroft_karp': [
                ex('Worker-task matching', 'Loads a bipartite graph with three possible matches.', {}, null, matchingGraph)
            ],
            'graph/blossom_matching': [
                ex('Odd-cycle blossom', 'Contracts an odd cycle while finding a maximum matching in a general graph.', {}, null, blossomGraph)
            ],
            'graph/stoer_wagner': [
                ex('Global min cut', 'Contracts supernodes until the lightest separating cut is found.', {}, null, minCutGraph)
            ],
            'graph/gomory_hu_tree': [
                ex('Cut-equivalent tree', 'Builds a tree that answers all-pairs minimum-cut queries.', {}, null, minCutGraph)
            ],
            'graph/prim': [
                ex('City MST', 'Loads weighted city roads and grows an MST from A.', { source: 'A' }, 'city_road_network')
            ],
            'graph/kruskal': [
                ex('City MST', 'Loads weighted city roads for edge-sorted MST construction.', {}, 'city_road_network')
            ],
            'graph/topological_sort': [
                ex('Weighted DAG order', 'Loads a directed acyclic graph for topological sorting.', {}, 'weighted_dag')
            ],
            'graph/dag_longest_path': [
                ex('Critical path', 'Finds the longest weighted path from S to T in a DAG.', { source: 'S', target: 'T' }, 'weighted_dag')
            ],
            'graph/dominator_tree': [
                ex('Control-flow joins', 'Computes immediate dominators and dominance frontiers from entry S.', { source: 'S' }, null, controlFlowGraph)
            ],
            'graph/directed_mst': [
                ex('Cycle contraction', 'Builds a minimum rooted arborescence and expands a contracted directed cycle.', { source: 'R' }, null, directedMstGraph)
            ],
            'graph/yen_k_shortest_paths': [
                ex('Three alternatives', 'Generates ranked loopless alternatives from S to T.', { source: 'S', target: 'T', k: 3 }, null, kShortestGraph)
            ],
            'graph/suurballe_disjoint_paths': [
                ex('Disjoint backup routes', 'Finds two edge-disjoint low-cost routes from S to T.', { source: 'S', target: 'T' }, null, kShortestGraph)
            ],
            'graph/karp_minimum_mean_cycle': [
                ex('Low-average cycle', 'Computes DP walk costs and recovers the directed cycle with minimum average weight.', {}, null, meanCycleGraph)
            ],
            'graph/minimum_cycle_basis': [
                ex('Independent light cycles', 'Builds candidate cycles and selects a minimum independent cycle basis.', {}, null, cycleBasisGraph)
            ],
            'graph/euler_path': [
                ex('Euler trail', 'Consumes every edge exactly once with Hierholzer traversal.', { start: 'A' }, null, eulerGraph)
            ],
            'graph/cycle_detection': [
                ex('Cycle present', 'Loads a directed graph with two cyclic SCCs.', {}, 'directed_cycle_scc'),
                ex('Acyclic comparison', 'Loads a DAG so the no-cycle path is visible.', {}, 'weighted_dag')
            ],
            'graph/connected_components': [
                ex('Three components', 'Loads an undirected graph split into three components.', {}, 'disconnected_components')
            ],
            'graph/tarjan_scc': [
                ex('Two SCCs', 'Loads a directed graph with two strong components.', {}, 'directed_cycle_scc')
            ],
            'graph/kosaraju_scc': [
                ex('Two SCCs', 'Runs two DFS passes on the directed SCC graph.', {}, 'directed_cycle_scc')
            ],
            'graph/union_find': [
                ex('Component grouping', 'Loads disconnected components for union-find grouping.', {}, 'disconnected_components'),
                ex('MST-ready graph', 'Loads weighted city roads for edge unions.', {}, 'city_road_network')
            ],
            'graph/bipartite': [
                ex('Bipartite chains', 'Loads disconnected paths that satisfy bipartite coloring.', {}, 'disconnected_components')
            ],
            'graph/floyd_warshall': [
                ex('All-pairs city paths', 'Loads weighted city roads for all-pairs shortest paths.', {}, 'city_road_network'),
                ex('DAG all-pairs paths', 'Loads the weighted DAG for directed all-pairs paths.', {}, 'weighted_dag')
            ],
            'graph/bridges_articulation': [
                ex('Chain bridges', 'Loads disconnected chains with clear bridge edges.', {}, 'disconnected_components')
            ],
            'array/bubble_sort': [
                ex('Mixed values', 'Unsorted numeric list with several adjacent swaps.', { values: '5,1,4,2,8' }),
                ex('Nearly sorted', 'Shows early exit after only a small correction.', { values: '1,2,4,3,5' }),
                ex('Duplicates', 'Checks stable behavior with repeated values.', { values: '4,2,4,1,2' })
            ],
            'array/quick_sort': [
                ex('Partition demo', 'Classic pivot partitioning example.', { values: '9,3,7,1,8,2,5' }),
                ex('Reverse ordered', 'Worst-direction input for many pivot choices.', { values: '9,8,7,6,5,4,3' }),
                ex('Repeated values', 'Shows how equals move around the pivot.', { values: '5,3,5,2,8,5,1' })
            ],
            'array/merge_sort': [
                ex('Balanced splits', 'Even-sized list for divide and merge steps.', { values: '8,3,7,4,9,2,6,5' }),
                ex('Odd length', 'Shows uneven recursive splitting.', { values: '10,1,9,2,8,3,7' })
            ],
            'array/heap_sort': [
                ex('Heapify demo', 'Builds a max heap with several sift-downs.', { values: '4,10,3,5,1,8,2' }),
                ex('Sorted tail growth', 'Shows repeated max extraction clearly.', { values: '12,11,13,5,6,7' })
            ],
            'array/binary_search': [
                ex('Found middle', 'Target is present near the center.', { values: '1,2,4,5,8,12,16', target: '8' }),
                ex('Missing value', 'Target is absent but inside the numeric range.', { values: '1,2,4,5,8,12,16', target: '7' }),
                ex('Boundary target', 'Target is the first item.', { values: '3,6,9,12,15', target: '3' })
            ],
            'dp/lcs': [
                ex('Simple subsequence', 'Small strings with LCS ace.', { text_a: 'abcde', text_b: 'ace' }),
                ex('Classic LCS', 'Textbook example with length 4.', { text_a: 'AGGTAB', text_b: 'GXTXAYB' })
            ],
            'dp/edit_distance': [
                ex('Kitten to sitting', 'Classic Levenshtein distance 3.', { text_a: 'kitten', text_b: 'sitting' }),
                ex('Flaw to lawn', 'Short edit path with substitutions and insertions.', { text_a: 'flaw', text_b: 'lawn' })
            ],
            'dp/knapsack': [
                ex('Small capacity', 'Best value comes from combining item 0 and 1.', { weights: '2,3,4', capacity: '5', values: '3,4,5' }),
                ex('Budget tradeoff', 'Shows skip/take choices across several capacities.', { weights: '1,3,4,5', capacity: '7', values: '1,4,5,7' })
            ],
            'dp/lis': [
                ex('Classic LIS', 'Expected LIS length is 4.', { values: '10,9,2,5,3,7,101,18' }),
                ex('Already increasing', 'Every item extends the subsequence.', { values: '1,2,3,4,5,6' }),
                ex('With drops', 'Several local decreases before the best sequence.', { values: '3,4,-1,0,6,2,3' })
            ],
            'dp/coin_change': [
                ex('Few coins', 'Classic minimum-coin example with amount 11.', { coins: '1,2,5', amount: '11' }),
                ex('Unreachable gap', 'Shows when a target amount cannot be formed.', { coins: '2,4,6', amount: '7' })
            ],
            'dp/matrix_chain_multiplication': [
                ex('Textbook chain', 'Classic dimensions with optimal cost 15125.', { dimensions: '30,35,15,5,10,20,25' }),
                ex('Small chain', 'Three matrices with a clear split choice.', { dimensions: '10,30,5,60' })
            ],
            'dp/fibonacci_dp': [
                ex('F(10)', 'Builds the DP table up to 10.', { n: '10' }),
                ex('F(15)', 'A slightly longer Fibonacci table.', { n: '15' })
            ],
            'dp/subset_sum': [
                ex('Reachable target', 'Finds a subset that sums to 9.', { values: '3,34,4,12,5,2', target: '9' }),
                ex('Unreachable target', 'Shows a false final cell.', { values: '2,4,6,10', target: '17' })
            ],
            'dp/word_break': [
                ex('Segmentable text', 'Splits the text into dictionary words.', { text: 'leetcode', words: 'leet,code,lee,tcode' }),
                ex('Multiple words', 'Shows a longer segmentation path.', { text: 'catsanddog', words: 'cat,cats,and,sand,dog' })
            ],
            'dp/hungarian': [
                ex('Worker assignment', 'Finds the minimum-cost unique worker-task assignment.', { costs: '9,2,7;6,4,3;5,8,1' }),
                ex('Four tasks', 'Rectangular assignment with more tasks than workers.', { costs: '4,1,3,6;2,0,5,3;3,2,2,4' })
            ],
            'tree/bst': [
                ex('Balanced-ish insertions', 'Builds a readable binary search tree.', { values: '50,30,70,20,40,60,80' }),
                ex('Skewed insertions', 'Shows the worst-case chain shape.', { values: '10,20,30,40,50' })
            ],
            'tree/avl': [
                ex('Rotation sequence', 'Triggers AVL rotations while inserting.', { values: '30,20,10,25,40,50' }),
                ex('Mixed balance', 'Builds a larger balanced AVL tree.', { values: '10,20,30,40,50,25' }),
                ex('Delete and rebalance', 'Deletes nodes after insertion and reports AVL rebalancing.', { values: '20,10,30,5,15,25,40,2,7', delete_values: '30,10' })
            ],
            'tree/red_black': [
                ex('Recolor and rotate', 'Triggers common red-black balancing cases.', { values: '10,20,30,15,25,5,1' }),
                ex('Larger tree', 'More insertions for multiple fix-up passes.', { values: '41,38,31,12,19,8' }),
                ex('Delete fix-up', 'Deletes nodes and shows red-black repair cases.', { values: '20,10,30,5,15,25,40,1,7', delete_values: '5,30' })
            ],
            'tree/treap': [
                ex('Priority rotations', 'Explicit priorities force both BST insertion and heap rotations.', { values: '50,30,70,20,40,60,80', priorities: '50,30,40,10,35,20,60' }),
                ex('Right-heavy repair', 'Shows right rotations after low-priority inserts.', { values: '10,20,30,40,50', priorities: '50,40,30,20,10' })
            ],
            'tree/btree': [
                ex('Order 3 splits', 'Small order causes node splits quickly.', { values: '10,20,5,15,25,30,35', order: '3' }),
                ex('Order 4 wider nodes', 'Shows fewer splits with a wider node.', { values: '8,9,10,11,15,20,17', order: '4' })
            ],
            'tree/bplus': [
                ex('Leaf splits', 'Shows leaf-level splits and linking.', { values: '10,20,5,15,25,30,35', order: '3' }),
                ex('Range-friendly leaves', 'More keys per internal node.', { values: '3,7,9,12,15,18,21,24', order: '4' })
            ],
            'tree/heap': [
                ex('Max heap', 'Builds a max heap by sift-up.', { values: '4,10,3,5,1,8,2', type: 'max' }),
                ex('Min heap', 'Builds a min heap from the same values.', { values: '4,10,3,5,1,8,2', type: 'min' })
            ],
            'tree/fenwick_tree': [
                ex('Prefix sum', 'Builds BIT and queries prefix sum through index 5.', { values: '1,7,3,0,7,8,3,2,6,2', query_index: '5' }),
                ex('Short updates', 'Small array with a clear query path.', { values: '2,4,5,7', query_index: '3' })
            ],
            'tree/segment_tree': [
                ex('Range sum', 'Builds a segment tree and queries values from index 1 to 4.', { values: '2,1,5,3,4,7', query_left: '1', query_right: '4' }),
                ex('Point update', 'Runs a range query, then updates one leaf and refreshes ancestors.', { values: '4,8,6,1,3,5', query_left: '2', query_right: '5', update_index: '3', update_value: '10' })
            ],
            'tree/lca': [
                ex('Sibling leaves', 'Finds the common ancestor of D and E in the balanced tree.', { source: 'A', node_a: 'D', node_b: 'E' }, 'binary_tree'),
                ex('Across subtrees', 'Lifts nodes from different branches until they meet at the root.', { source: 'A', node_a: 'D', node_b: 'G' }, 'binary_tree')
            ],
            'tree/heavy_light_decomposition': [
                ex('Path sum', 'Decomposes the balanced tree and queries the path from D to G.', { source: 'A', node_a: 'D', node_b: 'G', values: '1,2,3,4,5,6,7' }, 'binary_tree'),
                ex('Same chain', 'Shows a query that stays mostly inside one heavy chain.', { source: 'A', node_a: 'D', node_b: 'B', values: '1,2,3,4,5,6,7' }, 'binary_tree')
            ],
            'tree/trie': [
                ex('Shared prefixes', 'Words share app/ap and ba prefixes.', { words: 'apple,app,apt,bat,bar', query_prefix: 'ap' }),
                ex('Lookup-style words', 'Compact vocabulary with overlapping starts.', { words: 'cat,car,cart,dog,dot', query_prefix: 'car' }),
                ex('Delete and count', 'Deletes a word while preserving longer prefixes and reports prefix counts.', { words: 'app,apple,apt,bat', query_prefix: 'ap', delete_words: 'app' })
            ],
            'tree/aho_corasick': [
                ex('Classic multi-match', 'Patterns overlap inside the text.', { patterns: 'he,she,his,hers', text: 'ushers' }),
                ex('Short word scan', 'Several words appear in a compact sentence.', { patterns: 'cat,car,cart', text: 'thecartandcat' })
            ],
            'tree/huffman': [
                ex('Frequency contrast', 'Classic Huffman coding example.', { text: 'aaabbc' }),
                ex('Sentence sample', 'More characters with varied frequencies.', { text: 'visual algorithm lab' })
            ],
            'tree/tree_bfs': [
                ex('Binary tree from root', 'Loads the balanced tree and starts at A.', { source: 'A' }, 'binary_tree'),
                ex('Large tree traversal', 'Loads the 15-node tree and starts at N1.', { source: 'N1' }, 'large_tree')
            ],
            'tree/tree_dfs': [
                ex('Binary tree DFS', 'Loads the balanced tree and starts at A.', { source: 'A' }, 'binary_tree'),
                ex('Unbalanced DFS', 'Loads a skewed tree for deep traversal.', { source: 'A' }, 'unbalanced_tree')
            ],
            'tree/level_order': [
                ex('Balanced levels', 'Loads the balanced tree and visits level by level.', { source: 'A' }, 'binary_tree'),
                ex('Large levels', 'Loads a 15-node binary tree for multiple levels.', { source: 'N1' }, 'large_tree')
            ],
            'string/kmp': [
                ex('Classic pattern', 'Searches for a repeated substring in a short text.', { text: 'abxabcabcaby', pattern: 'abcaby' }),
                ex('Multiple matches', 'Pattern appears more than once.', { text: 'aaaaa', pattern: 'aaa' })
            ],
            'string/rabin_karp': [
                ex('Rolling hash search', 'Verifies a hash hit before confirming the match.', { text: 'ababcabcabababd', pattern: 'ababd' }),
                ex('Collision check', 'Shows repeated hash rolling across a short string.', { text: 'aaaaab', pattern: 'aaab' })
            ],
            'string/boyer_moore': [
                ex('Right-to-left compare', 'Highlights the bad-character shift rule.', { text: 'HERE IS A SIMPLE EXAMPLE', pattern: 'EXAMPLE' }),
                ex('Compact scan', 'A shorter text with one clear match.', { text: 'FIND IN A HAYSTACK', pattern: 'HAY' })
            ],
            'string/z_algorithm': [
                ex('Prefix overlap', 'Builds the Z array on a repeated prefix text.', { text: 'aabxaabxcaabxaabxay', pattern: 'aabxa' }),
                ex('Linear search', 'Finds all matches by scanning the combined string.', { text: 'aaaaa', pattern: 'aaa' })
            ],
            'string/manacher': [
                ex('Odd palindrome', 'Finds bab or aba as the longest palindrome.', { text: 'babad' }),
                ex('Even palindrome', 'Finds the even-length palindrome bb.', { text: 'cbbd' })
            ],
            'string/suffix_array': [
                ex('Banana search', 'Builds suffix ranks and searches ana.', { text: 'banana', pattern: 'ana' }),
                ex('Repeated prefix', 'Several repeated suffix prefixes make rank updates visible.', { text: 'mississippi', pattern: 'issi' })
            ],
            'string/suffix_automaton': [
                ex('Clone split', 'Builds a suffix automaton and shows clone-state link rewiring.', { text: 'abcbc', query: 'bcb' }),
                ex('Repeated substrings', 'Indexes banana and reports substring statistics.', { text: 'banana', query: 'ana' })
            ],
            'array/kadane': [
                ex('Profit window', 'Classic maximum subarray example.', { values: '-2,1,-3,4,-1,2,1,-5,4' }),
                ex('All negative', 'Returns the largest single element.', { values: '-8,-3,-6,-2,-5,-4' })
            ],
            'array/sparse_table': [
                ex('Range minimum', 'Preprocesses intervals and answers an O(1) range minimum query.', { values: '7,2,3,0,5,10,3,12,18', query_left: '1', query_right: '6', operation: 'min' }),
                ex('Range maximum', 'Uses the same sparse table structure for a static range maximum query.', { values: '4,6,1,9,3,8,2', query_left: '2', query_right: '5', operation: 'max' })
            ]
        };
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

        this._renderNextAlgorithms(algo);
    }

    _renderNextAlgorithms(algo) {
        const container = document.getElementById('edu-next');
        if (!container) return;

        container.innerHTML = '';
        const currentKey = `${algo.category}/${algo.name}`;
        const recommendations = this._getNextAlgorithms(currentKey).slice(0, 4);

        recommendations.forEach(item => {
            const nextAlgo = this._findAlgorithmByKey(item.key);
            if (!nextAlgo) return;

            const button = document.createElement('button');
            button.className = 'edu-next-item';
            button.type = 'button';
            button.dataset.key = item.key;

            const name = document.createElement('span');
            name.className = 'edu-next-name';
            name.textContent = `${nextAlgo.emoji || ''} ${nextAlgo.name}`.trim();

            const reason = document.createElement('span');
            reason.className = 'edu-next-reason';
            reason.textContent = item.reason;

            button.appendChild(name);
            button.appendChild(reason);
            button.addEventListener('click', () => this._selectAlgorithmByKey(item.key));
            container.appendChild(button);
        });

        if (!container.children.length) {
            const fallback = document.createElement('div');
            fallback.className = 'quick-access-empty';
            fallback.textContent = 'No related algorithms available.';
            container.appendChild(fallback);
        }
    }

    _getNextAlgorithms(key) {
        const explicit = {
            'graph/bfs': [
                ['graph/dfs', 'Traversal'],
                ['graph/dijkstra', 'Weighted']
            ],
            'graph/dfs': [
                ['graph/topological_sort', 'DAG'],
                ['graph/tarjan_scc', 'SCC']
            ],
            'graph/dijkstra': [
                ['graph/bellman_ford', 'Negative edges'],
                ['graph/astar', 'Heuristic'],
                ['graph/floyd_warshall', 'All pairs']
            ],
            'graph/bellman_ford': [
                ['graph/spfa', 'Queue variant'],
                ['graph/johnson', 'All pairs']
            ],
            'graph/edmonds_karp': [
                ['graph/dinic', 'Faster flow']
            ],
            'graph/prim': [
                ['graph/kruskal', 'Edge sorted']
            ],
            'graph/kruskal': [
                ['graph/union_find', 'DSU']
            ],
            'string/kmp': [
                ['string/rabin_karp', 'Hashing'],
                ['string/boyer_moore', 'Skip rule'],
                ['string/z_algorithm', 'Prefix table']
            ],
            'string/rabin_karp': [
                ['string/kmp', 'Deterministic'],
                ['string/boyer_moore', 'Right-to-left']
            ],
            'array/bubble_sort': [
                ['array/merge_sort', 'Stable sort'],
                ['array/quick_sort', 'Partition']
            ],
            'array/quick_sort': [
                ['array/merge_sort', 'Guaranteed split'],
                ['array/heap_sort', 'In-place heap']
            ],
            'array/binary_search': [
                ['array/merge_sort', 'Sorted input'],
                ['tree/bst', 'Tree lookup']
            ],
            'array/kadane': [
                ['dp/lis', 'Sequence DP'],
                ['dp/subset_sum', 'Subset DP']
            ],
            'dp/fibonacci_dp': [
                ['dp/coin_change', '1D table'],
                ['dp/lis', 'Sequence DP']
            ],
            'dp/lcs': [
                ['dp/edit_distance', '2D table'],
                ['string/kmp', 'String matching']
            ],
            'dp/knapsack': [
                ['dp/subset_sum', 'Feasibility'],
                ['dp/coin_change', 'Unbounded']
            ],
            'tree/bst': [
                ['tree/avl', 'Balanced'],
                ['tree/red_black', 'Balanced']
            ],
            'tree/trie': [
                ['tree/aho_corasick', 'Multi-pattern'],
                ['string/kmp', 'Pattern match']
            ]
        };

        const result = [];
        const seen = new Set([key]);
        (explicit[key] || []).forEach(([candidateKey, reason]) => {
            if (this._findAlgorithmByKey(candidateKey) && !seen.has(candidateKey)) {
                seen.add(candidateKey);
                result.push({ key: candidateKey, reason });
            }
        });

        const currentAlgo = this._findAlgorithmByKey(key);
        if (!currentAlgo) return result;

        const currentTags = new Set(this._getAlgorithmTagIds(currentAlgo));
        this.algorithms.forEach(candidate => {
            const candidateKey = `${candidate.category}/${candidate.name}`;
            if (seen.has(candidateKey)) return;
            const overlap = this._getAlgorithmTagIds(candidate).filter(tag => currentTags.has(tag));
            if (!overlap.length) return;
            seen.add(candidateKey);
            result.push({
                key: candidateKey,
                reason: this._formatTagLabel(overlap[0])
            });
        });

        return result;
    }

    _formatTagLabel(tagId) {
        const tag = this.algorithmTags.find(item => item.id === tagId);
        return tag ? tag.label : this._formatStateKey(tagId);
    }

    async _generateRandomParams(algo) {
        try {
            const graph = this.editor.toJSON();
            const resp = await fetch('/api/algorithms/random-params', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    algorithm_key: `${algo.category}/${algo.name}`,
                    graph: { nodes: graph.nodes, edges: graph.edges },
                    complexity: null  // random complexity
                })
            });
            if (!resp.ok) throw new Error('Failed');
            const data = await resp.json();
            const params = data.params;

            // Fill form fields
            Object.entries(params).forEach(([name, value]) => {
                const el = document.getElementById(`param-${name}`);
                if (el) {
                    el.value = value;
                    // Trigger change event for select elements
                    el.dispatchEvent(new Event('change'));
                }
            });
            showToast(`Random params (${data.complexity})`, 'info');
        } catch (e) {
            showToast('Failed to generate random params', 'error');
        }
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
        this._clearParamErrors();

        if (!this.selectedAlgorithm) {
            this._showParamError('Please select an algorithm first');
            showToast('Please select an algorithm first', 'error');
            return false;
        }

        const algo = this.algorithms.find(a => `${a.category}/${a.name}` === this.selectedAlgorithm);
        if (!algo) return false;

        const params = this._collectParams();
        for (const param of (algo.parameters || [])) {
            if (param.required && !params[param.name]) {
                const message = `Parameter '${param.name}' is required`;
                this._showParamError(message, [param.name]);
                showToast(`Parameter '${param.description || param.name}' is required`, 'error');
                const el = document.getElementById(`param-${param.name}`);
                if (el) el.focus();
                return false;
            }
        }

        const graph = this.editor.toJSON();

        // Skip empty-graph check only for algorithms that build their own structure.
        const algo_meta = this.algorithms.find(a => `${a.category}/${a.name}` === this.selectedAlgorithm);
        const buildsStructure = algo_meta && (algo_meta.builds_structure || algo_meta.requires_graph === false);
        if (!graph.nodes || graph.nodes.length === 0) {
            if (!buildsStructure) {
                this._showParamError('Graph has no nodes');
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

    _setupTimelineControls() {
        const startBtn = document.getElementById('btn-timeline-start');
        const prevBtn = document.getElementById('btn-timeline-prev');
        const playBtn = document.getElementById('btn-timeline-play');
        const nextBtn = document.getElementById('btn-timeline-next');
        const endBtn = document.getElementById('btn-timeline-end');
        const slider = document.getElementById('timeline-slider');
        const exportBtn = document.getElementById('btn-export-run');
        const keyToggle = document.getElementById('timeline-key-steps');
        const bookmarkPrevBtn = document.getElementById('btn-bookmark-prev');
        const bookmarkToggleBtn = document.getElementById('btn-bookmark-toggle');
        const bookmarkNextBtn = document.getElementById('btn-bookmark-next');
        const bookmarkToggle = document.getElementById('timeline-bookmark-steps');

        if (!startBtn || !prevBtn || !playBtn || !nextBtn || !endBtn || !slider) return;

        startBtn.addEventListener('click', () => this._renderTimelineIndex(0));
        prevBtn.addEventListener('click', () => this._renderTimelineIndex(this._timelineTargetIndex(-1)));
        nextBtn.addEventListener('click', () => this._renderTimelineIndex(this._timelineTargetIndex(1)));
        endBtn.addEventListener('click', () => this._renderTimelineIndex(this.timeline.steps.length));

        playBtn.addEventListener('click', () => {
            if (this.timeline.playbackActive) {
                this._stopTimelinePlayback();
            } else {
                this._startTimelinePlayback();
            }
        });

        const scrubToClientX = (clientX) => {
            if (slider.disabled || !this._timelineCanReview()) return;
            const rect = slider.getBoundingClientRect();
            if (!rect.width) return;

            const min = Number(slider.min || 0);
            const max = Number(slider.max || 0);
            const step = Number(slider.step || 1) || 1;
            const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
            const value = Math.max(min, Math.min(max, Math.round((min + ratio * (max - min)) / step) * step));

            this._stopTimelinePlayback();
            this._renderTimelineIndex(value);
        };

        const previewAtClientX = (clientX) => {
            if (slider.disabled || !this._timelineCanReview()) return;
            const rect = slider.getBoundingClientRect();
            if (!rect.width) return;

            const max = Number(slider.max || 0);
            const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
            const index = Math.max(0, Math.min(max, Math.round(ratio * max)));
            this._showTimelinePreview(index, rect, ratio);
        };

        let activeTimelinePointerId = null;
        slider.addEventListener('pointerdown', (e) => {
            if (e.button !== 0 || slider.disabled) return;
            activeTimelinePointerId = e.pointerId;
            try {
                slider.setPointerCapture(e.pointerId);
            } catch (err) {}
            previewAtClientX(e.clientX);
            scrubToClientX(e.clientX);
            e.preventDefault();
        });
        slider.addEventListener('pointermove', (e) => {
            previewAtClientX(e.clientX);
            if (activeTimelinePointerId === e.pointerId) scrubToClientX(e.clientX);
            e.preventDefault();
        });
        const stopPointerScrub = (e) => {
            if (activeTimelinePointerId !== e.pointerId) return;
            activeTimelinePointerId = null;
            try {
                slider.releasePointerCapture(e.pointerId);
            } catch (err) {}
        };
        slider.addEventListener('pointerup', stopPointerScrub);
        slider.addEventListener('pointercancel', stopPointerScrub);
        slider.addEventListener('pointerleave', (e) => {
            if (activeTimelinePointerId !== e.pointerId) this._hideTimelinePreview();
        });
        slider.addEventListener('focus', () => this._showTimelinePreview(this.timeline.currentIndex));
        slider.addEventListener('blur', () => this._hideTimelinePreview());

        slider.addEventListener('input', (e) => {
            this._stopTimelinePlayback();
            this._renderTimelineIndex(parseInt(e.target.value, 10));
        });

        if (keyToggle) {
            keyToggle.addEventListener('change', (e) => {
                this.timeline.keyOnly = e.target.checked;
                this._syncTimelineUI();
            });
        }

        if (bookmarkPrevBtn) {
            bookmarkPrevBtn.addEventListener('click', () => this._renderTimelineIndex(this._bookmarkTargetIndex(-1)));
        }
        if (bookmarkToggleBtn) {
            bookmarkToggleBtn.addEventListener('click', () => this._toggleTimelineBookmark());
        }
        if (bookmarkNextBtn) {
            bookmarkNextBtn.addEventListener('click', () => this._renderTimelineIndex(this._bookmarkTargetIndex(1)));
        }
        if (bookmarkToggle) {
            bookmarkToggle.addEventListener('change', (e) => {
                this.timeline.bookmarkOnly = e.target.checked;
                this._syncTimelineUI();
            });
        }

        if (exportBtn) {
            exportBtn.addEventListener('click', () => this._exportRun());
        }

        this._syncTimelineUI();
    }

    _setupLogFilters() {
        const search = document.getElementById('log-search');
        const phase = document.getElementById('log-phase-filter');
        const clear = document.getElementById('btn-clear-log-filter');
        const copy = document.getElementById('btn-copy-log');
        const exportLog = document.getElementById('btn-export-log');

        if (search) {
            search.addEventListener('input', (e) => {
                this.logFilter.query = e.target.value || '';
                this._applyLogFilters();
            });
        }

        if (phase) {
            phase.addEventListener('change', (e) => {
                this.logFilter.phase = e.target.value || 'all';
                this._applyLogFilters();
            });
        }

        if (clear) {
            clear.addEventListener('click', () => {
                this._resetLogFilters();
                this._applyLogFilters();
            });
        }

        if (copy) {
            copy.addEventListener('click', () => this._copyFilteredLog());
        }

        if (exportLog) {
            exportLog.addEventListener('click', () => this._exportFilteredLog());
        }

        this._applyLogFilters();
    }

    _setupRunHistory() {
        const save = document.getElementById('btn-save-run');
        if (save) {
            save.addEventListener('click', () => this._saveCurrentRunRecord());
        }
    }

    _resetLogFilters() {
        this.logFilter = { query: '', phase: 'all' };
        const search = document.getElementById('log-search');
        const phase = document.getElementById('log-phase-filter');
        if (search) search.value = '';
        if (phase) phase.value = 'all';
    }

    _setupPanelToggles() {
        document.querySelectorAll('[data-panel-toggle]').forEach(button => {
            const panelId = button.dataset.panelToggle;
            if (!panelId) return;
            button.addEventListener('click', () => {
                this._setPanelCollapsed(panelId, !this.collapsedPanels.has(panelId));
            });
            this._syncPanelCollapse(panelId);
        });
    }

    _setPanelCollapsed(panelId, collapsed) {
        if (collapsed) {
            this.collapsedPanels.add(panelId);
        } else {
            this.collapsedPanels.delete(panelId);
        }
        this._syncPanelCollapse(panelId);
    }

    _syncPanelCollapse(panelId) {
        const panel = document.getElementById(panelId);
        const button = document.querySelector(`[data-panel-toggle="${panelId}"]`);
        const collapsed = this.collapsedPanels.has(panelId);

        if (panel) panel.classList.toggle('is-collapsed', collapsed);
        if (button) {
            button.textContent = collapsed ? '+' : '-';
            button.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
            button.title = `${collapsed ? 'Expand' : 'Collapse'} ${this._panelLabel(panelId)}`;
        }
    }

    _panelLabel(panelId) {
        const labels = {
            'run-summary': 'Run Summary',
            'step-detail': 'Step Detail',
            'state-panel': 'State',
            'step-log': 'Step Log'
        };
        return labels[panelId] || this._formatStateKey(panelId);
    }

    loadRunRecord(record) {
        const normalized = this._normalizeRunRecord(record);
        if (!normalized) {
            showToast('Invalid run record', 'error');
            return false;
        }

        const { algorithmKey, params, baseGraph, steps, startedAt, finishedAt, visualization, runMetrics, bookmarks } = normalized;
        const algo = this.algorithms.find(a => `${a.category}/${a.name}` === algorithmKey) || null;

        this._stopTimelinePlayback();
        this.isRunning = false;
        this.isPaused = false;
        this._pendingStepPause = false;

        this.searchQuery = '';
        const searchInput = document.getElementById('algorithm-search');
        if (searchInput) searchInput.value = '';
        this.categoryCollapsed.clear();
        this._renderAlgorithmCards();

        if (algo) {
            const card = document.querySelector(`.algo-card[data-key="${algorithmKey}"]`);
            if (card) this._selectAlgorithm(algo, card);
        } else if (visualization) {
            this.selectedAlgorithm = algorithmKey;
            this.selectedVisualization = visualization;
            if (this.visualizer && this.visualizer.setVisualizationMode) {
                this.visualizer.setVisualizationMode(visualization);
            }
            if (visualization === 'graph' && this.editor && this.editor.setStructureType) {
                if (baseGraph.directed && baseGraph.root_id) {
                    this.editor.setStructureType('tree');
                } else {
                    this.editor.setStructureType('graph');
                }
            }
        }

        this.timeline.baseGraph = JSON.parse(JSON.stringify(baseGraph));
        this.timeline.algorithmKey = algorithmKey;
        this.timeline.params = JSON.parse(JSON.stringify(params));
        this.timeline.startedAt = startedAt || null;
        this.timeline.finishedAt = finishedAt || null;
        this.timeline.steps = JSON.parse(JSON.stringify(steps));
        this.timeline.currentIndex = this.timeline.steps.length;
        this.timeline.completed = true;
        this.timeline.playbackTimer = null;
        this.timeline.playbackActive = false;
        this.timeline.bookmarkOnly = false;
        this.timeline.bookmarks = new Set(bookmarks || []);
        this.runMetrics = runMetrics || this._computeRunMetrics(this.timeline.steps);

        this.editor.lockLayout();
        this.editor.restoreSnapshot(this.timeline.baseGraph, { save: false });
        this.visualizer.storeOriginalLabels();
        this.editor.setMode('view');

        const paramEntries = Object.entries(params || {});
        paramEntries.forEach(([name, value]) => {
            const el = document.getElementById(`param-${name}`);
            if (el) {
                el.value = value;
                el.dispatchEvent(new Event('change'));
            }
        });

        this._clearStepLog({ resetFilters: true });
        this.timeline.steps.forEach((step, index) => {
            if (step && step.message) {
                this._appendToLog(step.message, step.phase || 'explore', index);
            }
        });

        if (this.timeline.steps.length > 0) {
            this._renderTimelineIndex(this.timeline.steps.length);
        } else {
            this._clearState();
            this._syncTimelineUI();
        }
        this._renderRunSummary();
        this._renderRunHistory();

        this._setStatus('replay', 'Imported');
        showToast('Run record imported', 'success');
        return true;
    }

    _normalizeRunRecord(record) {
        if (!record || typeof record !== 'object') return null;

        const algorithmKey = record.algorithm_key || record.algorithmKey;
        const baseGraph = record.base_graph || record.baseGraph;
        const steps = record.steps || record.timeline || [];
        const params = record.params || {};
        const startedAt = record.started_at || record.startedAt || null;
        const finishedAt = record.finished_at || record.finishedAt || null;
        const visualization = record.visualization || record.visualization_mode || null;
        const runMetrics = record.run_metrics || record.runMetrics || null;
        const bookmarks = this._normalizeTimelineBookmarks(record.bookmarks || record.timeline_bookmarks || [], steps.length);

        if (!algorithmKey || !baseGraph || !Array.isArray(steps) || steps.length === 0) {
            return null;
        }

        return {
            algorithmKey,
            baseGraph,
            params,
            steps,
            startedAt,
            finishedAt,
            visualization,
            runMetrics,
            bookmarks
        };
    }

    _normalizeTimelineBookmarks(bookmarks, stepCount = this.timeline.steps.length) {
        if (!Array.isArray(bookmarks)) return [];
        return [...new Set(bookmarks
            .map(value => Number(value))
            .filter(value => Number.isInteger(value) && value > 0 && value <= stepCount))]
            .sort((a, b) => a - b);
    }

    _findAlgorithmByKey(key) {
        return this.algorithms.find(a => `${a.category}/${a.name}` === key) || null;
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

        this._startTimelineCapture(graph, this.selectedAlgorithm, params);

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

        this._clearStepLog({ resetFilters: true });
        this._clearState();
        this._clearParamErrors();
        this._syncTimelineUI();
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
            this._startTimelineCapture(graph, this.selectedAlgorithm, params);
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
            this._clearStepLog({ resetFilters: true });
            this._clearState();
            this._clearParamErrors();
            this._syncTimelineUI();

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
        const baseGraph = this.timeline.baseGraph
            ? JSON.parse(JSON.stringify(this.timeline.baseGraph))
            : null;
        this.isRunning = false;
        this.isPaused = false;
        this._pendingStepPause = false;
        this._clearTimeline();
        this.editor.unlockLayout();
        if (this.visualizer && this.visualizer.setVisualizationMode) {
            this.visualizer.setVisualizationMode(this.selectedVisualization || 'graph');
            if (this.selectedVisualization !== 'graph' && this.visualizer.clearStructure) {
                this.visualizer.clearStructure();
            }
        }
        this.editor.setMode('edit');
        if (baseGraph) {
            this.editor.restoreSnapshot(baseGraph, { save: false });
            this.visualizer.storeOriginalLabels();
        } else {
            this.editor.resetAllStyles();
            this.visualizer.restoreOriginalLabels();
        }

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
        this._clearStepLog({ resetFilters: true });
        this._clearState();
        this._clearParamErrors();
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
            this.timeline.steps.push(data);
            this.timeline.currentIndex = this.timeline.steps.length;
            this._updateRunMetrics();
            this._syncTimelineUI();
            this.visualizer.applyStep(data);
            if (data.message) {
                this._appendToLog(data.message, data.phase || 'explore', this.timeline.steps.length - 1);
            }
            if (data.state) {
                this._renderState(data.state);
            }
            this._renderStepDetail(data, this.timeline.steps.length, this.timeline.steps.length);
            this._highlightTimelineLog(this.timeline.steps.length - 1);
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
            this.timeline.completed = true;
            this.timeline.finishedAt = new Date().toISOString();
            this.timeline.currentIndex = this.timeline.steps.length;
            this._updateRunMetrics();
            this._stopTimelinePlayback();
            this.editor.setMode('view');
            this._setStatus('finished', 'Finished');
            this._updateButtonStates();
            this._syncTimelineUI();
            this._renderRunHistory();
            this._appendToLog('Algorithm completed!', 'result');
            showToast('Algorithm finished!', 'success');
        });

        this.ws.on('paused', () => {
            this.isPaused = true;
            this._setStatus('paused', 'Paused');
            this._updateButtonStates();
            this._syncTimelineUI();
        });

        this.ws.on('reset_done', () => {
            this.isRunning = false;
            this.isPaused = false;
            this._clearTimeline();
            this.editor.unlockLayout();
            this.editor.setMode('edit');
            this._setStatus('', 'Ready');
            this._updateButtonStates();
            this._clearState();
            this._clearParamErrors();
        });

        this.ws.on('error', (data) => {
            const message = data.message || 'Algorithm error';
            this._showParamError(message, this._inferErrorFields(message));
            showToast(message, 'error');
            this._appendToLog(`Error: ${message}`, 'result');
            this.isRunning = false;
            this.isPaused = false;
            this._pendingStepPause = false;
            this.timeline.completed = false;
            this._stopTimelinePlayback();
            this.editor.unlockLayout();
            this._setStatus('', 'Error');
            this._updateButtonStates();
            this._updateRunMetrics();
            this._syncTimelineUI();
        });
    }

    _startTimelineCapture(baseGraph, algorithmKey, params) {
        this._stopTimelinePlayback();
        this._hideTimelinePreview();
        this.timeline.baseGraph = JSON.parse(JSON.stringify(baseGraph));
        this.timeline.algorithmKey = algorithmKey || this.selectedAlgorithm;
        this.timeline.params = JSON.parse(JSON.stringify(params || {}));
        this.timeline.startedAt = new Date().toISOString();
        this.timeline.finishedAt = null;
        this.timeline.steps = [];
        this.timeline.currentIndex = 0;
        this.timeline.completed = false;
        this.timeline.bookmarkOnly = false;
        this.timeline.bookmarks = new Set();
        this.runMetrics = this._createEmptyRunMetrics();
        this._highlightTimelineLog(-1);
        this._clearStepDetail();
        this._renderRunSummary();
        this._syncTimelineUI();
        this._renderRunHistory();
    }

    _clearTimeline() {
        this._stopTimelinePlayback();
        this._hideTimelinePreview();
        this.timeline.baseGraph = null;
        this.timeline.algorithmKey = null;
        this.timeline.params = {};
        this.timeline.startedAt = null;
        this.timeline.finishedAt = null;
        this.timeline.steps = [];
        this.timeline.currentIndex = 0;
        this.timeline.completed = false;
        this.timeline.bookmarkOnly = false;
        this.timeline.bookmarks = new Set();
        this.runMetrics = this._createEmptyRunMetrics();
        this._highlightTimelineLog(-1);
        this._clearStepDetail();
        this._clearRunSummary();
        this._syncTimelineUI();
        this._renderRunHistory();
    }

    _createEmptyRunMetrics() {
        return {
            step_count: 0,
            duration_ms: null,
            visited_node_count: 0,
            touched_edge_count: 0,
            message_count: 0,
            phase_counts: {},
            action_counts: {}
        };
    }

    _computeRunMetrics(steps = this.timeline.steps) {
        const metrics = this._createEmptyRunMetrics();
        const visitedNodes = new Set();
        const touchedEdges = new Set();

        (steps || []).forEach(step => {
            if (!step) return;
            metrics.step_count += 1;
            if (step.message) metrics.message_count += 1;

            const phase = step.phase || 'unknown';
            const action = step.action || 'unknown';
            metrics.phase_counts[phase] = (metrics.phase_counts[phase] || 0) + 1;
            metrics.action_counts[action] = (metrics.action_counts[action] || 0) + 1;

            if (step.target_type === 'node' && step.target_id) {
                visitedNodes.add(String(step.target_id));
            }
            if (step.target_type === 'edge' && step.target_id) {
                touchedEdges.add(String(step.target_id));
            }
        });

        metrics.visited_node_count = visitedNodes.size;
        metrics.touched_edge_count = touchedEdges.size;

        if (this.timeline.startedAt && this.timeline.finishedAt) {
            const start = Date.parse(this.timeline.startedAt);
            const finish = Date.parse(this.timeline.finishedAt);
            if (!Number.isNaN(start) && !Number.isNaN(finish) && finish >= start) {
                metrics.duration_ms = finish - start;
            }
        }

        return metrics;
    }

    _updateRunMetrics() {
        this.runMetrics = this._computeRunMetrics();
        this._renderRunSummary();
    }

    _renderRunSummary() {
        const panel = document.getElementById('run-summary');
        const content = document.getElementById('run-summary-content');
        if (!panel || !content) return;

        const metrics = this.runMetrics || this._createEmptyRunMetrics();
        if (!metrics.step_count && !this.isRunning && !this.timeline.completed) {
            this._clearRunSummary();
            return;
        }

        content.innerHTML = '';
        const items = [
            ['Steps', metrics.step_count],
            ['Nodes', metrics.visited_node_count],
            ['Edges', metrics.touched_edge_count],
            ['Messages', metrics.message_count]
        ];
        if (this.timeline.steps.length > 0) {
            const current = Math.max(0, Math.min(this.timeline.currentIndex, this.timeline.steps.length));
            items.push(['Position', `${current} / ${this.timeline.steps.length}`]);
        }
        if (metrics.duration_ms !== null && metrics.duration_ms !== undefined) {
            items.push(['Duration', `${metrics.duration_ms}ms`]);
        }

        items.forEach(([label, value]) => {
            content.appendChild(this._renderRunMetric(label, value));
        });

        const phaseSummary = this._formatCountBreakdown(metrics.phase_counts, 3);
        if (phaseSummary) content.appendChild(this._renderRunMetric('Phases', phaseSummary, 'detail'));

        const actionSummary = this._formatCountBreakdown(metrics.action_counts, 3);
        if (actionSummary) content.appendChild(this._renderRunMetric('Actions', actionSummary, 'detail'));

        panel.style.display = 'flex';
    }

    _renderRunMetric(label, value, extraClass = '') {
        const item = document.createElement('div');
        item.className = extraClass ? `run-metric ${extraClass}` : 'run-metric';

        const labelEl = document.createElement('span');
        labelEl.className = 'run-metric-label';
        labelEl.textContent = label;

        const valueEl = document.createElement('span');
        valueEl.className = 'run-metric-value';
        valueEl.textContent = this._formatStateValue(value);
        valueEl.title = valueEl.textContent;

        item.appendChild(labelEl);
        item.appendChild(valueEl);
        return item;
    }

    _formatCountBreakdown(counts, limit = 3) {
        const entries = Object.entries(counts || {})
            .filter(([, count]) => Number(count) > 0)
            .sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0])));

        if (entries.length === 0) return '';

        const visible = entries.slice(0, limit)
            .map(([name, count]) => `${this._formatStateKey(name)} ${count}`);
        const remaining = entries.slice(limit).reduce((sum, [, count]) => sum + Number(count || 0), 0);
        if (remaining > 0) visible.push(`other ${remaining}`);
        return visible.join(', ');
    }

    _clearRunSummary() {
        const panel = document.getElementById('run-summary');
        const content = document.getElementById('run-summary-content');
        if (content) content.innerHTML = '';
        if (panel) panel.style.display = 'none';
    }

    _timelineCanReview() {
        return this.timeline.completed && this.timeline.steps.length > 0;
    }

    _timelineStepAt(index) {
        if (index <= 0) return null;
        return this.timeline.steps[index - 1] || null;
    }

    _isKeyTimelineIndex(index) {
        if (index <= 0 || index >= this.timeline.steps.length) return true;

        const step = this._timelineStepAt(index);
        if (!step) return false;

        const phase = String(step.phase || '').toLowerCase();
        if (['init', 'relax', 'finalize', 'result'].includes(phase)) return true;

        const action = String(step.action || '').toLowerCase();
        return [
            'render_array',
            'render_matrix',
            'update_node_label',
            'update_edge_label',
            'update_node_position',
            'update_array_item',
            'swap_array_items',
            'update_matrix_cell',
            'mark_path',
            'add_node',
            'add_edge',
            'remove_node',
            'remove_edge'
        ].includes(action);
    }

    _timelineTargetIndex(direction) {
        const total = this.timeline.steps.length;
        const current = Math.max(0, Math.min(this.timeline.currentIndex, total));
        const delta = direction < 0 ? -1 : 1;

        if (this.timeline.bookmarkOnly) {
            return this._bookmarkTargetIndex(direction);
        }

        if (!this.timeline.keyOnly) {
            return Math.max(0, Math.min(total, current + delta));
        }

        for (let index = current + delta; index >= 0 && index <= total; index += delta) {
            if (this._isKeyTimelineIndex(index)) return index;
        }
        return current;
    }

    _timelineBookmarksArray() {
        return this._normalizeTimelineBookmarks([...this.timeline.bookmarks], this.timeline.steps.length);
    }

    _bookmarkTargetIndex(direction) {
        const bookmarks = this._timelineBookmarksArray();
        const current = Math.max(0, Math.min(this.timeline.currentIndex, this.timeline.steps.length));
        if (!bookmarks.length) return current;

        if (direction < 0) {
            return [...bookmarks].reverse().find(index => index < current) || current;
        }
        return bookmarks.find(index => index > current) || current;
    }

    _toggleTimelineBookmark() {
        if (!this._timelineCanReview()) return;
        const current = Math.max(0, Math.min(this.timeline.currentIndex, this.timeline.steps.length));
        if (current <= 0) return;

        if (this.timeline.bookmarks.has(current)) {
            this.timeline.bookmarks.delete(current);
        } else {
            this.timeline.bookmarks.add(current);
        }
        if (this.timeline.bookmarks.size === 0) {
            this.timeline.bookmarkOnly = false;
        }
        this._syncTimelineUI();
    }

    handleTimelineKeyboard(key) {
        if (!this._timelineCanReview() || this.isRunning) return false;
        if (key !== 'ArrowLeft' && key !== 'ArrowRight') return false;

        this._stopTimelinePlayback();
        const target = this._timelineTargetIndex(key === 'ArrowLeft' ? -1 : 1);
        this._renderTimelineIndex(target);
        return true;
    }

    _showTimelinePreview(index, sliderRect = null, ratio = null) {
        const preview = document.getElementById('timeline-preview');
        if (!preview || !this._timelineCanReview()) return;

        const total = this.timeline.steps.length;
        const bounded = Math.max(0, Math.min(index, total));
        const step = this._timelineStepAt(bounded);
        const phase = step ? (step.phase || 'step') : 'start';
        const action = step ? (step.action || '') : '';
        const message = step && step.message
            ? step.message
            : (step ? this._formatStateKey(action || phase) : 'Initial graph state');

        preview.innerHTML = '';

        const meta = document.createElement('div');
        meta.className = 'timeline-preview-meta';
        meta.textContent = `${bounded} / ${total} · ${phase}${action ? ` · ${this._formatStateKey(action)}` : ''}`;

        const text = document.createElement('div');
        text.className = 'timeline-preview-message';
        text.textContent = message;

        preview.appendChild(meta);
        preview.appendChild(text);

        if (sliderRect && ratio !== null) {
            const bar = document.getElementById('timeline-bar');
            const barRect = bar ? bar.getBoundingClientRect() : null;
            if (barRect) {
                const rawLeft = sliderRect.left - barRect.left + ratio * sliderRect.width;
                const left = Math.max(92, Math.min(rawLeft, barRect.width - 92));
                preview.style.left = `${left}px`;
            }
        }

        preview.classList.add('visible');
    }

    _hideTimelinePreview() {
        const preview = document.getElementById('timeline-preview');
        if (preview) preview.classList.remove('visible');
    }

    _syncTimelineUI() {
        const slider = document.getElementById('timeline-slider');
        const label = document.getElementById('timeline-label');
        const playIcon = document.getElementById('timeline-play-icon');
        const exportBtn = document.getElementById('btn-export-run');
        const keyToggle = document.getElementById('timeline-key-steps');
        const bookmarkPrevBtn = document.getElementById('btn-bookmark-prev');
        const bookmarkToggleBtn = document.getElementById('btn-bookmark-toggle');
        const bookmarkToggleIcon = document.getElementById('bookmark-toggle-icon');
        const bookmarkNextBtn = document.getElementById('btn-bookmark-next');
        const bookmarkToggle = document.getElementById('timeline-bookmark-steps');
        const ids = [
            'btn-timeline-start',
            'btn-timeline-prev',
            'btn-timeline-play',
            'btn-timeline-next',
            'btn-timeline-end'
        ];

        const total = this.timeline.steps.length;
        const current = Math.max(0, Math.min(this.timeline.currentIndex, total));
        const canReview = this._timelineCanReview();
        const bookmarks = this._timelineBookmarksArray();
        const hasPreviousBookmark = bookmarks.some(index => index < current);
        const hasNextBookmark = bookmarks.some(index => index > current);

        if (slider) {
            slider.max = String(total);
            slider.value = String(current);
            slider.disabled = !canReview;
        }
        if (label) label.textContent = `${current} / ${total}`;
        if (playIcon) playIcon.textContent = this.timeline.playbackActive ? '⏸️' : '▶️';

        if (keyToggle) {
            keyToggle.checked = !!this.timeline.keyOnly;
            keyToggle.disabled = !canReview;
        }
        if (bookmarkToggle) {
            bookmarkToggle.checked = !!this.timeline.bookmarkOnly;
            bookmarkToggle.disabled = !canReview || this.timeline.bookmarks.size === 0;
        }

        ids.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            el.disabled = !canReview;
        });

        if (exportBtn) exportBtn.disabled = !canReview;
        this._renderRunHistory();

        const startBtn = document.getElementById('btn-timeline-start');
        const prevBtn = document.getElementById('btn-timeline-prev');
        const nextBtn = document.getElementById('btn-timeline-next');
        const endBtn = document.getElementById('btn-timeline-end');
        if (canReview) {
            if (startBtn) startBtn.disabled = current <= 0;
            if (prevBtn) prevBtn.disabled = this.timeline.bookmarkOnly ? !hasPreviousBookmark : current <= 0;
            if (nextBtn) nextBtn.disabled = this.timeline.bookmarkOnly ? !hasNextBookmark : current >= total;
            if (endBtn) endBtn.disabled = current >= total;
        }

        const isBookmarked = current > 0 && this.timeline.bookmarks.has(current);
        if (bookmarkPrevBtn) bookmarkPrevBtn.disabled = !canReview || !hasPreviousBookmark;
        if (bookmarkNextBtn) bookmarkNextBtn.disabled = !canReview || !hasNextBookmark;
        if (bookmarkToggleBtn) {
            bookmarkToggleBtn.disabled = !canReview || current <= 0;
            bookmarkToggleBtn.classList.toggle('active', isBookmarked);
            bookmarkToggleBtn.title = isBookmarked ? 'Remove bookmark from current step' : 'Bookmark current step';
        }
        if (bookmarkToggleIcon) bookmarkToggleIcon.textContent = isBookmarked ? '★' : '☆';
    }

    _createRunRecordPayload() {
        const steps = this.timeline.steps.map(step => JSON.parse(JSON.stringify(step)));
        const finalStep = steps.length ? steps[steps.length - 1] : null;
        const algo = this._findAlgorithmByKey(this.selectedAlgorithm);
        return {
            schema: 'visual-algorithm-run-v1',
            exported_at: new Date().toISOString(),
            algorithm_key: this.timeline.algorithmKey || this.selectedAlgorithm,
            visualization: this.selectedVisualization || (algo && algo.visualization) || 'graph',
            params: JSON.parse(JSON.stringify(this.timeline.params || {})),
            started_at: this.timeline.startedAt,
            finished_at: this.timeline.finishedAt,
            base_graph: JSON.parse(JSON.stringify(this.timeline.baseGraph || {})),
            step_count: steps.length,
            bookmarks: this._timelineBookmarksArray(),
            run_metrics: JSON.parse(JSON.stringify(this.runMetrics || this._computeRunMetrics(steps))),
            final_state: finalStep ? (finalStep.state || null) : null,
            steps
        };
    }

    _exportRun() {
        if (!this._timelineCanReview()) {
            showToast('Run export is available after an algorithm completes', 'error');
            return;
        }

        const payload = this._createRunRecordPayload();

        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        const safeKey = String(payload.algorithm_key || 'algorithm').replace(/[^a-z0-9_-]+/gi, '-');
        link.href = url;
        link.download = `${safeKey}-run-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
        showToast('Run exported', 'success');
    }

    _saveCurrentRunRecord() {
        if (!this._timelineCanReview()) {
            showToast('Run records are available after an algorithm completes', 'error');
            return;
        }

        const payload = this._createRunRecordPayload();
        const savedAt = new Date().toISOString();
        const label = `${this._formatStateKey(payload.algorithm_key || 'algorithm')} - ${payload.step_count} steps`;
        const record = {
            id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
            saved_at: savedAt,
            label,
            record: payload
        };

        this.savedRunRecords = [
            record,
            ...this.savedRunRecords
        ].slice(0, 10);
        this._storeSavedRunRecords();
        this._renderRunHistory();
        showToast('Run record saved', 'success');
    }

    _deleteSavedRunRecord(id) {
        this.savedRunRecords = this.savedRunRecords.filter(item => item.id !== id);
        this._storeSavedRunRecords();
        this._renderRunHistory();
    }

    _renderRunHistory() {
        const list = document.getElementById('run-history-list');
        const save = document.getElementById('btn-save-run');
        if (!list) return;

        if (save) save.disabled = !this._timelineCanReview();
        list.innerHTML = '';

        const records = Array.isArray(this.savedRunRecords) ? this.savedRunRecords : [];
        if (records.length === 0) {
            const empty = document.createElement('div');
            empty.className = 'run-history-empty';
            empty.textContent = 'No saved runs';
            list.appendChild(empty);
            return;
        }

        records.forEach(item => {
            const row = document.createElement('div');
            row.className = 'run-history-item';

            const load = document.createElement('button');
            load.type = 'button';
            load.className = 'run-history-load';
            load.dataset.recordId = item.id || '';
            const stepCount = item.record ? (item.record.step_count || (item.record.steps || []).length || 0) : 0;
            const savedDate = item.saved_at ? new Date(item.saved_at) : null;
            const savedLabel = savedDate && !Number.isNaN(savedDate.getTime())
                ? savedDate.toLocaleString()
                : 'saved run';

            const title = document.createElement('span');
            title.className = 'run-history-name';
            title.textContent = item.label || this._formatStateKey(item.record && item.record.algorithm_key || 'algorithm');

            const meta = document.createElement('span');
            meta.className = 'run-history-meta';
            meta.textContent = `${stepCount} steps - ${savedLabel}`;

            load.appendChild(title);
            load.appendChild(meta);
            load.addEventListener('click', () => this.loadRunRecord(item.record));

            const remove = document.createElement('button');
            remove.type = 'button';
            remove.className = 'run-history-delete';
            remove.textContent = 'x';
            remove.title = 'Delete saved run';
            remove.setAttribute('aria-label', `Delete ${title.textContent}`);
            remove.addEventListener('click', () => this._deleteSavedRunRecord(item.id));

            row.appendChild(load);
            row.appendChild(remove);
            list.appendChild(row);
        });
    }

    _renderTimelineIndex(index) {
        if (!this._timelineCanReview() || !this.timeline.baseGraph) return;

        const bounded = Math.max(0, Math.min(index, this.timeline.steps.length));
        this.timeline.currentIndex = bounded;

        this.editor.lockLayout();
        const baseViewport = this.timeline.baseGraph.viewport
            ? JSON.parse(JSON.stringify(this.timeline.baseGraph.viewport))
            : null;
        this.editor.restoreSnapshot(this.timeline.baseGraph, { save: false, viewport: false });
        this.visualizer.storeOriginalLabels();

        for (let i = 0; i < bounded; i++) {
            this.visualizer.applyStep(this.timeline.steps[i]);
        }

        const currentStep = bounded > 0 ? this.timeline.steps[bounded - 1] : null;
        if (currentStep && currentStep.state) {
            this._renderState(currentStep.state);
        } else {
            this._clearState();
        }

        this.editor.setMode('view');
        if (baseViewport) {
            this.editor.restoreViewport(baseViewport);
            requestAnimationFrame(() => this.editor.restoreViewport(baseViewport));
        }
        this._setStatus('replay', bounded === this.timeline.steps.length ? 'Replay End' : 'Replaying');
        this._renderStepDetail(currentStep, bounded, this.timeline.steps.length);
        this._highlightTimelineLog(bounded - 1);
        this._syncTimelineUI();
        this._renderRunSummary();
    }

    _startTimelinePlayback() {
        if (!this._timelineCanReview()) return;

        if (this.timeline.currentIndex >= this.timeline.steps.length) {
            this._renderTimelineIndex(0);
        }

        this.timeline.playbackActive = true;
        this._syncTimelineUI();

        this.timeline.playbackTimer = setInterval(() => {
            if (this.timeline.currentIndex >= this.timeline.steps.length) {
                this._stopTimelinePlayback();
                return;
            }
            const nextIndex = this._timelineTargetIndex(1);
            if (nextIndex === this.timeline.currentIndex) {
                this._stopTimelinePlayback();
                return;
            }
            this._renderTimelineIndex(nextIndex);
        }, Math.max(50, this.currentSpeed));
    }

    _stopTimelinePlayback() {
        if (this.timeline.playbackTimer) {
            clearInterval(this.timeline.playbackTimer);
            this.timeline.playbackTimer = null;
        }
        this.timeline.playbackActive = false;
        this._syncTimelineUI();
    }

    _highlightTimelineLog(stepIndex) {
        document.querySelectorAll('.log-entry.active').forEach(el => el.classList.remove('active'));
        if (stepIndex < 0) return;
        const el = document.querySelector(`.log-entry[data-step-index="${stepIndex}"]`);
        if (el) {
            el.classList.add('active');
            el.scrollIntoView({ block: 'nearest' });
        }
    }

    _renderState(state) {
        const panel = document.getElementById('state-panel');
        const content = document.getElementById('state-content');
        if (!panel || !content || !state || Object.keys(state).length === 0) return;

        content.innerHTML = '';
        const previousState = this.lastRenderedState || {};
        const hasPreviousState = !!this.lastRenderedState;
        const entries = Object.entries(state);
        const changes = [];

        entries.forEach(([key, value]) => {
            const hadPreviousValue = Object.prototype.hasOwnProperty.call(previousState, key);
            if (hasPreviousState && (!hadPreviousValue || this._stateValueChanged(previousState[key], value))) {
                changes.push({
                    key,
                    previous: hadPreviousValue ? previousState[key] : undefined,
                    current: value,
                    isNew: !hadPreviousValue
                });
            }
        });

        if (changes.length > 0) {
            content.appendChild(this._renderStateDiffDetail(changes));
        }

        entries.forEach(([key, value]) => {
            const section = document.createElement('div');
            section.className = 'state-section';
            if (changes.some(change => change.key === key)) {
                section.classList.add('changed');
            }

            const label = document.createElement('div');
            label.className = 'state-section-title';
            label.textContent = this._formatStateKey(key);

            section.appendChild(label);
            section.appendChild(this._renderStateValue(key, value, 0));
            content.appendChild(section);
        });

        this._renderStateDiffSummary(changes);
        this.lastRenderedState = this._cloneState(state);
        panel.style.display = 'flex';
    }

    _renderStateDiffSummary(changes = []) {
        const summary = document.getElementById('state-diff-summary');
        if (!summary) return;

        if (!changes.length) {
            summary.textContent = '';
            summary.title = '';
            return;
        }

        const labels = changes.map(change => this._formatStateKey(change.key));
        const visible = labels.slice(0, 3);
        const extra = labels.length - visible.length;
        const text = `Changed: ${visible.join(', ')}${extra > 0 ? ` +${extra}` : ''}`;
        summary.textContent = text;
        summary.title = `Changed fields: ${labels.join(', ')}`;
    }

    _renderStateDiffDetail(changes = []) {
        const detail = document.createElement('div');
        detail.className = 'state-diff-detail';

        changes.slice(0, 6).forEach(change => {
            const row = document.createElement('div');
            row.className = 'state-diff-row';

            const key = document.createElement('span');
            key.className = 'state-diff-key';
            key.textContent = this._formatStateKey(change.key);

            const before = document.createElement('span');
            before.className = 'state-diff-before';
            before.textContent = `Before: ${change.isNew ? 'new' : this._formatInlineStateValue(change.previous)}`;
            before.title = before.textContent;

            const after = document.createElement('span');
            after.className = 'state-diff-after';
            after.textContent = `After: ${this._formatInlineStateValue(change.current)}`;
            after.title = after.textContent;

            row.appendChild(key);
            row.appendChild(before);
            row.appendChild(after);
            detail.appendChild(row);
        });

        if (changes.length > 6) {
            const more = document.createElement('div');
            more.className = 'state-diff-more';
            more.textContent = `+${changes.length - 6} more changes`;
            detail.appendChild(more);
        }

        return detail;
    }

    _renderStateValue(key, value, depth = 0) {
        if (key === 'distances' || key === 'previous' || key === 'predecessors') {
            return this._renderDictionaryTable(key, value);
        }

        if (value && typeof value === 'object' && value.type === 'matrix') {
            return this._renderMatrix(value, key);
        }

        if (Array.isArray(value)) {
            if (value.length === 0) return this._renderEmptyState();
            if (value.every(item => Array.isArray(item))) {
                return key.includes('component') ? this._renderGroups(value) : this._renderSimpleMatrix(value);
            }
            if (value.every(item => this._isPrimitive(item))) {
                return this._renderChips(value);
            }
            if (value.every(item => item && typeof item === 'object' && !Array.isArray(item))) {
                return this._renderObjectTable(value, key);
            }
            return this._renderPre(value);
        }

        if (value && typeof value === 'object') {
            if (this._objectHasOnlyPrimitiveValues(value)) {
                return this._renderDictionaryTable(key, value);
            }
            return this._renderKeyValueList(value, depth);
        }

        const scalar = document.createElement('div');
        scalar.className = 'state-scalar';
        scalar.textContent = this._formatStateValue(value);
        return scalar;
    }

    _renderChips(items) {
        const wrap = document.createElement('div');
        wrap.className = 'state-chip-row';

        items.forEach(item => {
            const chip = document.createElement('span');
            chip.className = 'state-chip';
            chip.textContent = this._formatStateValue(item);
            wrap.appendChild(chip);
        });

        return wrap;
    }

    _renderGroups(groups) {
        const wrap = document.createElement('div');
        wrap.className = 'state-group-list';

        groups.forEach((group, idx) => {
            const groupEl = document.createElement('div');
            groupEl.className = 'state-group';

            const name = document.createElement('span');
            name.className = 'state-group-name';
            name.textContent = `#${idx + 1}`;

            groupEl.appendChild(name);
            groupEl.appendChild(this._renderChips(group));
            wrap.appendChild(groupEl);
        });

        return wrap;
    }

    _renderKeyValueList(obj, depth = 0) {
        const wrap = document.createElement('div');
        wrap.className = depth > 0 ? 'state-kv-list nested' : 'state-kv-list';

        Object.entries(obj).forEach(([key, value]) => {
            const row = document.createElement('div');
            row.className = 'state-row';

            const keyEl = document.createElement('span');
            keyEl.className = 'state-key';
            keyEl.textContent = this._formatStateKey(key);

            const valueEl = document.createElement('div');
            valueEl.className = 'state-value';
            valueEl.appendChild(this._renderNestedStateValue(key, value, depth + 1));

            row.appendChild(keyEl);
            row.appendChild(valueEl);
            wrap.appendChild(row);
        });

        return wrap;
    }

    _renderNestedStateValue(key, value, depth) {
        if (this._isPrimitive(value)) {
            const scalar = document.createElement('span');
            scalar.className = 'state-inline-scalar';
            scalar.textContent = this._formatStateValue(value);
            return scalar;
        }

        if (Array.isArray(value)) {
            if (value.length === 0) return this._renderEmptyState();
            if (value.every(item => this._isPrimitive(item))) {
                return this._renderChips(value);
            }
            if (value.every(item => item && typeof item === 'object' && !Array.isArray(item))) {
                return depth > 1 ? this._renderInlineObjectValue(value) : this._renderObjectTable(value, key);
            }
            return this._renderPre(value);
        }

        if (value && typeof value === 'object') {
            if (value.type === 'matrix') return this._renderMatrix(value, key);
            if (depth >= 3 || this._objectHasOnlyPrimitiveValues(value)) {
                return this._renderInlineObjectValue(value);
            }
            return this._renderKeyValueList(value, depth);
        }

        const scalar = document.createElement('span');
        scalar.className = 'state-inline-scalar';
        scalar.textContent = this._formatStateValue(value);
        return scalar;
    }

    _renderInlineObjectValue(value) {
        const span = document.createElement('span');
        span.className = 'state-inline-object';
        span.textContent = this._formatInlineStateValue(value);
        span.title = span.textContent;
        return span;
    }

    _renderDictionaryTable(key, obj) {
        if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return this._renderEmptyState();

        const rows = Object.entries(obj).map(([name, value]) => ({
            name,
            value
        }));
        const table = document.createElement('table');
        table.className = `state-table state-dictionary-table state-${this._stateClassName(key)}-table`;

        const thead = document.createElement('thead');
        const headRow = document.createElement('tr');
        [this._dictionaryKeyLabel(key), this._dictionaryValueLabel(key)].forEach(text => {
            const th = document.createElement('th');
            th.textContent = text;
            headRow.appendChild(th);
        });
        thead.appendChild(headRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        rows.forEach(row => {
            const tr = document.createElement('tr');
            const keyCell = document.createElement('th');
            keyCell.textContent = row.name;
            const valueCell = document.createElement('td');
            valueCell.textContent = this._formatStateValue(row.value);
            valueCell.className = this._stateValueClass(row.value);
            tr.appendChild(keyCell);
            tr.appendChild(valueCell);
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);

        return table;
    }

    _renderObjectTable(items, key = '') {
        const columns = [...new Set(items.flatMap(item => Object.keys(item)))];
        const table = document.createElement('table');
        table.className = `state-table ${this._stateObjectTableClass(key)}`;

        const thead = document.createElement('thead');
        const headRow = document.createElement('tr');
        columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            headRow.appendChild(th);
        });
        thead.appendChild(headRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        items.forEach(item => {
            const row = document.createElement('tr');
            columns.forEach(col => {
                const td = document.createElement('td');
                const cellValue = item[col];
                if (this._isPrimitive(cellValue)) {
                    td.textContent = this._formatStateValue(cellValue);
                    td.className = this._stateValueClass(cellValue);
                } else {
                    td.appendChild(this._renderInlineObjectValue(cellValue));
                }
                row.appendChild(td);
            });
            tbody.appendChild(row);
        });
        table.appendChild(tbody);

        return table;
    }

    _renderMatrix(matrix, key = '') {
        const rows = matrix.rows || [];
        const columns = matrix.columns || [];
        const values = matrix.values || [];
        const table = document.createElement('table');
        table.className = `state-table state-matrix state-${this._stateClassName(key)}-matrix`;

        const thead = document.createElement('thead');
        const headRow = document.createElement('tr');
        headRow.appendChild(document.createElement('th'));
        columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            headRow.appendChild(th);
        });
        thead.appendChild(headRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        values.forEach((rowValues, rowIdx) => {
            const tr = document.createElement('tr');
            const rowHead = document.createElement('th');
            rowHead.textContent = rows[rowIdx] || rowIdx;
            tr.appendChild(rowHead);

            rowValues.forEach(value => {
                const td = document.createElement('td');
                td.textContent = this._formatStateValue(value);
                td.className = this._stateValueClass(value);
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);

        return table;
    }

    _renderSimpleMatrix(values) {
        return this._renderMatrix({
            type: 'matrix',
            rows: values.map((_, idx) => idx),
            columns: values[0] ? values[0].map((_, idx) => idx) : [],
            values
        });
    }

    _renderPre(value) {
        const pre = document.createElement('pre');
        pre.className = 'state-pre';
        pre.textContent = JSON.stringify(value, null, 2);
        return pre;
    }

    _renderEmptyState() {
        const empty = document.createElement('div');
        empty.className = 'state-empty';
        empty.textContent = 'empty';
        return empty;
    }

    _isPrimitive(value) {
        return value === null || ['string', 'number', 'boolean'].includes(typeof value);
    }

    _objectHasOnlyPrimitiveValues(obj) {
        return Object.values(obj).every(value => this._isPrimitive(value));
    }

    _stateValueChanged(previous, current) {
        if (previous === undefined) return false;
        return JSON.stringify(previous) !== JSON.stringify(current);
    }

    _cloneState(state) {
        try {
            return JSON.parse(JSON.stringify(state));
        } catch (e) {
            return null;
        }
    }

    _stateClassName(key) {
        return String(key || 'value').replace(/[^a-z0-9_-]+/gi, '-').toLowerCase();
    }

    _stateObjectTableClass(key) {
        const normalized = String(key || '').toLowerCase();
        if (normalized.includes('residual') || normalized.includes('flow')) return 'state-flow-table';
        if (normalized.includes('dp')) return 'state-dp-table';
        if (normalized.includes('path') || normalized.includes('augment')) return 'state-path-table';
        return '';
    }

    _dictionaryKeyLabel(key) {
        const normalized = String(key || '').toLowerCase();
        if (normalized.includes('distance')) return 'Node';
        if (normalized.includes('previous') || normalized.includes('predecessor')) return 'Node';
        return 'Key';
    }

    _dictionaryValueLabel(key) {
        const normalized = String(key || '').toLowerCase();
        if (normalized.includes('distance')) return 'Distance';
        if (normalized.includes('previous') || normalized.includes('predecessor')) return 'Previous';
        return 'Value';
    }

    _stateValueClass(value) {
        if (value === true || value === 'T' || value === 'true') return 'state-cell-true';
        if (value === false || value === 'F' || value === 'false') return 'state-cell-false';
        if (value === Infinity || value === 'Infinity' || value === '∞') return 'state-cell-infinity';
        if (value === null || value === undefined || value === '') return 'state-cell-empty';
        return '';
    }

    _formatStateKey(key) {
        return String(key).replace(/_/g, ' ');
    }

    _formatInlineStateValue(value) {
        if (this._isPrimitive(value)) return this._formatStateValue(value);
        if (Array.isArray(value)) {
            return `[${value.map(item => this._formatInlineStateValue(item)).join(', ')}]`;
        }
        if (value && typeof value === 'object') {
            return Object.entries(value)
                .map(([key, item]) => `${this._formatStateKey(key)}: ${this._formatInlineStateValue(item)}`)
                .join(', ');
        }
        return this._formatStateValue(value);
    }

    _formatStateValue(value) {
        if (value === null || value === undefined) return 'null';
        if (value === Infinity || value === 'Infinity') return '∞';
        if (value === -Infinity || value === '-Infinity') return '-∞';
        if (Array.isArray(value)) {
            if (value.length === 0) return '[]';
            if (value.every(v => typeof v !== 'object')) {
                return `[${value.join(', ')}]`;
            }
            return JSON.stringify(value);
        }
        if (value && typeof value === 'object') {
            return JSON.stringify(value);
        }
        return String(value);
    }

    _clearState() {
        const panel = document.getElementById('state-panel');
        const content = document.getElementById('state-content');
        if (content) content.innerHTML = '';
        if (panel) panel.style.display = 'none';
        this._renderStateDiffSummary([]);
        this.lastRenderedState = null;
    }

    _renderStepDetail(step, index = this.timeline.currentIndex, total = this.timeline.steps.length) {
        const panel = document.getElementById('step-detail');
        const content = document.getElementById('step-detail-content');
        if (!panel || !content) return;

        if (!step) {
            this._clearStepDetail();
            return;
        }

        content.innerHTML = '';
        const items = [
            ['Step', `${index} / ${total}`],
            ['Phase', step.phase || 'step'],
            ['Action', this._formatStateKey(step.action || 'unknown')]
        ];

        if (step.target_type || step.target_id) {
            const targetType = step.target_type || 'target';
            const targetId = step.target_id || '';
            items.push(['Target', targetId ? `${targetType}:${targetId}` : targetType]);
        }

        items.forEach(([label, value]) => {
            content.appendChild(this._renderStepDetailItem(label, value));
        });

        if (step.message) {
            const message = document.createElement('div');
            message.className = 'step-detail-message';
            message.textContent = step.message;
            message.title = step.message;
            content.appendChild(message);
        }

        panel.style.display = 'flex';
    }

    _renderStepDetailItem(label, value) {
        const item = document.createElement('div');
        item.className = 'step-detail-item';

        const labelEl = document.createElement('span');
        labelEl.className = 'step-detail-label';
        labelEl.textContent = label;

        const valueEl = document.createElement('span');
        valueEl.className = 'step-detail-value';
        valueEl.textContent = this._formatStateValue(value);
        valueEl.title = valueEl.textContent;

        item.appendChild(labelEl);
        item.appendChild(valueEl);
        return item;
    }

    _clearStepDetail() {
        const panel = document.getElementById('step-detail');
        const content = document.getElementById('step-detail-content');
        if (content) content.innerHTML = '';
        if (panel) panel.style.display = 'none';
    }

    _appendToLog(message, phase, stepIndex = null) {
        const log = document.getElementById('step-log-content');
        if (!log) return;
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.dataset.phase = phase || 'info';
        entry.dataset.message = String(message || '').toLowerCase();
        if (stepIndex !== null && stepIndex !== undefined) {
            entry.dataset.stepIndex = String(stepIndex);
            entry.classList.add('clickable');
            entry.title = 'Jump to this timeline step';
            entry.setAttribute('role', 'button');
            entry.tabIndex = 0;
            const jumpToStep = () => {
                if (!this._timelineCanReview()) return;
                this._stopTimelinePlayback();
                this._renderTimelineIndex(Number(stepIndex) + 1);
            };
            entry.addEventListener('click', jumpToStep);
            entry.addEventListener('keydown', (event) => {
                if (event.key !== 'Enter' && event.key !== ' ') return;
                event.preventDefault();
                jumpToStep();
            });
        }

        const phaseSpan = document.createElement('span');
        phaseSpan.className = `log-phase ${phase}`;
        phaseSpan.textContent = phase;

        const msgSpan = document.createElement('span');
        msgSpan.className = 'log-msg';
        msgSpan.textContent = message;

        entry.appendChild(phaseSpan);
        entry.appendChild(msgSpan);
        log.appendChild(entry);
        this._applyLogFilters();
        log.scrollTop = log.scrollHeight;
    }

    _clearStepLog({ resetFilters = false } = {}) {
        const log = document.getElementById('step-log-content');
        if (log) log.innerHTML = '';
        if (resetFilters) this._resetLogFilters();
        this._applyLogFilters();
    }

    _getFilteredLogEntries() {
        const log = document.getElementById('step-log-content');
        if (!log) return [];
        return [...log.querySelectorAll('.log-entry')].filter(entry => !entry.hidden);
    }

    _formatLogEntries(entries) {
        return entries.map(entry => {
            const phase = entry.dataset.phase || 'info';
            const message = entry.querySelector('.log-msg')?.textContent || entry.textContent || '';
            const stepIndex = Number(entry.dataset.stepIndex);
            const prefix = Number.isInteger(stepIndex) ? `#${stepIndex + 1} ` : '';
            return `${prefix}[${phase}] ${message.trim()}`.trim();
        }).join('\n');
    }

    async _copyFilteredLog() {
        const entries = this._getFilteredLogEntries();
        if (!entries.length) {
            showToast('No log entries to copy', 'error');
            return;
        }

        const text = this._formatLogEntries(entries);
        try {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(text);
            } else {
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.setAttribute('readonly', '');
                textarea.style.position = 'fixed';
                textarea.style.left = '-9999px';
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                textarea.remove();
            }
            showToast('Log copied', 'success');
        } catch (e) {
            showToast('Could not copy log', 'error');
        }
    }

    _exportFilteredLog() {
        const entries = this._getFilteredLogEntries();
        if (!entries.length) {
            showToast('No log entries to export', 'error');
            return;
        }

        const text = this._formatLogEntries(entries);
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        const safeKey = String(this.timeline.algorithmKey || this.selectedAlgorithm || 'algorithm').replace(/[^a-z0-9_-]+/gi, '-');
        link.href = url;
        link.download = `${safeKey}-log-${new Date().toISOString().replace(/[:.]/g, '-')}.txt`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
        showToast('Log exported', 'success');
    }

    _applyLogFilters() {
        const log = document.getElementById('step-log-content');
        const count = document.getElementById('log-match-count');
        if (!log) {
            if (count) count.textContent = '0 steps';
            return;
        }

        const query = String(this.logFilter.query || '').trim().toLowerCase();
        const phase = this.logFilter.phase || 'all';
        const entries = [...log.querySelectorAll('.log-entry')];
        let visible = 0;

        entries.forEach(entry => {
            const entryPhase = entry.dataset.phase || '';
            const message = entry.dataset.message || entry.textContent.toLowerCase();
            const matchesPhase = phase === 'all' || entryPhase === phase;
            const matchesQuery = !query || message.includes(query) || entryPhase.includes(query);
            const matches = matchesPhase && matchesQuery;
            entry.hidden = !matches;
            if (matches) visible += 1;
        });

        if (count) {
            const total = entries.length;
            count.textContent = query || phase !== 'all'
                ? `${visible} / ${total} steps`
                : `${total} steps`;
        }
    }
}
