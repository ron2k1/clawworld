import { describe, it, expect } from 'vitest';
import { findPath } from '../engine/pathfinding';
import { TileMap } from '../engine/tilemap';

function makeTilemap(width: number, height: number, blocked: [number, number][] = []): TileMap {
  const tm = new TileMap();
  tm.width = width;
  tm.height = height;
  tm.tileSize = 32;
  tm.data = new Array(width * height).fill(1);
  tm.collision = new Array(width * height).fill(0);
  for (const [col, row] of blocked) {
    tm.collision[row * width + col] = 1;
  }
  return tm;
}

describe('findPath', () => {
  it('finds straight-line path on open grid', () => {
    const tm = makeTilemap(10, 10);
    const path = findPath(tm, 0, 0, 4, 0);
    expect(path).not.toBeNull();
    expect(path!.length).toBe(4);
    expect(path![path!.length - 1]).toEqual({ col: 4, row: 0 });
  });

  it('returns empty array for same start and goal', () => {
    const tm = makeTilemap(5, 5);
    const path = findPath(tm, 2, 2, 2, 2);
    expect(path).toEqual([]);
  });

  it('navigates around obstacles', () => {
    // Wall at col 2, rows 0-3 (leaves row 4 open)
    const blocked: [number, number][] = [[2, 0], [2, 1], [2, 2], [2, 3]];
    const tm = makeTilemap(5, 5, blocked);
    const path = findPath(tm, 0, 0, 4, 0);
    expect(path).not.toBeNull();
    expect(path!.length).toBeGreaterThan(4); // must go around
    // Path should not cross blocked tiles
    for (const step of path!) {
      expect(blocked.some(([c, r]) => c === step.col && r === step.row)).toBe(false);
    }
    expect(path![path!.length - 1]).toEqual({ col: 4, row: 0 });
  });

  it('returns null when goal is unreachable', () => {
    // Completely wall off goal
    const blocked: [number, number][] = [[3, 0], [3, 1], [3, 2], [3, 3], [3, 4]];
    const tm = makeTilemap(5, 5, blocked);
    const path = findPath(tm, 0, 0, 4, 0);
    expect(path).toBeNull();
  });

  it('returns null when goal tile is unwalkable', () => {
    const tm = makeTilemap(5, 5, [[4, 0]]);
    const path = findPath(tm, 0, 0, 4, 0);
    expect(path).toBeNull();
  });

  it('avoids occupied tiles', () => {
    const tm = makeTilemap(5, 5);
    const occupied = new Set(['2,0']); // Block direct path
    const path = findPath(tm, 0, 0, 4, 0, occupied);
    expect(path).not.toBeNull();
    // Should not pass through occupied tile
    for (const step of path!) {
      if (step.col === 4 && step.row === 0) continue; // goal is ok
      expect(occupied.has(`${step.col},${step.row}`)).toBe(false);
    }
  });

  it('allows goal tile even if occupied', () => {
    const tm = makeTilemap(5, 5);
    const occupied = new Set(['4,0']); // Goal is occupied
    const path = findPath(tm, 0, 0, 4, 0, occupied);
    expect(path).not.toBeNull();
    expect(path![path!.length - 1]).toEqual({ col: 4, row: 0 });
  });

  it('handles out-of-bounds gracefully', () => {
    const tm = makeTilemap(3, 3);
    const path = findPath(tm, 0, 0, 10, 10);
    expect(path).toBeNull();
  });
});
