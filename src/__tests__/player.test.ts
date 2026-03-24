import { describe, it, expect, beforeEach } from "vitest";
import { Player } from "../engine/player";
import { TileMap, type TiledMap } from "../engine/tilemap";

/** Create a simple open 10x10 tilemap (all walkable). */
function makeOpenTileMap(): TileMap {
  const tm = new TileMap();
  const map: TiledMap = {
    width: 10,
    height: 10,
    tilewidth: 32,
    tileheight: 32,
    layers: [
      {
        name: "ground",
        type: "tilelayer",
        data: Array(100).fill(1),
        width: 10,
        height: 10,
      },
    ],
    tilesets: [{ firstgid: 1, columns: 8, image: "tileset.png" }],
  };
  tm.loadFromJSON(map);
  return tm;
}

/** Create a tilemap with a wall at column 5 (collision layer). */
function makeWalledTileMap(): TileMap {
  const tm = new TileMap();
  const collision = Array(100).fill(0);
  // Block column 5 entirely
  for (let row = 0; row < 10; row++) {
    collision[row * 10 + 5] = 1;
  }
  const map: TiledMap = {
    width: 10,
    height: 10,
    tilewidth: 32,
    tileheight: 32,
    layers: [
      {
        name: "ground",
        type: "tilelayer",
        data: Array(100).fill(1),
        width: 10,
        height: 10,
      },
      {
        name: "collision",
        type: "tilelayer",
        data: collision,
        width: 10,
        height: 10,
      },
    ],
    tilesets: [{ firstgid: 1, columns: 8, image: "tileset.png" }],
  };
  tm.loadFromJSON(map);
  return tm;
}

function pressKey(key: string) {
  window.dispatchEvent(new KeyboardEvent("keydown", { key }));
}

function releaseKey(key: string) {
  window.dispatchEvent(new KeyboardEvent("keyup", { key }));
}

describe("Player", () => {
  let player: Player;

  beforeEach(() => {
    player = new Player(64, 64);
  });

  describe("constructor", () => {
    it("initializes at start position", () => {
      expect(player.x).toBe(64);
      expect(player.y).toBe(64);
    });

    it("defaults to facing down", () => {
      expect(player.facing).toBe("down");
    });

    it("starts unlocked", () => {
      expect(player.locked).toBe(false);
    });

    it("starts at frame 0", () => {
      expect(player.frame).toBe(0);
    });
  });

  describe("spriteRow", () => {
    it("returns 2 for down", () => {
      player.facing = "down";
      expect(player.spriteRow).toBe(2);
    });

    it("returns 1 for left", () => {
      player.facing = "left";
      expect(player.spriteRow).toBe(1);
    });

    it("returns 3 for right", () => {
      player.facing = "right";
      expect(player.spriteRow).toBe(3);
    });

    it("returns 0 for up", () => {
      player.facing = "up";
      expect(player.spriteRow).toBe(0);
    });
  });

  describe("sprite dimensions", () => {
    it("reports 64x64 sprite size", () => {
      expect(player.spriteWidth).toBe(64);
      expect(player.spriteHeight).toBe(64);
    });
  });

  describe("movement", () => {
    it("moves right when ArrowRight is pressed", () => {
      const tilemap = makeOpenTileMap();
      pressKey("ArrowRight");
      player.update(tilemap);
      expect(player.x).toBe(66); // 64 + SPEED(2)
      expect(player.facing).toBe("right");
      releaseKey("ArrowRight");
    });

    it("moves left when ArrowLeft is pressed", () => {
      const tilemap = makeOpenTileMap();
      pressKey("ArrowLeft");
      player.update(tilemap);
      expect(player.x).toBe(62);
      expect(player.facing).toBe("left");
      releaseKey("ArrowLeft");
    });

    it("moves down when ArrowDown is pressed", () => {
      const tilemap = makeOpenTileMap();
      pressKey("ArrowDown");
      player.update(tilemap);
      expect(player.y).toBe(66);
      expect(player.facing).toBe("down");
      releaseKey("ArrowDown");
    });

    it("moves up when ArrowUp is pressed", () => {
      const tilemap = makeOpenTileMap();
      pressKey("ArrowUp");
      player.update(tilemap);
      expect(player.y).toBe(62);
      expect(player.facing).toBe("up");
      releaseKey("ArrowUp");
    });

    it("supports WASD keys", () => {
      const tilemap = makeOpenTileMap();
      pressKey("d");
      player.update(tilemap);
      expect(player.x).toBe(66);
      expect(player.facing).toBe("right");
      releaseKey("d");
    });

    it("does not move when locked", () => {
      const tilemap = makeOpenTileMap();
      player.locked = true;
      pressKey("ArrowRight");
      player.update(tilemap);
      expect(player.x).toBe(64);
      expect(player.frame).toBe(0);
      releaseKey("ArrowRight");
    });

    it("stops moving when key is released", () => {
      const tilemap = makeOpenTileMap();
      pressKey("ArrowRight");
      player.update(tilemap);
      expect(player.x).toBe(66);
      releaseKey("ArrowRight");
      player.update(tilemap);
      expect(player.x).toBe(66); // no further movement
    });
  });

  describe("collision", () => {
    it("is blocked by collision tiles", () => {
      const tilemap = makeWalledTileMap();
      // Position player just left of wall at column 5 (pixel 160)
      // Player is 32px wide, so at x=126 the right edge is at 157, one step right puts right edge at 159 (col 4, ok)
      // At x=128, right edge at 159 → col 4, ok. At x=130, right edge at 161 → col 5, blocked
      const p = new Player(128, 64);
      pressKey("ArrowRight");
      // Move right until blocked
      for (let i = 0; i < 20; i++) {
        p.update(tilemap);
      }
      // Player right edge (x + 31) should not enter column 5 (pixel 160)
      expect(p.x + 31).toBeLessThan(160);
      releaseKey("ArrowRight");
    });
  });

  describe("animation", () => {
    it("cycles frames while moving", () => {
      const tilemap = makeOpenTileMap();
      pressKey("ArrowRight");
      // Frame advances every 8 update ticks
      for (let i = 0; i < 8; i++) {
        player.update(tilemap);
      }
      expect(player.frame).toBe(1);
      releaseKey("ArrowRight");
    });

    it("resets frame when idle", () => {
      const tilemap = makeOpenTileMap();
      pressKey("ArrowRight");
      for (let i = 0; i < 8; i++) {
        player.update(tilemap);
      }
      expect(player.frame).toBe(1);
      releaseKey("ArrowRight");
      player.update(tilemap);
      expect(player.frame).toBe(0);
    });

    it("cycles through 3 frames", () => {
      const tilemap = makeOpenTileMap();
      pressKey("ArrowRight");
      for (let i = 0; i < 8 * 3; i++) {
        player.update(tilemap);
      }
      // After 3 full cycles, frame wraps to 0
      expect(player.frame).toBe(0);
      releaseKey("ArrowRight");
    });
  });
});
