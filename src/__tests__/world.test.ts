import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";

// Clear localStorage and module cache before importing the store
// so each test starts fresh
beforeEach(() => {
  localStorage.clear();
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

// We need to re-import the store fresh each time to reset the Zustand state.
// Vitest module cache makes this tricky, so we test against a single import
// and use store.setState to reset between tests.
import { useWorldStore } from "../store/world";

describe("useWorldStore", () => {
  beforeEach(() => {
    // Reset store to defaults
    useWorldStore.setState({
      playerX: 320,
      playerY: 240,
      currentMap: "world",
      facing: "down",
      transitioning: false,
    });
  });

  describe("default values", () => {
    it("has default player position 320, 240", () => {
      const state = useWorldStore.getState();
      expect(state.playerX).toBe(320);
      expect(state.playerY).toBe(240);
    });

    it("has default map world", () => {
      expect(useWorldStore.getState().currentMap).toBe("world");
    });

    it("has default facing down", () => {
      expect(useWorldStore.getState().facing).toBe("down");
    });

    it("is not transitioning by default", () => {
      expect(useWorldStore.getState().transitioning).toBe(false);
    });
  });

  describe("setPosition", () => {
    it("updates playerX and playerY", () => {
      useWorldStore.getState().setPosition(100, 200);
      const state = useWorldStore.getState();
      expect(state.playerX).toBe(100);
      expect(state.playerY).toBe(200);
    });
  });

  describe("setFacing", () => {
    it("updates facing direction", () => {
      useWorldStore.getState().setFacing("up");
      expect(useWorldStore.getState().facing).toBe("up");
    });
  });

  describe("setMap", () => {
    it("updates currentMap", () => {
      useWorldStore.getState().setMap("world");
      expect(useWorldStore.getState().currentMap).toBe("world");
    });
  });

  describe("setTransitioning", () => {
    it("updates transitioning flag", () => {
      useWorldStore.getState().setTransitioning(true);
      expect(useWorldStore.getState().transitioning).toBe(true);
    });
  });

  describe("localStorage persistence", () => {
    it("saves state to localStorage after debounce", () => {
      useWorldStore.getState().setPosition(500, 600);
      // Advance past the 1s debounce
      vi.advanceTimersByTime(1100);
      const raw = localStorage.getItem("clawworld-save");
      expect(raw).toBeTruthy();
      const saved = JSON.parse(raw!);
      expect(saved.playerX).toBe(500);
      expect(saved.playerY).toBe(600);
    });

    it("does not save before debounce period", () => {
      localStorage.clear();
      useWorldStore.getState().setPosition(500, 600);
      vi.advanceTimersByTime(500); // only 500ms
      const raw = localStorage.getItem("clawworld-save");
      expect(raw).toBeNull();
    });

    it("saves currentMap and facing", () => {
      useWorldStore.getState().setMap("guild-hall");
      useWorldStore.getState().setFacing("left");
      vi.advanceTimersByTime(1100);
      const saved = JSON.parse(localStorage.getItem("clawworld-save")!);
      expect(saved.currentMap).toBe("guild-hall");
      expect(saved.facing).toBe("left");
    });

    it("does not save transitioning state", () => {
      useWorldStore.getState().setTransitioning(true);
      vi.advanceTimersByTime(1100);
      const saved = JSON.parse(localStorage.getItem("clawworld-save")!);
      expect(saved.transitioning).toBeUndefined();
    });

    it("debounces rapid changes (only saves final state)", () => {
      useWorldStore.getState().setPosition(100, 100);
      vi.advanceTimersByTime(500);
      useWorldStore.getState().setPosition(200, 200);
      vi.advanceTimersByTime(500);
      useWorldStore.getState().setPosition(300, 300);
      vi.advanceTimersByTime(1100);
      const saved = JSON.parse(localStorage.getItem("clawworld-save")!);
      expect(saved.playerX).toBe(300);
      expect(saved.playerY).toBe(300);
    });
  });
});
