'use client';

import { EventEmitter } from 'events';

interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
  event?: string;
  data?: any;
}

interface WebSocketOptions {
  url: string;
  reconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
  autoConnect?: boolean;
}

class WebSocketService extends EventEmitter {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnect: boolean;
  private maxReconnectAttempts: number;
  private reconnectInterval: number;
  private reconnectAttempts = 0;
  private isConnected = false;
  private messageQueue: WebSocketMessage[] = [];
  private heartbeatInterval: ReturnType<typeof setInterval> | null = null;

  constructor(options: WebSocketOptions) {
    super();
    this.url = options.url;
    this.reconnect = options.reconnect ?? true;
    this.maxReconnectAttempts = options.maxReconnectAttempts ?? 5;
    this.reconnectInterval = options.reconnectInterval ?? 3000;

    if (options.autoConnect !== false) {
      this.connect();
    }
  }

  connect(): void {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        console.log('[WebSocket] Connected to', this.url);
        this.emit('connected');

        // Send queued messages
        while (this.messageQueue.length > 0) {
          const msg = this.messageQueue.shift();
          if (msg) this.send(msg);
        }

        // Start heartbeat
        this.startHeartbeat();
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          this.emit('message', data);
          this.emit(data.type || 'data', data.payload || data.data);
        } catch (err) {
          console.error('[WebSocket] Message parse error:', err);
          this.emit('error', err);
        }
      };

      this.ws.onerror = (event: Event) => {
        console.error('[WebSocket] Error:', event);
        this.emit('error', event);
      };

      this.ws.onclose = (event: CloseEvent) => {
        this.isConnected = false;
        this.stopHeartbeat();
        console.log('[WebSocket] Disconnected. Code:', event.code, 'Reason:', event.reason);
        this.emit('disconnected', { code: event.code, reason: event.reason });

        if (this.reconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
          const delay = Math.min(
            this.reconnectInterval * Math.pow(2, this.reconnectAttempts),
            30000
          );
          this.reconnectAttempts++;
          console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
          setTimeout(() => this.connect(), delay);
        }
      };
    } catch (err) {
      console.error('[WebSocket] Connection failed:', err);
      this.emit('error', err);
    }
  }

  send(data: WebSocketMessage | string): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      if (typeof data === 'object') {
        this.messageQueue.push(data);
      }
      return false;
    }

    const payload = typeof data === 'string' ? data : JSON.stringify(data);
    this.ws.send(payload);
    return true;
  }

  subscribe(event: string, callback: (data: any) => void): () => void {
    this.on(event, callback);
    return () => this.off(event, callback);
  }

  onMessage(callback: (data: WebSocketMessage) => void): () => void {
    this.on('message', callback);
    return () => this.off('message', callback);
  }

  onConnected(callback: () => void): () => void {
    this.on('connected', callback);
    return () => this.off('connected', callback);
  }

  onDisconnected(callback: (info: { code: number; reason: string }) => void): () => void {
    this.on('disconnected', callback);
    return () => this.off('disconnected', callback);
  }

  onError(callback: (error: any) => void): () => void {
    this.on('error', callback);
    return () => this.off('error', callback);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  getIsConnected(): boolean {
    return this.isConnected;
  }

  disconnect(): void {
    this.reconnect = false;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.stopHeartbeat();
  }

  destroy(): void {
    this.disconnect();
    this.removeAllListeners();
  }
}

// Singleton instance factory
let instance: WebSocketService | null = null;

export function getWebSocket(url?: string): WebSocketService {
  if (!instance || url) {
    const wsUrl = url || (typeof window !== 'undefined'
      ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws`
      : 'ws://localhost:8000/api/v1/ws');

    instance = new WebSocketService({ url: wsUrl });
  }
  return instance;
}

export function createWebSocketConnection(options: WebSocketOptions): WebSocketService {
  return new WebSocketService(options);
}

export { WebSocketService };
export type { WebSocketMessage, WebSocketOptions };