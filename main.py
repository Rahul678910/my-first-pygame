"""
main.py  –  Phase 2
Game loop with player-follow camera, entity updates, attacks, and collisions.

Controls
--------
WASD / Arrow keys  – Move
Space              – Melee attack
F                  – Ranged attack (fires a projectile)
R                  – New dungeon (next floor)
ESC                – Quit
"""

import sys
import pygame

from settings import (
    TITLE, SCREEN_W, SCREEN_H, FPS, TILE,
    COLS, ROWS,
    DARK_BG, WALL_DARK, WALL_LIT, FLOOR_DARK, FLOOR_LIT,
    CORRIDOR_DARK, CORRIDOR_LIT,
    CHEST_COL, PLAYER_COL, UI_TEXT, UI_HIGHLIGHT,
    T_EMPTY, T_WALL, T_FLOOR, T_CORRIDOR, T_DOOR, T_STAIRS,
)
from dungeon import generate_dungeon, Dungeon
from entities import Player, spawn_enemies


# ─────────────────────────────────────────────────────────────────────────────
# Tile colour map
# ─────────────────────────────────────────────────────────────────────────────

TILE_COLOURS = {
    T_EMPTY:    (DARK_BG,          DARK_BG),
    T_WALL:     (WALL_DARK,        WALL_LIT),
    T_FLOOR:    (FLOOR_DARK,       FLOOR_LIT),
    T_CORRIDOR: (CORRIDOR_DARK,    CORRIDOR_LIT),
    T_DOOR:     ((60, 40, 20),     (140, 100, 50)),
    T_STAIRS:   ((20, 80, 40),     (60,  200, 100)),
}


# ─────────────────────────────────────────────────────────────────────────────
# Camera — smooth-follows a pixel target
# ─────────────────────────────────────────────────────────────────────────────

