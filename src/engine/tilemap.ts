export interface TiledProperty {
  name: string;
  type: string;
  value: string | number | boolean;
}

export interface TiledObject {
  id: number;
  name: string;
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  properties?: TiledProperty[];
}

export interface TiledLayer {
  name: string;
  type: 'tilelayer' | 'objectgroup';
  data?: number[];
  objects?: TiledObject[];
  width?: number;
  height?: number;
}

interface TiledTileset {
  firstgid: number;
  columns: number;
  image: string;
}

export interface TiledMap {
  width: number;
  height: number;
  tilewidth: number;
  tileheight: number;
  layers: TiledLayer[];
  tilesets: TiledTileset[];
}

// Tile IDs that block movement (buildings, walls, etc.)
const COLLISION_TILES = new Set([22, 23]);

export class TileMap {
  data: number[] = [];
  collision: number[] = [];
  objects: TiledObject[] = [];
  width = 0;
  height = 0;
  tileSize = 32;
  tilesetColumns = 0;
  tilesetImage = '';

  async load(url: string): Promise<void> {
    const res = await fetch(url);
    const map: TiledMap = await res.json();
    this.loadFromJSON(map);
  }

  loadFromJSON(map: TiledMap): void {
    this.width = map.width;
    this.height = map.height;
    this.tileSize = map.tilewidth;
    if (map.tilesets.length > 0) {
      this.tilesetColumns = map.tilesets[0].columns;
      this.tilesetImage = map.tilesets[0].image;
    }

    const ground = map.layers.find((l) => l.name === 'ground');
    if (!ground || !ground.data) throw new Error('No ground layer found');
    this.data = ground.data;

    const collisionLayer = map.layers.find((l) => l.name === 'collision');
    this.collision = collisionLayer?.data ?? [];

    const objectLayer = map.layers.find((l) => l.type === 'objectgroup');
    this.objects = objectLayer?.objects ?? [];
  }

  getTile(col: number, row: number): number {
    if (col < 0 || col >= this.width || row < 0 || row >= this.height) return 0;
    return this.data[row * this.width + col];
  }

  getCollision(col: number, row: number): number {
    if (col < 0 || col >= this.width || row < 0 || row >= this.height) return 1;
    if (this.collision.length > 0) {
      return this.collision[row * this.width + col];
    }
    return 0;
  }

  isWalkable(col: number, row: number): boolean {
    if (this.collision.length > 0) {
      return this.getCollision(col, row) === 0;
    }
    // Fallback: use tile ID heuristic
    const tile = this.getTile(col, row);
    return tile > 0 && !COLLISION_TILES.has(tile);
  }
}
