import { describe, it, expect } from "vitest";
import { TileMap, type TiledMap } from "../engine/tilemap";

function makeTiledMap(overrides: Partial<TiledMap> = {}): TiledMap {
  // 4x4 grid, tile IDs 1-16, no collision layer
  return {
    width: 4,
    height: 4,
    tilewidth: 32,
    tileheight: 32,
    layers: [
      {
        name: "ground",
        type: "tilelayer",
        data: [
          1, 2, 3, 4,
          5, 6, 7, 8,
          9, 10, 11, 12,
          13, 14, 15, 16,
        ],
        width: 4,
        height: 4,
      },
    ],
    tilesets: [{ firstgid: 1, columns: 8, image: "tileset.png" }],
    ...overrides,
  };
}

function makeTiledMapWithCollision(): TiledMap {
  return {
    width: 4,
    height: 4,
    tilewidth: 32,
    tileheight: 32,
    layers: [
      {
        name: "ground",
        type: "tilelayer",
        data: [
          1, 2, 3, 4,
          5, 6, 7, 8,
          9, 10, 11, 12,
          13, 14, 15, 16,
        ],
        width: 4,
        height: 4,
      },
      {
        name: "collision",
        type: "tilelayer",
        data: [
          0, 0, 0, 0,
          0, 1, 1, 0,
          0, 1, 0, 0,
          0, 0, 0, 0,
        ],
        width: 4,
        height: 4,
      },
    ],
    tilesets: [{ firstgid: 1, columns: 8, image: "tileset.png" }],
  };
}

describe("TileMap", () => {
  describe("loadFromJSON", () => {
    it("parses width, height, and tileSize from map data", () => {
      const tm = new TileMap();
      tm.loadFromJSON(makeTiledMap());
      expect(tm.width).toBe(4);
      expect(tm.height).toBe(4);
      expect(tm.tileSize).toBe(32);
    });

    it("loads ground layer tile data", () => {
      const tm = new TileMap();
      tm.loadFromJSON(makeTiledMap());
      expect(tm.data).toHaveLength(16);
      expect(tm.data[0]).toBe(1);
      expect(tm.data[15]).toBe(16);
    });

    it("loads tileset columns", () => {
      const tm = new TileMap();
      tm.loadFromJSON(makeTiledMap());
      expect(tm.tilesetColumns).toBe(8);
    });

    it("throws when ground layer is missing", () => {
      const map = makeTiledMap({
        layers: [{ name: "other", type: "tilelayer", data: [1], width: 1, height: 1 }],
      });
      const tm = new TileMap();
      expect(() => tm.loadFromJSON(map)).toThrow("No ground layer found");
    });

    it("loads collision layer when present", () => {
      const tm = new TileMap();
      tm.loadFromJSON(makeTiledMapWithCollision());
      expect(tm.collision).toHaveLength(16);
      expect(tm.collision[5]).toBe(1); // row 1, col 1
    });

    it("defaults to empty collision when no collision layer", () => {
      const tm = new TileMap();
      tm.loadFromJSON(makeTiledMap());
      expect(tm.collision).toEqual([]);
    });

    it("extracts objects from object layers", () => {
      const map = makeTiledMap({
        layers: [
          ...makeTiledMap().layers,
          {
            name: "objects",
            type: "objectgroup",
            objects: [
              { id: 1, name: "spawn", type: "spawn", x: 64, y: 96, width: 32, height: 32 },
            ],
          },
        ],
      });
      const tm = new TileMap();
      tm.loadFromJSON(map);
      expect(tm.objects).toHaveLength(1);
      expect(tm.objects[0].name).toBe("spawn");
    });
  });

  describe("getTile", () => {
    it("returns tile ID at valid position", () => {
      const tm = new TileMap();
      tm.loadFromJSON(makeTiledMap());
      expect(tm.getTile(0, 0)).toBe(1);
      expect(tm.getTile(3, 3)).toBe(16);
      expect(tm.getTile(2, 1)).toBe(7);
    });

    it("returns 0 for out-of-bounds positions", () => {
      const tm = new TileMap();
      tm.loadFromJSON(makeTiledMap());
      expect(tm.getTile(-1, 0)).toBe(0);
      expect(tm.getTile(0, -1)).toBe(0);
      expect(tm.getTile(4, 0)).toBe(0);
      expect(tm.getTile(0, 4)).toBe(0);
    });
  });

  describe("getCollision", () => {
    it("returns collision value from collision layer", () => {
      const tm = new TileMap();
      tm.loadFromJSON(makeTiledMapWithCollision());
      expect(tm.getCollision(0, 0)).toBe(0);
      expect(tm.getCollision(1, 1)).toBe(1);
      expect(tm.getCollision(2, 1)).toBe(1);
    });

    it("returns 1 for out-of-bounds (blocked)", () => {
      const tm = new TileMap();
      tm.loadFromJSON(makeTiledMapWithCollision());
      expect(tm.getCollision(-1, 0)).toBe(1);
      expect(tm.getCollision(0, -1)).toBe(1);
      expect(tm.getCollision(4, 0)).toBe(1);
    });

    it("returns 0 when no collision layer exists", () => {
      const tm = new TileMap();
      tm.loadFromJSON(makeTiledMap());
      expect(tm.getCollision(0, 0)).toBe(0);
    });
  });

  describe("isWalkable", () => {
    it("uses collision layer when present", () => {
      const tm = new TileMap();
      tm.loadFromJSON(makeTiledMapWithCollision());
      expect(tm.isWalkable(0, 0)).toBe(true);
      expect(tm.isWalkable(1, 1)).toBe(false);
      expect(tm.isWalkable(2, 2)).toBe(true);
    });

    it("falls back to tile ID heuristic when no collision layer", () => {
      const tm = new TileMap();
      tm.loadFromJSON(makeTiledMap());
      // Tile IDs 1-21 are walkable, 22-23 are collision tiles
      expect(tm.isWalkable(0, 0)).toBe(true); // tile 1
    });

    it("blocks collision tile IDs 22 and 23 in heuristic mode", () => {
      const map: TiledMap = {
        width: 3,
        height: 1,
        tilewidth: 32,
        tileheight: 32,
        layers: [
          { name: "ground", type: "tilelayer", data: [21, 22, 23], width: 3, height: 1 },
        ],
        tilesets: [{ firstgid: 1, columns: 8, image: "tileset.png" }],
      };
      const tm = new TileMap();
      tm.loadFromJSON(map);
      expect(tm.isWalkable(0, 0)).toBe(true);  // tile 21
      expect(tm.isWalkable(1, 0)).toBe(false); // tile 22
      expect(tm.isWalkable(2, 0)).toBe(false); // tile 23
    });

    it("treats tile ID 0 (empty) as not walkable in heuristic mode", () => {
      const map: TiledMap = {
        width: 2,
        height: 1,
        tilewidth: 32,
        tileheight: 32,
        layers: [
          { name: "ground", type: "tilelayer", data: [0, 1], width: 2, height: 1 },
        ],
        tilesets: [{ firstgid: 1, columns: 8, image: "tileset.png" }],
      };
      const tm = new TileMap();
      tm.loadFromJSON(map);
      expect(tm.isWalkable(0, 0)).toBe(false); // tile 0
      expect(tm.isWalkable(1, 0)).toBe(true);  // tile 1
    });
  });
});
