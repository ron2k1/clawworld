"""
build_tileset.py — Assemble the ClawWorld city tileset.

Combines AI-generated textures (downscaled from 512x512) with
programmatically drawn structural tiles into a single tileset PNG.

Output: public/tilesets/city.png  (21 columns, N rows, 32x32 per tile)
"""

import os
import math
from PIL import Image, ImageDraw, ImageFilter

# ── constants ──────────────────────────────────────────────────────────
TILE = 32
COLS = 21
COMFY = "./assets/comfyui-output"
OUT_DIR = "./public/tilesets"
OUT_PATH = os.path.join(OUT_DIR, "city.png")

# ── helpers ────────────────────────────────────────────────────────────

def load_ai_tile(filename: str) -> Image.Image:
    """Load a ComfyUI texture and downscale to 32x32 with nearest-neighbor."""
    path = os.path.join(COMFY, filename)
    img = Image.open(path).convert("RGBA")
    # Crop center 480x480 (avoid edge artifacts), then resize
    w, h = img.size
    cx, cy = w // 2, h // 2
    half = min(w, h) // 2 - 16  # small margin
    box = (cx - half, cy - half, cx + half, cy + half)
    cropped = img.crop(box)
    return cropped.resize((TILE, TILE), Image.NEAREST)


def new_tile(color=(0, 0, 0, 255)) -> Image.Image:
    """Create a blank 32x32 RGBA tile filled with color."""
    img = Image.new("RGBA", (TILE, TILE), color)
    return img


def draw_noise(draw: ImageDraw.ImageDraw, base_color: tuple, density=40, variance=8):
    """Add subtle pixel noise for texture."""
    import random
    random.seed(42)
    r, g, b = base_color[:3]
    for _ in range(density):
        x = random.randint(0, TILE - 1)
        y = random.randint(0, TILE - 1)
        dr = random.randint(-variance, variance)
        nr = max(0, min(255, r + dr))
        ng = max(0, min(255, g + dr))
        nb = max(0, min(255, b + dr))
        draw.point((x, y), fill=(nr, ng, nb, 255))


# ── tile generators ───────────────────────────────────────────────────

def make_asphalt():
    """Dark asphalt - solid dark grey with subtle noise."""
    base = (58, 58, 58)
    img = new_tile((*base, 255))
    draw = ImageDraw.Draw(img)
    draw_noise(draw, base, density=60, variance=6)
    return img


def make_asphalt_yellow_h():
    """Asphalt with horizontal yellow center dashed line."""
    img = make_asphalt()
    draw = ImageDraw.Draw(img)
    y = TILE // 2
    # Dashed line: 8px on, 8px off, 8px on, 8px off
    for sx in range(0, TILE, 16):
        draw.rectangle([sx, y - 1, sx + 7, y], fill=(220, 200, 50, 255))
    return img


def make_asphalt_yellow_v():
    """Asphalt with vertical yellow center dashed line."""
    img = make_asphalt()
    draw = ImageDraw.Draw(img)
    x = TILE // 2
    for sy in range(0, TILE, 16):
        draw.rectangle([x - 1, sy, x, sy + 7], fill=(220, 200, 50, 255))
    return img


def make_asphalt_white_h():
    """Asphalt with horizontal white edge line."""
    img = make_asphalt()
    draw = ImageDraw.Draw(img)
    # Solid white line near bottom edge
    draw.rectangle([0, TILE - 3, TILE - 1, TILE - 1], fill=(230, 230, 230, 255))
    return img


def make_asphalt_white_v():
    """Asphalt with vertical white edge line."""
    img = make_asphalt()
    draw = ImageDraw.Draw(img)
    draw.rectangle([TILE - 3, 0, TILE - 1, TILE - 1], fill=(230, 230, 230, 255))
    return img


def make_crosswalk():
    """Crosswalk — horizontal white bars on asphalt."""
    img = make_asphalt()
    draw = ImageDraw.Draw(img)
    for y in range(2, TILE, 6):
        draw.rectangle([0, y, TILE - 1, y + 2], fill=(240, 240, 240, 255))
    return img


