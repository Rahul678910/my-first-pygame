"""
game.py - Core game loop engine, wave controller,
collision mechanics, and cycle detection for Chroma-Strand.
"""

import math
import random
import pygame
from visuals import (
    COLOR_BG, COLOR_CYAN, COLOR_MAGENTA, COLOR_GOLD, COLOR_WHITE,
    COLOR_CRIMSON, COLOR_VIOLET, COLOR_EMERALD, Starfield, ParticleSystem, Camera
)
from physics import (
    distance, point_line_segment_dist, line_segments_intersect,
    polygon_area, is_point_in_polygon
)
from entities import (
    Player, ResonanceAnchor, Strand, ResonanceField, StarMote,
    VoidMite, DisruptorSphere, ChronoPhantom, SingularityCore, VoidBullet
)
from ui import HUD

class GameEngine:
    def __init__(self, screen_w=1280, screen_h=720):
        self.width = screen_w
        self.height = screen_h
        self.starfield = Starfield(screen_w, screen_h, count=220)
        self.particle_sys = ParticleSystem()
        self.camera = Camera(screen_w, screen_h)
        self.hud = HUD(screen_w, screen_h)

        # Game State
        self.state = "MENU" # MENU, PLAYING, TUTORIAL, GAMEOVER
        self.score = 0
        self.high_score = 0
        self.combo = 1
        self.combo_timer = 0.0
        self.wave = 1
        self.wave_timer = 0.0
        self.wave_cleared = False
        self.time_elapsed = 0.0

        # Stats
        self.stats = {
            "plucks": 0,
            "kills": 0,
            "fields": 0,
            "max_combo": 1
        }

        # Entities
        self.player = Player(0, 0)
        self.anchors = []
        self.strands = []
        self.fields = []
        self.enemies = []
        self.bullets = []
        self.motes = []
        self.boss = None

        # Interaction state
        self.drag_start_anchor = None
        self.selected_anchor = None
        self.current_hint = ""
        self.hint_timer = 0.0

        # Center camera on player initially
        self.camera.x = self.player.x - self.width / 2
        self.camera.y = self.player.y - self.height / 2

        self.reset_game()

    def set_hint(self, text, duration=4.5):
        self.current_hint = text
        self.hint_timer = duration

    def reset_game(self):
        self.score = 0
        self.combo = 1
        self.combo_timer = 0.0
        self.wave = 1
        self.wave_timer = 0.0
        self.wave_cleared = False
        self.time_elapsed = 0.0
        self.boss = None

        self.stats = {
            "plucks": 0,
            "kills": 0,
            "fields": 0,
            "max_combo": 1
        }

        self.player = Player(0, 0)
        self.camera.x = self.player.x - self.width / 2
        self.camera.y = self.player.y - self.height / 2
        self.camera.trauma = 0.0
        self.camera.shake_x = 0.0
        self.camera.shake_y = 0.0

        self.anchors.clear()
        self.strands.clear()
        self.fields.clear()
        self.enemies.clear()
        self.bullets.clear()
        self.motes.clear()

        # Generate Cosmic Constellation of Anchors
        self._spawn_anchor_constellation()

        # Connect a few starting strands to form an initial celestial harp!
        if len(self.anchors) >= 3:
            self._create_strand(self.anchors[0], self.anchors[1], sound_engine=None)
            self._create_strand(self.anchors[1], self.anchors[2], sound_engine=None)

        self.set_hint("CLICK AN ANCHOR TO TETHER  |  PULL BACK & RELEASE TO SLINGSHOT!", 6.0)
        self._spawn_wave_enemies()

    def _spawn_anchor_constellation(self):
        """Creates an artistic ring and star-cluster of Resonance Anchors."""
        colors = [COLOR_CYAN, COLOR_MAGENTA, COLOR_GOLD, COLOR_EMERALD, COLOR_VIOLET]
        
        # Center anchor
        self.anchors.append(ResonanceAnchor(0, 0, 0, COLOR_GOLD))

        # Inner ring of 6 anchors
        inner_r = 340.0
        for i in range(6):
            ang = i * (math.tau / 6)
            x = math.cos(ang) * inner_r
            y = math.sin(ang) * inner_r
            c = colors[i % len(colors)]
            self.anchors.append(ResonanceAnchor(i + 1, x, y, c))

        # Outer ring of 8 anchors
        outer_r = 750.0
        for i in range(8):
            ang = i * (math.tau / 8) + (math.pi / 8)
            x = math.cos(ang) * outer_r
            y = math.sin(ang) * outer_r
            c = colors[(i + 2) % len(colors)]
            self.anchors.append(ResonanceAnchor(i + 7, x, y, c))

    def _create_strand(self, a1, a2, sound_engine=None):
        if a1 == a2:
            return None
        # Check if strand already exists
        for s in self.strands:
            if (s.anchor_a == a1 and s.anchor_b == a2) or (s.anchor_a == a2 and s.anchor_b == a1):
                return None

        strand = Strand(a1, a2)
        self.strands.append(strand)
        strand.pluck(velocity_mag=200, sound_engine=sound_engine)
        self._detect_enclosed_fields(sound_engine)
        return strand

    def _detect_enclosed_fields(self, sound_engine=None):
        """Detects 3-anchor cycles (triangles) formed by strands to create resonance fields."""
        adj = {a.id: set() for a in self.anchors}
        id_to_anchor = {a.id: a for a in self.anchors}
        for s in self.strands:
            adj[s.anchor_a.id].add(s.anchor_b.id)
            adj[s.anchor_b.id].add(s.anchor_a.id)

        existing_field_keys = {tuple(sorted(a.id for a in f.anchors)) for f in self.fields}

        # Look for triangles: A - B - C - A
        for u in adj:
            for v in adj[u]:
                if v <= u:
                    continue
                # Common neighbors of u and v
                common = adj[u].intersection(adj[v])
                for w in common:
                    if w <= v:
                        continue
                    key = tuple(sorted([u, v, w]))
                    if key not in existing_field_keys:
                        # Found a new triangle!
                        tri_anchors = [id_to_anchor[u], id_to_anchor[v], id_to_anchor[w]]
                        new_field = ResonanceField(tri_anchors)
                        self.fields.append(new_field)
                        self.stats["fields"] += 1
                        self.add_score(500, "RESONANCE FIELD FORMED!")
                        if sound_engine:
                            sound_engine.play_sfx("purify", volume=1.0)
                        cx = (id_to_anchor[u].x + id_to_anchor[v].x + id_to_anchor[w].x) / 3
                        cy = (id_to_anchor[u].y + id_to_anchor[v].y + id_to_anchor[w].y) / 3
                        self.particle_sys.emit_shockwave(cx, cy, tri_anchors[0].base_color, max_radius=220, duration=0.8)

    def _spawn_wave_enemies(self):
        self.wave_cleared = False
        w = self.wave

        if w % 5 == 0:
            # Boss Encounter Wave!
            self.set_hint("WARNING: SINGULARITY CORE DETECTED! SLINGSHOT TO CLEAVE!", 6.0)
            self.boss = SingularityCore(0, -600)
            self.enemies.append(self.boss)
            return

        # Regular Wave Scaling
        num_mites = 4 + w * 3
        num_disruptors = max(0, w - 1)
        num_phantoms = max(0, w - 2)

        for _ in range(num_mites):
            ang = random.uniform(0, math.tau)
            dist = random.uniform(700, 1100)
            self.enemies.append(VoidMite(self.player.x + math.cos(ang) * dist, self.player.y + math.sin(ang) * dist))

        for _ in range(num_disruptors):
            ang = random.uniform(0, math.tau)
            dist = random.uniform(850, 1200)
            self.enemies.append(DisruptorSphere(self.player.x + math.cos(ang) * dist, self.player.y + math.sin(ang) * dist))

        for _ in range(num_phantoms):
            ang = random.uniform(0, math.tau)
            dist = random.uniform(900, 1300)
            self.enemies.append(ChronoPhantom(self.player.x + math.cos(ang) * dist, self.player.y + math.sin(ang) * dist))

    def add_score(self, base_pts, popup_text=""):
        pts = base_pts * self.combo
        self.score += pts
        if self.score > self.high_score:
            self.high_score = self.score

        if popup_text:
            self.particle_sys.add_floating_text(f"+{pts:,} {popup_text}", self.player.x, self.player.y - 30, COLOR_GOLD)

    def add_combo(self):
        self.combo = min(16, self.combo + 1)
        self.combo_timer = 4.0
        self.stats["max_combo"] = max(self.stats["max_combo"], self.combo)
        self.hud.trigger_combo_pulse()

    def handle_mouse_down(self, pos, button, sound_engine):
        if self.state != "PLAYING":
            return

        world_x = pos[0] + self.camera.render_x
        world_y = pos[1] + self.camera.render_y

        if button == 1: # Left Click
            # Check if clicked on an anchor
            clicked_anchor = None
            for a in self.anchors:
                if distance((world_x, world_y), (a.x, a.y)) <= a.radius + 28:
                    clicked_anchor = a
                    break

            if clicked_anchor:
                # If player is within tether range, tether Lumina to it
                dist_to_player = distance((self.player.x, self.player.y), (clicked_anchor.x, clicked_anchor.y))
                if dist_to_player <= self.player.tether_max_dist + 100:
                    self.player.tether_to(clicked_anchor)
                self.drag_start_anchor = clicked_anchor
            else:
                self.drag_start_anchor = None

        elif button == 3: # Right Click: Slingshot release or Harmonic Strum
            if self.player.tethered_anchor:
                self.player.release_slingshot(sound_engine, self.particle_sys, self.camera)
            else:
                # Harmonic pulse strum: vibrate all nearby strings
                self._strum_nearby_strands(sound_engine)

    def handle_mouse_up(self, pos, button, sound_engine):
        if self.state != "PLAYING":
            return

        world_x = pos[0] + self.camera.render_x
        world_y = pos[1] + self.camera.render_y

        if button == 1: # Left Click release
            woven = False
            if self.drag_start_anchor:
                # Check if released on a different anchor
                for a in self.anchors:
                    if a != self.drag_start_anchor and distance((world_x, world_y), (a.x, a.y)) <= a.radius + 24:
                        new_s = self._create_strand(self.drag_start_anchor, a, sound_engine)
                        if new_s:
                            self.particle_sys.emit_sparks(a.x, a.y, a.base_color, count=16)
                            self.add_score(150, "STRAND WOVEN!")
                            woven = True
                        break
                self.drag_start_anchor = None

            # If not connected to another anchor, and player is tethered, fire slingshot!
            if not woven and self.player.tethered_anchor:
                dist = distance((self.player.x, self.player.y), (self.player.tethered_anchor.x, self.player.tethered_anchor.y))
                if dist > 45.0:
                    self.player.release_slingshot(sound_engine, self.particle_sys, self.camera)

    def _strum_nearby_strands(self, sound_engine):
        """Strums all strands within range of Lumina, creating an acoustic pulse."""
        strummed_any = False
        for s in self.strands:
            d, _, _, _ = point_line_segment_dist(self.player.x, self.player.y, s.anchor_a.x, s.anchor_a.y, s.anchor_b.x, s.anchor_b.y)
            if d < 180.0:
                s.pluck(velocity_mag=450.0, sound_engine=sound_engine)
                strummed_any = True
                self.stats["plucks"] += 1
                # Emit stun shockwave
                for e in self.enemies:
                    if distance((self.player.x, self.player.y), (e.x, e.y)) < 240:
                        e.health -= 15
                        if hasattr(e, "stun_timer"):
                            e.stun_timer = 1.2

        if strummed_any:
            self.particle_sys.emit_shockwave(self.player.x, self.player.y, COLOR_CYAN, max_radius=180, duration=0.45)
            self.camera.add_trauma(0.2)

    def handle_key_down(self, key, sound_engine):
        if self.state == "PLAYING":
            if key == pygame.K_SPACE:
                if self.player.tethered_anchor:
                    self.player.release_slingshot(sound_engine, self.particle_sys, self.camera)
                else:
                    self._strum_nearby_strands(sound_engine)
            elif key == pygame.K_f:
                self.player.activate_supernova(sound_engine, self.particle_sys, self.camera)

    def update(self, keys, mouse_pos, dt, sound_engine):
        self.time_elapsed += dt

        # Update Hint timer
        if self.hint_timer > 0:
            self.hint_timer -= dt
            if self.hint_timer <= 0:
                self.current_hint = ""

        # Update Combo timer
        if self.combo > 1:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 1

        self.hud.update(dt)
        self.particle_sys.update(dt)

        if self.state != "PLAYING":
            return

        # 1. Update Player
        self.player.update(keys, mouse_pos, self.camera.render_x, self.camera.render_y, dt)

        # 2. Update Camera
        self.camera.update(self.player.x, self.player.y, self.player.vx, self.player.vy, dt)

        # 3. Update Anchors & Hover detection
        world_mx = mouse_pos[0] + self.camera.render_x
        world_my = mouse_pos[1] + self.camera.render_y
        for a in self.anchors:
            a.hovered = (distance((world_mx, world_my), (a.x, a.y)) <= a.radius + 18)
            a.update(dt)

        # 4. Update Strands & Player Pluck Interaction
        for s in self.strands:
            s.update(dt)
            # Check if player crossed strand
            d, t, px, py = point_line_segment_dist(self.player.x, self.player.y, s.anchor_a.x, s.anchor_a.y, s.anchor_b.x, s.anchor_b.y)
            player_spd = math.hypot(self.player.vx, self.player.vy)
            if d < self.player.radius + 12 and player_spd > 120 and (self.time_elapsed - s.last_pluck_time > 0.18):
                s.pluck(velocity_mag=player_spd, sound_engine=sound_engine)
                s.last_pluck_time = self.time_elapsed
                self.stats["plucks"] += 1
                self.particle_sys.emit_sparks(px, py, s.color, count=8, speed=160)
                
                # If Hyper-Cleaving or in Supernova, plucking emits explosive acoustic resonance!
                if self.player.is_invulnerable:
                    sound_engine.play_sfx("shockwave", volume=0.8)
                    self.particle_sys.emit_shockwave(px, py, COLOR_GOLD, max_radius=190, duration=0.45)
                    self.camera.add_trauma(0.35)
                    # Damage nearby enemies
                    for e in self.enemies:
                        if distance((px, py), (e.x, e.y)) < 220:
                            e.health -= 50
                            if e.health <= 0:
                                self._destroy_enemy(e, sound_engine)

        # 5. Update Resonance Fields (Purify trapped enemies)
        for f in self.fields:
            f.update(dt)
            for e in self.enemies:
                if f.contains_point(e.x, e.y):
                    # Damage per second
                    e.health -= 120.0 * dt
                    self.particle_sys.emit_sparks(e.x, e.y, f.color, count=2, speed=80)
                    if e.health <= 0:
                        self._destroy_enemy(e, sound_engine, field_kill=True)

        # 6. Update Star Motes
        alive_motes = []
        for m in self.motes:
            m.update(self.player.x, self.player.y, dt)
            if distance((self.player.x, self.player.y), (m.x, m.y)) < self.player.radius + m.radius + 8:
                # Collected!
                sound_engine.play_sfx("mote", volume=0.4)
                self.player.resonance_energy = min(self.player.max_energy, self.player.resonance_energy + 4.5)
                self.add_score(25)
            elif m.life > 0:
                alive_motes.append(m)
        self.motes = alive_motes

        # 7. Update Bullets
        alive_bullets = []
        for b in self.bullets:
            b.update(dt)
            # Hit player?
            if distance((b.x, b.y), (self.player.x, self.player.y)) < self.player.radius + b.radius:
                self.player.take_damage(16.0, self.particle_sys, self.camera)
            elif b.life > 0:
                alive_bullets.append(b)
        self.bullets = alive_bullets

        # 8. Update Enemies & Combat
        alive_enemies = []
        for e in self.enemies:
            if isinstance(e, VoidMite):
                e.update(self.player.x, self.player.y, dt)
            elif isinstance(e, DisruptorSphere):
                e.update(self.player.x, self.player.y, dt, self.bullets)
            elif isinstance(e, ChronoPhantom):
                e.update(self.player.x, self.player.y, dt)
            elif isinstance(e, SingularityCore):
                e.update(self.player.x, self.player.y, dt, self.bullets, sound_engine)

            # Player Collision
            d_p = distance((e.x, e.y), (self.player.x, self.player.y))
            if d_p < self.player.radius + e.radius:
                if self.player.is_invulnerable:
                    # Cleave through enemy!
                    e.health -= 80.0
                    self.camera.add_trauma(0.3)
                    self.particle_sys.emit_sparks(e.x, e.y, COLOR_WHITE, count=14, speed=260)
                    if e.health <= 0:
                        self._destroy_enemy(e, sound_engine)
                else:
                    # Take damage from enemy
                    dmg = 25.0 if not isinstance(e, SingularityCore) else 45.0
                    self.player.take_damage(dmg, self.particle_sys, self.camera)

            if e.health > 0:
                alive_enemies.append(e)

        self.enemies = alive_enemies

        # Check Boss Defeat
        if self.boss and self.boss.health <= 0:
            self.boss = None
            self.particle_sys.emit_shockwave(self.player.x, self.player.y, COLOR_GOLD, max_radius=450, duration=1.2, width=12)
            self.camera.add_trauma(1.0)
            self.add_score(10000, "SINGULARITY CORE PURIFIED!")
            sound_engine.play_sfx("shatter", volume=1.0)

        # 9. Wave Progression
        if len(self.enemies) == 0:
            self.wave_timer += dt
            if self.wave_timer > 2.0:
                self.wave += 1
                self.wave_timer = 0.0
                self.set_hint(f"HARMONIC FREQUENCY ESCALATING: WAVE {self.wave}!", 3.5)
                self._spawn_wave_enemies()

        # 10. Player Death Check
        if self.player.health <= 0:
            self.state = "GAMEOVER"
            sound_engine.play_sfx("shatter", volume=1.0)
            self.particle_sys.emit_shatter(self.player.x, self.player.y, COLOR_CYAN, count=40)
            self.camera.add_trauma(0.9)

    def _destroy_enemy(self, e, sound_engine, field_kill=False):
        sound_engine.play_sfx("shatter", volume=0.7)
        self.particle_sys.emit_shatter(e.x, e.y, e.color, count=22)
        self.camera.add_trauma(0.2)
        self.stats["kills"] += 1
        self.add_combo()

        # Spawn Star Motes
        mote_count = 5 if not isinstance(e, SingularityCore) else 25
        for _ in range(mote_count):
            self.motes.append(StarMote(e.x + random.uniform(-10, 10), e.y + random.uniform(-10, 10)))

        txt = "HARMONIC PURIFICATION!" if field_kill else "CLEAVED!"
        self.add_score(e.score_value, txt)

    def render(self, surface):
        surface.fill(COLOR_BG)
        time_sec = self.time_elapsed

        cam_x = self.camera.render_x
        cam_y = self.camera.render_y

        # 1. Cosmic Starfield & Nebula
        self.starfield.draw(surface, cam_x, cam_y, time_sec)

        # 2. Resonance Fields (Enclosed Polygon Meshes)
        for f in self.fields:
            f.draw(surface, cam_x, cam_y)

        # 3. Active Strands (Vibrating Harmonic Lines)
        for s in self.strands:
            s.draw(surface, cam_x, cam_y)

        # 4. Drag line preview (while user is dragging a strand)
        if self.drag_start_anchor and self.state == "PLAYING":
            mx, my = pygame.mouse.get_pos()
            ax = self.drag_start_anchor.x - cam_x
            ay = self.drag_start_anchor.y - cam_y
            pygame.draw.line(surface, COLOR_WHITE, (int(ax), int(ay)), (mx, my), 2)
            pygame.draw.circle(surface, COLOR_CYAN, (mx, my), 6)

        # 5. Resonance Anchors
        for a in self.anchors:
            a.draw(surface, cam_x, cam_y)

        # 6. Star Motes
        for m in self.motes:
            m.draw(surface, cam_x, cam_y)

        # 7. Void Bullets
        for b in self.bullets:
            b.draw(surface, cam_x, cam_y)

        # 8. Void Enemies
        for e in self.enemies:
            e.draw(surface, cam_x, cam_y)

        # 9. Player (Lumina)
        if self.state == "PLAYING":
            self.player.draw(surface, cam_x, cam_y)

        # 10. Dynamic Particles, Shockwaves, and Floating Text
        self.particle_sys.draw(surface, cam_x, cam_y, self.hud.font_small)

        # 11. UI & Overlays
        mouse_pos = pygame.mouse.get_pos()
        if self.state == "MENU":
            return self.hud.draw_main_menu(surface, mouse_pos)
        elif self.state == "TUTORIAL":
            self.hud.draw_instructions_modal(surface)
        elif self.state == "PLAYING":
            self.hud.draw_game_hud(surface, self.player, self.score, self.combo, self.wave, self.boss, self.current_hint)
            self.hud.draw_minimap(surface, self.player, self.anchors, self.enemies)
            self.hud.draw_audio_visualizer(surface, self.time_elapsed, self.combo)
            self.hud.draw_crosshair(surface, mouse_pos, self.time_elapsed)
        elif self.state == "GAMEOVER":
            self.hud.draw_game_over(surface, self.score, self.high_score, self.wave, self.stats)

        return None
