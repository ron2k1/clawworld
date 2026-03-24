import { TileMap } from './tilemap';

interface Node {
  col: number;
  row: number;
  g: number;
  h: number;
  f: number;
  parent: Node | null;
}

function manhattan(a: { col: number; row: number }, b: { col: number; row: number }): number {
  return Math.abs(a.col - b.col) + Math.abs(a.row - b.row);
}

const DIRS = [
  { dc: 0, dr: -1 }, // up
  { dc: 0, dr: 1 },  // down
  { dc: -1, dr: 0 }, // left
  { dc: 1, dr: 0 },  // right
];

const MAX_NODES = 500;

/**
 * A* pathfinding on a TileMap grid.
 * Returns array of {col, row} from start (exclusive) to goal (inclusive), or null if unreachable.
 */
export function findPath(
  tilemap: TileMap,
  startCol: number,
  startRow: number,
  goalCol: number,
  goalRow: number,
  occupied: Set<string> = new Set(),
): { col: number; row: number }[] | null {
  if (startCol === goalCol && startRow === goalRow) return [];

  const key = (c: number, r: number) => `${c},${r}`;

  // Goal must be walkable (but ignore occupied — NPC will wait)
  if (!tilemap.isWalkable(goalCol, goalRow)) return null;

  const open: Node[] = [];
  const closed = new Set<string>();

  const start: Node = {
    col: startCol,
    row: startRow,
    g: 0,
    h: manhattan({ col: startCol, row: startRow }, { col: goalCol, row: goalRow }),
    f: 0,
    parent: null,
  };
  start.f = start.g + start.h;
  open.push(start);

  let explored = 0;

  while (open.length > 0 && explored < MAX_NODES) {
    // Find node with lowest f
    let bestIdx = 0;
    for (let i = 1; i < open.length; i++) {
      if (open[i].f < open[bestIdx].f) bestIdx = i;
    }
    const current = open.splice(bestIdx, 1)[0];
    explored++;

    if (current.col === goalCol && current.row === goalRow) {
      // Reconstruct path (exclude start)
      const path: { col: number; row: number }[] = [];
      let node: Node | null = current;
      while (node && !(node.col === startCol && node.row === startRow)) {
        path.push({ col: node.col, row: node.row });
        node = node.parent;
      }
      return path.reverse();
    }

    closed.add(key(current.col, current.row));

    for (const dir of DIRS) {
      const nc = current.col + dir.dc;
      const nr = current.row + dir.dr;
      const nk = key(nc, nr);

      if (closed.has(nk)) continue;
      if (!tilemap.isWalkable(nc, nr)) continue;
      // Allow goal tile even if occupied, block other occupied tiles
      if (occupied.has(nk) && !(nc === goalCol && nr === goalRow)) continue;

      const g = current.g + 1;
      const existing = open.find((n) => n.col === nc && n.row === nr);

      if (existing) {
        if (g < existing.g) {
          existing.g = g;
          existing.f = g + existing.h;
          existing.parent = current;
        }
      } else {
        const h = manhattan({ col: nc, row: nr }, { col: goalCol, row: goalRow });
        open.push({ col: nc, row: nr, g, h, f: g + h, parent: current });
      }
    }
  }

  return null; // No path found
}
