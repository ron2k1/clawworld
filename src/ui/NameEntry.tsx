import { useState, useRef, useEffect } from "react";

const STORAGE_KEY = "clawworld-playerName";

export function getPlayerName(): string {
  return localStorage.getItem(STORAGE_KEY) ?? "";
}

interface NameEntryProps {
  onSubmit: (name: string) => void;
}

export function NameEntry({ onSubmit }: NameEntryProps) {
  const [name, setName] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    localStorage.setItem(STORAGE_KEY, trimmed);
    onSubmit(trimmed);
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0, 0, 0, 0.85)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        fontFamily: "'Press Start 2P', monospace",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          background: "linear-gradient(180deg, #1a1a2e 0%, #16213e 100%)",
          border: "2px solid #e2e8f0",
          borderRadius: 8,
          padding: "32px 40px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 20,
          maxWidth: 400,
        }}
      >
        <h2
          style={{
            color: "#e2e8f0",
            fontSize: 16,
            margin: 0,
            textAlign: "center",
          }}
        >
          Welcome to ClawWorld
        </h2>
        <p
          style={{
            color: "#a0aec0",
            fontSize: 10,
            margin: 0,
            lineHeight: 1.8,
            textAlign: "center",
          }}
        >
          What is your name, traveler?
        </p>
        <input
          ref={inputRef}
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={16}
          placeholder="Enter your name..."
          style={{
            width: "100%",
            padding: "10px 12px",
            background: "#2d3748",
            color: "#e2e8f0",
            border: "1px solid #4a5568",
            borderRadius: 4,
            fontFamily: "inherit",
            fontSize: 12,
            outline: "none",
            textAlign: "center",
            boxSizing: "border-box",
          }}
        />
        <button
          type="submit"
          disabled={!name.trim()}
          style={{
            padding: "10px 24px",
            background: name.trim() ? "#4299e1" : "#2d3748",
            color: "#e2e8f0",
            border: "none",
            borderRadius: 4,
            cursor: name.trim() ? "pointer" : "default",
            fontFamily: "inherit",
            fontSize: 11,
          }}
        >
          Begin Adventure
        </button>
      </form>
    </div>
  );
}
