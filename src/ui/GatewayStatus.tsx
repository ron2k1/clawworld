interface GatewayStatusProps {
  connected: boolean;
}

export function GatewayStatus({ connected }: GatewayStatusProps) {
  return (
    <div
      style={{
        position: "absolute",
        top: 8,
        right: 8,
        display: "flex",
        alignItems: "center",
        gap: "6px",
        zIndex: 50,
      }}
    >
      {!connected && (
        <span
          style={{
            fontSize: 11,
            color: "#fc8181",
            fontFamily: "monospace",
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        >
          Reconnecting…
        </span>
      )}
      <div
        title={connected ? "Gateway connected" : "Gateway disconnected"}
        style={{
          width: 10,
          height: 10,
          borderRadius: "50%",
          background: connected ? "#48bb78" : "#fc8181",
          boxShadow: connected
            ? "0 0 6px #48bb78"
            : "0 0 6px #fc8181",
          border: "1px solid rgba(255,255,255,0.2)",
          cursor: "default",
          transition: "background 0.3s, box-shadow 0.3s",
        }}
      />
    </div>
  );
}
