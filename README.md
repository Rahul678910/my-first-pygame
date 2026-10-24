# ✦ CHROMA-STRAND: HARMONIC VOID ✦
### *An Acoustic-Kinetic Celestial Weaving Odyssey*

A groundbreaking, never-before-seen arcade physics game built in Python & Pygame.

---

## 🌟 The Vision: Why It Has Never Been Seen Before

Most action/arcade games rely on shooting bullets or jumping across platforms. **Chroma-Strand** introduces an entirely new genre: **Acoustic-Kinetic String Weaving**.

You play as **Lumina**, an ethereal photon needle weaving living harmonic threads across ancient cosmic quantum prisms (**Resonance Anchors**):

1. **Physical Elastic Light Strands**: Every strand you weave acts as an elastic cello/harp string simulated with physical harmonic oscillation.
2. **Procedural Pentatonic Synthesis (Real-Time Audio)**: Zero external audio files! When strings are plucked or cut, a real-time mathematical synthesizer produces celestial pentatonic harp tones (A3 to C6) tuned dynamically to each string's physical length.
3. **Kinetic Bowstring Slingshotting**: Tether Lumina to an anchor, pull back to build elastic potential energy ($E = \frac{1}{2} k x^2$), and release to launch at relativistic speed in **Hyper-Cleave Mode**, slicing through Void swarms.
4. **Resonance Field Purification (Geometric Enclosure)**: Weave 3 or more anchors into a closed polygon (triangles, quads). The enclosed interior erupts into a shimmering harmonic resonance field, purifying all trapped void entities into glowing golden **Star Motes**.
5. **Overdrive Supernova**: Absorb Star Motes to fill your resonance gauge to 100%, then trigger a slow-motion celestial supernova that detonates continuous shockwaves.
6. **Dynamic Boss Anomaly (Singularity Core)**: At Wave 5, face the colossal rotating hyper-cube with orbiting shield nodes and spiral anti-resonance barrages.

---

## 🎮 Controls

| Action | Control | Description |
| :--- | :--- | :--- |
| **Move Lumina** | `W, A, S, D` or `Arrow Keys` | Smooth inertial flight through cosmic space |
| **Tether to Anchor** | `Left Click` on an Anchor | Attaches Lumina to the anchor with an elastic band |
| **Slingshot Launch** | `Pull Back & Release Left Click` or `Spacebar` / `Right Click` | Releases tether with explosive kinetic speed + Hyper-Cleave invulnerability |
| **Weave Strand** | `Click & Drag` between 2 Anchors | Connects two anchors with a vibrating acoustic light strand |
| **Harmonic Pulse Strum** | `Spacebar` or `Right Click` (untethered) | Plucks all nearby strands, emitting an acoustic stun shockwave |
| **Overdrive Supernova** | `F` (when meter is 100%) | Triggers screen-clearing invulnerable slow-mo supernova |
| **Fullscreen** | `F11` | Toggles borderless fullscreen mode |
| **Toggle Music** | `M` | Mutes or unmutes procedural ambient music |
| **Restart (Game Over)** | `R` | Instantly restarts a fresh cosmic run |
| **Menu / Pause** | `ESC` | Returns to main menu |

---

## 🚀 How to Run the Game

### Method 1: Double-Click Launcher
Simply double-click `run_game.bat` inside the folder!

### Method 2: Command Line
```bash
.venv\Scripts\python.exe main.py
```
*(Or `python main.py` if python with pygame-ce and numpy is in your PATH)*

---

## 🧬 Architectural Overview

```
attame/
├── main.py          # Game lifecycle, window management, event routing, 60 FPS clock
├── game.py          # Core game engine, wave management, polygon cycle detection, combat
├── entities.py      # Player (Lumina), Anchors, Strands, Resonance Fields, Void Entities & Boss
├── physics.py       # Harmonic vibration differential equations, tension spring math, ray-polygon tests
├── audio_synth.py   # Pure NumPy procedural audio synthesizer (12 harp notes, sfx, ambient pads)
├── visuals.py       # Particle systems, additive glow cache, camera shake, starfield parallax
├── ui.py            # Futuristic HUD, live 12-band frequency equalizer, minimap radar, menus
└── run_game.bat     # One-click Windows runner
```

---

## 🎨 Visual & Audio Highlights
- **Additive Blending Neon Glow**: Layered soft radial glows for high-contrast cyberpunk/celestial aesthetic.
- **Physical Sine-Wave Displacements**: Strings realistically vibrate and ripple upon contact.
- **Dynamic 12-Band Audio Visualizer**: Equalizer at the bottom-right reacting to musical frequencies in real time.
- **100% Asset-Free**: No downloaded MP3s, PNGs, or dependencies beyond `pygame-ce` and `numpy`.
