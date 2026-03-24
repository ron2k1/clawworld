import { useCallback, useEffect, useRef, useState } from "react";
import { Renderer } from "./engine/renderer";
import { Camera } from "./engine/camera";
import { Player } from "./engine/player";
import { NPC } from "./engine/npc";
import { MapLoader, WarpTrigger } from "./engine/mapLoader";
import { npcRegistry } from "./data/agents";
import { useWorldStore } from "./store/world";
import { HUD } from "./ui/HUD";
import { NameEntry, getPlayerName } from "./ui/NameEntry";
import { TouchControls } from "./ui/TouchControls";
import { DialogueBox } from "./ui/DialogueBox";
import { GatewayStatus } from "./ui/GatewayStatus";
import { InteractPrompt } from "./ui/InteractPrompt";
import { ErrorBoundary } from "./ui/ErrorBoundary";
import { GatewayClient } from "./gateway/client";
import { TypewriterBuffer } from "./gateway/stream";
import { npcManager } from "./engine/npcManager";
import { Dashboard } from "./ui/Dashboard";
import { Minimap } from "./ui/Minimap";
import { getZoneAt } from "./engine/zones";

const CANVAS_W = 800;
const CANVAS_H = 600;

function createPlaceholderSprite(color: string): HTMLImageElement {
  const canvas = document.createElement("canvas");
  canvas.width = 64;
  canvas.height = 128;
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = color;
  for (let row = 0; row < 4; row++) {
    for (let col = 0; col < 2; col++) {
      ctx.fillRect(col * 32 + 4, row * 32 + 4, 24, 24);
    }
  }
  const img = new Image();
  img.src = canvas.toDataURL();
  return img;
}

function loadNPCSprite(agentId: string, fallbackColor: string): Promise<HTMLImageElement> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => resolve(createPlaceholderSprite(fallbackColor));
    img.src = `/sprites/npcs/${agentId}/sprite.png`;
  });
}

const NPC_COLORS: Record<string, string> = {
  assistant: "#4af",
  analyst: "#f84",
  coder: "#8f4",
  lorekeeper: "#c8f",
  trader: "#fc4",
  townsfolk: "#aaa",
  jake: "#da5",
  tom: "#8a6",
  mira: "#f8a",
  inspector: "#f64",
  debugger: "#6cf",
  "hermes-agent": "#f0c",
};

const DIR_KEYS: Record<string, string> = {
  up: "ArrowUp",
  down: "ArrowDown",
  left: "ArrowLeft",
  right: "ArrowRight",
};

const isTouchDevice =
  typeof window !== "undefined" && ("ontouchstart" in window || navigator.maxTouchPoints > 0);

