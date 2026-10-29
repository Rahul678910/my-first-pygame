# 🗡️ Dungeon Crawler

A procedurally generated dungeon crawler built with **Python + Pygame**.  
No external assets — every sprite, tile, and effect is drawn with Pygame shapes and colours.

![Gameplay GIF placeholder](docs/gameplay.gif)

---

## Features

| Category | Details |
|----------|---------|
| 🗺️ **Procedural generation** | Random rooms connected by L-shaped corridors — new dungeon every run |
| 🧍 **Player** | Top-down WASD movement with wall-sliding, facing indicator, melee swing (arc), ranged projectile |
| 👾 **Enemies** | 3 types — **Chaser** (rushes), **Patroller** (waypoints → chase), **Shooter** (standoff + projectiles) |
| 💎 **Loot** *(Phase 3)* | Potions, weapons, coins from chests and enemy drops |
| 🎒 **Inventory** *(Phase 3)* | Grid UI toggled with `I`; use/equip items |
| 🗺️ **Minimap** *(Phase 3)* | Explored rooms, player position, exit; toggle with `M` |
| 🌫️ **Fog of war** | Circular visibility radius around the player — darkness beyond |
| 💥 **Juice** *(Phase 4)* | Screen shake on hits, particle effects, glowing loot & stairs |
| 🏆 **Best floor** *(Phase 4)* | Saved to `best_floor.txt` across sessions |

---

## Controls

| Key | Action |
|-----|--------|
| `WASD` / `↑↓←→` | Move |
| `Space` | Melee attack (arc in front of player) |
| `F` | Ranged attack — fires a projectile |
| `I` | Toggle inventory *(Phase 3)* |
| `M` | Toggle minimap *(Phase 3)* |
| `R` | Next floor / restart after death |
| `ESC` | Quit |

---

## Install & Run

```bash
# 1. Clone
git clone https://github.com/your-username/dungeon-crawler.git
cd dungeon-crawler

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python main.py
```

Requires **Python 3.9+** and **Pygame 2.1+**.

---

## Project Structure

```
dungeon-crawler/
├── main.py          # Entry point — game loop, camera (smooth follow), rendering, HUD
├── dungeon.py       # Procedural generation: rooms, L-corridors, doors, stairs, BFS check
├── entities.py      # Player · Chaser · Patroller · Shooter · Projectile · spawn_enemies()
├── inventory.py     # (Phase 3) Inventory grid, item use/equip logic
├── minimap.py       # (Phase 3) Minimap rendering and fog-of-war tile tracking
├── settings.py      # All constants, colours, tile IDs, tunable parameters
├── tests/
│   └── test_dungeon.py   # Pytest — room overlap, BFS reachability, stairs, walkable start
├── requirements.txt
├── .gitignore
└── LICENSE
```

---

## Enemy Types

| Type | Colour | Behaviour |
|------|--------|-----------|
| **Chaser** | 🔴 Red | Sprints straight at the player once in sight range |
| **Patroller** | 🟠 Orange | Loops random waypoints in its room; switches to chase on sight |
| **Shooter** | 🟣 Purple | Keeps a 5-tile standoff distance; fires projectiles every ~1.2 s |

Enemy HP and speed scale up **+15 % / +5 %** per floor.

---

## Running Tests

```bash
pytest tests/ -v
```

Tests cover: no room overlap, minimum room count, all rooms BFS-reachable, stairs tile type, walkable player start, `Room` dataclass helpers.

---

## Roadmap

- [x] **Phase 1** — Procedural dungeon generation, tile renderer, fog of war, camera
- [x] **Phase 2** — Player movement + attacks, 3 enemy AI types, projectiles, smooth camera follow, death screen
- [ ] **Phase 3** — Inventory system, loot drops, minimap, real fog-of-war reveal
- [ ] **Phase 4** — Main menu, game-over screen, floor scaling, particles, screen shake, best-floor save

---

## License

MIT — see [LICENSE](LICENSE).
