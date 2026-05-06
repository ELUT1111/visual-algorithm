/* ===== Preset Manager - Import/Export ===== */

class PresetManager {
    constructor(graphEditor) {
        this.editor = graphEditor;
        this.presets = [];
    }

    async init() {
        await this.loadPresets();
        this._setupButtons();
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
                    this.editor.loadFromJSON(data);
                    showToast(`Imported: ${data.name || file.name}`, 'success');
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
}