class Camera:
    """Converts world-pixel coordinates to screen coordinates."""

    def __init__(self, world_w: int, world_h: int):
        self.x       = 0.0
        self.y       = 0.0
        self.world_w = world_w
        self.world_h = world_h

    def clamp(self) -> None:
        max_x = max(0, self.world_w  - SCREEN_W)
        max_y = max(0, self.world_h - SCREEN_H)
        self.x = max(0.0, min(self.x, float(max_x)))
        self.y = max(0.0, min(self.y, float(max_y)))

    def centre_on(self, tile_col: int, tile_row: int) -> None:
        """Snap instantly to a tile."""
        self.x = tile_col * TILE - SCREEN_W // 2 + TILE // 2
        self.y = tile_row * TILE - SCREEN_H // 2 + TILE // 2
        self.clamp()

    def follow(self, px: float, py: float) -> None:
        """Lerp toward the player's pixel position each frame."""
        target_x = px - SCREEN_W / 2
        target_y = py - SCREEN_H / 2
        self.x += (target_x - self.x) * 0.12
        self.y += (target_y - self.y) * 0.12
        self.clamp()

    def apply(self, wx: float, wy: float):
        """World-pixel → screen-pixel."""
        return int(wx - self.x), int(wy - self.y)

    def visible_tile_range(self):
        """Tile range currently on screen (with one-tile margin)."""
        c0 = max(0,    int(self.x) // TILE - 1)
        r0 = max(0,    int(self.y) // TILE - 1)
        c1 = min(COLS, c0 + SCREEN_W // TILE + 3)
        r1 = min(ROWS, r0 + SCREEN_H // TILE + 3)
        return c0, r0, c1, r1


# ─────────────────────────────────────────────────────────────────────────────
# Rendering helpers
# ─────────────────────────────────────────────────────────────────────────────

def _draw_tile(
    surface: pygame.Surface,
    tile_type: int,
    sx: int, sy: int,
    lit: bool,
) -> None:
    """Draw one tile at screen position (sx, sy)."""
    dark_col, lit_col = TILE_COLOURS.get(tile_type, (DARK_BG, DARK_BG))
    col = lit_col if lit else dark_col
    pygame.draw.rect(surface, col, (sx, sy, TILE, TILE))
    if lit and tile_type in (T_FLOOR, T_CORRIDOR):
        darker = (max(0,col[0]-8), max(0,col[1]-8), max(0,col[2]-8))
        pygame.draw.rect(surface, darker, (sx, sy, TILE, TILE), 1)


def _draw_dungeon(
    surface: pygame.Surface,
    dungeon: Dungeon,
    camera: Camera,
    lit: set,
) -> None:
    """Render visible dungeon tiles and the animated staircase glow."""
    c0, r0, c1, r1 = camera.visible_tile_range()
    for row in range(r0, r1):
        for col in range(c0, c1):
            tt = dungeon.grid[row][col]
            if tt == T_EMPTY:
                continue
            sx, sy = camera.apply(col * TILE, row * TILE)
            _draw_tile(surface, tt, sx, sy, (col, row) in lit)

    # Glowing stairs pulse
    ec, er = dungeon.exit_pos
    if (ec, er) in lit:
        sx, sy = camera.apply(ec * TILE, er * TILE)
        pulse  = abs(pygame.time.get_ticks() % 1000 - 500) / 500
        gr     = int(TILE * 0.7 + pulse * TILE * 0.3)
        gsurf  = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
        pygame.draw.circle(gsurf, (60, 255, 120, 60), (gr, gr), gr)
        surface.blit(gsurf, (sx + TILE // 2 - gr, sy + TILE // 2 - gr))


def _draw_chests(
    surface: pygame.Surface,
    dungeon: Dungeon,
    camera: Camera,
    lit: set,
) -> None:
    """Render chest sprites as coloured squares on top of floor tiles."""
    for tc, tr in dungeon.chest_spawns:
        if (tc, tr) not in lit:
            continue
        sx, sy = camera.apply(tc * TILE, tr * TILE)
        pad = TILE // 5
        pygame.draw.rect(surface, CHEST_COL,
                         (sx + pad, sy + pad, TILE - pad*2, TILE - pad*2))
        pygame.draw.rect(surface, (200, 170, 80),
                         (sx + pad, sy + pad, TILE - pad*2, TILE - pad*2), 2)
        # Lock symbol
        pygame.draw.circle(surface, (80, 50, 10),
                           (sx + TILE // 2, sy + TILE // 2), 3)


def _compute_lit_tiles(dungeon: Dungeon, pc: int, pr: int, radius: int = 7) -> set:
    """Return the set of (col, row) tiles within *radius* of the player tile."""
    lit = set()
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            if dr*dr + dc*dc <= radius*radius:
                c, r = pc + dc, pr + dr
                if 0 <= c < COLS and 0 <= r < ROWS:
                    lit.add((c, r))
    return lit


# ─────────────────────────────────────────────────────────────────────────────
# Collision detection
# ─────────────────────────────────────────────────────────────────────────────

def _check_projectile_collisions(
    projectiles: list,
    player: Player,
    enemies: list,
) -> None:
    """
    Test each live projectile against the correct target group.
    Player shots → enemies.  Enemy shots → player.
    Kills the projectile on first hit.
    """
    for proj in projectiles:
        if not proj.alive:
            continue
        pr = proj.get_rect()
        if proj.owner == "player":
            for enemy in enemies:
                if enemy.alive and pr.colliderect(enemy.get_rect()):
                    enemy.take_damage(proj.damage)
                    enemy.hit_flash = 6
                    proj.alive = False
                    break
        else:
            if player.alive and pr.colliderect(player.get_rect()):
                player.take_damage(proj.damage)
                proj.alive = False


# ─────────────────────────────────────────────────────────────────────────────
# HUD
# ─────────────────────────────────────────────────────────────────────────────

def _draw_hud(
    surface: pygame.Surface,
    font: pygame.font.Font,
    dungeon: Dungeon,
    player: Player,
    enemies: list,
) -> None:
    """Render floor, enemy count, and a big player health bar at the bottom."""
    alive_count = sum(1 for e in enemies if e.alive)
    lines = [
        f"Floor  : {dungeon.floor}",
        f"Enemies: {alive_count}",
        "",
        "[Space] Melee",
        "[F]     Shoot",
        "[R]     Next floor",
        "[ESC]   Quit",
    ]
    x, y = SCREEN_W - 170, 8
    for line in lines:
        col = UI_HIGHLIGHT if line.startswith("[") else UI_TEXT
        surface.blit(font.render(line, True, col), (x, y))
        y += 18

    # ── Big HP bar at bottom centre ──────────────────────────────────────────
    bw, bh = 200, 14
    bx = (SCREEN_W - bw) // 2
    by = SCREEN_H - bh - 8
    pct = player.hp / player.max_hp
    pygame.draw.rect(surface, (60, 20, 20),    (bx - 1, by - 1, bw + 2, bh + 2))
    pygame.draw.rect(surface, (80,  30,  30),  (bx, by, bw, bh))
    pygame.draw.rect(surface, (80, 220, 80),   (bx, by, int(bw * pct), bh))
    pygame.draw.rect(surface, (150, 150, 150), (bx, by, bw, bh), 1)
    hp_txt = font.render(f"HP  {player.hp} / {player.max_hp}", True, UI_TEXT)
    surface.blit(hp_txt, (bx + bw + 8, by))


def _draw_dead_overlay(surface: pygame.Surface, font: pygame.font.Font) -> None:
    """Semi-transparent 'You Died' overlay (full game-over screen in Phase 4)."""
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))
    big   = pygame.font.SysFont("consolas", 48, bold=True)
    small = pygame.font.SysFont("consolas", 18)
    surface.blit(big.render("YOU DIED", True, (220, 40, 40)),
                 (SCREEN_W // 2 - 130, SCREEN_H // 2 - 50))
    surface.blit(small.render("Press  R  to restart", True, UI_TEXT),
                 (SCREEN_W // 2 - 90, SCREEN_H // 2 + 20))


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def _new_dungeon(floor: int):
    """Generate a dungeon and return (dungeon, player, enemies, projectiles)."""
    dungeon     = generate_dungeon(floor)
    player      = Player(*dungeon.player_start)
    enemies     = spawn_enemies(dungeon)
    projectiles = []
    return dungeon, player, enemies, projectiles


def main() -> None:
    """Entry point — Phase 2 game loop."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE + "  –  Phase 2")
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("consolas", 14)

    floor               = 1
    dungeon, player, enemies, projectiles = _new_dungeon(floor)

    camera = Camera(COLS * TILE, ROWS * TILE)
    camera.centre_on(*dungeon.player_start)

    player_dead = False

    while True:
        dt_ms = clock.tick(FPS)

        # ── Events ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

                # Restart / next floor
                if event.key == pygame.K_r:
                    floor  = 1 if player_dead else floor + 1
                    dungeon, player, enemies, projectiles = _new_dungeon(floor)
                    camera.centre_on(*dungeon.player_start)
                    player_dead = False

                if not player_dead:
                    # Melee  (Space)
                    if event.key == pygame.K_SPACE:
                        player.try_melee(enemies)

                    # Ranged (F)
                    if event.key == pygame.K_f:
                        proj = player.try_ranged()
                        if proj:
                            projectiles.append(proj)

        # ── Update (skip when dead) ───────────────────────────────────────────
        if not player_dead:
            keys = pygame.key.get_pressed()
            player.handle_input(keys, dungeon, dt_ms)

            if not player.alive:
                player_dead = True

            # Update enemies
            for enemy in enemies:
                if enemy.alive:
                    enemy.update(player, dungeon, projectiles, dt_ms)

            # Update projectiles
            for proj in projectiles:
                proj.update(dungeon.grid)

            # Collision: projectiles vs entities
            _check_projectile_collisions(projectiles, player, enemies)

            # Purge dead objects
            projectiles = [p for p in projectiles if p.alive]
            enemies     = [e for e in enemies     if e.alive]

            # Smooth camera follow
            camera.follow(player.x, player.y)

        # ── Lighting (centered on player tile) ───────────────────────────────
        pc = int(player.x) // TILE
        pr = int(player.y) // TILE
        lit = _compute_lit_tiles(dungeon, pc, pr, radius=7)

        # ── Draw ─────────────────────────────────────────────────────────────
        screen.fill(DARK_BG)
        _draw_dungeon(screen, dungeon, camera, lit)
        _draw_chests(screen, dungeon, camera, lit)

        # Draw enemies (only in lit range)
        for enemy in enemies:
            ec = int(enemy.x) // TILE
            er = int(enemy.y) // TILE
            if (ec, er) in lit:
                enemy.draw(screen, camera)

        # Draw projectiles
        for proj in projectiles:
            proj.draw(screen, camera)

        # Draw player
        player.draw(screen, camera)

        # HUD
        _draw_hud(screen, font, dungeon, player, enemies)

        if player_dead:
            _draw_dead_overlay(screen, font)

        pygame.display.flip()


if __name__ == "__main__":
    main()
