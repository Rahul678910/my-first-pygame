"""
entities.py  –  Phase 2
Player, Enemy (Chaser / Patroller / Shooter), and Projectile classes.

Public API
----------
spawn_enemies(dungeon) -> list[Enemy]
    Instantiate and return all enemies from dungeon.enemy_spawns.
"""

import math
import random

import pygame

from settings import (
    TILE, COLS, ROWS,
    PLAYER_COL, PLAYER_HP, PLAYER_SPEED, PLAYER_DAMAGE, PLAYER_RANGE,
    ENEMY_COL, ENEMY_STATS,
    HEALTH_BAR_FG, HEALTH_BAR_BG,
    FLOOR_HP_MULT, FLOOR_SPEED_MULT,
    T_FLOOR, T_CORRIDOR, T_DOOR, T_STAIRS,
)
from dungeon import is_walkable

# Pixel radius used for circle-vs-wall collision checks
_ENTITY_RADIUS = TILE // 2 - 4


# ─────────────────────────────────────────────────────────────────────────────
# Internal movement helper
# ─────────────────────────────────────────────────────────────────────────────

def _can_move(grid, px: float, py: float, radius: int = 10) -> bool:
    """
    Return True if a circle of *radius* pixels centred at (px, py)
    does not overlap any non-walkable tile.
    Tests the 4 cardinal compass points around the circle.
    """
    for dx, dy in [(-radius, 0), (radius, 0), (0, -radius), (0, radius)]:
        c = int(px + dx) // TILE
        r = int(py + dy) // TILE
        if not is_walkable(grid, c, r):
            return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Projectile
# ─────────────────────────────────────────────────────────────────────────────

class Projectile:
    """A small fast-moving projectile fired by the player or a Shooter enemy."""

    SPEED  = 5.0
    RADIUS = 4

    def __init__(
        self,
        x: float, y: float,
        dx: float, dy: float,
        damage: int, owner: str, colour: tuple,
    ):
        self.x      = x
        self.y      = y
        self.dx     = dx        # unit direction vector
        self.dy     = dy
        self.damage = damage
        self.owner  = owner     # "player" or "enemy"
        self.colour = colour
        self.alive  = True

    def update(self, grid) -> None:
        """Advance the projectile; deactivate on wall contact."""
        self.x += self.dx * self.SPEED
        self.y += self.dy * self.SPEED
        c = int(self.x) // TILE
        r = int(self.y) // TILE
        if not is_walkable(grid, c, r):
            self.alive = False

    def draw(self, surface: pygame.Surface, camera) -> None:
        if not self.alive:
            return
        sx, sy = camera.apply(int(self.x), int(self.y))
        # Soft glow halo
        glow_r = self.RADIUS * 3
        glow   = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.colour, 70), (glow_r, glow_r), glow_r)
        surface.blit(glow, (sx - glow_r, sy - glow_r))
        pygame.draw.circle(surface, self.colour, (sx, sy), self.RADIUS)

    def get_rect(self) -> pygame.Rect:
        r = self.RADIUS
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)


# ─────────────────────────────────────────────────────────────────────────────
# Base Entity
# ─────────────────────────────────────────────────────────────────────────────

class Entity:
    """Shared base class for Player and Enemy."""

    def __init__(
        self,
        x: float, y: float,
        hp: int, speed: float,
        colour: tuple,
        radius: int = _ENTITY_RADIUS,
    ):
        self.x      = x
        self.y      = y
        self.hp     = hp
        self.max_hp = hp
        self.speed  = speed
        self.colour = colour
        self.radius = radius
        self.alive  = True

    # ── Damage ───────────────────────────────────────────────────────────────
    def take_damage(self, amount: int) -> None:
        """Subtract *amount* HP; mark dead when HP reaches zero."""
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.alive = False

    # ── Geometry ─────────────────────────────────────────────────────────────
    def get_rect(self) -> pygame.Rect:
        r = self.radius
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

    def dist_to(self, other: "Entity") -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    # ── HUD element ──────────────────────────────────────────────────────────
    def draw_health_bar(
        self,
        surface: pygame.Surface,
        camera,
        w: int = 30, h: int = 5, y_off: int = -18,
    ) -> None:
        """Render a thin HP bar above the entity."""
        sx, sy = camera.apply(int(self.x), int(self.y))
        bx = sx - w // 2
        by = sy + y_off
        pct = self.hp / self.max_hp
        pygame.draw.rect(surface, HEALTH_BAR_BG, (bx, by, w, h))
        pygame.draw.rect(surface, HEALTH_BAR_FG, (bx, by, int(w * pct), h))
        pygame.draw.rect(surface, (180, 180, 180), (bx, by, w, h), 1)


