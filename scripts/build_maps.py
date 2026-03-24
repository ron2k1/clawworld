"""Generate all 8 map JSON files for ClawWorld using the Kenney Urban tileset."""
import json
import random
import os

random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "data", "maps")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Urban tileset metadata (27 cols × 18 rows, 32×32 tiles) ──
TILESET_META = {
    "columns": 27,
    "firstgid": 1,
    "image": "../tilesets/urban.png",
    "imageheight": 576,
    "imagewidth": 864,
    "margin": 0,
    "name": "urban",
    "spacing": 0,
    "tilecount": 486,
    "tileheight": 32,
    "tilewidth": 32,
}

# ── Tile IDs (1-based) ──

# Grass autotile
GRASS_NW, GRASS_N, GRASS_NE = 1, 2, 3
GRASS_W, GRASS_C, GRASS_E = 28, 29, 30
GRASS_SW, GRASS_S, GRASS_SE = 55, 56, 57
GRASS_FILL = [6, 7, 33, 34]  # solid fill alternatives

# Sidewalk autotile
SIDE_NW, SIDE_N, SIDE_NE = 9, 10, 11
SIDE_W, SIDE_C, SIDE_E = 36, 37, 38
SIDE_SW, SIDE_S, SIDE_SE = 63, 64, 65
SIDE_FILL = [14, 15, 41, 42]

# Road / asphalt
ROAD = 434
ROAD2 = 461
ROAD3 = 462
ROAD_MARK1 = 407
ROAD_MARK2 = 408
ROAD_CURB_N = 438
ROAD_CURB_S = 465
ROAD_CURB_W = 439
ROAD_CURB_E = 466
CROSSWALK = 437
ROAD_FILLS = [440, 441, 442, 443, 467, 468, 469, 470]

# Red brick roof autotile
# NOTE: cols 22-26 (0-indexed 21-26) are character sprites — avoid tile IDs
# where (id-1)%27 >= 21, i.e. 22,23,49,50,76,77,103,104,130,131,157,158...
ROOF_NW, ROOF_N, ROOF_NE = 17, 18, 19
ROOF_FILL1, ROOF_E, ROOF_W = 20, 21, 20  # was 23 (char col) -> reuse 20
ROOF_FILL2 = 20  # was 22 (char col) -> reuse 20
ROOF_BOT = [71, 72, 73, 74, 75, 76, 71]  # was 77 (char col) -> reuse 71
ROOF_MID = [44, 45, 46, 47, 48, 44, 45]  # was 49,50 (char col) -> safe dupes

# Brown/orange roof (trim last 2 entries that fall in char cols)
BROOF_TOP = [98, 99, 100, 101, 102, 98, 99]    # was 103,104 -> safe dupes
BROOF_MID = [125, 126, 127, 128, 129, 125, 126]  # was 130,131 -> safe dupes
BROOF_BOT = [152, 153, 154, 155, 156, 152, 153]  # was 157,158 -> safe dupes

# Building facades (south-facing wall/front)
AWNING_L, AWNING_C1, AWNING_C2, AWNING_R = 329, 330, 331, 332
AWNING_SMALL = 333
STORE_WINDOW_L, STORE_WINDOW_R = 413, 414
BLDG_WALL_DARK = [415, 416]
BLDG_WALL_PURPLE = [435, 436]
DOOR_1, DOOR_2 = 361, 362
FENCE_ORANGE = [383, 384, 385, 386]

# Traffic lights
TRAFFIC_LIGHT = [409, 410, 411, 412]

# Vehicles
TAXI = [421, 422, 423, 424]
RED_CAR = [448, 449, 475, 476]
GREEN_TRUCK = [427, 454]

# Interior floors
# Beige/tan (office)
BEIGE_NW, BEIGE_N, BEIGE_NE = 82, 83, 84
BEIGE_W, BEIGE_C, BEIGE_E = 109, 110, 111
BEIGE_SW, BEIGE_S, BEIGE_SE = 136, 137, 138

# Gray/checkered (lab/guild)
GCHECK_NW, GCHECK_N, GCHECK_NE = 90, 91, 92
GCHECK_W, GCHECK_C, GCHECK_E = 117, 118, 119
GCHECK_SW, GCHECK_S, GCHECK_SE = 144, 145, 146

# Dark blue (workshop)
DBLUE = [85, 86, 112, 113, 139, 140, 141, 142]

# Light beige/wood
WOOD_NW, WOOD_N = 87, 88
WOOD_W, WOOD_E = 114, 115

# Gray plain walls
WALL_NW, WALL_NE = 93, 94
WALL_W, WALL_E = 120, 121
WALL_SW, WALL_SE = 147, 148

# Light blue/checkered (townhall)
LBLUE_NW, LBLUE_N = 95, 96
LBLUE_W, LBLUE_E = 122, 123

# Water
WATER_NW, WATER_N, WATER_NE = 171, 172, 173
WATER_W, WATER_C, WATER_E = 198, 199, 200
WATER_SW, WATER_S, WATER_SE = 225, 226, 227

# Trees (green) — top=canopy, bottom=trunk
TREE_TOP, TREE_BOT = 233, 260
TREE_CLUSTER = [234, 235, 236, 261, 262, 263]
SMALL_TREE = [287, 288, 289, 290, 291, 292]  # removed 293 (character sprite)

# Trees (autumn)
ATREE = [314, 315, 316, 341, 342, 343]

# Props
STREETLIGHT1, STREETLIGHT2 = 163, 164
SIGN1, SIGN2, SIGN3 = 165, 166, 167
BENCH = 244
BARRIER = 190