def make_sidewalk():
    """Light grey sidewalk with subtle grid lines."""
    base = (176, 176, 176)
    img = new_tile((*base, 255))
    draw = ImageDraw.Draw(img)
    draw_noise(draw, base, density=50, variance=5)
    # Grid lines every 16px
    grid_color = (155, 155, 155, 255)
    for i in range(0, TILE, 16):
        draw.line([(i, 0), (i, TILE - 1)], fill=grid_color, width=1)
        draw.line([(0, i), (TILE - 1, i)], fill=grid_color, width=1)
    return img


def make_curb_h():
    """Curb edge horizontal: top=sidewalk, bottom=asphalt, curb line between."""
    img = new_tile()
    sw = make_sidewalk()
    asph = make_asphalt()
    img.paste(sw.crop((0, 0, TILE, TILE // 2 - 1)), (0, 0))
    img.paste(asph.crop((0, 0, TILE, TILE // 2 - 1)), (0, TILE // 2 + 1))
    draw = ImageDraw.Draw(img)
    # Curb line
    draw.rectangle([0, TILE // 2 - 1, TILE - 1, TILE // 2], fill=(140, 140, 140, 255))
    return img


def make_curb_v():
    """Curb edge vertical: left=sidewalk, right=asphalt."""
    img = new_tile()
    sw = make_sidewalk()
    asph = make_asphalt()
    img.paste(sw.crop((0, 0, TILE // 2 - 1, TILE)), (0, 0))
    img.paste(asph.crop((0, 0, TILE // 2 - 1, TILE)), (TILE // 2 + 1, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([TILE // 2 - 1, 0, TILE // 2, TILE - 1], fill=(140, 140, 140, 255))
    return img


def make_brick_roof():
    """Red brick roof — top-down brick pattern."""
    base = (139, 58, 58)
    img = new_tile((*base, 255))
    draw = ImageDraw.Draw(img)
    mortar = (100, 45, 45, 255)
    # Horizontal mortar lines every 6px
    for y in range(0, TILE, 6):
        draw.line([(0, y), (TILE - 1, y)], fill=mortar, width=1)
    # Vertical mortar — offset every other row
    for row in range(0, TILE // 6 + 1):
        offset = 8 if row % 2 else 0
        y_start = row * 6
        for x in range(offset, TILE, 16):
            draw.line([(x, y_start), (x, y_start + 5)], fill=mortar, width=1)
    draw_noise(draw, base, density=30, variance=8)
    return img


def make_concrete_roof():
    """Grey concrete roof with subtle noise."""
    base = (112, 112, 112)
    img = new_tile((*base, 255))
    draw = ImageDraw.Draw(img)
    draw_noise(draw, base, density=80, variance=4)
    return img


def make_metal_roof():
    """Dark metal roof with rivet dots."""
    base = (64, 64, 80)
    img = new_tile((*base, 255))
    draw = ImageDraw.Draw(img)
    draw_noise(draw, base, density=40, variance=5)
    rivet = (90, 90, 105, 255)
    for y in range(4, TILE, 8):
        for x in range(4, TILE, 8):
            draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=rivet)
    return img


def make_wall_edge(side: str):
    """Building wall edge with shadow line on the given side (n/s/e/w)."""
    base = (150, 140, 130, 255)
    shadow = (60, 55, 50, 255)
    img = new_tile(base)
    draw = ImageDraw.Draw(img)
    draw_noise(draw, base[:3], density=30, variance=5)
    if side == "n":
        draw.rectangle([0, 0, TILE - 1, 2], fill=shadow)
    elif side == "s":
        draw.rectangle([0, TILE - 3, TILE - 1, TILE - 1], fill=shadow)
    elif side == "e":
        draw.rectangle([TILE - 3, 0, TILE - 1, TILE - 1], fill=shadow)
    elif side == "w":
        draw.rectangle([0, 0, 2, TILE - 1], fill=shadow)
    return img


def make_wall_corner(corner: str):
    """Building corner tile. corner = 'nw','ne','sw','se'."""
    base = (150, 140, 130, 255)
    shadow = (60, 55, 50, 255)
    img = new_tile(base)
    draw = ImageDraw.Draw(img)
    draw_noise(draw, base[:3], density=30, variance=5)
    if "n" in corner:
        draw.rectangle([0, 0, TILE - 1, 2], fill=shadow)
    if "s" in corner:
        draw.rectangle([0, TILE - 3, TILE - 1, TILE - 1], fill=shadow)
    if "w" in corner:
        draw.rectangle([0, 0, 2, TILE - 1], fill=shadow)
    if "e" in corner:
        draw.rectangle([TILE - 3, 0, TILE - 1, TILE - 1], fill=shadow)
    return img


def make_tile_floor():
    """White/grey checkerboard tile floor."""
    img = new_tile((220, 220, 220, 255))
    draw = ImageDraw.Draw(img)
    dark = (195, 195, 200, 255)
    size = 8
    for r in range(TILE // size):
        for c in range(TILE // size):
            if (r + c) % 2 == 0:
                draw.rectangle([c * size, r * size, (c + 1) * size - 1, (r + 1) * size - 1], fill=dark)
    return img


def make_carpet():
    """Dark blue carpet with subtle texture."""
    base = (42, 42, 90)
    img = new_tile((*base, 255))
    draw = ImageDraw.Draw(img)
    draw_noise(draw, base, density=80, variance=6)
    return img


def make_lab_floor():
    """White lab floor with faint grid."""
    base = (235, 235, 240)
    img = new_tile((*base, 255))
    draw = ImageDraw.Draw(img)
    grid = (215, 215, 220, 255)
    for i in range(0, TILE, 8):
        draw.line([(i, 0), (i, TILE - 1)], fill=grid, width=1)
        draw.line([(0, i), (TILE - 1, i)], fill=grid, width=1)
    return img


def make_tree_canopy():
    """Tree canopy — green circle on grass-colored background."""
    # Grass base
    grass = load_ai_tile("CW_V3_grass_00001_.png")
    img = grass.copy()
    draw = ImageDraw.Draw(img)
    # Dark green canopy circle
    cx, cy = TILE // 2, TILE // 2
    r = 12
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(30, 100, 30, 255))
    # Lighter highlights
    draw.ellipse([cx - r + 3, cy - r + 2, cx + 4, cy + 4], fill=(45, 130, 45, 200))
    draw.ellipse([cx - 2, cy - 4, cx + r - 3, cy + r - 5], fill=(38, 115, 38, 180))
    return img


def make_bush():
    """Bush/hedge — smaller green shape on grass."""
    grass = load_ai_tile("CW_V3_grass_00001_.png")
    img = grass.copy()
    draw = ImageDraw.Draw(img)
    cx, cy = TILE // 2, TILE // 2
    r = 7
    draw.ellipse([cx - r - 3, cy - r, cx + r + 3, cy + r], fill=(35, 95, 35, 255))
    draw.ellipse([cx - r, cy - r + 2, cx + r, cy + r - 2], fill=(50, 120, 45, 230))
    return img


def make_streetlight():
    """Streetlight — small bright circle and post dot on sidewalk."""
    img = make_sidewalk()
    draw = ImageDraw.Draw(img)
    cx, cy = TILE // 2, TILE // 2
    # Post base (dark circle)
    draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(50, 50, 50, 255))
    # Light glow
    draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 255, 200, 80))
    draw.ellipse([cx - 1, cy - 1, cx + 1, cy + 1], fill=(255, 255, 220, 255))
    return img


def make_bench():
    """Bench — brown rectangle on sidewalk."""
    img = make_sidewalk()
    draw = ImageDraw.Draw(img)
    # Bench seat
    draw.rectangle([6, 12, 25, 19], fill=(120, 70, 30, 255))
    # Legs
    draw.rectangle([7, 10, 9, 12], fill=(90, 55, 25, 255))
    draw.rectangle([22, 10, 24, 12], fill=(90, 55, 25, 255))
    draw.rectangle([7, 19, 9, 21], fill=(90, 55, 25, 255))
    draw.rectangle([22, 19, 24, 21], fill=(90, 55, 25, 255))
    # Back rest
    draw.rectangle([6, 10, 25, 11], fill=(110, 65, 28, 255))
    return img


def make_manhole():
    """Manhole cover — dark circle on asphalt."""
    img = make_asphalt()
    draw = ImageDraw.Draw(img)
    cx, cy = TILE // 2, TILE // 2
    r = 8
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(45, 45, 45, 255))
    draw.ellipse([cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1], fill=(55, 55, 55, 255))
    # Cross pattern
    draw.line([(cx - 5, cy), (cx + 5, cy)], fill=(40, 40, 40, 255), width=1)
    draw.line([(cx, cy - 5), (cx, cy + 5)], fill=(40, 40, 40, 255), width=1)
    return img


def make_doormat():
    """Door mat / entrance marker on sidewalk."""
    img = make_sidewalk()
    draw = ImageDraw.Draw(img)
    draw.rectangle([4, 10, 27, 21], fill=(140, 100, 60, 255))
    draw.rectangle([5, 11, 26, 20], fill=(160, 115, 70, 255))
    # Subtle stripe
    draw.line([(6, 15), (25, 15)], fill=(140, 100, 55, 255), width=1)
    draw.line([(6, 16), (25, 16)], fill=(140, 100, 55, 255), width=1)
    return img


def make_water():
    """Water tile — blue with subtle wave pattern."""
    base = (40, 80, 160)
    img = new_tile((*base, 255))
    draw = ImageDraw.Draw(img)
    import random
    random.seed(99)
    # Wave highlights
    for y in range(0, TILE, 4):
        offset = (y // 4) % 2 * 3
        for x in range(offset, TILE, 8):
            w = random.randint(2, 5)
            c = random.randint(60, 110)
            draw.line([(x, y), (x + w, y)], fill=(c, c + 40, 200, 255), width=1)
    # Slight overall noise
    draw_noise(draw, base, density=30, variance=10)
    return img


def make_water_edge():
    """Water edge — top half grass, bottom half water."""
    grass = load_ai_tile("CW_V3_grass_00001_.png")
    water = make_water()
    img = new_tile()
    img.paste(grass.crop((0, 0, TILE, TILE // 2)), (0, 0))
    img.paste(water.crop((0, 0, TILE, TILE // 2)), (0, TILE // 2))
    # Transition line
    draw = ImageDraw.Draw(img)
    import random
    random.seed(77)
    for x in range(TILE):
        jitter = random.choice([-1, 0, 0, 1])
        y = TILE // 2 + jitter
        draw.point((x, y), fill=(60, 110, 80, 255))
    return img


# ── main assembly ─────────────────────────────────────────────────────

def build():
    tiles = []
    index = {}

    def add(tile_img, desc):
        tid = len(tiles)
        tiles.append(tile_img)
        index[tid] = desc
        return tid

    # === AI-generated ground textures (IDs 0-6) ===
    add(load_ai_tile("CW_V3_grass_00001_.png"),         "Grass")
    add(load_ai_tile("CW_V3_grass_flowers_00001_.png"), "Grass with flowers")
    add(load_ai_tile("CW_V3_wood_floor_00001_.png"),    "Wood floor")
    add(load_ai_tile("CW_V3_dirt_path_00001_.png"),     "Dirt path")
    add(load_ai_tile("CW_V3_sand_00001_.png"),          "Sand")
    add(load_ai_tile("CW_V3_gravel_00001_.png"),        "Gravel")
    add(load_ai_tile("CW_V3_glass_skylight_00001_.png"),"Glass skylight (prop)")

    # === Road / Ground tiles (IDs 7-15) ===
    add(make_asphalt(),          "Dark asphalt")
    add(make_asphalt_yellow_h(), "Asphalt + yellow dashed line (horizontal)")
    add(make_asphalt_yellow_v(), "Asphalt + yellow dashed line (vertical)")
    add(make_asphalt_white_h(),  "Asphalt + white edge line (horizontal)")
    add(make_asphalt_white_v(),  "Asphalt + white edge line (vertical)")
    add(make_crosswalk(),        "Crosswalk stripes")
    add(make_sidewalk(),         "Sidewalk")
    add(make_curb_h(),           "Curb edge (horizontal: sidewalk top, asphalt bottom)")
    add(make_curb_v(),           "Curb edge (vertical: sidewalk left, asphalt right)")

    # === Building / Structure tiles (IDs 16-27) ===
    add(make_brick_roof(),       "Red brick roof")
    add(make_concrete_roof(),    "Grey concrete roof")
    add(make_metal_roof(),       "Dark metal roof with rivets")
    add(make_wall_edge("n"),     "Building wall edge — north shadow")
    add(make_wall_edge("s"),     "Building wall edge — south shadow")
    add(make_wall_edge("e"),     "Building wall edge — east shadow")
    add(make_wall_edge("w"),     "Building wall edge — west shadow")
    add(make_wall_corner("nw"),  "Building corner — NW")
    add(make_wall_corner("ne"),  "Building corner — NE")
    add(make_wall_corner("sw"),  "Building corner — SW")
    add(make_wall_corner("se"),  "Building corner — SE")

    # === Interior tiles (IDs 28-30) ===
    add(make_tile_floor(),       "Checkerboard tile floor")
    add(make_carpet(),           "Dark blue carpet")
    add(make_lab_floor(),        "Lab floor (white + grid)")

    # === Props / Decoration (IDs 31-36) ===
    add(make_tree_canopy(),      "Tree canopy")
    add(make_bush(),             "Bush / hedge")
    add(make_streetlight(),      "Streetlight")
    add(make_bench(),            "Bench")
    add(make_manhole(),          "Manhole cover")
    add(make_doormat(),          "Door mat / entrance marker")

    # === Water tiles (IDs 37-38) ===
    add(make_water(),            "Water")
    add(make_water_edge(),       "Water edge (grass/water)")

    # === Extra AI textures we have available (IDs 39+) ===
    extras = [
        ("CW_V3_asphalt_00001_.png",        "AI asphalt texture"),
        ("CW_V3_brick_roof_00001_.png",      "AI brick roof texture"),
        ("CW_V3_brick_wall_top_00001_.png",  "AI brick wall (top-down)"),
        ("CW_V3_carpet_00001_.png",          "AI carpet texture"),
        ("CW_V3_crosswalk_00001_.png",       "AI crosswalk texture"),
        ("CW_V3_curb_edge_00001_.png",       "AI curb edge texture"),
        ("CW_V3_grey_roof_00001_.png",       "AI grey roof texture"),
        ("CW_V3_hedge_00001_.png",           "AI hedge texture"),
        ("CW_V3_metal_roof_00001_.png",      "AI metal roof texture"),
        ("CW_V3_road_yellow_line_00001_.png","AI road with yellow line"),
        ("CW_V3_sidewalk_00001_.png",        "AI sidewalk texture"),
        ("CW_V3_tile_floor_00001_.png",      "AI tile floor texture"),
        ("CW_V3_water_00001_.png",           "AI water texture"),
    ]
    for fname, desc in extras:
        path = os.path.join(COMFY, fname)
        if os.path.exists(path):
            add(load_ai_tile(fname), desc)

    # ── assemble into sheet ────────────────────────────────────────────
    num_tiles = len(tiles)
    rows = math.ceil(num_tiles / COLS)
    sheet_w = COLS * TILE
    sheet_h = rows * TILE

    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    for i, tile in enumerate(tiles):
        col = i % COLS
        row = i // COLS
        sheet.paste(tile, (col * TILE, row * TILE))

    os.makedirs(OUT_DIR, exist_ok=True)
    sheet.save(OUT_PATH, "PNG")

    # ── print results ──────────────────────────────────────────────────
    print(f"Tileset saved: {OUT_PATH}")
    print(f"Dimensions: {sheet_w}x{sheet_h} ({COLS} cols x {rows} rows)")
    print(f"Total tiles: {num_tiles}")
    print()
    print("TILE INDEX")
    print("=" * 60)
    for tid, desc in sorted(index.items()):
        col = tid % COLS
        row = tid // COLS
        print(f"  {tid:3d}  ({col:2d},{row:2d})  {desc}")


if __name__ == "__main__":
    build()
