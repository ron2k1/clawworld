"""Generate all map JSON files for ClawWorld with proper buildings."""
import json
import random
import os

random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "data", "maps")

TILESET_META = {
    "firstgid": 1, "columns": 21,
    "image": "../tilesets/outdoor.png",
    "imageheight": 736, "imagewidth": 672,
    "margin": 0, "name": "outdoor", "spacing": 0,
    "tilecount": 483, "tileheight": 32, "tilewidth": 32
}

# Tile palette (from tileset analysis)
GRASS = [128, 129, 137, 140]  # green variants
GRASS_POOL = [128]*50 + [129]*25 + [137]*15 + [140]*10
SAND = 2      # sandy path
SAND_ALT = 3  # path variation
DIRT = 5      # brown border/tree
WATER = 124   # blue water
STONE_FLOOR = 401  # gray stone (interior floors)
STONE_ALT = 402    # stone variation
WALL = 380    # dark stone (walls)
BRICK = 381   # brick


def make_map(width, height, ground, collision, objects):
    return {
        "compressionlevel": -1,
        "height": height, "width": width, "infinite": False,
        "orientation": "orthogonal", "renderorder": "right-down",
        "tileheight": 32, "tilewidth": 32,
        "tiledversion": "1.10.2", "type": "map", "version": "1.10",
        "nextlayerid": 4, "nextobjectid": 100,
        "layers": [
            {"id": 1, "name": "ground", "type": "tilelayer",
             "visible": True, "opacity": 1, "x": 0, "y": 0,
             "width": width, "height": height, "data": ground},
            {"id": 2, "name": "collision", "type": "tilelayer",
             "visible": False, "opacity": 1, "x": 0, "y": 0,
             "width": width, "height": height, "data": collision},
            {"id": 3, "name": "objects", "type": "objectgroup",
             "visible": True, "opacity": 1, "x": 0, "y": 0,
             "objects": objects}
        ],
        "tilesets": [TILESET_META]
    }


def npc_obj(oid, name, agent_id, tx, ty, facing="down"):
    return {
        "id": oid, "name": name, "type": "npc",
        "x": tx * 32, "y": ty * 32, "width": 32, "height": 32,
        "properties": [
            {"name": "agentId", "type": "string", "value": agent_id},
            {"name": "facing", "type": "string", "value": facing}
        ]
    }


def warp_obj(oid, name, px, py, pw, ph, target_map, target_x, target_y):
    return {
        "id": oid, "name": name, "type": "warp",
        "x": px, "y": py, "width": pw, "height": ph,
        "properties": [
            {"name": "targetMap", "type": "string", "value": target_map},
            {"name": "targetX", "type": "int", "value": target_x},
            {"name": "targetY", "type": "int", "value": target_y}
        ]
    }


class MapBuilder:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.ground = [random.choice(GRASS_POOL) for _ in range(w * h)]
        self.collision = [0] * (w * h)
        self.objects = []
        self._oid = 1

    def set(self, x, y, tile, coll=False):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.ground[y * self.w + x] = tile
            if coll:
                self.collision[y * self.w + x] = 1

    def fill(self, x1, y1, x2, y2, tile, coll=False):
        for y in range(y1, y2):
            for x in range(x1, x2):
                self.set(x, y, tile, coll)

    def border(self, tile=DIRT):
        for x in range(self.w):
            self.set(x, 0, tile, True)
            self.set(x, self.h - 1, tile, True)
        for y in range(self.h):
            self.set(0, y, tile, True)
            self.set(self.w - 1, y, tile, True)

    def path_h(self, y, x1=1, x2=None):
        if x2 is None:
            x2 = self.w - 1
        for x in range(x1, x2):
            self.set(x, y, random.choice([SAND, SAND_ALT]))

    def path_v(self, x, y1=1, y2=None):
        if y2 is None:
            y2 = self.h - 1
        for y in range(y1, y2):
            self.set(x, y, random.choice([SAND, SAND_ALT]))

    def building(self, bx, by, bw, bh, wall=WALL, floor=STONE_FLOOR):
        """Draw a building. Roof = top 2 rows, walls = sides, floor = interior."""
        # Roof
        self.fill(bx, by, bx + bw, by + 2, wall, coll=True)
        # Left/right walls
        for y in range(by + 2, by + bh):
            self.set(bx, y, wall, True)
            self.set(bx + bw - 1, y, wall, True)
        # Bottom wall
        for x in range(bx, bx + bw):
            self.set(x, by + bh - 1, wall, True)
        # Interior floor
        self.fill(bx + 1, by + 2, bx + bw - 1, by + bh - 1, floor)
        # Door (center bottom)
        door_x = bx + bw // 2
        self.set(door_x, by + bh - 1, SAND)
        self.collision[(by + bh - 1) * self.w + door_x] = 0
        return door_x, by + bh - 1

    def open_border(self, x, y):
        """Make a border tile walkable."""
        self.set(x, y, SAND)
        self.collision[y * self.w + x] = 0

    def add_npc(self, name, agent_id, tx, ty, facing="down"):
        obj = npc_obj(self._oid, name, agent_id, tx, ty, facing)
        self.objects.append(obj)
        self._oid += 1

    def add_warp(self, name, px, py, pw, ph, target_map, tx, ty):
        obj = warp_obj(self._oid, name, px, py, pw, ph, target_map, tx, ty)
        self.objects.append(obj)
        self._oid += 1

    def trees(self, positions):
        for tx, ty in positions:
            self.set(tx, ty, DIRT, True)

    def pond(self, x1, y1, x2, y2):
        # Dirt border
        self.fill(x1 - 1, y1 - 1, x2 + 1, y2 + 1, DIRT)
        # Water center
        self.fill(x1, y1, x2, y2, WATER, coll=True)

    def export(self, filename):
        m = make_map(self.w, self.h, self.ground, self.collision, self.objects)
        path = os.path.join(OUT_DIR, filename)
        with open(path, "w") as f:
            json.dump(m, f, indent=2)
        print(f"  {filename} ({self.w}x{self.h}, {len(self.objects)} objects)")