# Building walls
BWALL1, BWALL2, BWALL3 = 325, 326, 327
BWALL_WIN1, BWALL_WIN2 = 282, 283
BWALL_WIN3, BWALL_WIN4 = 309, 310
BWALL_DOOR = 360


# ── Helper functions ──

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


class MapBuilder:
    def __init__(self, w, h, default_tile=0):
        self.w = w
        self.h = h
        self.ground = [default_tile] * (w * h)
        self.collision = [0] * (w * h)
        self.objects = []
        self._oid = 1

    def idx(self, x, y):
        return y * self.w + x

    def in_bounds(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def set(self, x, y, tile, coll=None):
        if self.in_bounds(x, y):
            self.ground[self.idx(x, y)] = tile
            if coll is not None:
                self.collision[self.idx(x, y)] = 1 if coll else 0

    def set_coll(self, x, y, val=1):
        if self.in_bounds(x, y):
            self.collision[self.idx(x, y)] = val

    def get(self, x, y):
        if self.in_bounds(x, y):
            return self.ground[self.idx(x, y)]
        return 0

    def fill(self, x1, y1, x2, y2, tile, coll=None):
        for y in range(y1, y2):
            for x in range(x1, x2):
                self.set(x, y, tile, coll)

    def fill_random(self, x1, y1, x2, y2, tiles, coll=None):
        for y in range(y1, y2):
            for x in range(x1, x2):
                self.set(x, y, random.choice(tiles), coll)

    def grass_rect(self, x1, y1, x2, y2):
        """Fill a rectangle with proper grass autotile edges."""
        for y in range(y1, y2):
            for x in range(x1, x2):
                top = (y == y1)
                bot = (y == y2 - 1)
                left = (x == x1)
                right = (x == x2 - 1)
                if top and left:
                    t = GRASS_NW
                elif top and right:
                    t = GRASS_NE
                elif bot and left:
                    t = GRASS_SW
                elif bot and right:
                    t = GRASS_SE
                elif top:
                    t = GRASS_N
                elif bot:
                    t = GRASS_S
                elif left:
                    t = GRASS_W
                elif right:
                    t = GRASS_E
                else:
                    t = random.choice([GRASS_C, GRASS_C, GRASS_C] + GRASS_FILL)
                self.set(x, y, t, False)

    def sidewalk_rect(self, x1, y1, x2, y2):
        """Fill rectangle with sidewalk autotile."""
        for y in range(y1, y2):
            for x in range(x1, x2):
                top = (y == y1)
                bot = (y == y2 - 1)
                left = (x == x1)
                right = (x == x2 - 1)
                if top and left:
                    t = SIDE_NW
                elif top and right:
                    t = SIDE_NE
                elif bot and left:
                    t = SIDE_SW
                elif bot and right:
                    t = SIDE_SE
                elif top:
                    t = SIDE_N
                elif bot:
                    t = SIDE_S
                elif left:
                    t = SIDE_W
                elif right:
                    t = SIDE_E
                else:
                    t = random.choice([SIDE_C, SIDE_C] + SIDE_FILL[:2])
                self.set(x, y, t, False)

    def road_h(self, y, x1, x2):
        """Horizontal road with curbs."""
        for x in range(x1, x2):
            self.set(x, y, ROAD_CURB_N, False)
            self.set(x, y + 1, random.choice([ROAD, ROAD2]), False)
            self.set(x, y + 2, ROAD_CURB_S, False)

    def road_h_wide(self, y, x1, x2):
        """Wider 2-lane road."""
        for x in range(x1, x2):
            self.set(x, y, ROAD_CURB_N, False)
            self.set(x, y + 1, random.choice([ROAD_MARK1, ROAD_MARK2]), False)
            self.set(x, y + 2, random.choice([ROAD, ROAD2, ROAD3]), False)
            self.set(x, y + 3, ROAD_CURB_S, False)

    def road_v(self, x, y1, y2):
        """Vertical road (2 tiles wide)."""
        for y in range(y1, y2):
            self.set(x, y, ROAD_CURB_W, False)
            self.set(x + 1, y, random.choice([ROAD, ROAD2]), False)
            self.set(x + 2, y, ROAD_CURB_E, False)

    def building_roof_red(self, x1, y1, w, h):
        """Place a red brick roof building with facade at bottom row.
        Top rows = roof tiles, bottom row = storefront/awning facade."""
        roof_h = h - 1  # all rows except the last are roof
        for y in range(y1, y1 + roof_h):
            for x in range(x1, x1 + w):
                ry = y - y1
                rx = x - x1
                top = (ry == 0)
                bot = (ry == roof_h - 1)
                left = (rx == 0)
                right = (rx == w - 1)
                if top and left:
                    t = ROOF_NW
                elif top and right:
                    t = ROOF_NE
                elif bot and left:
                    t = ROOF_BOT[0]
                elif bot and right:
                    t = ROOF_BOT[min(6, w - 1)]
                elif top:
                    t = ROOF_N
                elif bot:
                    t = random.choice(ROOF_BOT[1:5])
                elif left:
                    t = ROOF_W
                elif right:
                    t = ROOF_E
                else:
                    t = random.choice([ROOF_FILL1, ROOF_FILL2])
                self.set(x, y, t, True)

        # Bottom row: facade with awning/storefront
        facade_y = y1 + roof_h
        for x in range(x1, x1 + w):
            rx = x - x1
            if rx == 0:
                t = AWNING_L
            elif rx == w - 1:
                t = AWNING_R
            elif rx == w // 2:
                t = DOOR_1  # door in the middle
            elif rx == w // 2 - 1:
                t = STORE_WINDOW_L
            elif rx == w // 2 + 1:
                t = STORE_WINDOW_R
            else:
                t = random.choice([AWNING_C1, AWNING_C2])
            self.set(x, facade_y, t, True)

    def building_roof_brown(self, x1, y1, w, h):
        """Place a brown/orange roof building with facade at bottom row."""
        roof_h = h - 1  # all rows except last are roof
        rows = [BROOF_TOP, BROOF_MID, BROOF_BOT]
        for y in range(y1, y1 + roof_h):
            ry = y - y1
            row_tiles = rows[min(ry, 2)]
            for x in range(x1, x1 + w):
                rx = x - x1
                ti = min(rx, len(row_tiles) - 1)
                self.set(x, y, row_tiles[ti], True)

        # Bottom row: facade with dark wall + door
        facade_y = y1 + roof_h
        for x in range(x1, x1 + w):
            rx = x - x1
            if rx == w // 2:
                t = DOOR_2
            elif rx < w // 2:
                t = BLDG_WALL_DARK[rx % len(BLDG_WALL_DARK)]
            else:
                t = BLDG_WALL_PURPLE[rx % len(BLDG_WALL_PURPLE)]
            self.set(x, facade_y, t, True)

    def place_tree(self, x, y):
        """Place a single tree (2 tiles tall: canopy on top, trunk below). Both blocked."""
        self.set(x, y, TREE_TOP, True)
        self.set(x, y + 1, TREE_BOT, True)

    def place_tree_cluster(self, x, y):
        """Place a 2x2 tree cluster."""
        self.set(x, y, 234, True)
        self.set(x + 1, y, 235, True)
        self.set(x, y + 1, 261, True)
        self.set(x + 1, y + 1, 262, True)

    def place_autumn_tree(self, x, y):
        """Single autumn tree (2 tall)."""
        self.set(x, y, 314, True)
        self.set(x, y + 1, 341, True)

    def water_rect(self, x1, y1, x2, y2):
        """Fill with water autotile edges, all blocked."""
        for y in range(y1, y2):
            for x in range(x1, x2):
                top = (y == y1)
                bot = (y == y2 - 1)
                left = (x == x1)
                right = (x == x2 - 1)
                if top and left:
                    t = WATER_NW
                elif top and right:
                    t = WATER_NE
                elif bot and left:
                    t = WATER_SW
                elif bot and right:
                    t = WATER_SE
                elif top:
                    t = WATER_N
                elif bot:
                    t = WATER_S
                elif left:
                    t = WATER_W
                elif right:
                    t = WATER_E
                else:
                    t = WATER_C
                self.set(x, y, t, True)

    def interior_floor(self, x1, y1, x2, y2, nw, n, ne, w, c, e, sw, s, se):
        """Fill interior with proper autotile floor."""
        for y in range(y1, y2):
            for x in range(x1, x2):
                top = (y == y1)
                bot = (y == y2 - 1)
                left = (x == x1)
                right = (x == x2 - 1)
                if top and left:
                    t = nw
                elif top and right:
                    t = ne
                elif bot and left:
                    t = sw
                elif bot and right:
                    t = se
                elif top:
                    t = n
                elif bot:
                    t = s
                elif left:
                    t = w
                elif right:
                    t = e
                else:
                    t = c
                self.set(x, y, t, False)

    def wall_border(self):
        """Dark wall border around entire map (blocked)."""
        for x in range(self.w):
            self.set(x, 0, WALL_NW if x == 0 else WALL_NE if x == self.w - 1 else DBLUE[0], True)
            self.set(x, self.h - 1, WALL_SW if x == 0 else WALL_SE if x == self.w - 1 else DBLUE[1], True)
        for y in range(1, self.h - 1):
            self.set(0, y, WALL_W, True)
            self.set(self.w - 1, y, WALL_E, True)

    def add_obj(self, obj):
        obj["id"] = self._oid
        self._oid += 1
        self.objects.append(obj)

    def add_npc(self, name, agent_id, px, py, facing="down"):
        self.add_obj({
            "name": name, "type": "npc",
            "x": px, "y": py, "width": 32, "height": 32,
            "properties": [
                {"name": "agentId", "type": "string", "value": agent_id},
                {"name": "facing", "type": "string", "value": facing}
            ]
        })

    def add_warp(self, name, px, py, pw, ph, target_map, tx, ty):
        self.add_obj({
            "name": name, "type": "warp",
            "x": px, "y": py, "width": pw, "height": ph,
            "properties": [
                {"name": "targetMap", "type": "string", "value": target_map},
                {"name": "targetX", "type": "int", "value": tx},
                {"name": "targetY", "type": "int", "value": ty}
            ]
        })

    def ensure_walkable(self, px, py, pw, ph, margin=1):
        """Ensure a pixel-area is walkable (for warp zones), with margin tiles around."""
        x1 = max(0, px // 32 - margin)
        y1 = max(0, py // 32 - margin)
        x2 = min(self.w, (px + pw - 1) // 32 + 1 + margin)
        y2 = min(self.h, (py + ph - 1) // 32 + 1 + margin)
        for y in range(y1, y2):
            for x in range(x1, x2):
                self.set_coll(x, y, 0)

    def place_vehicle(self, x, y, tiles_2x2):
        """Place a 2x2 vehicle (e.g. taxi, red car). tiles_2x2 = [TL, TR, BL, BR]."""
        self.set(x, y, tiles_2x2[0], True)
        self.set(x + 1, y, tiles_2x2[1], True)
        self.set(x, y + 1, tiles_2x2[2], True)
        self.set(x + 1, y + 1, tiles_2x2[3], True)

    def export(self, filename):
        m = make_map(self.w, self.h, self.ground, self.collision, self.objects)
        path = os.path.join(OUT_DIR, filename)
        with open(path, "w") as f:
            json.dump(m, f, indent=2)
        print(f"  -> {filename} ({self.w}x{self.h}, {len(self.objects)} objects)")


# ====================================================================
# 1. WORLD MAP — Combined Outdoor (100×50)
# ====================================================================
# NPC positions (for src/data/agents.ts reference):
#   jake (Blacksmith): col 15, row 18 (Downtown sidewalk)
#   tom (Planner): col 35, row 18 (Downtown sidewalk)
#   mira (Innkeeper): col 30, row 24 (Downtown near park)
#   lorekeeper (Elder): col 56, row 18 (Market District sidewalk)
#   trader: col 85, row 24 (Harbor District sidewalk)
print("Generating maps with urban tileset...")
m = MapBuilder(100, 50)

# ======================
# CITY SECTION (cols 0-45, rows 0-30)
# ======================

# --- Rows 0-4: Top park strip (grass + trees) ---
m.grass_rect(0, 0, 46, 5)

# Scatter trees in the park
city_park_trees = [
    (2, 0), (5, 0), (9, 0), (13, 0), (17, 0), (21, 0),
    (26, 0), (30, 0), (34, 0), (38, 0), (42, 0),
    (3, 2), (7, 2), (11, 2), (15, 2), (19, 2), (23, 2),
    (28, 2), (32, 2), (36, 2), (40, 2), (44, 2),
]
for tx, ty in city_park_trees:
    if ty + 1 < 5:
        m.place_tree(tx, ty)

# Autumn trees for variety
for tx, ty in [(1, 2), (14, 0), (35, 2), (43, 0)]:
    if ty + 1 < 5:
        m.place_autumn_tree(tx, ty)

# --- Rows 5-6: Sidewalk ---
m.sidewalk_rect(0, 5, 46, 7)

# Streetlights on sidewalk
for sx in range(3, 46, 8):
    m.set(sx, 5, STREETLIGHT1, True)
    m.set(sx, 6, STREETLIGHT2, True)

# --- Rows 7-10: Main east-west road (4 tiles wide) ---
for x in range(46):
    m.set(x, 7, ROAD_CURB_N, False)
    m.set(x, 8, random.choice([ROAD_MARK1, ROAD_MARK2]), False)
    m.set(x, 9, random.choice([ROAD, ROAD2, ROAD3]), False)
    m.set(x, 10, ROAD_CURB_S, False)

# Place vehicles on road
m.place_vehicle(8, 8, TAXI)
m.place_vehicle(16, 8, RED_CAR)
m.place_vehicle(35, 8, TAXI)

# --- Rows 11-12: Sidewalk ---
m.sidewalk_rect(0, 11, 46, 13)

# Streetlights with every 8 tiles
for sx in range(5, 46, 8):
    m.set(sx, 11, STREETLIGHT1, True)
    m.set(sx, 12, STREETLIGHT2, True)

# --- Rows 13-16: Building block 1 ---
# Lab building (red roof) cols 3-8 (w=6, h=4)
m.building_roof_red(3, 13, 6, 4)

# Sidewalk gap
m.sidewalk_rect(9, 13, 11, 17)

# Building 2 (brown roof) cols 11-16 (w=6, h=4)
m.building_roof_brown(11, 13, 6, 4)

# Sidewalk gap
m.sidewalk_rect(17, 13, 19, 17)

# Town Hall building (red, wider) cols 19-25 (w=7, h=4)
m.building_roof_red(19, 13, 7, 4)

# Sidewalk gap
m.sidewalk_rect(26, 13, 28, 17)

# Building 3 (brown) cols 28-33 (w=6, h=4)
m.building_roof_brown(28, 13, 6, 4)

# Sidewalk gap
m.sidewalk_rect(34, 13, 36, 17)

# Analyst office building (red) cols 36-41 (w=6, h=4)
m.building_roof_red(36, 13, 6, 4)

# Fill remaining with sidewalk
m.sidewalk_rect(42, 13, 46, 17)
m.sidewalk_rect(0, 13, 3, 17)

# --- Rows 17-18: Sidewalk ---
m.sidewalk_rect(0, 17, 46, 19)

# Streetlights
for sx in range(5, 46, 10):
    m.set(sx, 17, STREETLIGHT1, True)
    m.set(sx, 18, STREETLIGHT2, True)

# --- Rows 19-22: Second east-west road ---
for x in range(46):
    m.set(x, 19, ROAD_CURB_N, False)
    m.set(x, 20, random.choice([ROAD_MARK1, ROAD_MARK2]), False)
    m.set(x, 21, random.choice([ROAD, ROAD2, ROAD3]), False)
    m.set(x, 22, ROAD_CURB_S, False)

# Vehicle on second road
m.place_vehicle(30, 20, RED_CAR)

# --- Rows 23-24: Sidewalk ---
m.sidewalk_rect(0, 23, 46, 25)

# --- Rows 25-28: Building block 2 + park ---
# Coder workshop building (red) cols 3-8 (w=6, h=4)
m.building_roof_red(3, 25, 6, 4)

# Sidewalk gap
m.sidewalk_rect(9, 25, 11, 29)

# Building (brown) cols 11-16 (w=6, h=4)
m.building_roof_brown(11, 25, 6, 4)

# Sidewalk gap
m.sidewalk_rect(17, 25, 19, 29)

# Park area with grass and trees cols 19-35
m.grass_rect(19, 25, 36, 29)
for tx in [20, 23, 26, 29, 32]:
    m.place_tree(tx, 25)
for tx in [21, 25, 30, 34]:
    if tx < 36:
        m.place_autumn_tree(tx, 27)
# Benches in park
m.set(24, 28, BENCH, True)
m.set(28, 28, BENCH, True)

# Guild Hall (red, wider) cols 37-43 (w=7, h=4)
m.building_roof_red(37, 25, 7, 4)

# Fill rest with sidewalk
m.sidewalk_rect(44, 25, 46, 29)
m.sidewalk_rect(0, 25, 3, 29)
m.sidewalk_rect(36, 25, 37, 29)

# --- Rows 29-30: Sidewalk ---
m.sidewalk_rect(0, 29, 46, 31)

# --- Rows 31-34: Waterfront ---
m.sidewalk_rect(0, 31, 46, 32)
m.water_rect(0, 32, 46, 50)

# --- Vertical road at cols 25-27 connecting the two E-W roads ---
for y in range(5, 31):
    if y in range(7, 11) or y in range(19, 23):
        # Intersection: fill with road
        m.set(24, y, ROAD, False)
        m.set(25, y, ROAD, False)
        m.set(26, y, ROAD, False)
        m.set(27, y, ROAD, False)
    elif 13 <= y <= 16 or 25 <= y <= 28:
        # Skip building rows — N-S road stops at sidewalks
        pass
    else:
        m.set(24, y, ROAD_CURB_W, False)
        m.set(25, y, random.choice([ROAD, ROAD2]), False)
        m.set(26, y, random.choice([ROAD, ROAD2]), False)
        m.set(27, y, ROAD_CURB_E, False)

# Crosswalk markings at intersections
for x in [24, 25, 26, 27]:
    m.set(x, 7, CROSSWALK, False)
    m.set(x, 10, CROSSWALK, False)
    m.set(x, 19, CROSSWALK, False)
    m.set(x, 22, CROSSWALK, False)

# Traffic lights at intersections
m.set(23, 7, TRAFFIC_LIGHT[0], True)
m.set(28, 10, TRAFFIC_LIGHT[1], True)
m.set(23, 19, TRAFFIC_LIGHT[2], True)
m.set(28, 22, TRAFFIC_LIGHT[3], True)

# ======================
# MARKET DISTRICT (cols 46-65, rows 0-50)
# ======================

# --- Rows 0-4: Park continues ---
m.grass_rect(46, 0, 66, 5)
for tx, ty in [(48, 0), (52, 0), (56, 0), (60, 0), (64, 0),
               (50, 2), (54, 2), (58, 2), (62, 2)]:
    if ty + 1 < 5:
        m.place_tree(tx, ty)
for tx, ty in [(49, 2), (61, 0)]:
    if ty + 1 < 5:
        m.place_autumn_tree(tx, ty)

# --- Rows 5-6: Sidewalk ---
m.sidewalk_rect(46, 5, 66, 7)
for sx in range(48, 66, 8):
    m.set(sx, 5, STREETLIGHT1, True)
    m.set(sx, 6, STREETLIGHT2, True)

# --- Rows 7-10: E-W Road 1 extends east ---
for x in range(46, 66):
    m.set(x, 7, ROAD_CURB_N, False)
    m.set(x, 8, random.choice([ROAD_MARK1, ROAD_MARK2]), False)
    m.set(x, 9, random.choice([ROAD, ROAD2, ROAD3]), False)
    m.set(x, 10, ROAD_CURB_S, False)
m.place_vehicle(50, 8, TAXI)

# --- Rows 11-12: Sidewalk ---
m.sidewalk_rect(46, 11, 66, 13)
for sx in range(48, 66, 8):
    m.set(sx, 11, STREETLIGHT1, True)
    m.set(sx, 12, STREETLIGHT2, True)

# --- Rows 13-16: Market buildings ---
m.building_roof_red(48, 13, 6, 4)
m.building_roof_brown(59, 13, 6, 4)

# --- Rows 17-18: Sidewalk ---
m.sidewalk_rect(46, 17, 66, 19)
for sx in range(48, 66, 8):
    m.set(sx, 17, STREETLIGHT1, True)
    m.set(sx, 18, STREETLIGHT2, True)
m.set(52, 18, BENCH, True)
m.set(62, 18, BENCH, True)

# --- Rows 19-22: E-W Road 2 extends east ---
for x in range(46, 66):
    m.set(x, 19, ROAD_CURB_N, False)
    m.set(x, 20, random.choice([ROAD_MARK1, ROAD_MARK2]), False)
    m.set(x, 21, random.choice([ROAD, ROAD2, ROAD3]), False)
    m.set(x, 22, ROAD_CURB_S, False)
m.place_vehicle(58, 20, RED_CAR)

# --- Rows 23-24: Sidewalk ---
m.sidewalk_rect(46, 23, 66, 25)
for sx in range(48, 66, 8):
    m.set(sx, 23, STREETLIGHT1, True)
    m.set(sx, 24, STREETLIGHT2, True)

# --- Rows 25-28: Commercial buildings ---
m.building_roof_brown(48, 25, 6, 4)
m.building_roof_red(59, 25, 6, 4)

# --- Rows 29-30: Sidewalk ---
m.sidewalk_rect(46, 29, 66, 31)
for sx in range(48, 66, 8):
    m.set(sx, 29, STREETLIGHT1, True)
    m.set(sx, 30, STREETLIGHT2, True)

# --- Rows 31-34: Waterfront (sidewalk + water edge) ---
m.sidewalk_rect(46, 31, 66, 33)
m.water_rect(46, 33, 66, 35)

# --- Rows 35-49: Water ---
m.water_rect(46, 35, 66, 50)

# --- N-S Road at cols 55-58 ---
for y in range(5, 31):
    m.set(55, y, ROAD_CURB_W, False)
    m.set(56, y, random.choice([ROAD, ROAD2, ROAD3]), False)
    m.set(57, y, random.choice([ROAD, ROAD2, ROAD3]), False)
    m.set(58, y, ROAD_CURB_E, False)

# N-S road intersections with E-W roads (rows 7-10, 19-22) — clear curbs
for y in [7, 8, 9, 10]:
    for x in [55, 56, 57, 58]:
        m.set(x, y, random.choice([ROAD, ROAD2, ROAD3]), False)
for y in [19, 20, 21, 22]:
    for x in [55, 56, 57, 58]:
        m.set(x, y, random.choice([ROAD, ROAD2, ROAD3]), False)

# Traffic lights at Market District intersections
m.set(54, 7, TRAFFIC_LIGHT[0], True)
m.set(59, 7, TRAFFIC_LIGHT[1], True)
m.set(54, 10, TRAFFIC_LIGHT[2], True)
m.set(59, 10, TRAFFIC_LIGHT[3], True)
m.set(54, 19, TRAFFIC_LIGHT[0], True)
m.set(59, 19, TRAFFIC_LIGHT[1], True)
m.set(54, 22, TRAFFIC_LIGHT[2], True)
m.set(59, 22, TRAFFIC_LIGHT[3], True)

# ======================
# HARBOR DISTRICT (cols 66-99, rows 0-50)
# ======================

# --- Rows 0-4: Park continues ---
m.grass_rect(66, 0, 100, 5)
for tx, ty in [(68, 0), (72, 0), (76, 0), (80, 0), (84, 0), (88, 0), (92, 0), (96, 0),
               (70, 2), (74, 2), (78, 2), (86, 2), (90, 2), (94, 2), (98, 2)]:
    if tx < 100 and ty + 1 < 5:
        m.place_tree(tx, ty)
for tx, ty in [(69, 2), (77, 0), (91, 2), (97, 0)]:
    if tx < 100 and ty + 1 < 5:
        m.place_autumn_tree(tx, ty)

# --- Rows 5-6: Sidewalk ---
m.sidewalk_rect(66, 5, 100, 7)
for sx in range(68, 100, 8):
    m.set(sx, 5, STREETLIGHT1, True)
    m.set(sx, 6, STREETLIGHT2, True)

# --- Rows 7-10: E-W Road 1 extends to east edge ---
for x in range(66, 100):
    m.set(x, 7, ROAD_CURB_N, False)
    m.set(x, 8, random.choice([ROAD_MARK1, ROAD_MARK2]), False)
    m.set(x, 9, random.choice([ROAD, ROAD2, ROAD3]), False)
    m.set(x, 10, ROAD_CURB_S, False)
m.place_vehicle(70, 8, RED_CAR)
m.place_vehicle(90, 8, TAXI)

# --- Rows 11-12: Sidewalk ---
m.sidewalk_rect(66, 11, 100, 13)
for sx in range(68, 100, 8):
    m.set(sx, 11, STREETLIGHT1, True)
    m.set(sx, 12, STREETLIGHT2, True)

# --- Rows 13-16: Harbor buildings (3 buildings) ---
m.building_roof_red(68, 13, 6, 4)
m.building_roof_brown(77, 13, 6, 4)
m.building_roof_red(87, 13, 6, 4)

# --- Rows 17-18: Sidewalk ---
m.sidewalk_rect(66, 17, 100, 19)
for sx in range(68, 100, 8):
    m.set(sx, 17, STREETLIGHT1, True)
    m.set(sx, 18, STREETLIGHT2, True)
m.set(75, 18, BENCH, True)
m.set(85, 18, BENCH, True)
m.set(95, 18, BENCH, True)

# --- Rows 19-22: E-W Road 2 extends to east edge ---
for x in range(66, 100):
    m.set(x, 19, ROAD_CURB_N, False)
    m.set(x, 20, random.choice([ROAD_MARK1, ROAD_MARK2]), False)
    m.set(x, 21, random.choice([ROAD, ROAD2, ROAD3]), False)
    m.set(x, 22, ROAD_CURB_S, False)
m.place_vehicle(76, 20, TAXI)

# --- Rows 23-24: Sidewalk ---
m.sidewalk_rect(66, 23, 100, 25)
for sx in range(68, 100, 8):
    m.set(sx, 23, STREETLIGHT1, True)
    m.set(sx, 24, STREETLIGHT2, True)
m.set(75, 24, BENCH, True)
m.set(95, 24, BENCH, True)

# --- Rows 25-28: Warehouse buildings (2 wider buildings) ---
m.building_roof_brown(68, 25, 8, 4)
m.building_roof_red(80, 25, 8, 4)

# --- Rows 29-30: Sidewalk ---
m.sidewalk_rect(66, 29, 100, 31)
for sx in range(68, 100, 8):
    m.set(sx, 29, STREETLIGHT1, True)
    m.set(sx, 30, STREETLIGHT2, True)

# --- Rows 31-34: Harbor waterfront with dock pier ---
m.sidewalk_rect(66, 31, 100, 33)
m.water_rect(66, 33, 100, 35)
# Dock pier: 3-wide sidewalk extending into water at col 83
for y in range(33, 38):
    m.set(82, y, SIDE_W, False)
    m.set(83, y, SIDE_C, False)
    m.set(84, y, SIDE_E, False)

# --- Rows 35-49: Water ---
m.water_rect(66, 35, 100, 50)
# Re-place pier over water
for y in range(35, 38):
    m.set(82, y, SIDE_W, False)
    m.set(83, y, SIDE_C, False)
    m.set(84, y, SIDE_E, False)

# --- N-S Road at cols 82-85 ---
for y in range(5, 31):
    m.set(82, y, ROAD_CURB_W, False)
    m.set(83, y, random.choice([ROAD, ROAD2, ROAD3]), False)
    m.set(84, y, random.choice([ROAD, ROAD2, ROAD3]), False)
    m.set(85, y, ROAD_CURB_E, False)

# N-S road intersections with E-W roads
for y in [7, 8, 9, 10]:
    for x in [82, 83, 84, 85]:
        m.set(x, y, random.choice([ROAD, ROAD2, ROAD3]), False)
for y in [19, 20, 21, 22]:
    for x in [82, 83, 84, 85]:
        m.set(x, y, random.choice([ROAD, ROAD2, ROAD3]), False)

# Traffic lights at Harbor District intersections
m.set(81, 7, TRAFFIC_LIGHT[0], True)
m.set(86, 7, TRAFFIC_LIGHT[1], True)
m.set(81, 10, TRAFFIC_LIGHT[2], True)
m.set(86, 10, TRAFFIC_LIGHT[3], True)
m.set(81, 19, TRAFFIC_LIGHT[0], True)
m.set(86, 19, TRAFFIC_LIGHT[1], True)
m.set(81, 22, TRAFFIC_LIGHT[2], True)
m.set(86, 22, TRAFFIC_LIGHT[3], True)

# ======================
# CITY BUILDING WARPS (world.json objects layer)
# ======================
# Block 1 facades are at row 16. Warps on facade row, centered on door.
# Block 2 facades are at row 28.

# Lab: cols 3-8, facade at row 16. Warp centered on door.
m.add_warp("to-lab", 4*32, 16*32, 128, 64, "lab-interior", 320, 384)
m.ensure_walkable(4*32, 16*32, 128, 64, margin=2)
for cx in range(3, 9):
    m.set(cx, 17, SIDE_C, False)
    m.set(cx, 18, SIDE_C, False)

# Town Hall: cols 19-25, facade at row 16.
m.add_warp("to-townhall", 20*32, 16*32, 128, 64, "townhall-interior", 320, 384)
m.ensure_walkable(20*32, 16*32, 128, 64, margin=2)
for cx in range(19, 26):
    m.set(cx, 17, SIDE_C, False)
    m.set(cx, 18, SIDE_C, False)

# Analyst office: cols 36-41, facade at row 16.
m.add_warp("to-analyst-office", 37*32, 16*32, 128, 64, "analyst-office", 224, 288)
m.ensure_walkable(37*32, 16*32, 128, 64, margin=2)
for cx in range(36, 42):
    m.set(cx, 17, SIDE_C, False)
    m.set(cx, 18, SIDE_C, False)

# Coder workshop: cols 3-8, facade at row 28.
for cx in range(0, 46):
    for ry in [29, 30]:
        if m.get(cx, ry) == 0:
            m.set(cx, ry, SIDE_C, False)
m.add_warp("to-coder-workshop", 4*32, 28*32, 128, 64, "coder-workshop", 224, 288)
m.ensure_walkable(4*32, 28*32, 128, 64, margin=2)

# Guild Hall: cols 37-43, facade at row 28.
m.add_warp("to-guild-hall", 38*32, 28*32, 128, 64, "guild-hall-interior", 224, 416)
m.ensure_walkable(38*32, 28*32, 128, 64, margin=2)
for cx in range(37, 44):
    m.set(cx, 29, SIDE_C, False)
    m.set(cx, 30, SIDE_C, False)

# (Roads already extended in Market/Harbor District sections above)

# ======================
# BORDER COLLISION — block all 4 edges as safety guardrail
# ======================
for x in range(m.w):
    m.set_coll(x, 0, 1)
    m.set_coll(x, m.h - 1, 1)
for y in range(m.h):
    m.set_coll(0, y, 1)
    m.set_coll(m.w - 1, y, 1)

# ======================
# FINAL PASS: No tile-0 gaps
# ======================
for y in range(50):
    for x in range(100):
        if m.get(x, y) == 0:
            # All sections: fill gaps with sidewalk
            m.set(x, y, SIDE_C, False)

m.export("world.json")

# ====================================================================
# 2. LAB INTERIOR (18×14) — exit to "world"
# ====================================================================
m = MapBuilder(18, 14)
m.wall_border()

# Gray checkered floor
m.interior_floor(1, 1, 17, 13,
    GCHECK_NW, GCHECK_N, GCHECK_NE,
    GCHECK_W, GCHECK_C, GCHECK_E,
    GCHECK_SW, GCHECK_S, GCHECK_SE)

# Dark blue accents along top wall interior
for x in range(2, 16):
    m.set(x, 1, random.choice(DBLUE[:4]), True)

# Lab benches / equipment (blocked furniture)
m.fill(2, 3, 6, 4, DBLUE[2], True)   # bench left
m.fill(12, 3, 16, 4, DBLUE[3], True)  # bench right
m.fill(2, 6, 4, 8, DBLUE[4], True)    # side equipment
m.fill(14, 6, 16, 8, DBLUE[5], True)  # side equipment

# NPC: Personal Assistant
m.add_npc("Personal Assistant", "assistant", 320, 224, "down")

# Exit warp at bottom center — points to sidewalk in front of lab in world map
# Lab is at cols 3-8, so sidewalk in front is ~col 5, row 18
for x in range(6, 12):
    m.set(x, 12, GCHECK_S, False)
    m.set(x, 13, GCHECK_S, False)
    m.set_coll(x, 12, 0)
    m.set_coll(x, 13, 0)
m.add_warp("exit", 224, 384, 160, 64, "world", 5*32, 18*32)
m.ensure_walkable(224, 384, 160, 64)

m.export("lab-interior.json")

# ====================================================================
# 3. ANALYST OFFICE (15×12) — exit to "world"
# ====================================================================
m = MapBuilder(15, 12)
m.wall_border()

# Beige/tan floor
m.interior_floor(1, 1, 14, 11,
    BEIGE_NW, BEIGE_N, BEIGE_NE,
    BEIGE_W, BEIGE_C, BEIGE_E,
    BEIGE_SW, BEIGE_S, BEIGE_SE)

# Desk in upper area (blocked)
m.fill(3, 2, 7, 3, DBLUE[0], True)
m.fill(9, 2, 12, 3, DBLUE[1], True)

# Bookshelf along left wall
m.fill(1, 2, 2, 6, DBLUE[2], True)

# NPC
m.add_npc("Senior Analyst", "analyst", 224, 160, "down")

# Exit — points to sidewalk in front of analyst office in world map
# Analyst office at cols 36-41, so sidewalk ~col 38, row 18
for x in range(5, 10):
    m.set(x, 10, BEIGE_S, False)
    m.set(x, 11, BEIGE_S, False)
    m.set_coll(x, 10, 0)
    m.set_coll(x, 11, 0)
m.add_warp("exit", 160, 320, 160, 64, "world", 38*32, 18*32)
m.ensure_walkable(160, 320, 160, 64)

m.export("analyst-office.json")

# ====================================================================
# 4. CODER WORKSHOP (15×12) — exit to "world"
# ====================================================================
m = MapBuilder(15, 12)
m.wall_border()

# Dark blue floor mixed with gray checkered
for y in range(1, 11):
    for x in range(1, 14):
        if (x + y) % 3 == 0:
            m.set(x, y, random.choice(DBLUE), False)
        else:
            m.set(x, y, GCHECK_C, False)

# Workbenches
m.fill(2, 2, 5, 3, DBLUE[0], True)
m.fill(10, 2, 13, 3, DBLUE[1], True)
m.fill(2, 7, 5, 8, DBLUE[2], True)

# NPC
m.add_npc("The Coder", "coder", 224, 160, "down")

# Exit — points to sidewalk in front of coder workshop in world map
# Coder workshop at cols 3-8, so sidewalk ~col 5, row 30
for x in range(5, 10):
    m.set(x, 10, GCHECK_S, False)
    m.set(x, 11, GCHECK_S, False)
    m.set_coll(x, 10, 0)
    m.set_coll(x, 11, 0)
m.add_warp("exit", 160, 320, 160, 64, "world", 5*32, 30*32)
m.ensure_walkable(160, 320, 160, 64)

m.export("coder-workshop.json")

# ====================================================================
# 5. GUILD HALL INTERIOR (20×15) — exit to "world"
# ====================================================================
m = MapBuilder(20, 15)
m.wall_border()

# Light beige wood floor base
for y in range(1, 14):
    for x in range(1, 19):
        if x == 1:
            t = WOOD_W
        elif x == 18:
            t = WOOD_E
        elif y == 1:
            t = WOOD_N
        elif y == 13:
            t = WOOD_W  # reuse
        else:
            t = random.choice([WOOD_NW, WOOD_N, WOOD_W, WOOD_E])
        m.set(x, y, t, False)

# Checkered center runner (rows 5-9, cols 6-13)
for y in range(5, 10):
    for x in range(6, 14):
        m.set(x, y, GCHECK_C if (x + y) % 2 == 0 else BEIGE_C, False)

# Pillars / decorative columns
for px, py in [(3, 3), (16, 3), (3, 11), (16, 11)]:
    m.set(px, py, DBLUE[0], True)

# Long table
m.fill(7, 6, 13, 8, DBLUE[2], True)

# NPCs
m.add_npc("Senior Analyst", "analyst", 320, 256, "left")
m.add_npc("The Coder", "coder", 576, 384, "down")

# Exit — points to sidewalk in front of guild hall in world map
# Guild hall at cols 37-43, so sidewalk ~col 39, row 30
for x in range(7, 13):
    m.set(x, 13, WOOD_E, False)
    m.set(x, 14, WOOD_E, False)
    m.set_coll(x, 13, 0)
    m.set_coll(x, 14, 0)
m.add_warp("exit", 224, 416, 192, 64, "world", 39*32, 30*32)
m.ensure_walkable(224, 416, 192, 64)

m.export("guild-hall-interior.json")

# ====================================================================
# 6. TOWN HALL INTERIOR (16×13) — exit to "world"
# ====================================================================
m = MapBuilder(16, 13)
m.wall_border()

# Light blue/checkered floor with beige borders
for y in range(1, 12):
    for x in range(1, 15):
        edge_x = (x == 1 or x == 14)
        edge_y = (y == 1 or y == 11)
        if edge_x or edge_y:
            m.set(x, y, BEIGE_C, False)
        else:
            if (x + y) % 2 == 0:
                m.set(x, y, LBLUE_NW, False)
            else:
                m.set(x, y, LBLUE_N, False)

# Reception desk
m.fill(5, 3, 11, 4, DBLUE[0], True)

# Seating
m.fill(3, 7, 5, 8, DBLUE[2], True)
m.fill(11, 7, 13, 8, DBLUE[3], True)

# Exit — points to sidewalk in front of town hall in world map
# Town hall at cols 19-25, so sidewalk ~col 21, row 18
for x in range(5, 11):
    m.set(x, 11, BEIGE_S, False)
    m.set(x, 12, BEIGE_S, False)
    m.set_coll(x, 11, 0)
    m.set_coll(x, 12, 0)
m.add_warp("exit", 160, 352, 192, 64, "world", 21*32, 18*32)
m.ensure_walkable(160, 352, 192, 64)

m.export("townhall-interior.json")

# ====================================================================
# DELETE old maps that are now replaced by world.json
# ====================================================================
for old_map in ["claw-town.json", "route-1.json", "lore-village.json"]:
    old_path = os.path.join(OUT_DIR, old_map)
    if os.path.exists(old_path):
        os.remove(old_path)
        print(f"  Deleted {old_map}")

print("\nAll maps generated successfully!")
