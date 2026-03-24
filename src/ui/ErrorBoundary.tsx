import { Component, type ReactNode } from "react";

interface ErrorBoundaryProps {
  fallback?: ReactNode;
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo): void {
    console.error("[ClawWorld] Uncaught error:", error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100%",
            background: "#111",
            color: "#e2e8f0",
            fontFamily: "'Press Start 2P', monospace",
            fontSize: "12px",
            padding: "20px",
            textAlign: "center",
          }}
        >
          <p style={{ marginBottom: "12px" }}>Something went wrong.</p>
          <p style={{ fontSize: "10px", color: "#fc8181", marginBottom: "16px" }}>
            {this.state.error?.message}
          </p>
          <button
            onClick={this.handleReset}
            style={{
              padding: "8px 16px",
              background: "#4299e1",
              color: "#e2e8f0",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontFamily: "inherit",
              fontSize: "11px",
            }}
          >
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
