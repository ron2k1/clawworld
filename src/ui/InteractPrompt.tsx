interface InteractPromptProps {
  npcName: string;
  visible: boolean;
}

export function InteractPrompt({ npcName, visible }: InteractPromptProps) {
  if (!visible) return null;

  return (
    <div
      style={{
        position: "absolute",
        bottom: 80,
        left: "50%",
        transform: "translateX(-50%)",
        background: "rgba(0, 0, 0, 0.75)",
        color: "#fff",
        padding: "6px 16px",
        borderRadius: 8,
        fontSize: 14,
        fontFamily: "monospace",
        pointerEvents: "none",
        zIndex: 40,
        whiteSpace: "nowrap",
      }}
    >
      Press <strong>Space</strong> to talk to {npcName}
    </div>
  );
}
