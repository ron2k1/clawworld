import { TileMap } from './tilemap';
import { findPath } from './pathfinding';

export type Direction = 'up' | 'down' | 'left' | 'right';
export type Locomotion = 'stationary' | 'wandering' | 'summoned' | 'returning';
export type Activity = 'idle' | 'busy';

const FRAME_INTERVAL = 500;
const SPRITE_SIZE = 32;
const NPC_SPEED = 1; // pixels per frame (half player speed)
const WALK_FRAME_INTERVAL = 8; // frames per animation step
const IDLE_MIN = 120; // min frames before wander (2s at 60fps)
const IDLE_MAX = 360; // max frames before wander (6s)
const WANDER_RADIUS = 3; // tiles from home
const STUCK_THRESHOLD = 60; // frames before recompute
const ARRIVAL_TOLERANCE = 2; // pixels from tile center to snap

const DIRECTION_ROW: Record<Direction, number> = {
  down: 0,
  left: 1,
  right: 2,
  up: 3,
};

export interface Camera {
  x: number;
  y: number;
}

export class NPC {
  agentId: string;
  name: string;
  x: number;
  y: number;
  facing: Direction;
  spriteSheet: HTMLImageElement;

  // Activity state (driven by gateway streaming)
  activity: Activity = 'idle';

  // Backwards-compatible active flag
  get active(): boolean {
    return this.activity === 'busy';
  }
  set active(v: boolean) {
    this.activity = v ? 'busy' : 'idle';
  }

  // Locomotion state (driven by movement system)
  locomotion: Locomotion = 'stationary';

  // Home position
  homeMap = '';
  homeTileX = 0;
  homeTileY = 0;
  currentMap = '';

  // Movement internals
  private path: { col: number; row: number }[] = [];
  private pathIndex = 0;
  private idleTimer = 0;
  private stuckCounter = 0;
  private walkTimer = 0;
  private frame = 0;
  private lastFrameTime = 0;
  private lastTileCol = -1;
  private lastTileRow = -1;

  constructor(
    agentId: string,
    name: string,
    x: number,
    y: number,
    spriteSheet: HTMLImageElement,
    facing: Direction = 'down',
  ) {
    this.agentId = agentId;
    this.name = name;
    this.x = x;
    this.y = y;
    this.spriteSheet = spriteSheet;
    this.facing = facing;
    this.homeTileX = Math.floor(x / 32);
    this.homeTileY = Math.floor(y / 32);
    this.idleTimer = randomInt(IDLE_MIN, IDLE_MAX);
  }

  /** Get current tile position */
  get tileCol(): number {
    return Math.floor((this.x + SPRITE_SIZE / 2) / 32);
  }
  get tileRow(): number {
    return Math.floor((this.y + SPRITE_SIZE / 2) / 32);
  }

  /** Per-frame update — call from game loop */
  update(tilemap: TileMap, occupied: Set<string>): void {
    // Don't move while busy (answering a chat)
    if (this.activity === 'busy') {
      this.locomotion = 'stationary';
      this.path = [];
      this.pathIndex = 0;
      return;
    }

    switch (this.locomotion) {
      case 'stationary':
        this.updateIdle(tilemap, occupied);
        break;
      case 'wandering':
      case 'summoned':
      case 'returning':
        this.updateMoving(tilemap, occupied);
        break;
    }
  }

  private updateIdle(tilemap: TileMap, occupied: Set<string>): void {
    this.idleTimer--;
    if (this.idleTimer <= 0) {
      // Pick a random walkable tile near home
      const targetCol = this.homeTileX + randomInt(-WANDER_RADIUS, WANDER_RADIUS);
      const targetRow = this.homeTileY + randomInt(-WANDER_RADIUS, WANDER_RADIUS);

      if (tilemap.isWalkable(targetCol, targetRow)) {
        const path = findPath(
          tilemap,
          this.tileCol,
          this.tileRow,
          targetCol,
          targetRow,
          occupied,
        );
        if (path && path.length > 0) {
          this.path = path;
          this.pathIndex = 0;
          this.locomotion = 'wandering';
          this.stuckCounter = 0;
        }
      }
      this.idleTimer = randomInt(IDLE_MIN, IDLE_MAX);
    }
  }

