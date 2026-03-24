/**
 * JSON-RPC frame parsing and typewriter text buffer for gateway streaming.
 */

export interface RPCFrame {
  jsonrpc: "2.0";
  id?: number | string;
  method?: string;
  result?: unknown;
  error?: { code: number; message: string; data?: unknown };
  params?: Record<string, unknown>;
}

/** Parse a raw WebSocket message into a typed RPC frame. Returns null on invalid JSON. */
export function parseRPCFrame(data: string): RPCFrame | null {
  try {
    const parsed = JSON.parse(data);
    if (parsed?.jsonrpc !== "2.0") return null;
    return parsed as RPCFrame;
  } catch {
    return null;
  }
}

/**
 * Accumulates streamed text and reveals characters one at a time
 * at a configurable speed (default 30ms per character).
 */
export class TypewriterBuffer {
  private buffer = "";
  private revealed = 0;
  private timer: ReturnType<typeof setInterval> | null = null;
  private listener: ((visible: string) => void) | null = null;
  private readonly msPerChar: number;

  constructor(msPerChar = 30) {
    this.msPerChar = msPerChar;
  }

  /** Register a callback that fires each time a new character is revealed. */
  onReveal(cb: (visible: string) => void): void {
    this.listener = cb;
  }

  /** Append new text from a streaming delta. */
  push(text: string): void {
    this.buffer += text;
    if (!this.timer) this.startTick();
  }

  /** Get currently visible (revealed) text. */
  get visible(): string {
    return this.buffer.slice(0, this.revealed);
  }

  /** True when all buffered text has been revealed. */
  get done(): boolean {
    return this.revealed >= this.buffer.length;
  }

  /** Immediately reveal all remaining text. */
  flush(): void {
    this.stopTick();
    this.revealed = this.buffer.length;
    this.listener?.(this.visible);
  }

  /** Reset the buffer to empty. */
  reset(): void {
    this.stopTick();
    this.buffer = "";
    this.revealed = 0;
  }

  /** Stop all timers and remove listener — call before discarding. */
  destroy(): void {
    this.stopTick();
    this.listener = null;
    this.buffer = "";
    this.revealed = 0;
  }

  private startTick(): void {
    this.timer = setInterval(() => {
      if (this.revealed < this.buffer.length) {
        this.revealed++;
        this.listener?.(this.visible);
      } else {
        this.stopTick();
      }
    }, this.msPerChar);
  }

  private stopTick(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }
}
