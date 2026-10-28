"""
main.py  –  Phase 1
Bootstraps Pygame, renders the dungeon grid with a free-roaming camera,
and shows a basic HUD (floor number, tile-type legend).

Controls (Phase 1)
------------------
WASD / Arrow keys  – scroll camera
R                  – regenerate dungeon
ESC                – quit
"""

import sys
import pygame

from settings import (
    TITLE, SCREEN_W, SCREEN_H, FPS, TILE,
    COLS, ROWS,
    DARK_BG, WALL_DARK, WALL_LIT, FLOOR_DARK, FLOOR_LIT,
    CORRIDOR_DARK, CORRIDOR_LIT,
    COIN_COL, PLAYER_COL, UI_TEXT,
    T_EMPTY, T_WALL, T_FLOOR, T_CORRIDOR, T_DOOR, T_STAIRS,
)
from dungeon import generate_dungeon, Dungeon


# ─────────────────────────────────────────────────────────────────────────────
# Colour map: tile-type → (dark_colour, lit_colour)
# ─────────────────────────────────────────────────────────────────────────────
TILE_COLOURS = {
    T_EMPTY:    (DARK_BG,       DARK_BG),
    T_WALL:     (WALL_DARK,     WALL_LIT),
    T_FLOOR:    (FLOOR_DARK,    FLOOR_LIT),
    T_CORRIDOR: (CORRIDOR_DARK, CORRIDOR_LIT),
    T_DOOR:     ((60, 40, 20),  (140, 100, 50)),
    T_STAIRS:   ((20, 80, 40),  ( 60, 200, 100)),
}


# ─────────────────────────────────────────────────────────────────────────────
# Camera
# ─────────────────────────────────────────────────────────────────────────────