  private updateMoving(tilemap: TileMap, occupied: Set<string>): void {
    if (this.pathIndex >= this.path.length) {
      // Path complete
      this.locomotion = 'stationary';
      this.path = [];
      this.pathIndex = 0;
      this.frame = 0;
      return;
    }

    const target = this.path[this.pathIndex];
    const targetPx = target.col * 32;
    const targetPy = target.row * 32;
    const dx = targetPx - this.x;
    const dy = targetPy - this.y;

    // Check if arrived at target tile
    if (Math.abs(dx) <= ARRIVAL_TOLERANCE && Math.abs(dy) <= ARRIVAL_TOLERANCE) {
      this.x = targetPx;
      this.y = targetPy;
      this.pathIndex++;
      this.stuckCounter = 0;
      return;
    }

    // Move along dominant axis
    const speed = this.locomotion === 'summoned' ? NPC_SPEED * 1.5 : NPC_SPEED;
    let moveX = 0;
    let moveY = 0;

    if (Math.abs(dx) > Math.abs(dy)) {
      moveX = dx > 0 ? speed : -speed;
      this.facing = dx > 0 ? 'right' : 'left';
    } else {
      moveY = dy > 0 ? speed : -speed;
      this.facing = dy > 0 ? 'down' : 'up';
    }

    // Collision check before move
    const newX = this.x + moveX;
    const newY = this.y + moveY;
    const newCol = Math.floor((newX + SPRITE_SIZE / 2) / 32);
    const newRow = Math.floor((newY + SPRITE_SIZE / 2) / 32);
    const newKey = `${newCol},${newRow}`;

    const canMove =
      tilemap.isWalkable(newCol, newRow) &&
      (!occupied.has(newKey) || (newCol === this.tileCol && newRow === this.tileRow));

    if (canMove) {
      this.x = newX;
      this.y = newY;
      this.stuckCounter = 0;
    } else {
      this.stuckCounter++;
    }

    // Stuck detection — recompute path
    if (this.stuckCounter > STUCK_THRESHOLD) {
      const goal = this.path[this.path.length - 1];
      if (goal) {
        const newPath = findPath(tilemap, this.tileCol, this.tileRow, goal.col, goal.row, occupied);
        if (newPath && newPath.length > 0) {
          this.path = newPath;
          this.pathIndex = 0;
        } else {
          // Give up
          this.locomotion = 'stationary';
          this.path = [];
          this.pathIndex = 0;
        }
      }
      this.stuckCounter = 0;
    }

    // Track tile changes for occupancy
    this.lastTileCol = this.tileCol;
    this.lastTileRow = this.tileRow;

    // Walk animation
    this.walkTimer++;
    if (this.walkTimer >= WALK_FRAME_INTERVAL) {
      this.frame = (this.frame + 1) % 2;
      this.walkTimer = 0;
    }
  }

  /** Set a path to a specific tile (for summoning) */
  moveTo(tilemap: TileMap, targetCol: number, targetRow: number, occupied: Set<string>, mode: Locomotion = 'summoned'): boolean {
    const path = findPath(tilemap, this.tileCol, this.tileRow, targetCol, targetRow, occupied);
    if (path && path.length > 0) {
      this.path = path;
      this.pathIndex = 0;
      this.locomotion = mode;
      this.stuckCounter = 0;
      return true;
    }
    return false;
  }

  render(ctx: CanvasRenderingContext2D, camera: Camera): void {
    const now = performance.now();

    // Idle animation (frame toggle) only when stationary
    if (this.locomotion === 'stationary') {
      if (now - this.lastFrameTime >= FRAME_INTERVAL) {
        this.frame = (this.frame + 1) % 2;
        this.lastFrameTime = now;
      }
    }

    const row = DIRECTION_ROW[this.facing];
    const sx = this.frame * SPRITE_SIZE;
    const sy = row * SPRITE_SIZE;
    const dx = Math.floor(this.x - camera.x);
    const dy = Math.floor(this.y - camera.y);

    ctx.save();
    try {
      // Activity indicator — pulsing glow when agent is working
      if (this.active) {
        const pulse = 0.4 + 0.3 * Math.sin(now / 300);
        ctx.shadowColor = '#4af';
        ctx.shadowBlur = 12 * pulse;
        ctx.globalAlpha = 0.9;
      }

      ctx.drawImage(
        this.spriteSheet,
        sx, sy, SPRITE_SIZE, SPRITE_SIZE,
        dx, dy, SPRITE_SIZE, SPRITE_SIZE,
      );
    } finally {
      ctx.restore();
    }

    // Status dot above head
    const dotX = dx + SPRITE_SIZE / 2;
    const dotY = dy - 6;

    if (this.active) {
      // Busy: pulsing red dot
      const dotPulse = 0.5 + 0.5 * Math.sin(now / 400);
      ctx.fillStyle = `rgba(255, 72, 72, ${dotPulse})`;
    } else if (this.locomotion !== 'stationary') {
      // Walking: yellow dot
      ctx.fillStyle = 'rgba(255, 200, 72, 0.9)';
    } else {
      // Idle: green dot
      ctx.fillStyle = 'rgba(72, 255, 72, 0.9)';
    }
    ctx.beginPath();
    ctx.arc(dotX, dotY, 3, 0, Math.PI * 2);
    ctx.fill();
  }

  faceTo(playerX: number, playerY: number): void {
    const diffX = playerX - this.x;
    const diffY = playerY - this.y;

    if (Math.abs(diffX) > Math.abs(diffY)) {
      this.facing = diffX > 0 ? 'right' : 'left';
    } else {
      this.facing = diffY > 0 ? 'down' : 'up';
    }
  }

  isInRange(playerX: number, playerY: number, range = 64): boolean {
    const dx = playerX - this.x;
    const dy = playerY - this.y;
    return dx * dx + dy * dy <= range * range;
  }
}

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}
