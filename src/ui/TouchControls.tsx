import { useCallback } from "react";

interface TouchControlsProps {
  onDirection: (dir: "up" | "down" | "left" | "right", pressed: boolean) => void;
  onAction: () => void;
}

const BTN_SIZE = 48;
const BTN_STYLE: React.CSSProperties = {
  width: BTN_SIZE,
  height: BTN_SIZE,
  background: "rgba(255, 255, 255, 0.15)",
  border: "2px solid rgba(255, 255, 255, 0.3)",
  borderRadius: 8,
  color: "#fff",
  fontSize: 20,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  userSelect: "none",
  touchAction: "none",
  cursor: "pointer",
};

export function TouchControls({ onDirection, onAction }: TouchControlsProps) {
  const press = useCallback(
    (dir: "up" | "down" | "left" | "right") => () => onDirection(dir, true),
    [onDirection],
  );
  const release = useCallback(
    (dir: "up" | "down" | "left" | "right") => () => onDirection(dir, false),
    [onDirection],
  );

  return (
    <div
      style={{
        position: "fixed",
        bottom: 0,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-end",
        padding: 16,
        pointerEvents: "none",
        zIndex: 200,
      }}
      aria-hidden="true"
    >
      {/* D-pad */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `${BTN_SIZE}px ${BTN_SIZE}px ${BTN_SIZE}px`,
          gridTemplateRows: `${BTN_SIZE}px ${BTN_SIZE}px ${BTN_SIZE}px`,
          gap: 4,
          pointerEvents: "auto",
        }}
      >
        <div />
        <button
          style={BTN_STYLE}
          onTouchStart={press("up")}
          onTouchEnd={release("up")}
          onMouseDown={press("up")}
          onMouseUp={release("up")}
          aria-label="Move up"
        >
          &#9650;
        </button>
        <div />
        <button
          style={BTN_STYLE}
          onTouchStart={press("left")}
          onTouchEnd={release("left")}
          onMouseDown={press("left")}
          onMouseUp={release("left")}
          aria-label="Move left"
        >
          &#9664;
        </button>
        <div />
        <button
          style={BTN_STYLE}
          onTouchStart={press("right")}
          onTouchEnd={release("right")}
          onMouseDown={press("right")}
          onMouseUp={release("right")}
          aria-label="Move right"
        >
          &#9654;
        </button>
        <div />
        <button
          style={BTN_STYLE}
          onTouchStart={press("down")}
          onTouchEnd={release("down")}
          onMouseDown={press("down")}
          onMouseUp={release("down")}
          aria-label="Move down"
        >
          &#9660;
        </button>
        <div />
      </div>

      {/* Action button */}
      <button
        style={{
          ...BTN_STYLE,
          width: 64,
          height: 64,
          borderRadius: 32,
          fontSize: 16,
          fontFamily: "'Press Start 2P', monospace",
          pointerEvents: "auto",
        }}
        onTouchStart={onAction}
        onMouseDown={onAction}
        aria-label="Interact"
      >
        A
      </button>
    </div>
  );
}