class Camera:
    """
    Tracks an (offset_x, offset_y) in pixels so the viewport stays centred
    on a world position.  In Phase 1 it is driven by keyboard scrolling;
    from Phase 2 onward it follows the player.
    """

    def __init__(self, world_w: int, world_h: int):
        self.x = 0
        self.y = 0
        self.world_w = world_w
        self.world_h = world_h

    def clamp(self) -> None:
        """Keep the camera inside dungeon bounds."""
        max_x = max(0, self.world_w  - SCREEN_W)
        max_y = max(0, self.world_h - SCREEN_H)
        self.x = max(0, min(self.x, max_x))
        self.y = max(0, min(self.y, max_y))

    def centre_on(self, tile_col: int, tile_row: int) -> None:
        """Snap the camera so that *tile* appears at the screen centre."""
        self.x = tile_col * TILE - SCREEN_W // 2 + TILE // 2
        self.y = tile_row * TILE - SCREEN_H // 2 + TILE // 2
        self.clamp()

    def apply(self, world_x: int, world_y: int):
        """Convert world-pixel coords to screen-pixel coords."""
        return world_x - self.x, world_y - self.y

    def visible_tile_range(self):
        """
        Return (col_start, row_start, col_end, row_end) of tiles
        currently visible on screen (with one tile of margin).
        """
        col_start = max(0,    self.x // TILE - 1)
        row_start = max(0,    self.y // TILE - 1)
        col_end   = min(COLS, col_start + SCREEN_W // TILE + 3)
        row_end   = min(ROWS, row_start + SCREEN_H // TILE + 3)
        return col_start, row_start, col_end, row_end


# ─────────────────────────────────────────────────────────────────────────────
# Rendering helpers
# ─────────────────────────────────────────────────────────────────────────────

def _draw_tile(
    surface: pygame.Surface,
    tile_type: int,
    screen_x: int,
    screen_y: int,
    lit: bool,
) -> None:
    """Draw one tile rectangle onto *surface* at screen coordinates."""
    dark_col, lit_col = TILE_COLOURS.get(tile_type, (DARK_BG, DARK_BG))
    colour = lit_col if lit else dark_col
    pygame.draw.rect(surface, colour, (screen_x, screen_y, TILE, TILE))

    # Subtle grid lines on lit floor/corridor tiles
    if lit and tile_type in (T_FLOOR, T_CORRIDOR):
        pygame.draw.rect(
            surface, (colour[0]-8, colour[1]-8, colour[2]-8),
            (screen_x, screen_y, TILE, TILE), 1,
        )


def _draw_dungeon(
    surface: pygame.Surface,
    dungeon: Dungeon,
    camera: Camera,
    lit_tiles: set,
) -> None:
    """
    Render only the tiles visible through the camera viewport.
    *lit_tiles* is a set of (col, row) tuples that are currently illuminated.
    """
    c0, r0, c1, r1 = camera.visible_tile_range()

    for row in range(r0, r1):
        for col in range(c0, c1):
            tile_type = dungeon.grid[row][col]
            if tile_type == T_EMPTY:
                continue                      # skip solid rock for speed

            sx, sy = camera.apply(col * TILE, row * TILE)
            lit    = (col, row) in lit_tiles
            _draw_tile(surface, tile_type, sx, sy, lit)

    # Stairs glow
    ec, er = dungeon.exit_pos
    if (ec, er) in lit_tiles:
        sx, sy = camera.apply(ec * TILE, er * TILE)
        # pulsing glow ring
        pulse = abs(pygame.time.get_ticks() % 1000 - 500) / 500   # 0→1→0
        glow_r = int(TILE * 0.7 + pulse * TILE * 0.3)
        glow_surf = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (60, 255, 120, 60),
                           (glow_r, glow_r), glow_r)
        surface.blit(glow_surf, (sx + TILE//2 - glow_r, sy + TILE//2 - glow_r))


def _draw_player_placeholder(
    surface: pygame.Surface,
    camera: Camera,
    col: int, row: int,
) -> None:
    """Phase-1 stand-in for the player sprite (filled circle)."""
    sx, sy = camera.apply(col * TILE + TILE // 2, row * TILE + TILE // 2)
    pygame.draw.circle(surface, PLAYER_COL, (sx, sy), TILE // 2 - 2)
    pygame.draw.circle(surface, (200, 240, 255), (sx, sy), TILE // 2 - 2, 2)


def _compute_lit_tiles(dungeon: Dungeon, player_col: int, player_row: int,
                       radius: int = 7) -> set:
    """
    Simple square-radius visibility (real raycasting comes in Phase 3 with fog of war).
    Returns a set of (col, row) tuples that are considered lit.
    """
    lit = set()
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            if dr*dr + dc*dc <= radius*radius:
                c, r = player_col + dc, player_row + dr
                if 0 <= c < COLS and 0 <= r < ROWS:
                    lit.add((c, r))
    return lit


# ─────────────────────────────────────────────────────────────────────────────
# HUD
# ─────────────────────────────────────────────────────────────────────────────

def _draw_hud(surface: pygame.Surface, font: pygame.font.Font,
              dungeon: Dungeon, player_col: int, player_row: int) -> None:
    """Render floor number, player tile position, and a quick legend."""
    lines = [
        f"Floor : {dungeon.floor}",
        f"Pos   : ({player_col}, {player_row})",
        f"Rooms : {len(dungeon.rooms)}",
        "",
        "[R]  Regenerate",
        "[ESC] Quit",
    ]
    pad = 8
    x, y = SCREEN_W - 180, pad
    for line in lines:
        txt = font.render(line, True, UI_TEXT)
        surface.blit(txt, (x, y))
        y += 18

    # Legend strip at bottom-left
    legend = [
        (T_FLOOR,   FLOOR_LIT,     "Floor"),
        (T_WALL,    WALL_LIT,      "Wall"),
        (T_CORRIDOR,CORRIDOR_LIT,  "Corridor"),
        (T_DOOR,    (140,100,50),  "Door"),
        (T_STAIRS,  (60,200,100),  "Stairs"),
    ]
    lx, ly = 8, SCREEN_H - 8 - len(legend) * 20
    for _, col, label in legend:
        pygame.draw.rect(surface, col, (lx, ly, 14, 14))
        surface.blit(font.render(label, True, UI_TEXT), (lx + 18, ly))
        ly += 20


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Entry point — initialise Pygame and run the Phase-1 game loop."""
    pygame.init()
    screen  = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE + "  –  Phase 1")
    clock   = pygame.time.Clock()
    font    = pygame.font.SysFont("consolas", 14)

    # ── Generate first dungeon ────────────────────────────────────────────────
    floor   = 1
    dungeon = generate_dungeon(floor)
    camera  = Camera(COLS * TILE, ROWS * TILE)

    # Player tile position (moves freely in Phase 1 via teleport-on-press)
    pc, pr  = dungeon.player_start   # (col, row)
    camera.centre_on(pc, pr)

    # ── Event / render loop ───────────────────────────────────────────────────
    scroll_speed = 4   # pixels per frame while key held

    while True:
        dt = clock.tick(FPS)

        # ── Events ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    floor   += 1
                    dungeon  = generate_dungeon(floor)
                    pc, pr   = dungeon.player_start
                    camera.centre_on(pc, pr)

        # ── Held-key camera scroll ────────────────────────────────────────────
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
            camera.x -= scroll_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            camera.x += scroll_speed
        if keys[pygame.K_UP]    or keys[pygame.K_w]:
            camera.y -= scroll_speed
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]:
            camera.y += scroll_speed
        camera.clamp()

        # ── Compute visibility ────────────────────────────────────────────────
        lit_tiles = _compute_lit_tiles(dungeon, pc, pr, radius=7)

        # ── Draw ──────────────────────────────────────────────────────────────
        screen.fill(DARK_BG)
        _draw_dungeon(screen, dungeon, camera, lit_tiles)
        _draw_player_placeholder(screen, camera, pc, pr)
        _draw_hud(screen, font, dungeon, pc, pr)
        pygame.display.flip()


if __name__ == "__main__":
    main()
