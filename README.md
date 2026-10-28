# 🗡️ Dungeon Crawler

A procedurally generated dungeon crawler built with Python and Pygame. No external assets — everything is drawn with shapes and colours.

![Gameplay GIF placeholder](docs/gameplay.gif)

---

## Features

- 🗺️ **Procedural generation** — random rooms and L-shaped corridors, new layout every run
- 🧍 **Player** — top-down WASD/arrow movement, melee + ranged attack, health bar
- 👾 **Enemies** — 3 types (Chaser, Patrol, Shooter) with simple AI
- 💎 **Loot** — potions, weapons, coins drop from enemies and chests
- 🎒 **Inventory** — grid UI toggled with `I`, use/equip items
- 🗺️ **Minimap** — explored rooms, player position, exit marker; toggle with `M`
- 🌫️ **Fog of war** — only the area around the player is illuminated
- 💥 **Juice** — screen shake on hits, particle effects, glowing loot & stairs
- 🏆 **Best floor** saved to `best_floor.txt` across sessions

---

## Controls

| Key | Action |
|-----|--------|
| `WASD` / `↑↓←→` | Move |
| `Space` | Melee attack |
| `F` | Ranged attack |
| `I` | Toggle inventory |
| `M` | Toggle minimap |
| `R` | New dungeon (Phase 1: regenerate) |
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
├── main.py          # Entry point, game loop, camera, rendering
├── dungeon.py       # Procedural generation (rooms, corridors, doors, stairs)
├── entities.py      # Player, Enemy classes and AI
├── inventory.py     # Inventory grid, item use/equip logic
├── minimap.py       # Minimap rendering and fog-of-war tracking
├── settings.py      # All constants, colours, tunable parameters
├── tests/
│   └── test_dungeon.py   # Pytest tests for dungeon generation & inventory
├── requirements.txt
├── .gitignore
└── LICENSE
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Roadmap

- [x] Phase 1 — Dungeon generation + render loop
- [ ] Phase 2 — Player & enemy entities with AI
- [ ] Phase 3 — Inventory, loot, minimap, fog of war
- [ ] Phase 4 — Menus, game-over, floor scaling, particles, screen shake

---

## License

MIT — see [LICENSE](LICENSE).
