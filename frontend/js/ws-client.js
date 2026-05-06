/* ===== WebSocket Client ===== */

class WSClient {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.handlers = new Map();
        this.reconnectDelay = 1000;
        this._shouldReconnect = true;
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.log('[WS] Connected');
            this.reconnectDelay = 1000;
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
            if (this._shouldReconnect) {
                setTimeout(() => this.connect(), this.reconnectDelay);
                this.reconnectDelay = Math.min(this.reconnectDelay * 2, 10000);
            }
        };

        this.ws.onerror = (err) => {
            console.error('[WS] Error:', err);
        };
    }

    on(messageType, callback) {
        this.handlers.set(messageType, callback);
    }

    send(command, data = {}) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ command, ...data }));
        } else {
            console.warn('[WS] Not connected, cannot send');
        }
    }

    disconnect() {
        this._shouldReconnect = false;
        if (this.ws) {
            this.ws.close();
        }
    }
}
