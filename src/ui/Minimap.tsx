import { useEffect, useRef } from 'react';
import { useWorldStore } from '../store/world';
import { npcManager } from '../engine/npcManager';

interface MinimapProps {
  tileData: number[];
  mapWidth: number;
  mapHeight: number;
  tileSize: number;
}

const SCALE = 2; // 2px per tile

// Tile-ID-to-color classification based on build_maps.py constants
const GRASS_IDS = new Set([1, 2, 3, 4, 5, 6, 7, 28, 29, 30, 31, 32, 33, 34, 55, 56, 57]);
const SIDEWALK_IDS = new Set([9, 10, 11, 14, 15, 36, 37, 38, 41, 42, 63, 64, 65]);
const ROAD_IDS = new Set([434, 461, 462, 407, 408, 437, 438, 465, 439, 466, 440, 441, 442, 443, 467, 468, 469, 470]);
const RED_ROOF_IDS = new Set([17, 18, 19, 20, 21, 44, 45, 46, 47, 48, 71, 72, 73, 74, 75, 76]);
const BROWN_ROOF_IDS = new Set([98, 99, 100, 101, 102, 125, 126, 127, 128, 129, 152, 153, 154, 155, 156]);
const WATER_IDS = new Set([171, 172, 173, 198, 199, 200, 225, 226, 227]);
const FACADE_IDS = new Set([329, 330, 331, 332, 333, 361, 362, 413, 414, 415, 416, 435, 436]);
const TREE_IDS = new Set([233, 260, 234, 235, 236, 261, 262, 263, 287, 288, 289, 290, 291, 292, 314, 315, 316, 341, 342, 343]);
const VEHICLE_IDS = new Set([421, 422, 423, 424, 448, 449, 475, 476, 427, 454]);

function tileColor(id: number): string {
  if (GRASS_IDS.has(id)) return '#5a5';
  if (SIDEWALK_IDS.has(id)) return '#bbb';
  if (ROAD_IDS.has(id)) return '#555';
  if (RED_ROOF_IDS.has(id)) return '#a44';
  if (BROWN_ROOF_IDS.has(id)) return '#964';
  if (WATER_IDS.has(id)) return '#38c';
  if (FACADE_IDS.has(id)) return '#876';
  if (TREE_IDS.has(id)) return '#3a3';
  if (VEHICLE_IDS.has(id)) return '#666';
  return '#999';
}

function statusDotColor(activity: string, locomotion: string): string {
  if (activity === 'busy') return '#f44';
  if (locomotion !== 'stationary') return '#fc4';
  return '#4f4';
}

export function Minimap({ tileData, mapWidth, mapHeight, tileSize }: MinimapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const baseImageRef = useRef<ImageData | null>(null);

  const canvasW = mapWidth * SCALE;
  const canvasH = mapHeight * SCALE;

  // Pre-render base image when tile data changes
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || tileData.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const imageData = ctx.createImageData(canvasW, canvasH);
    const pixels = imageData.data;

    for (let row = 0; row < mapHeight; row++) {
      for (let col = 0; col < mapWidth; col++) {
        const tileId = tileData[row * mapWidth + col];
        const color = tileColor(tileId);

        // Parse hex color
        const r = parseInt(color[1], 16) * 17;
        const g = parseInt(color[2], 16) * 17;
        const b = parseInt(color[3], 16) * 17;

        // Fill SCALE×SCALE block
        for (let dy = 0; dy < SCALE; dy++) {
          for (let dx = 0; dx < SCALE; dx++) {
            const px = (col * SCALE + dx);
            const py = (row * SCALE + dy);
            const idx = (py * canvasW + px) * 4;
            pixels[idx] = r;
            pixels[idx + 1] = g;
            pixels[idx + 2] = b;
            pixels[idx + 3] = 255;
          }
        }
      }
    }

    baseImageRef.current = imageData;
    ctx.putImageData(imageData, 0, 0);
  }, [tileData, mapWidth, mapHeight, canvasW, canvasH]);

  // Dynamic overlay: subscribe to store for player/camera position
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId = 0;
    let npcStates = npcManager.getStates();

    // Refresh NPC states every 500ms
    const npcInterval = setInterval(() => {
      npcStates = npcManager.getStates();
    }, 500);

    const draw = () => {
      const base = baseImageRef.current;
      if (!base) {
        animId = requestAnimationFrame(draw);
        return;
      }

      const { playerX, playerY, cameraX, cameraY } = useWorldStore.getState();

      // Restore base image
      ctx.putImageData(base, 0, 0);

      // Camera viewport rectangle
      const vpX = (cameraX / tileSize) * SCALE;
      const vpY = (cameraY / tileSize) * SCALE;
      const vpW = (800 / tileSize) * SCALE;  // 800px viewport
      const vpH = (600 / tileSize) * SCALE;  // 600px viewport
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.35)';
      ctx.lineWidth = 1;
      ctx.strokeRect(vpX + 0.5, vpY + 0.5, vpW, vpH);

      // NPC dots
      for (const npc of npcStates) {
        if (npc.currentMap !== useWorldStore.getState().currentMap) continue;
        const nx = npc.tileX * SCALE + SCALE / 2;
        const ny = npc.tileY * SCALE + SCALE / 2;
        ctx.fillStyle = statusDotColor(npc.activity, npc.locomotion);
        ctx.fillRect(nx - 1, ny - 1, 3, 3);
      }

      // Player dot (white with black outline)
      const px = (playerX / tileSize) * SCALE;
      const py = (playerY / tileSize) * SCALE;
      ctx.fillStyle = '#000';
      ctx.fillRect(px - 2, py - 2, 5, 5);
      ctx.fillStyle = '#fff';
      ctx.fillRect(px - 1, py - 1, 3, 3);

      animId = requestAnimationFrame(draw);
    };

    animId = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animId);
      clearInterval(npcInterval);
    };
  }, [tileSize, canvasW, canvasH]);

  return (
    <div style={{
      position: 'absolute',
      top: 8,
      left: 8,
      background: 'rgba(10, 10, 20, 0.8)',
      border: '1px solid #556',
      borderRadius: 4,
      padding: 3,
      zIndex: 10,
      pointerEvents: 'none',
    }}>
      <canvas
        ref={canvasRef}
        width={canvasW}
        height={canvasH}
        style={{
          display: 'block',
          imageRendering: 'pixelated',
        }}
      />
    </div>
  );
}