# ─────────────────────────────────────────────────────────────────────────────
# Player
# ─────────────────────────────────────────────────────────────────────────────

class Player(Entity):
    """Player character — keyboard-controlled, melee + ranged attacks."""

    MELEE_COOLDOWN  = 400   # ms between melee swings
    RANGED_COOLDOWN = 600   # ms between shots

    def __init__(self, tile_col: int, tile_row: int):
        px = tile_col * TILE + TILE // 2
        py = tile_row * TILE + TILE // 2
        super().__init__(px, py, PLAYER_HP, PLAYER_SPEED, PLAYER_COL)
        self.facing        = (1.0, 0.0)   # normalised direction vector
        self._melee_timer  = 0
        self._ranged_timer = 0
        self.hit_flash     = 0            # frames of white flash when hurt

    def handle_input(
        self,
        keys: pygame.key.ScancodeWrapper,
        dungeon,
        dt_ms: int,
    ) -> None:
        """Move the player and tick attack cooldowns."""
        dx = dy = 0.0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1

        if dx or dy:
            length  = math.hypot(dx, dy)
            dx /= length
            dy /= length
            self.facing = (dx, dy)

        # Separate-axis collision so the player slides along walls
        nx, ny = self.x + dx * self.speed, self.y + dy * self.speed
        if _can_move(dungeon.grid, nx, self.y):
            self.x = nx
        if _can_move(dungeon.grid, self.x, ny):
            self.y = ny

        self._melee_timer  = max(0, self._melee_timer  - dt_ms)
        self._ranged_timer = max(0, self._ranged_timer - dt_ms)
        self.hit_flash     = max(0, self.hit_flash - 1)

    def try_melee(self, enemies: list) -> bool:
        """
        Swing melee weapon.  Hits enemies within PLAYER_RANGE pixels
        that are roughly in the facing direction (dot-product ≥ 0.25).
        Returns True if the attack went off (cooldown was ready).
        """
        if self._melee_timer > 0:
            return False
        self._melee_timer = self.MELEE_COOLDOWN
        for enemy in enemies:
            if not enemy.alive:
                continue
            d = self.dist_to(enemy)
            if d <= PLAYER_RANGE:
                ex = (enemy.x - self.x) / max(d, 1)
                ey = (enemy.y - self.y) / max(d, 1)
                if ex * self.facing[0] + ey * self.facing[1] > 0.25:
                    enemy.take_damage(PLAYER_DAMAGE)
                    enemy.hit_flash = 6
        return True

    def try_ranged(self) -> "Projectile | None":
        """
        Fire a projectile in the current facing direction.
        Returns a Projectile instance or None if still on cooldown.
        """
        if self._ranged_timer > 0:
            return None
        self._ranged_timer = self.RANGED_COOLDOWN
        return Projectile(
            self.x, self.y,
            self.facing[0], self.facing[1],
            damage=15, owner="player",
            colour=(100, 200, 255),
        )

    def take_damage(self, amount: int) -> None:
        super().take_damage(amount)
        self.hit_flash = 10

    def draw(self, surface: pygame.Surface, camera) -> None:
        sx, sy = camera.apply(int(self.x), int(self.y))
        col = (255, 255, 255) if self.hit_flash > 0 else self.colour
        pygame.draw.circle(surface, col,          (sx, sy), self.radius)
        pygame.draw.circle(surface, (200, 240, 255), (sx, sy), self.radius, 2)
        # Facing indicator dot
        fx = sx + int(self.facing[0] * (self.radius + 5))
        fy = sy + int(self.facing[1] * (self.radius + 5))
        pygame.draw.circle(surface, (255, 255, 255), (fx, fy), 3)
        self.draw_health_bar(surface, camera, w=44, h=6, y_off=-24)


