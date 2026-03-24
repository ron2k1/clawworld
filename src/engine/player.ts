import type { TileMap } from "./tilemap";

export type Facing = "down" | "up" | "left" | "right";

const SPEED = 2; // pixels per frame
const SPRITE_W = 64; // frame size in the sprite sheet (576/9 = 64)
const SPRITE_H = 64; // frame size in the sprite sheet (256/4 = 64)
// Collision box — small area at the feet of the sprite for natural overlap
const COLL_W = 24;
const COLL_H = 20;
const COLL_OX = (SPRITE_W - COLL_W) / 2; // 20
const COLL_OY = SPRITE_H - COLL_H;        // 44

// Maps facing direction to sprite-sheet row (matches this sprite sheet's layout)
const FACING_ROW: Record<Facing, number> = {
  up: 0,
  left: 1,
  down: 2,
  right: 3,
};

export class Player {
  x: number;
  y: number;
  facing: Facing = "down";
  frame = 0;
  locked = false;
  private frameTimer = 0;
  private keys = new Set<string>();
  private spriteImg: HTMLImageElement | null = null;
  private ready = false;

  private onKeyDown = (e: KeyboardEvent) => this.keys.add(e.key);
  private onKeyUp = (e: KeyboardEvent) => this.keys.delete(e.key);

  constructor(startX: number, startY: number) {
    this.x = startX;
    this.y = startY;
    window.addEventListener("keydown", this.onKeyDown);
    window.addEventListener("keyup", this.onKeyUp);
  }

  /** Remove event listeners — call before discarding. */
  destroy(): void {
    window.removeEventListener("keydown", this.onKeyDown);
    window.removeEventListener("keyup", this.onKeyUp);
    this.keys.clear();
  }

  pressKey(key: string): void {
    this.keys.add(key);
  }

  releaseKey(key: string): void {
    this.keys.delete(key);
  }

  clearKeys(): void {
    this.keys.clear();
  }

  loadSprite(src: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        this.spriteImg = img;
        this.ready = true;
        resolve();
      };
      img.onerror = reject;
      img.src = src;
    });
  }

  update(tilemap: TileMap): void {
    if (this.locked) {
      this.frame = 0;
      this.frameTimer = 0;
      return;
    }

    let dx = 0;
    let dy = 0;

    if (this.keys.has("ArrowUp") || this.keys.has("w") || this.keys.has("W")) {
      dy = -SPEED;
      this.facing = "up";
    } else if (this.keys.has("ArrowDown") || this.keys.has("s") || this.keys.has("S")) {
      dy = SPEED;
      this.facing = "down";
    }

    if (this.keys.has("ArrowLeft") || this.keys.has("a") || this.keys.has("A")) {
      dx = -SPEED;
      this.facing = "left";
    } else if (this.keys.has("ArrowRight") || this.keys.has("d") || this.keys.has("D")) {
      dx = SPEED;
      this.facing = "right";
    }

    const moving = dx !== 0 || dy !== 0;

    // Collision check — use feet collision box, not full sprite
    if (dx !== 0 || dy !== 0) {
      const ts = tilemap.tileSize;
      const cx = this.x + COLL_OX;
      const cy = this.y + COLL_OY;

      // Check horizontal movement
      if (dx !== 0) {
        const newCX = cx + dx;
        const col = Math.floor((newCX + (dx > 0 ? COLL_W - 1 : 0)) / ts);
        const rowTop = Math.floor(cy / ts);
        const rowBot = Math.floor((cy + COLL_H - 1) / ts);
        if (tilemap.isWalkable(col, rowTop) && tilemap.isWalkable(col, rowBot)) {
          this.x += dx;
        }
      }

      // Check vertical movement
      if (dy !== 0) {
        const newCY = cy + dy;
        const row = Math.floor((newCY + (dy > 0 ? COLL_H - 1 : 0)) / ts);
        const colLeft = Math.floor(cx / ts);
        const colRight = Math.floor((cx + COLL_W - 1) / ts);
        if (tilemap.isWalkable(colLeft, row) && tilemap.isWalkable(colRight, row)) {
          this.y += dy;
        }
      }
    }

    // Animation
    if (moving) {
      this.frameTimer++;
      if (this.frameTimer >= 8) {
        this.frameTimer = 0;
        this.frame = (this.frame + 1) % 3;
      }
    } else {
      this.frame = 0;
      this.frameTimer = 0;
    }
  }

  get spriteRow(): number {
    return FACING_ROW[this.facing];
  }

  get sprite(): HTMLImageElement | null {
    return this.spriteImg;
  }

  get spriteWidth(): number {
    return SPRITE_W;
  }

  get spriteHeight(): number {
    return SPRITE_H;
  }
}
