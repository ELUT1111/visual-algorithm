/* ===== Utility Functions ===== */

function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function showModal(title, fields, onSubmit) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';

    let fieldsHTML = fields.map(f => `
        <div class="param-group">
            <label>${f.label}</label>
            <input type="${f.type || 'text'}" id="modal-${f.name}" value="${f.value || ''}" placeholder="${f.placeholder || ''}">
        </div>
    `).join('');

    overlay.innerHTML = `
        <div class="modal-box">
            <h3>${title}</h3>
            ${fieldsHTML}
            <div class="modal-actions">
                <button class="btn" id="modal-cancel">Cancel</button>
                <button class="btn btn-primary" id="modal-ok">OK</button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    const firstInput = overlay.querySelector('input');
    if (firstInput) firstInput.focus();

    return new Promise(resolve => {
        overlay.querySelector('#modal-cancel').onclick = () => {
            overlay.remove();
            resolve(null);
        };
        overlay.querySelector('#modal-ok').onclick = () => {
            const values = {};
            fields.forEach(f => {
                values[f.name] = document.getElementById(`modal-${f.name}`).value;
            });
            overlay.remove();
            resolve(values);
        };
        overlay.addEventListener('keydown', e => {
            if (e.key === 'Enter') {
                overlay.querySelector('#modal-ok').click();
            } else if (e.key === 'Escape') {
                overlay.remove();
                resolve(null);
            }
        });
    });
}

function generateId() {
    return Math.random().toString(36).substr(2, 8);
}