# ─────────────────────────────────────────────────────────────────────────────
# Enemy base
# ─────────────────────────────────────────────────────────────────────────────

class Enemy(Entity):
    """Base enemy — provides scaled stats, drawing, and movement helpers."""

    def __init__(self, tile_col: int, tile_row: int, etype: str, floor: int = 1):
        stats = ENEMY_STATS[etype]
        hp    = int(stats["hp"]    * FLOOR_HP_MULT    ** (floor - 1))
        speed = stats["speed"] * FLOOR_SPEED_MULT ** (floor - 1)
        px = tile_col * TILE + TILE // 2
        py = tile_row * TILE + TILE // 2
        super().__init__(px, py, hp, speed, ENEMY_COL[etype])
        self.etype          = etype
        self.damage         = stats["damage"]
        self.sight          = stats["sight"]
        self.state          = "idle"
        self.hit_flash      = 0
        self._attack_timer  = 0

    # ── Shared movement ───────────────────────────────────────────────────────
    def _move_toward(self, tx: float, ty: float, grid) -> None:
        """Step toward target pixel position with wall collision."""
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist < 2:
            return
        dx /= dist
        dy /= dist
        nx, ny = self.x + dx * self.speed, self.y + dy * self.speed
        if _can_move(grid, nx, self.y, radius=8):
            self.x = nx
        if _can_move(grid, self.x, ny, radius=8):
            self.y = ny

    # ── Rendering ─────────────────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface, camera) -> None:
        sx, sy = camera.apply(int(self.x), int(self.y))
        col = (255, 255, 255) if self.hit_flash > 0 else self.colour
        self.hit_flash = max(0, self.hit_flash - 1)
        r = self.radius
        pygame.draw.rect(surface, col,         (sx - r, sy - r, r * 2, r * 2))
        pygame.draw.rect(surface, (255,255,255),(sx - r, sy - r, r * 2, r * 2), 1)
        self.draw_health_bar(surface, camera)


# ─────────────────────────────────────────────────────────────────────────────
# Chaser — sprints straight at the player
# ─────────────────────────────────────────────────────────────────────────────

class Chaser(Enemy):
    """Activates when the player enters sight range; charges and melee-hits."""

    ATTACK_RANGE    = TILE * 1.2
    ATTACK_COOLDOWN = 700    # ms

    def __init__(self, tile_col: int, tile_row: int, floor: int = 1):
        super().__init__(tile_col, tile_row, "chaser", floor)

    def update(
        self, player: Player, dungeon, projectiles: list, dt_ms: int
    ) -> None:
        self._attack_timer = max(0, self._attack_timer - dt_ms)
        d = self.dist_to(player)
        if d <= self.sight:
            self.state = "chase"
        if self.state == "chase":
            if d > self.ATTACK_RANGE:
                self._move_toward(player.x, player.y, dungeon.grid)
            elif self._attack_timer == 0:
                player.take_damage(self.damage)
                self._attack_timer = self.ATTACK_COOLDOWN


# ─────────────────────────────────────────────────────────────────────────────
# Patroller — wanders waypoints, chases on sight
# ─────────────────────────────────────────────────────────────────────────────

