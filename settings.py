"""
settings.py
Global constants, colours, and tuneable parameters for the dungeon crawler.
All other modules import from here so changes propagate everywhere.
"""

# ── Window ─────────────────────────────────────────────────────────────────
TITLE          = "Dungeon Crawler"
SCREEN_W       = 960
SCREEN_H       = 640
FPS            = 60

# ── Tile grid ───────────────────────────────────────────────────────────────
TILE            = 32          # pixel size of one tile
COLS            = 60          # dungeon width  in tiles
ROWS            = 40          # dungeon height in tiles

# ── Dungeon generation ───────────────────────────────────────────────────────
MIN_ROOMS       = 8
MAX_ROOMS       = 14
ROOM_MIN_W      = 5           # tiles
ROOM_MAX_W      = 12
ROOM_MIN_H      = 4
ROOM_MAX_H      = 9

# ── Camera ───────────────────────────────────────────────────────────────────
CAM_SPEED       = 8           # unused in Phase 1; used later by camera follow

# ── Colours (dark dungeon palette) ──────────────────────────────────────────
BLACK           = (0,   0,   0)
DARK_BG         = (12,  10,  20)     # deep-space background
WALL_DARK       = (30,  25,  45)     # unlit wall
WALL_LIT        = (70,  60,  90)     # lit wall
FLOOR_DARK      = (20,  18,  30)     # unlit floor
FLOOR_LIT       = (50,  45,  65)     # lit floor
CORRIDOR_DARK   = (18,  15,  25)
CORRIDOR_LIT    = (45,  40,  58)

# Entities
PLAYER_COL      = (100, 200, 255)    # icy blue
ENEMY_COL       = {
    "chaser":  (220,  60,  60),      # red
    "patrol":  (220, 160,  40),      # orange
    "shooter": (180,  60, 220),      # purple
}
HEALTH_BAR_FG   = (80, 220,  80)
HEALTH_BAR_BG   = (80,  30,  30)

# Loot
POTION_COL      = ( 60, 220, 100)
WEAPON_COL      = (200, 200,  50)
COIN_COL        = (255, 215,   0)
CHEST_COL       = (160, 120,  40)

# UI
UI_BG           = (20,  18,  35, 200)   # semi-transparent (used with Surface alpha)
UI_BORDER       = (80,  70, 120)
UI_TEXT         = (210, 200, 230)
UI_HIGHLIGHT    = (120, 200, 255)
MINIMAP_WALL    = (60,  55,  80)
MINIMAP_FLOOR   = (110, 100, 140)
MINIMAP_PLAYER  = (100, 200, 255)
MINIMAP_EXIT    = (80,  255, 120)
MINIMAP_BG      = (10,   8,  18, 180)

# ── Tile type IDs ────────────────────────────────────────────────────────────
T_EMPTY     = 0
T_WALL      = 1
T_FLOOR     = 2
T_CORRIDOR  = 3
T_DOOR      = 4
T_STAIRS    = 5          # exit / descend point

# ── Player stats ─────────────────────────────────────────────────────────────
PLAYER_SPEED    = 3      # tiles per second (movement applied in pixels)
PLAYER_HP       = 100
PLAYER_DAMAGE   = 20
PLAYER_RANGE    = 80     # melee reach in pixels

# ── Enemy stats (per type) ───────────────────────────────────────────────────
ENEMY_STATS = {
    "chaser":  {"hp": 30, "speed": 1.5, "damage": 8,  "sight": 200},
    "patrol":  {"hp": 20, "speed": 1.0, "damage": 6,  "sight": 160},
    "shooter": {"hp": 15, "speed": 0.8, "damage": 12, "sight": 280},
}

# ── Loot ─────────────────────────────────────────────────────────────────────
LOOT_DROP_CHANCE    = 0.45   # probability an enemy drops loot
CHEST_LOOT_COUNT    = 3      # items per chest

# ── Difficulty scaling (per floor) ───────────────────────────────────────────
FLOOR_ENEMY_MULT    = 1.20   # +20 % enemies each floor
FLOOR_HP_MULT       = 1.15   # enemies get +15 % hp
FLOOR_SPEED_MULT    = 1.05   # enemies get +5 % speed

# ── Fog of war ───────────────────────────────────────────────────────────────
FOG_RADIUS      = 6      # tiles visible around player

# ── Particles ────────────────────────────────────────────────────────────────
PARTICLE_LIFE   = 30     # frames

# ── Paths ────────────────────────────────────────────────────────────────────
SAVE_FILE   = "best_floor.txt"
