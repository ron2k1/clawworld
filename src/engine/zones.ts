export interface MapZone {
  name: string;
  x1: number; y1: number;  // tile start (inclusive)
  x2: number; y2: number;  // tile end (exclusive)
}

// Design abstractions for district labeling on the world map.
// Each zone is a rectangular band — it contains roads, sidewalks, buildings, etc.
export const WORLD_ZONES: MapZone[] = [
  { name: 'City Park',        x1: 0,  y1: 0,  x2: 100, y2: 7  },
  { name: 'Downtown',         x1: 0,  y1: 7,  x2: 46,  y2: 31 },
  { name: 'Market District',  x1: 46, y1: 7,  x2: 66,  y2: 31 },
  { name: 'Harbor District',  x1: 66, y1: 7,  x2: 100, y2: 31 },
  { name: 'Waterfront',       x1: 0,  y1: 31, x2: 100, y2: 50 },
];

export function getZoneAt(col: number, row: number): MapZone | null {
  return WORLD_ZONES.find(z => col >= z.x1 && col < z.x2 && row >= z.y1 && row < z.y2) ?? null;
}
