/**
 * GatewayClient — WebSocket client for the ClawWorld gateway.
 * Uses JSON-RPC 2.0 over WebSocket.
 */

import { parseRPCFrame, type RPCFrame } from "./stream";

type DeltaCallback = (agentId: string, text: string) => void;
type EndCallback = (agentId: string) => void;
type ErrorCallback = (agentId: string, message: string) => void;
type StatusCallback = (connected: boolean) => void;

const MAX_BACKOFF_MS = 8000;
const STREAM_TIMEOUT_MS = 120_000; // 2 min — Ollama may need time to load model on first call

export class GatewayClient {
  private ws: WebSocket | null = null;
  private rpcId = 0;
  private deltaHandlers: DeltaCallback[] = [];
  private endHandlers: EndCallback[] = [];
  private errorHandlers: ErrorCallback[] = [];
  private statusHandlers: StatusCallback[] = [];
  private shouldReconnect = true;
  private backoff = 1000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private streamTimeout: ReturnType<typeof setTimeout> | null = null;
  private connecting = false;

  constructor(private readonly wsUrl = "ws://localhost:18790/gateway-ws") {}

  /** Open the WebSocket, send 'hello', and resolve once the server responds 'connected'. */
  connect(): Promise<void> {
    // Guard against double-connect
    if (this.connecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return Promise.resolve();
    }

    this.connecting = true;

    // Close any existing connection first
    if (this.ws) {
      try { this.ws.close(); } catch { /* ignore */ }
      this.ws = null;
    }

    return new Promise((resolve, reject) => {
      this.shouldReconnect = true;
      this.ws = new WebSocket(this.wsUrl);

      this.ws.onopen = () => {
        this.backoff = 1000;
        this.connecting = false;
        this.send("hello", {});
      };

      this.ws.onmessage = (ev) => {
        const frame = parseRPCFrame(String(ev.data));
        if (!frame) return;
        this.dispatch(frame, resolve);
      };

      this.ws.onerror = () => {
        this.connecting = false;
        reject(new Error("WebSocket error"));
      };

      this.ws.onclose = (ev) => {
        this.connecting = false;
        for (const cb of this.statusHandlers) cb(false);
        // Don't reconnect on policy violation or auth errors
        if (ev.code === 1008 || ev.code === 1003) return;
        this.scheduleReconnect();
      };
    });
  }

  /** Send a chat message to the given agent. */
  sendMessage(agentId: string, message: string): void {
    this.send("chat.send", { agentId, message });
    this.resetStreamTimeout(agentId);
  }

  /** Register a handler for streaming text deltas. */
  onDelta(cb: DeltaCallback): void {
    this.deltaHandlers.push(cb);
  }

  /** Register a handler for stream-end events. */
  onEnd(cb: EndCallback): void {
    this.endHandlers.push(cb);
  }

  /** Register a handler for errors (rate limit, server error, timeout). */
  onError(cb: ErrorCallback): void {
    this.errorHandlers.push(cb);
  }

  /** Register a handler for connection status changes. */
  onStatus(cb: StatusCallback): void {
    this.statusHandlers.push(cb);
  }

  /** Remove all registered handlers. */
  clearHandlers(): void {
    this.deltaHandlers = [];
    this.endHandlers = [];
    this.errorHandlers = [];
    this.statusHandlers = [];
  }

  /** Close the connection (no auto-reconnect). */
  disconnect(): void {
    this.shouldReconnect = false;
    this.connecting = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.clearStreamTimeout();
    this.ws?.close();
    this.ws = null;
  }

  // --- internals ---

  private send(method: string, params: Record<string, unknown>): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    this.rpcId++;
    const msg = JSON.stringify({ jsonrpc: "2.0", id: this.rpcId, method, params });
    this.ws.send(msg);
  }

  private dispatch(frame: RPCFrame, onConnected?: (value: void) => void): void {
    // Handle JSON-RPC error responses (rate limit, invalid params, etc.)
    if (frame.error) {
      for (const cb of this.errorHandlers) cb("", frame.error.message);
      this.clearStreamTimeout();
      return;
    }

    // Response to 'hello' — server returns result with status: "connected"
    const resultStatus = typeof frame.result === "object" && frame.result !== null
      ? (frame.result as Record<string, unknown>).status
      : frame.result;
    if (resultStatus === "connected") {
      for (const cb of this.statusHandlers) cb(true);
      onConnected?.();
      return;
    }

    // Notification-style events (no id, has method)
    if (frame.method === "chat.delta") {
      const p = frame.params as { agentId?: string; delta?: string } | undefined;
      if (p?.agentId && p.delta != null) {
        this.resetStreamTimeout(p.agentId);
        for (const cb of this.deltaHandlers) cb(p.agentId, p.delta);
      }
      return;
    }

    if (frame.method === "chat.error") {
      const p = frame.params as { agentId?: string; error?: string } | undefined;
      if (p?.agentId) {
        this.clearStreamTimeout();
        for (const cb of this.errorHandlers) cb(p.agentId, p.error ?? "Unknown error");
      }
      return;
    }

    if (frame.method === "chat.end") {
      const p = frame.params as { agentId?: string } | undefined;
      if (p?.agentId) {
        this.clearStreamTimeout();
        for (const cb of this.endHandlers) cb(p.agentId);
      }
    }
  }

  private resetStreamTimeout(agentId: string): void {
    this.clearStreamTimeout();
    this.streamTimeout = setTimeout(() => {
      for (const cb of this.errorHandlers) cb(agentId, "NPC seems lost in thought...");
      for (const cb of this.endHandlers) cb(agentId);
    }, STREAM_TIMEOUT_MS);
  }

  private clearStreamTimeout(): void {
    if (this.streamTimeout) {
      clearTimeout(this.streamTimeout);
      this.streamTimeout = null;
    }
  }

  private scheduleReconnect(): void {
    if (!this.shouldReconnect) return;
    // Guard against duplicate reconnect timers
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.backoff = Math.min(this.backoff * 2, MAX_BACKOFF_MS);
      this.connect().catch(() => {});
    }, this.backoff);
  }
}
