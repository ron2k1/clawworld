import { create } from 'zustand';

type Direction = 'up' | 'down' | 'left' | 'right';

interface WorldState {
  playerX: number;
  playerY: number;
  currentMap: string;
  facing: Direction;
  transitioning: boolean;
  movementLocked: boolean;
  dialogueOpen: boolean;
  activeNPCId: string | null;
  activeNPCName: string | null;
  activeNPCPortrait: string | null;
  gatewayConnected: boolean;
  dashboardOpen: boolean;
  cameraX: number;
  cameraY: number;
  setPosition: (x: number, y: number) => void;
  setCameraPosition: (x: number, y: number) => void;
  setFacing: (direction: Direction) => void;
  setMap: (mapName: string) => void;
  setTransitioning: (v: boolean) => void;
  openDialogue: (npcId: string, npcName: string, portrait?: string) => void;
  closeDialogue: () => void;
  setGatewayConnected: (v: boolean) => void;
  toggleDashboard: () => void;
}

const SAVE_KEY = 'clawworld-save';

function loadSave(): Partial<Pick<WorldState, 'playerX' | 'playerY' | 'currentMap' | 'facing'>> {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* ignore corrupt data */ }
  return {};
}

const saved = loadSave();

export const useWorldStore = create<WorldState>((set) => ({
  playerX: saved.playerX ?? 320,
  playerY: saved.playerY ?? 240,
  currentMap: saved.currentMap ?? 'world',
  facing: saved.facing ?? 'down',
  transitioning: false,
  movementLocked: false,
  dialogueOpen: false,
  activeNPCId: null,
  activeNPCName: null,
  activeNPCPortrait: null,
  gatewayConnected: false,
  dashboardOpen: false,
  cameraX: 0,
  cameraY: 0,
  setPosition: (x, y) => set({ playerX: x, playerY: y }),
  setCameraPosition: (x, y) => set({ cameraX: x, cameraY: y }),
  setFacing: (direction) => set({ facing: direction }),
  setMap: (mapName) => set({ currentMap: mapName }),
  setTransitioning: (v) => set({ transitioning: v }),
  openDialogue: (npcId, npcName, portrait) => set({ dialogueOpen: true, activeNPCId: npcId, activeNPCName: npcName, activeNPCPortrait: portrait ?? null, movementLocked: true }),
  closeDialogue: () => set({ dialogueOpen: false, activeNPCId: null, activeNPCName: null, activeNPCPortrait: null, movementLocked: false }),
  setGatewayConnected: (v) => set({ gatewayConnected: v }),
  toggleDashboard: () => set((s) => ({ dashboardOpen: !s.dashboardOpen })),
}));

// Debounced localStorage auto-save
let saveTimeout: ReturnType<typeof setTimeout> | null = null;

useWorldStore.subscribe((state) => {
  if (saveTimeout) clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => {
    const { playerX, playerY, currentMap, facing } = state;
    localStorage.setItem(SAVE_KEY, JSON.stringify({ playerX, playerY, currentMap, facing }));
  }, 1000);
});