# ====================================================================
# CLAW TOWN — Main overworld with distinct buildings
# ====================================================================
print("Generating maps...")
m = MapBuilder(50, 35)
m.border()

# === Main roads ===
# Horizontal main road (rows 16-17)
m.path_h(16)
m.path_h(17)
# Vertical main road (cols 25-26)
m.path_v(25)
m.path_v(26)
# Widen intersection
for y in [15, 18]:
    for x in range(23, 28):
        m.set(x, y, SAND)

# === TOWN HALL (center-top, large) ===
# 10 wide x 6 tall at (21, 4)
door_x, door_y = m.building(21, 4, 10, 6)
# Path from town hall to main road
m.path_v(26, 10, 16)
# Wider warp zone around door for easier entry
m.add_warp("to-townhall", (door_x - 1) * 32, (door_y - 1) * 32, 96, 96,
           "townhall-interior", 10 * 32, 12 * 32)

# === ASSISTANT'S LAB (top-left) ===
door_x, door_y = m.building(4, 4, 7, 5)
m.path_v(7, 9, 16)
m.add_warp("to-lab", (door_x - 1) * 32, (door_y - 1) * 32, 96, 96,
           "lab-interior", 10 * 32, 12 * 32)

# === ANALYST'S OFFICE (top-right) ===
door_x, door_y = m.building(37, 4, 7, 5)
m.path_v(40, 9, 16)
m.add_warp("to-analyst-office", (door_x - 1) * 32, (door_y - 1) * 32, 96, 96,
           "analyst-office", 7 * 32, 9 * 32)

# === CODER'S WORKSHOP (bottom-left) ===
door_x, door_y = m.building(4, 22, 7, 5)
m.path_v(7, 18, 22)
m.add_warp("to-coder-workshop", (door_x - 1) * 32, (door_y - 1) * 32, 96, 96,
           "coder-workshop", 7 * 32, 9 * 32)

# === MIRA'S INN (bottom-right) ===
door_x, door_y = m.building(37, 22, 7, 5)
m.path_v(40, 18, 22)

# === Decorative elements ===
# Pond near center
m.pond(14, 20, 17, 23)

# Trees scattered
m.trees([
    (2, 2), (3, 2), (12, 2), (13, 2), (16, 2), (17, 2),
    (33, 2), (34, 2), (46, 2), (47, 2),
    (2, 12), (2, 13), (47, 12), (48, 12),
    (2, 30), (3, 30), (12, 30), (13, 30),
    (35, 30), (36, 30), (46, 30), (47, 30),
    (15, 12), (16, 12), (33, 12), (34, 12),
])

# === Exits ===
# East exit to Route 1
m.open_border(49, 16)
m.open_border(49, 17)
m.add_warp("to-route-1", 49 * 32, 16 * 32, 32, 64,
           "route-1", 32, 14 * 32)

# South exit
m.open_border(25, 34)
m.open_border(26, 34)

m.export("claw-town.json")

# ====================================================================
# TOWN HALL INTERIOR — meeting room
# ====================================================================
m = MapBuilder(20, 15)
for y in range(15):
    for x in range(20):
        if x == 0 or x == 19 or y == 0 or y == 14:
            m.set(x, y, WALL, True)
        else:
            m.set(x, y, STONE_FLOOR)

