import { TileMap, TiledObject } from './tilemap';

export interface WarpTrigger {
  x: number;
  y: number;
  width: number;
  height: number;
  targetMap: string;
  targetX: number;
  targetY: number;
}

export interface NPCSpawn {
  agentId: string;
  name: string;
  x: number;
  y: number;
  facing: 'up' | 'down' | 'left' | 'right';
}

export interface MapData {
  tilemap: TileMap;
  npcs: NPCSpawn[];
  warps: WarpTrigger[];
}

function getProp(obj: TiledObject, name: string): string | number | boolean | undefined {
  return obj.properties?.find((p) => p.name === name)?.value;
}

export class MapLoader {
  private cache = new Map<string, MapData>();

  async load(mapName: string): Promise<MapData> {
    const cached = this.cache.get(mapName);
    if (cached) return cached;

    const tilemap = new TileMap();
    await tilemap.load(`/data/maps/${mapName}.json`);

    const npcs: NPCSpawn[] = [];
    const warps: WarpTrigger[] = [];

    for (const obj of tilemap.objects) {
      if (obj.type === 'npc') {
        npcs.push({
          agentId: String(getProp(obj, 'agentId') ?? obj.name.toLowerCase()),
          name: obj.name,
          x: obj.x,
          y: obj.y,
          facing: (getProp(obj, 'facing') as NPCSpawn['facing']) ?? 'down',
        });
      } else if (obj.type === 'warp') {
        warps.push({
          x: obj.x,
          y: obj.y,
          width: obj.width,
          height: obj.height,
          targetMap: String(getProp(obj, 'targetMap') ?? ''),
          targetX: Number(getProp(obj, 'targetX') ?? 0),
          targetY: Number(getProp(obj, 'targetY') ?? 0),
        });
      }
    }

    const data: MapData = { tilemap, npcs, warps };
    this.cache.set(mapName, data);
    return data;
  }

  checkWarps(playerX: number, playerY: number, playerW: number, playerH: number, warps: WarpTrigger[]): WarpTrigger | null {
    for (const w of warps) {
      if (
        playerX + playerW > w.x &&
        playerX < w.x + w.width &&
        playerY + playerH > w.y &&
        playerY < w.y + w.height
      ) {
        return w;
      }
    }
    return null;
  }
}