class Patroller(Enemy):
    """Loops through random waypoints in its spawn room; chases when player spotted."""

    ATTACK_RANGE    = TILE * 1.3
    ATTACK_COOLDOWN = 900

    def __init__(self, tile_col: int, tile_row: int, room, floor: int = 1):
        super().__init__(tile_col, tile_row, "patrol", floor)
        rng   = random.Random()
        inner = room.inner_tiles
        n     = min(4, max(1, len(inner)))
        self._waypoints = [
            (c * TILE + TILE // 2, r * TILE + TILE // 2)
            for c, r in rng.sample(inner, n)
        ]
        self._wp_idx = 0

    def update(
        self, player: Player, dungeon, projectiles: list, dt_ms: int
    ) -> None:
        self._attack_timer = max(0, self._attack_timer - dt_ms)
        d = self.dist_to(player)
        if d <= self.sight:
            self.state = "chase"

        if self.state == "chase":
            if d > self.ATTACK_RANGE:
                self._move_toward(player.x, player.y, dungeon.grid)
            elif self._attack_timer == 0:
                player.take_damage(self.damage)
                self._attack_timer = self.ATTACK_COOLDOWN
        else:
            if self._waypoints:
                tx, ty = self._waypoints[self._wp_idx]
                self._move_toward(tx, ty, dungeon.grid)
                if math.hypot(self.x - tx, self.y - ty) < TILE * 0.5:
                    self._wp_idx = (self._wp_idx + 1) % len(self._waypoints)


# ─────────────────────────────────────────────────────────────────────────────
# Shooter — keeps its distance, fires projectiles
# ─────────────────────────────────────────────────────────────────────────────

class Shooter(Enemy):
    """Maintains a preferred standoff distance and fires homing-free projectiles."""

    PREFERRED_DIST = TILE * 5
    SHOOT_COOLDOWN = 1200

    def __init__(self, tile_col: int, tile_row: int, floor: int = 1):
        super().__init__(tile_col, tile_row, "shooter", floor)

    def update(
        self, player: Player, dungeon, projectiles: list, dt_ms: int
    ) -> None:
        self._attack_timer = max(0, self._attack_timer - dt_ms)
        d = self.dist_to(player)
        if d <= self.sight:
            self.state = "chase"
        if self.state != "chase":
            return

        # Maintain preferred standoff distance
        if d < self.PREFERRED_DIST * 0.7:
            dx = (self.x - player.x) / max(d, 1)
            dy = (self.y - player.y) / max(d, 1)
            nx, ny = self.x + dx * self.speed, self.y + dy * self.speed
            if _can_move(dungeon.grid, nx, self.y, radius=8): self.x = nx
            if _can_move(dungeon.grid, self.x, ny, radius=8): self.y = ny
        elif d > self.PREFERRED_DIST * 1.3:
            self._move_toward(player.x, player.y, dungeon.grid)

        # Fire when ready
        if self._attack_timer == 0:
            dx = player.x - self.x
            dy = player.y - self.y
            dist = math.hypot(dx, dy) or 1
            projectiles.append(Projectile(
                self.x, self.y,
                dx / dist, dy / dist,
                damage=self.damage, owner="enemy",
                colour=(200, 80, 255),
            ))
            self._attack_timer = self.SHOOT_COOLDOWN


# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────

def spawn_enemies(dungeon) -> list:
    """
    Instantiate Enemy objects for every spawn point in *dungeon*.

    Enemy types are chosen randomly with weighted probabilities:
      50 % Chaser, 30 % Patroller, 20 % Shooter.

    Parameters
    ----------
    dungeon : Dungeon
        A fully-generated dungeon (enemy_spawns populated).

    Returns
    -------
    list[Enemy]
    """
    rng     = random.Random()
    types   = ["chaser", "patrol", "shooter"]
    weights = [0.50,     0.30,     0.20]

    # Build tile → room lookup so Patrollers know their room's waypoints
    room_map: dict = {}
    for room in dungeon.rooms:
        for tc, tr in room.inner_tiles:
            room_map[(tc, tr)] = room

    enemies = []
    for tc, tr in dungeon.enemy_spawns:
        etype = rng.choices(types, weights)[0]
        if etype == "chaser":
            enemies.append(Chaser(tc, tr, floor=dungeon.floor))
        elif etype == "patrol":
            room = room_map.get((tc, tr), dungeon.rooms[0])
            enemies.append(Patroller(tc, tr, room, floor=dungeon.floor))
        else:
            enemies.append(Shooter(tc, tr, floor=dungeon.floor))
    return enemies
