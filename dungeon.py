"""
dungeon.py
Procedural dungeon generation: random rooms, L-shaped corridors, door/stair placement.

Public API
----------
generate_dungeon(floor: int) -> Dungeon
    Returns a fully-built Dungeon object ready for the rest of the game.
"""

import random
from dataclasses import dataclass, field
from typing import List, Tuple

from settings import (
    COLS, ROWS,
    ROOM_MIN_W, ROOM_MAX_W, ROOM_MIN_H, ROOM_MAX_H,
    MIN_ROOMS, MAX_ROOMS,
    T_EMPTY, T_WALL, T_FLOOR, T_CORRIDOR, T_DOOR, T_STAIRS,
)


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Room:
    """Axis-aligned rectangular room in tile coordinates."""
    x: int   # left column
    y: int   # top row
    w: int   # width  in tiles
    h: int   # height in tiles

    # ── derived helpers ───────────────────────────────────────────────────────
    @property
    def cx(self) -> int:
        """Tile column of the room's centre."""
        return self.x + self.w // 2

    @property
    def cy(self) -> int:
        """Tile row of the room's centre."""
        return self.y + self.h // 2

    @property
    def inner_tiles(self) -> List[Tuple[int, int]]:
        """All (col, row) floor tiles inside this room (excluding walls)."""
        return [
            (c, r)
            for c in range(self.x + 1, self.x + self.w - 1)
            for r in range(self.y + 1, self.y + self.h - 1)
        ]

    def intersects(self, other: "Room", margin: int = 1) -> bool:
        """Return True if this room overlaps *other* (with an optional margin gap)."""
        return (
            self.x - margin < other.x + other.w and
            self.x + self.w + margin > other.x and
            self.y - margin < other.y + other.h and
            self.y + self.h + margin > other.y
        )


@dataclass
class Dungeon:
    """Container for all dungeon data passed between modules."""
    grid: List[List[int]]          # grid[row][col] tile-type ID
    rooms: List[Room]
    player_start: Tuple[int, int]  # (col, row) tile position
    exit_pos:     Tuple[int, int]  # stairs tile (col, row)
    floor: int

    # Filled by entities.py later:
    enemy_spawns: List[Tuple[int, int]] = field(default_factory=list)
    chest_spawns: List[Tuple[int, int]] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _empty_grid() -> List[List[int]]:
    """Return a ROWS × COLS grid filled with T_EMPTY (solid rock)."""
    return [[T_EMPTY] * COLS for _ in range(ROWS)]


def _carve_room(grid: List[List[int]], room: Room) -> None:
    """Stamp a room onto the grid: border = T_WALL, interior = T_FLOOR."""
    for r in range(room.y, room.y + room.h):
        for c in range(room.x, room.x + room.w):
            if r == room.y or r == room.y + room.h - 1:
                grid[r][c] = T_WALL
            elif c == room.x or c == room.x + room.w - 1:
                grid[r][c] = T_WALL
            else:
                grid[r][c] = T_FLOOR


def _carve_corridor(
    grid: List[List[int]],
    ax: int, ay: int,
    bx: int, by: int,
    rng: random.Random,
) -> None:
    """
    Carve an L-shaped corridor between tile (ax, ay) and (bx, by).
    The elbow direction is chosen randomly for variety.
    Wall cells adjacent to corridor become T_WALL; open cells stay T_FLOOR.
    """
    # Choose elbow
    if rng.random() < 0.5:
        # horizontal then vertical
        hx1, hy1, hx2, hy2 = min(ax, bx), ay, max(ax, bx), ay
        vx,  vy1, vy2       = bx, min(ay, by), max(ay, by)
    else:
        # vertical then horizontal
        vx,  vy1, vy2       = ax, min(ay, by), max(ay, by)
        hx1, hy1, hx2, hy2 = min(ax, bx), by, max(ax, bx), by

    # Carve horizontal segment
    for c in range(hx1, hx2 + 1):
        _place_corridor_tile(grid, c, hy1)

    # Carve vertical segment
    for r in range(vy1, vy2 + 1):
        _place_corridor_tile(grid, vx, r)


def _place_corridor_tile(grid: List[List[int]], c: int, r: int) -> None:
    """Set a single tile to corridor (or floor if already floor)."""
    if 0 <= r < ROWS and 0 <= c < COLS:
        if grid[r][c] == T_EMPTY:
            grid[r][c] = T_CORRIDOR
        # T_FLOOR / T_WALL already there → leave them (room takes priority)


def _add_walls_around_corridors(grid: List[List[int]]) -> None:
    """
    For every corridor tile that borders an T_EMPTY cell, turn that
    empty cell into T_WALL so corridors have visible edges.
    """
    neighbours = [(-1, 0), (1, 0), (0, -1), (0, 1),
                  (-1, -1), (-1, 1), (1, -1), (1, 1)]
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] == T_CORRIDOR:
                for dr, dc in neighbours:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS:
                        if grid[nr][nc] == T_EMPTY:
                            grid[nr][nc] = T_WALL


def _place_doors(
    grid: List[List[int]],
    rooms: List[Room],
    rng: random.Random,
) -> None:
    """
    Place T_DOOR tiles at corridor-to-room junctions.
    Finds corridor tiles adjacent to a room wall on exactly 2 sides.
    """
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] != T_CORRIDOR:
                continue
            adjacent_walls = sum(
                1 for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                if 0 <= r+dr < ROWS and 0 <= c+dc < COLS
                and grid[r+dr][c+dc] == T_WALL
            )
            if adjacent_walls >= 2 and rng.random() < 0.5:
                grid[r][c] = T_DOOR


