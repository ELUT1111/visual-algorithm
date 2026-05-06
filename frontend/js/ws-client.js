/* ===== WebSocket Client ===== */

class WSClient {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.handlers = new Map();
        this.reconnectDelay = 1000;
        this._shouldReconnect = true;
        this._connected = false;
        this._firstConnect = true;
        this._reconnectAttempts = 0;
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.log('[WS] Connected');
            this._connected = true;
            this.reconnectDelay = 1000;

            if (this._firstConnect) {
                this._firstConnect = false;
            } else if (this._reconnectAttempts > 0) {
                showToast('Reconnected to server', 'success');
            }

            this._reconnectAttempts = 0;
            this._updateConnectionUI(true);
        };

        this.ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                const handler = this.handlers.get(msg.type);
                if (handler) {
                    handler(msg.data || {});
                }
            } catch (e) {
                console.error('[WS] Parse error:', e);
            }
        };

        this.ws.onclose = () => {
            console.log('[WS] Disconnected');
            this._connected = false;

            if (this._shouldReconnect) {
                this._reconnectAttempts++;
                if (this._reconnectAttempts === 1) {
                    showToast('Connection lost, reconnecting...', 'error');
                }
                this._updateConnectionUI(false);
                setTimeout(() => this.connect(), this.reconnectDelay);
                this.reconnectDelay = Math.min(this.reconnectDelay * 2, 10000);
            }
        };

        this.ws.onerror = (err) => {
            console.error('[WS] Error:', err);
        };
    }

    _updateConnectionUI(connected) {
        const badge = document.getElementById('status-badge');
        if (!connected && badge) {
            badge.textContent = 'Disconnected';
            badge.className = 'status-badge';
            badge.style.background = 'rgba(248, 113, 113, 0.15)';
            badge.style.color = '#f87171';
        } else if (connected && badge && badge.textContent === 'Disconnected') {
            badge.textContent = 'Ready';
            badge.className = 'status-badge';
            badge.style.background = '';
            badge.style.color = '';
        }
    }

    get isConnected() {
        return this._connected;
    }

    on(messageType, callback) {
        this.handlers.set(messageType, callback);
    }

    send(command, data = {}) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ command, ...data }));
        } else {
            console.warn('[WS] Not connected, cannot send');
            showToast('Not connected to server', 'error');
        }
    }

    disconnect() {
        this._shouldReconnect = false;
        if (this.ws) {
            this.ws.close();
        }
    }
}
