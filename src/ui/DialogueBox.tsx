import { useState, useRef, useEffect } from "react";

export interface DialogueBoxProps {
  isOpen: boolean;
  npcName: string;
  npcPortrait?: string;
  displayText: string;
  isStreaming: boolean;
  error?: string | null;
  onSendMessage: (text: string) => void;
  onClose: () => void;
  onRetry?: () => void;
}

export function DialogueBox({
  isOpen,
  npcName,
  npcPortrait,
  displayText,
  isStreaming,
  error,
  onSendMessage,
  onClose,
  onRetry,
}: DialogueBoxProps) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const textRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      setInput(""); // Clear immediately in case movement keys leaked
      setTimeout(() => {
        setInput(""); // Clear again after any delayed key events
        inputRef.current?.focus();
      }, 150);
    } else {
      setInput("");
    }
  }, [isOpen]);

  useEffect(() => {
    if (textRef.current) {
      textRef.current.scrollTop = textRef.current.scrollHeight;
    }
  }, [displayText]);

  // Focus trap: keep Tab within the dialogue when open
  useEffect(() => {
    if (!isOpen) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        return;
      }
      if (e.key === "Tab" && containerRef.current) {
        const focusable = containerRef.current.querySelectorAll<HTMLElement>(
          'input, button, [tabindex]:not([tabindex="-1"])',
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [isOpen, onClose]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const msg = input.trim();
    if (!msg || isStreaming) return;
    onSendMessage(msg);
    setInput("");
  }

  return (
    <div
      ref={containerRef}
      role="dialog"
      aria-label={`Conversation with ${npcName}`}
      aria-modal="true"
      style={{
        position: "absolute",
        bottom: 0,
        left: 0,
        right: 0,
        height: isOpen ? "25%" : 0,
        overflow: "hidden",
        transition: "height 0.25s ease-out",
        zIndex: 100,
      }}
    >
      <div
        style={{
          height: "100%",
          background: "linear-gradient(180deg, #1a1a2e 0%, #16213e 100%)",
          border: "2px solid #e2e8f0",
          borderBottom: "none",
          borderRadius: "8px 8px 0 0",
          display: "flex",
          flexDirection: "column",
          fontFamily: "'Press Start 2P', monospace",
          fontSize: "12px",
          color: "#e2e8f0",
          padding: "8px",
        }}
      >
        {/* Header row */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
          {/* Portrait */}
          <div
            style={{
              width: 48,
              height: 48,
              minWidth: 48,
              borderRadius: 4,
              border: "2px solid #4a5568",
              background: npcPortrait
                ? `url(${npcPortrait}) no-repeat`
                : "#4a5568",
              backgroundSize: npcPortrait ? "200% 400%" : undefined,
              backgroundPosition: npcPortrait ? "0 0" : undefined,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "20px",
            }}
          >
            {!npcPortrait && "?"}
          </div>
          <span style={{ fontWeight: "bold", fontSize: "14px" }}>{npcName}</span>
        </div>

        {/* Text area */}
        <div
          ref={textRef}
          aria-live="polite"
          aria-atomic="false"
          style={{
            flex: 1,
            overflowY: "auto",
            lineHeight: 1.6,
            whiteSpace: "pre-wrap",
            padding: "4px",
          }}
        >
          {displayText}
          {isStreaming && <span style={{ opacity: 0.5 }}>|</span>}
          {error && (
            <div style={{ color: "#fc8181", marginTop: "4px" }}>
              {error}
              {onRetry && (
                <button
                  onClick={onRetry}
                  style={{
                    marginLeft: "8px",
                    padding: "2px 8px",
                    background: "#4a5568",
                    color: "#e2e8f0",
                    border: "1px solid #718096",
                    borderRadius: "4px",
                    cursor: "pointer",
                    fontFamily: "inherit",
                    fontSize: "10px",
                  }}
                >
                  Retry
                </button>
              )}
            </div>
          )}
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} style={{ display: "flex", gap: "4px", marginTop: "4px" }}>
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isStreaming ? "..." : "Say something..."}
            disabled={isStreaming}
            style={{
              flex: 1,
              padding: "6px 8px",
              background: "#2d3748",
              color: "#e2e8f0",
              border: "1px solid #4a5568",
              borderRadius: "4px",
              fontFamily: "inherit",
              fontSize: "11px",
              outline: "none",
            }}
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            style={{
              padding: "6px 12px",
              background: isStreaming ? "#2d3748" : "#4299e1",
              color: "#e2e8f0",
              border: "none",
              borderRadius: "4px",
              cursor: isStreaming ? "default" : "pointer",
              fontFamily: "inherit",
              fontSize: "11px",
            }}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