def _pick_random_floor(room: Room, rng: random.Random) -> Tuple[int, int]:
    """Return a random interior floor tile from a room."""
    tiles = room.inner_tiles
    return rng.choice(tiles)   # (col, row)


def _flood_reachable(
    grid: List[List[int]],
    start: Tuple[int, int],
) -> set:
    """
    BFS from *start* (col, row).
    Returns the set of all (col, row) walkable tiles reachable from start.
    Walkable = T_FLOOR | T_CORRIDOR | T_DOOR | T_STAIRS.
    """
    walkable = {T_FLOOR, T_CORRIDOR, T_DOOR, T_STAIRS}
    visited  = set()
    queue    = [start]
    visited.add(start)
    while queue:
        c, r   = queue.pop()
        for dc, dr in [(1,0),(-1,0),(0,1),(0,-1)]:
            nc, nr = c+dc, r+dr
            if (nc, nr) not in visited and 0 <= nr < ROWS and 0 <= nc < COLS:
                if grid[nr][nc] in walkable:
                    visited.add((nc, nr))
                    queue.append((nc, nr))
    return visited


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_dungeon(floor: int = 1, seed: int = None) -> Dungeon:
    """
    Build and return a procedurally generated Dungeon.

    Parameters
    ----------
    floor : int
        Current floor number (1-indexed). More rooms on deeper floors.
    seed  : int | None
        Optional RNG seed for reproducible generation (tests, debug).

    Returns
    -------
    Dungeon
        Fully initialised dungeon with grid, rooms, player_start, exit_pos.
    """
    rng = random.Random(seed)

    # Scale room count with depth
    max_rooms = min(MAX_ROOMS, MIN_ROOMS + floor - 1)

    grid  : List[List[int]] = _empty_grid()
    rooms : List[Room]      = []

    # ── 1. Place rooms ────────────────────────────────────────────────────────
    for _ in range(200):   # attempt limit
        if len(rooms) >= max_rooms:
            break

        w = rng.randint(ROOM_MIN_W, ROOM_MAX_W)
        h = rng.randint(ROOM_MIN_H, ROOM_MAX_H)
        x = rng.randint(1, COLS - w - 1)
        y = rng.randint(1, ROWS - h - 1)
        new_room = Room(x, y, w, h)

        if any(new_room.intersects(existing) for existing in rooms):
            continue

        _carve_room(grid, new_room)
        rooms.append(new_room)

    if len(rooms) < 2:
        # Fallback: guaranteed two rooms so the game is always playable
        rooms = [Room(2, 2, 8, 6), Room(COLS-12, ROWS-10, 8, 6)]
        for room in rooms:
            _carve_room(grid, room)

    # ── 2. Connect rooms with corridors (simple chain + a few shortcuts) ──────
    rng.shuffle(rooms)
    for i in range(len(rooms) - 1):
        a, b = rooms[i], rooms[i + 1]
        _carve_corridor(grid, a.cx, a.cy, b.cx, b.cy, rng)

    # A couple of extra connections for loops / variety
    extra = max(1, len(rooms) // 3)
    for _ in range(extra):
        a = rng.choice(rooms)
        b = rng.choice(rooms)
        if a is not b:
            _carve_corridor(grid, a.cx, a.cy, b.cx, b.cy, rng)

    # ── 3. Add wall borders around corridors, then doors ─────────────────────
    _add_walls_around_corridors(grid)
    _place_doors(grid, rooms, rng)

    # ── 4. Player start (first room) and exit stairs (last room) ─────────────
    player_start = _pick_random_floor(rooms[0],  rng)
    exit_tile    = _pick_random_floor(rooms[-1], rng)
    grid[exit_tile[1]][exit_tile[0]] = T_STAIRS

    # ── 5. Spawn hints for entities (filled in entities.py) ──────────────────
    enemy_spawns: List[Tuple[int, int]] = []
    chest_spawns: List[Tuple[int, int]] = []

    for room in rooms[1:]:          # skip the starting room
        tiles = room.inner_tiles
        if not tiles:
            continue
        # 1–3 enemies per room
        n_enemies = rng.randint(1, min(3, len(tiles)))
        chosen    = rng.sample(tiles, n_enemies)
        enemy_spawns.extend(chosen)

        # One chest per room with 40 % chance
        if rng.random() < 0.40:
            remaining = [t for t in tiles if t not in chosen]
            if remaining:
                chest_spawns.append(rng.choice(remaining))

    return Dungeon(
        grid         = grid,
        rooms        = rooms,
        player_start = player_start,
        exit_pos     = exit_tile,
        floor        = floor,
        enemy_spawns = enemy_spawns,
        chest_spawns = chest_spawns,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Utility (used by minimap, lighting, etc.)
# ─────────────────────────────────────────────────────────────────────────────

def is_walkable(grid: List[List[int]], col: int, row: int) -> bool:
    """Return True if the tile at (col, row) can be walked on."""
    if not (0 <= row < ROWS and 0 <= col < COLS):
        return False
    return grid[row][col] in {T_FLOOR, T_CORRIDOR, T_DOOR, T_STAIRS}