# Meeting table (center)
m.fill(7, 5, 13, 9, BRICK, True)

# Door
m.set(10, 14, SAND)
m.collision[14 * 20 + 10] = 0

m.add_warp("exit", 10 * 32, 14 * 32, 32, 32,
           "claw-town", 26 * 32, 11 * 32)

m.export("townhall-interior.json")

# ====================================================================
# ASSISTANT'S LAB — personal workspace
# ====================================================================
m = MapBuilder(20, 15)
for y in range(15):
    for x in range(20):
        if x == 0 or x == 19 or y == 0 or y == 14:
            m.set(x, y, WALL, True)
        else:
            m.set(x, y, STONE_FLOOR)

m.add_npc("Personal Assistant", "assistant", 10, 7, "down")

# Door
m.set(10, 14, SAND)
m.collision[14 * 20 + 10] = 0
m.add_warp("exit", 10 * 32, 14 * 32, 32, 32,
           "claw-town", 7 * 32, 10 * 32)

m.export("lab-interior.json")

# ====================================================================
# ANALYST'S OFFICE
# ====================================================================
m = MapBuilder(15, 12)
for y in range(12):
    for x in range(15):
        if x == 0 or x == 14 or y == 0 or y == 11:
            m.set(x, y, WALL, True)
        else:
            m.set(x, y, STONE_ALT)

m.add_npc("Senior Analyst", "analyst", 7, 5, "down")

m.set(7, 11, SAND)
m.collision[11 * 15 + 7] = 0
m.add_warp("exit", 7 * 32, 11 * 32, 32, 32,
           "claw-town", 40 * 32, 10 * 32)

m.export("analyst-office.json")

# ====================================================================
# CODER'S WORKSHOP
# ====================================================================
m = MapBuilder(15, 12)
for y in range(12):
    for x in range(15):
        if x == 0 or x == 14 or y == 0 or y == 11:
            m.set(x, y, WALL, True)
        else:
            m.set(x, y, STONE_FLOOR)

m.add_npc("The Coder", "coder", 7, 5, "down")

m.set(7, 11, SAND)
m.collision[11 * 15 + 7] = 0
m.add_warp("exit", 7 * 32, 11 * 32, 32, 32,
           "claw-town", 7 * 32, 28 * 32)

m.export("coder-workshop.json")

# ====================================================================
# GUILD HALL INTERIOR (kept for backwards compat)
# ====================================================================
m = MapBuilder(25, 18)
for y in range(18):
    for x in range(25):
        if x == 0 or x == 24 or y == 0 or y == 17:
            m.set(x, y, WALL, True)
        else:
            m.set(x, y, STONE_ALT)

m.add_npc("Senior Analyst", "analyst", 10, 8, "left")
m.add_npc("The Coder", "coder", 18, 12, "down")

m.set(12, 17, SAND)
m.collision[17 * 25 + 12] = 0
m.add_warp("exit", 12 * 32, 17 * 32, 32, 32,
           "claw-town", 26 * 32, 11 * 32)

m.export("guild-hall-interior.json")

# ====================================================================
# LORE VILLAGE
# ====================================================================
m = MapBuilder(35, 25)
m.border()

m.path_h(12)
m.path_h(13)

# Elder's Library
door_x, door_y = m.building(8, 5, 7, 5)
m.path_v(11, 10, 12)
m.add_npc("The Elder", "lorekeeper", 11, 7, "down")

# Trader's Market
door_x, door_y = m.building(22, 5, 7, 5)
m.path_v(25, 10, 12)
m.add_npc("Mysterious Trader", "trader", 25, 7, "down")

# Left entrance
m.open_border(0, 12)
m.open_border(0, 13)
m.add_warp("to-route-1", 0, 12 * 32, 32, 64,
           "route-1", 28 * 32, 14 * 32)

m.export("lore-village.json")

# ====================================================================
# ROUTE 1
# ====================================================================
m = MapBuilder(30, 20)
m.border()

m.path_h(14)
m.path_h(15)

# Exits
m.open_border(0, 14)
m.open_border(0, 15)
m.open_border(29, 14)
m.open_border(29, 15)

# Some trees along the route
m.trees([
    (5, 3), (6, 3), (14, 3), (15, 3), (22, 3), (23, 3),
    (5, 17), (6, 17), (14, 17), (15, 17), (22, 17), (23, 17),
    (10, 8), (11, 8), (18, 8), (19, 8),
])

m.add_warp("to-claw-town", 0, 14 * 32, 32, 64,
           "claw-town", 48 * 32, 16 * 32)
m.add_warp("to-lore-village", 29 * 32, 14 * 32, 32, 64,
           "lore-village", 32, 12 * 32)

m.export("route-1.json")

print("All maps generated!")