export default function App() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const playerRef = useRef<Player | null>(null);
  const npcsRef = useRef<NPC[]>([]);
  const [currentMap, setCurrentMap] = useState("world");
  const [playerName, setPlayerName] = useState(() => getPlayerName());
  const [nearbyNPC, setNearbyNPC] = useState<{ id: string; name: string; portraitUrl?: string } | null>(null);
  const [displayText, setDisplayText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [dialogueError, setDialogueError] = useState<string | undefined>();
  const [mapLoading, setMapLoading] = useState(true);
  const [minimapVisible, setMinimapVisible] = useState(true);
  const [currentZone, setCurrentZone] = useState<string | null>(null);
  const [minimapData, setMinimapData] = useState<{ tileData: number[]; width: number; height: number; tileSize: number } | null>(null);
  const prevZoneRef = useRef<string | null>(null);
  const gatewayRef = useRef<GatewayClient | null>(null);
  const twRef = useRef<TypewriterBuffer | null>(null);

  const { dialogueOpen, activeNPCId, activeNPCName, activeNPCPortrait, gatewayConnected, dashboardOpen, openDialogue, closeDialogue, setGatewayConnected, toggleDashboard } = useWorldStore();

  const handleTouchDirection = useCallback(
    (dir: "up" | "down" | "left" | "right", pressed: boolean) => {
      const p = playerRef.current;
      if (!p) return;
      if (pressed) p.pressKey(DIR_KEYS[dir]);
      else p.releaseKey(DIR_KEYS[dir]);
    },
    [],
  );

  const handleTouchAction = useCallback(() => {
    // Simulate Space key press for NPC interaction
    window.dispatchEvent(new KeyboardEvent("keydown", { key: " " }));
    setTimeout(() => {
      window.dispatchEvent(new KeyboardEvent("keyup", { key: " " }));
    }, 100);
  }, []);

  // Connect to gateway
  useEffect(() => {
    const gw = new GatewayClient();
    gatewayRef.current = gw;

    gw.onDelta((agentId, text) => {
      // Mark NPC as active while streaming
      const npc = npcsRef.current.find(n => n.agentId === agentId);
      if (npc) npc.active = true;

      // Only push text if this agent is the one we're talking to
      const activeId = useWorldStore.getState().activeNPCId;
      if (agentId !== activeId) return;

      if (!twRef.current) {
        twRef.current = new TypewriterBuffer();
        twRef.current.onReveal((visible) => setDisplayText(visible));
      }
      twRef.current.push(text);
    });

    gw.onEnd((agentId) => {
      // Mark NPC as no longer active
      const npc = npcsRef.current.find(n => n.agentId === agentId);
      if (npc) npc.active = false;

      // Only update streaming state if this is the active dialogue
      const activeId = useWorldStore.getState().activeNPCId;
      if (agentId === activeId) {
        setIsStreaming(false);
      }
    });

    gw.onError((agentId, message) => {
      const activeId = useWorldStore.getState().activeNPCId;
      if (!agentId || agentId === activeId) {
        setDialogueError(message);
        setIsStreaming(false);
      }
    });

    gw.onStatus((connected) => setGatewayConnected(connected));

    gw.connect()
      .then(() => setGatewayConnected(true))
      .catch(() => {
        console.warn("Gateway not available — NPC chat disabled (start gateway with: python -m gateway.server)");
        setGatewayConnected(false);
      });

    return () => {
      gw.clearHandlers();
      gw.disconnect();
      gatewayRef.current = null;
    };
  }, [setGatewayConnected]);

  // Space key to interact, Escape to close
  // Suppress movement keys while dialogue is open so they don't leak into the input
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      // Block movement keys while dialogue is open, but let text flow to the input
      if (dialogueOpen) {
        const isTypingInInput = document.activeElement?.tagName === "INPUT";
        if (isTypingInInput) {
          // Only block arrow keys and space when typing — let all letters through
          if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " "].includes(e.key)) {
            e.stopPropagation();
          }
          return; // let the input handle everything else
        }
        // No input focused — block all movement keys
        const movementKeys = ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "w", "a", "s", "d", "W", "A", "S", "D", " "];
        if (movementKeys.includes(e.key)) {
          e.preventDefault();
          e.stopPropagation();
        }
      }

      if (e.key === " " && !dialogueOpen && nearbyNPC) {
        e.preventDefault();
        e.stopPropagation();
        const player = playerRef.current;
        const npc = npcsRef.current.find(n => n.agentId === nearbyNPC.id);
        if (player && npc) {
          npc.faceTo(player.x, player.y);
        }
        openDialogue(nearbyNPC.id, nearbyNPC.name, nearbyNPC.portraitUrl);
        player!.locked = true;
        player!.clearKeys();
        setDisplayText("");
        setDialogueError(undefined);
        if (twRef.current) {
          twRef.current.destroy();
          twRef.current = null;
        }
      }
      if (e.key === "Escape" && dashboardOpen) {
        e.preventDefault();
        toggleDashboard();
        return;
      }
      if (e.key === "Tab" && !dialogueOpen) {
        e.preventDefault();
        toggleDashboard();
        return;
      }
      if ((e.key === "m" || e.key === "M") && !dialogueOpen) {
        setMinimapVisible((v) => !v);
        return;
      }
      if (e.key === "Escape" && dialogueOpen) {
        e.preventDefault();
        handleCloseDialogue();
      }
    }
    window.addEventListener("keydown", onKeyDown, { capture: true });
    return () => window.removeEventListener("keydown", onKeyDown, { capture: true });
  }, [dialogueOpen, nearbyNPC, openDialogue]);

  function handleSummonNPC(agentId: string) {
    const currentMapName = useWorldStore.getState().currentMap;
    const player = playerRef.current;
    if (!player) return;
    const targetCol = Math.floor((player.x + 32) / 32) + 2;
    const targetRow = Math.floor((player.y + 54) / 32);
    npcManager.summon(agentId, currentMapName, targetCol, targetRow);
  }

  function handleReturnNPC(agentId: string) {
    npcManager.returnHome(agentId);
  }

  function handleCloseDialogue() {
    // Clear active state on any streaming NPC before closing
    for (const npc of npcsRef.current) {
      npc.active = false;
    }
    closeDialogue();
    if (playerRef.current) {
      playerRef.current.clearKeys();
      playerRef.current.locked = false;
    }
    setDisplayText("");
    setIsStreaming(false);
    setDialogueError(undefined);
    if (twRef.current) {
      twRef.current.destroy();
      twRef.current = null;
    }
  }

  function handleSendMessage(message: string) {
    if (!gatewayRef.current || !activeNPCId) return;
    setDisplayText("");
    setIsStreaming(true);
    setDialogueError(undefined);
    if (twRef.current) twRef.current.destroy();
    const tw = new TypewriterBuffer();
    tw.onReveal((visible) => setDisplayText(visible));
    twRef.current = tw;
    gatewayRef.current.sendMessage(activeNPCId, message);
  }

  function handleRetry() {
    if (!gatewayRef.current || !activeNPCId) return;
    setDialogueError(undefined);
    setIsStreaming(true);
    if (twRef.current) twRef.current.destroy();
    const tw = new TypewriterBuffer();
    tw.onReveal((visible) => setDisplayText(visible));
    twRef.current = tw;
    gatewayRef.current.sendMessage(activeNPCId, "");
  }

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const renderer = new Renderer(ctx);
    const camera = new Camera(CANVAS_W, CANVAS_H);
    const player = new Player(25 * 32, 18 * 32); // Start at city crossroads sidewalk
    playerRef.current = player;
    const mapLoader = new MapLoader();
    npcManager.init(npcRegistry);

    let running = true;
    let syncCounter = 0;
    let disposed = false;
    let animId = 0;
    let npcs: NPC[] = [];
    let warps: WarpTrigger[] = [];
    let fadeAlpha = 0; // 0 = clear, 1 = black
    let transitioning = false;
    let lastNearbyId: string | null = null;

    async function spawnNPCs(mapName: string, mapNpcs: { agentId: string; name: string; x: number; y: number; facing: string }[]) {
      const spawns: Promise<NPC>[] = [];

      // Spawn from map objects
      for (const spawn of mapNpcs) {
        const color = NPC_COLORS[spawn.agentId] ?? "#888";
        spawns.push(
          loadNPCSprite(spawn.agentId, color).then(
            (sprite) => new NPC(spawn.agentId, spawn.name, spawn.x, spawn.y, sprite, spawn.facing as 'up' | 'down' | 'left' | 'right'),
          ),
        );
      }

      // Also spawn from npcRegistry for this map (if not already in map objects)
      const spawnedIds = new Set(mapNpcs.map(n => n.agentId));
      for (const reg of npcRegistry) {
        if (reg.map === mapName && !spawnedIds.has(reg.agentId)) {
          const color = NPC_COLORS[reg.agentId] ?? "#888";
          spawns.push(
            loadNPCSprite(reg.agentId, color).then(
              (sprite) => new NPC(reg.agentId, reg.name, reg.tileX * 32, reg.tileY * 32, sprite, reg.facing),
            ),
          );
        }
      }

      npcs = await Promise.all(spawns);
      // Set home/current map on all NPCs
      for (const npc of npcs) {
        const reg = npcRegistry.find(r => r.agentId === npc.agentId);
        npc.homeMap = reg?.map ?? mapName;
        npc.currentMap = mapName;
        npc.homeTileX = reg?.tileX ?? Math.floor(npc.x / 32);
        npc.homeTileY = reg?.tileY ?? Math.floor(npc.y / 32);
      }
      if (!disposed) npcsRef.current = npcs;
    }

    async function loadMap(mapName: string, spawnX?: number, spawnY?: number) {
      const data = await mapLoader.load(mapName);
      // Resolve tileset path from map JSON (relative to /data/maps/)
      const tilesetSrc = data.tilemap.tilesetImage
        ? `/tilesets/${data.tilemap.tilesetImage.split('/').pop()}`
        : '/tilesets/urban.png';
      await renderer.loadTileset(tilesetSrc, data.tilemap.tilesetColumns);

      warps = data.warps;
      await spawnNPCs(mapName, data.npcs);

      if (spawnX !== undefined && spawnY !== undefined) {
        player.x = spawnX;
        player.y = spawnY;
      }

      // Snap camera to player immediately on map change
      const mapPxW = data.tilemap.width * data.tilemap.tileSize;
      const mapPxH = data.tilemap.height * data.tilemap.tileSize;
      camera.follow(
        player.x + player.spriteWidth / 2,
        player.y + player.spriteHeight / 2,
        mapPxW,
        mapPxH,
      );
      // Force immediate snap (override lerp)
      camera.x = Math.max(0, Math.min(
        player.x + player.spriteWidth / 2 - CANVAS_W / 2,
        mapPxW - CANVAS_W,
      ));
      camera.y = Math.max(0, Math.min(
        player.y + player.spriteHeight / 2 - CANVAS_H / 2,
        mapPxH - CANVAS_H,
      ));

      useWorldStore.getState().setMap(mapName);
      useWorldStore.getState().setPosition(player.x, player.y);
      useWorldStore.getState().setCameraPosition(camera.x, camera.y);
      setCurrentMap(mapName);

      // Capture tile data for minimap
      setMinimapData({
        tileData: [...data.tilemap.data],
        width: data.tilemap.width,
        height: data.tilemap.height,
        tileSize: data.tilemap.tileSize,
      });

      return data;
    }

    let warpCooldownUntil = 0; // Prevents immediate warp bounce after transitions

    async function doTransition(warp: WarpTrigger) {
      if (transitioning) return;
      transitioning = true;

      // Fade to black over 300ms
      const fadeStart = performance.now();
      await new Promise<void>((resolve) => {
        function fadeOut() {
          const elapsed = performance.now() - fadeStart;
          fadeAlpha = Math.min(1, elapsed / 300);
          if (fadeAlpha < 1) {
            requestAnimationFrame(fadeOut);
          } else {
            resolve();
          }
        }
        fadeOut();
      });

      // Load new map and reposition player
      await loadMap(warp.targetMap, warp.targetX, warp.targetY);

      // Fade back in over 300ms
      const fadeInStart = performance.now();
      await new Promise<void>((resolve) => {
        function fadeIn() {
          const elapsed = performance.now() - fadeInStart;
          fadeAlpha = Math.max(0, 1 - elapsed / 300);
          if (fadeAlpha > 0) {
            requestAnimationFrame(fadeIn);
          } else {
            resolve();
          }
        }
        fadeIn();
      });

      // Cooldown: ignore warps for 500ms after transition to prevent bounce
      warpCooldownUntil = performance.now() + 500;
      transitioning = false;
    }

    async function init() {
      const data = await loadMap("world");
      await player.loadSprite("/sprites/player.png");
      setMapLoading(false);
      let tilemap = data.tilemap;

      function loop() {
        if (!running) return;

        if (!transitioning) {
          player.update(tilemap);

          // Build occupancy set for NPC collision avoidance
          const occupied = new Set<string>();
          const playerCol = Math.floor((player.x + 32) / 32);
          const playerRow = Math.floor((player.y + 54) / 32);
          occupied.add(`${playerCol},${playerRow}`);
          for (const npc of npcs) {
            occupied.add(`${npc.tileCol},${npc.tileRow}`);
          }

          // Update NPC movement
          for (const npc of npcs) {
            npc.update(tilemap, occupied);
          }

          // Sync NPC states to manager (throttled to every 30 frames ~500ms)
          syncCounter++;
          if (syncCounter >= 30) {
            syncCounter = 0;
            for (const npc of npcs) {
              npcManager.syncFromNPC(npc);
            }
          }

          // Check warp triggers (use feet area, not full sprite)
          const hit = performance.now() > warpCooldownUntil
            ? mapLoader.checkWarps(
                player.x + 20, player.y + 44,
                24, 20,
                warps,
              )
            : null;
          if (hit) {
            doTransition(hit).then(() => {
              // Update tilemap reference after transition
              const cached = mapLoader["cache"].get(useWorldStore.getState().currentMap);
              if (cached) tilemap = cached.tilemap;
            });
          }

          // Sync world store
          useWorldStore.getState().setPosition(player.x, player.y);

          // Zone tracking (world map only)
          const storeMap = useWorldStore.getState().currentMap;
          if (storeMap === 'world') {
            const pCol = Math.floor((player.x + 32) / tilemap.tileSize);
            const pRow = Math.floor((player.y + 54) / tilemap.tileSize);
            const zone = getZoneAt(pCol, pRow);
            const zName = zone?.name ?? null;
            if (zName !== prevZoneRef.current) {
              prevZoneRef.current = zName;
              setCurrentZone(zName);
            }
          } else if (prevZoneRef.current !== null) {
            prevZoneRef.current = null;
            setCurrentZone(null);
          }

          // NPC proximity detection — only update React state when the nearby NPC changes
          let closestNpc: NPC | null = null;
          for (const npc of npcs) {
            if (npc.isInRange(player.x, player.y)) {
              closestNpc = npc;
              break;
            }
          }
          const closestId = closestNpc?.agentId ?? null;
          if (closestId !== lastNearbyId) {
            lastNearbyId = closestId;
            if (closestNpc) {
              const reg = npcRegistry.find(r => r.agentId === closestNpc.agentId);
              setNearbyNPC({ id: closestNpc.agentId, name: closestNpc.name, portraitUrl: reg?.portraitUrl });
            } else {
              setNearbyNPC(null);
            }
          }
        }

        const mapPxW = tilemap.width * tilemap.tileSize;
        const mapPxH = tilemap.height * tilemap.tileSize;
        camera.follow(
          player.x + player.spriteWidth / 2,
          player.y + player.spriteHeight / 2,
          mapPxW,
          mapPxH,
        );
        useWorldStore.getState().setCameraPosition(camera.x, camera.y);

        renderer.clear(CANVAS_W, CANVAS_H);
        // Ensure pixel-crisp rendering every frame (save/restore can reset this)
        ctx!.imageSmoothingEnabled = false;

        // Draw map tiles
        const startCol = Math.max(0, Math.floor(camera.x / tilemap.tileSize));
        const endCol = Math.min(tilemap.width, Math.ceil((camera.x + CANVAS_W) / tilemap.tileSize));
        const startRow = Math.max(0, Math.floor(camera.y / tilemap.tileSize));
        const endRow = Math.min(tilemap.height, Math.ceil((camera.y + CANVAS_H) / tilemap.tileSize));

        for (let row = startRow; row < endRow; row++) {
          for (let col = startCol; col < endCol; col++) {
            const tileId = tilemap.getTile(col, row);
            if (tileId > 0) {
              renderer.drawTile(
                tileId,
                Math.floor(col * tilemap.tileSize - camera.x),
                Math.floor(row * tilemap.tileSize - camera.y),
              );
            }
          }
        }

        // Draw NPCs (guard against empty array during StrictMode remount)
        for (let i = 0; i < npcs.length; i++) {
          try {
            npcs[i].render(ctx!, camera);
          } catch {
            // Skip broken NPC render to prevent canvas corruption
          }
        }

        // Draw player sprite
        if (player.sprite) {
          renderer.drawSprite(
            player.sprite,
            player.frame,
            player.spriteRow,
            player.spriteWidth,
            player.spriteHeight,
            Math.floor(player.x - camera.x),
            Math.floor(player.y - camera.y),
          );
        }

        // Fade overlay
        if (fadeAlpha > 0) {
          ctx!.fillStyle = `rgba(0, 0, 0, ${fadeAlpha})`;
          ctx!.fillRect(0, 0, CANVAS_W, CANVAS_H);
        }

        animId = requestAnimationFrame(loop);
      }

      loop();
    }

    init().catch((err) => {
      console.error("Failed to initialize game:", err);
      setMapLoading(false);
    });

    return () => {
      running = false;
      disposed = true;
      cancelAnimationFrame(animId);
      player.destroy();
    };
  }, []);

  if (!playerName) {
    return <NameEntry onSubmit={setPlayerName} />;
  }

  return (
    <div style={{ position: "relative", display: "flex", justifyContent: "center", alignItems: "center", height: "100vh", background: "#111" }}>
      <div style={{ position: "relative" }}>
        <canvas ref={canvasRef} width={CANVAS_W} height={CANVAS_H} style={{ imageRendering: "pixelated" }} />
        {mapLoading && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "#111",
              color: "#e2e8f0",
              fontFamily: "'Press Start 2P', monospace",
              fontSize: "14px",
              zIndex: 200,
            }}
          >
            Loading map...
          </div>
        )}
        <HUD currentMap={currentMap} zoneName={currentZone} />
        {minimapVisible && minimapData && (
          <Minimap
            tileData={minimapData.tileData}
            mapWidth={minimapData.width}
            mapHeight={minimapData.height}
            tileSize={minimapData.tileSize}
          />
        )}
        <GatewayStatus connected={gatewayConnected} />
        {!gatewayConnected && !dialogueOpen && (
          <div
            style={{
              position: "absolute",
              bottom: 40,
              left: "50%",
              transform: "translateX(-50%)",
              background: "rgba(0,0,0,0.8)",
              color: "#fc8181",
              fontFamily: "'Press Start 2P', monospace",
              fontSize: "10px",
              padding: "6px 12px",
              borderRadius: "4px",
              zIndex: 50,
              whiteSpace: "nowrap",
            }}
          >
            Gateway disconnected — reconnecting...
          </div>
        )}
        <InteractPrompt npcName={nearbyNPC?.name ?? ""} visible={!dialogueOpen && !!nearbyNPC && gatewayConnected} />
        <ErrorBoundary fallback={<div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: "25%", background: "#1a1a2e", color: "#fc8181", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'Press Start 2P', monospace", fontSize: "12px" }}>Dialogue error — press Escape to close</div>}>
          <DialogueBox
            isOpen={dialogueOpen}
            npcName={activeNPCName ?? ""}
            npcPortrait={activeNPCPortrait ?? undefined}
            displayText={displayText}
            isStreaming={isStreaming}
            error={dialogueError}
            onSendMessage={handleSendMessage}
            onClose={handleCloseDialogue}
            onRetry={handleRetry}
          />
        </ErrorBoundary>
        <Dashboard onSummon={handleSummonNPC} onReturn={handleReturnNPC} />
      </div>
      {isTouchDevice && (
        <TouchControls onDirection={handleTouchDirection} onAction={handleTouchAction} />
      )}
    </div>
  );
}
