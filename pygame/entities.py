"""
entities.py - Game objects for Chroma-Strand:
Player (Lumina), Resonance Anchors, Vibrating Strands,
Resonance Fields, Star Motes, and multi-tier Void Entities.
"""

import math
import random
import pygame
from visuals import (
    COLOR_CYAN, COLOR_MAGENTA, COLOR_GOLD, COLOR_WHITE,
    COLOR_VIOLET, COLOR_CRIMSON, COLOR_EMERALD, GlowCache
)
from physics import (
    distance, point_line_segment_dist, HarmonicVibration,
    is_point_in_polygon, polygon_area, polygon_centroid
)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.radius = 16
        self.health = 100.0
        self.max_health = 100.0
        self.resonance_energy = 0.0 # 0 to 100
        self.max_energy = 100.0
        self.supernova_active = False
        self.supernova_timer = 0.0

        # Slingshot & Tether
        self.tethered_anchor = None
        self.tether_max_dist = 360.0
        self.is_hyper_cleaving = False
        self.cleave_timer = 0.0

        # Trail for ribbon visual
        self.trail = []
        self.trail_max_len = 16

        # Rotation & pulse phase
        self.angle = 0.0
        self.pulse = 0.0

    @property
    def is_invulnerable(self):
        return self.is_hyper_cleaving or self.supernova_active

    def tether_to(self, anchor):
        self.tethered_anchor = anchor

    def release_slingshot(self, sound_engine, particle_system, camera):
        """Release tethered anchor to execute high-velocity kinetic slingshot."""
        if not self.tethered_anchor:
            return False

        ax, ay = self.tethered_anchor.x, self.tethered_anchor.y
        dist = distance((self.x, self.y), (ax, ay))
        if dist > 30.0:
            # Direction vector towards and through anchor
            dx = ax - self.x
            dy = ay - self.y
            norm = math.hypot(dx, dy)
            nx, ny = dx / norm, dy / norm

            # Slingshot velocity proportional to stretch
            launch_speed = min(1400.0, 450.0 + (dist / self.tether_max_dist) * 950.0)
            self.vx = nx * launch_speed
            self.vy = ny * launch_speed

            # Activate Hyper-Cleave mode!
            self.is_hyper_cleaving = True
            self.cleave_timer = 0.75

            # Audio & Visual Punch
            sound_engine.play_sfx("slingshot", volume=1.0)
            camera.add_trauma(0.55)
            particle_system.emit_shockwave(self.x, self.y, COLOR_CYAN, max_radius=140, duration=0.4)
            particle_system.emit_sparks(self.x, self.y, COLOR_WHITE, count=18, speed=320)
            self.tethered_anchor.pulse_ring()
            self.tethered_anchor = None
            return True

        self.tethered_anchor = None
        return False

    def activate_supernova(self, sound_engine, particle_system, camera):
        if self.resonance_energy >= 100.0 and not self.supernova_active:
            self.supernova_active = True
            self.supernova_timer = 7.0
            self.resonance_energy = 0.0
            sound_engine.play_sfx("supernova", volume=1.0)
            camera.add_trauma(0.85)
            particle_system.emit_shockwave(self.x, self.y, COLOR_GOLD, max_radius=320, duration=0.9, width=8)
            particle_system.add_floating_text("HARMONIC SUPERNOVA!", self.x, self.y - 40, COLOR_GOLD, font_size=28)
            return True
        return False

    def take_damage(self, amount, particle_system, camera):
        if self.is_invulnerable:
            return False
        self.health = max(0.0, self.health - amount)
        camera.add_trauma(0.4)
        particle_system.emit_sparks(self.x, self.y, COLOR_CRIMSON, count=12, speed=200)
        return True

    def update(self, keys, mouse_pos, cam_x, cam_y, dt):
        self.pulse += dt * 5.0

        def is_down(k):
            try:
                return bool(keys[k])
            except (IndexError, KeyError, TypeError):
                return False

        # Normal WASD/Arrow Movement
        move_speed = 460.0
        accel_x, accel_y = 0.0, 0.0
        if is_down(pygame.K_w) or is_down(pygame.K_UP):
            accel_y -= 1.0
        if is_down(pygame.K_s) or is_down(pygame.K_DOWN):
            accel_y += 1.0
        if is_down(pygame.K_a) or is_down(pygame.K_LEFT):
            accel_x -= 1.0
        if is_down(pygame.K_d) or is_down(pygame.K_RIGHT):
            accel_x += 1.0

        accel_mag = math.hypot(accel_x, accel_y)
        if accel_mag > 0:
            accel_x /= accel_mag
            accel_y /= accel_mag
            self.vx += accel_x * move_speed * 6.0 * dt
            self.vy += accel_y * move_speed * 6.0 * dt

        # Tether Spring Resistance Physics
        if self.tethered_anchor:
            ax, ay = self.tethered_anchor.x, self.tethered_anchor.y
            dist = distance((self.x, self.y), (ax, ay))
            if dist > self.tether_max_dist:
                # Clamp position to max dist
                angle = math.atan2(self.y - ay, self.x - ax)
                self.x = ax + math.cos(angle) * self.tether_max_dist
                self.y = ay + math.sin(angle) * self.tether_max_dist
                self.vx *= 0.5
                self.vy *= 0.5
            elif dist > 50.0:
                # Elastic counter-force
                spring_k = 4.5
                self.vx -= ((self.x - ax) * spring_k) * dt
                self.vy -= ((self.y - ay) * spring_k) * dt

        # Apply friction/drag
        drag = 0.93 if not self.is_hyper_cleaving else 0.985
        self.vx *= drag
        self.vy *= drag

        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Update Cleave timer
        if self.is_hyper_cleaving:
            self.cleave_timer -= dt
            if self.cleave_timer <= 0:
                self.is_hyper_cleaving = False

        # Update Supernova timer
        if self.supernova_active:
            self.supernova_timer -= dt
            if self.supernova_timer <= 0:
                self.supernova_active = False

        # Aim towards mouse
        world_mx = mouse_pos[0] + cam_x
        world_my = mouse_pos[1] + cam_y
        self.angle = math.atan2(world_my - self.y, world_mx - self.x)

        # Update ribbon trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.trail_max_len:
            self.trail.pop(0)

    def draw(self, surface, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        # Draw ribbon trail
        if len(self.trail) > 1:
            for i in range(len(self.trail) - 1):
                p1 = (int(self.trail[i][0] - cam_x), int(self.trail[i][1] - cam_y))
                p2 = (int(self.trail[i+1][0] - cam_x), int(self.trail[i+1][1] - cam_y))
                alpha = int(255 * (i / len(self.trail)))
                color = COLOR_GOLD if self.supernova_active else (COLOR_MAGENTA if self.is_hyper_cleaving else COLOR_CYAN)
                width = max(1, int(4 * (i / len(self.trail))))
                pygame.draw.line(surface, color, p1, p2, width)

        # Draw tether line if attached to an anchor
        if self.tethered_anchor:
            ax = int(self.tethered_anchor.x - cam_x)
            ay = int(self.tethered_anchor.y - cam_y)
            stretch = min(1.0, distance((self.x, self.y), (self.tethered_anchor.x, self.tethered_anchor.y)) / self.tether_max_dist)
            # Interpolate tether color from Cyan to Crimson as tension builds
            tether_col = (
                int(COLOR_CYAN[0] + (COLOR_CRIMSON[0] - COLOR_CYAN[0]) * stretch),
                int(COLOR_CYAN[1] + (COLOR_CRIMSON[1] - COLOR_CYAN[1]) * stretch),
                int(COLOR_CYAN[2] + (COLOR_CRIMSON[2] - COLOR_CYAN[2]) * stretch),
            )
            pygame.draw.line(surface, tether_col, (sx, sy), (ax, ay), 3)
            # Draw tension pulse ripples
            mid_x = (sx + ax) // 2
            mid_y = (sy + ay) // 2
            pygame.draw.circle(surface, COLOR_WHITE, (mid_x, mid_y), int(3 + stretch * 5))

        # Main Celestial Needle Body
        body_color = COLOR_GOLD if self.supernova_active else (COLOR_MAGENTA if self.is_hyper_cleaving else COLOR_CYAN)
        glow_r = 44 if (self.supernova_active or self.is_hyper_cleaving) else 30
        glow = GlowCache.get_glow(glow_r, body_color)
        surface.blit(glow, (sx - glow.get_width() // 2, sy - glow.get_height() // 2), special_flags=pygame.BLEND_ADD)

        # Rotating photon needle diamond
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        tip_len = 22.0
        wing_w = 9.0
        back_len = 11.0

        p_tip = (sx + cos_a * tip_len, sy + sin_a * tip_len)
        p_left = (sx - sin_a * wing_w - cos_a * (back_len * 0.4), sy + cos_a * wing_w - sin_a * (back_len * 0.4))
        p_back = (sx - cos_a * back_len, sy - sin_a * back_len)
        p_right = (sx + sin_a * wing_w - cos_a * (back_len * 0.4), sy - cos_a * wing_w - sin_a * (back_len * 0.4))

        pygame.draw.polygon(surface, body_color, [p_tip, p_left, p_back, p_right])
        pygame.draw.polygon(surface, COLOR_WHITE, [p_tip, p_left, p_back, p_right], 2)

        # Inner pulsing core
        core_r = int(4.0 + 1.5 * math.sin(self.pulse))
        pygame.draw.circle(surface, COLOR_WHITE, (sx, sy), core_r)


class ResonanceAnchor:
    """Ancient Quantum Prisms that serve as string endpoints."""
    def __init__(self, anchor_id, x, y, color=COLOR_CYAN):
        self.id = anchor_id
        self.x = x
        self.y = y
        self.base_color = color
        self.radius = 24
        self.pulse = random.uniform(0, math.tau)
        self.pulse_ring_timer = 0.0
        self.orbital_angle = random.uniform(0, math.tau)
        self.hovered = False

    def pulse_ring(self):
        self.pulse_ring_timer = 0.4

    def update(self, dt):
        self.pulse += dt * 3.0
        self.orbital_angle += dt * 2.2
        if self.pulse_ring_timer > 0:
            self.pulse_ring_timer -= dt

    def draw(self, surface, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        # Outer soft glow
        glow_r = 50 if self.hovered else 36
        glow = GlowCache.get_glow(glow_r, self.base_color)
        surface.blit(glow, (sx - glow.get_width() // 2, sy - glow.get_height() // 2), special_flags=pygame.BLEND_ADD)

        # Central geometric core (pulsing octagon)
        r = self.radius + 2.5 * math.sin(self.pulse)
        points = []
        for i in range(8):
            ang = self.orbital_angle * 0.5 + i * (math.tau / 8)
            points.append((sx + math.cos(ang) * r, sy + math.sin(ang) * r))
        pygame.draw.polygon(surface, self.base_color, points, 2)
        pygame.draw.circle(surface, COLOR_WHITE, (sx, sy), 6)

        # Orbiting micro-satellites
        for i in range(3):
            sat_ang = self.orbital_angle + i * (math.tau / 3)
            sat_dist = self.radius + 14.0
            px = sx + math.cos(sat_ang) * sat_dist
            py = sy + math.sin(sat_ang) * sat_dist
            pygame.draw.circle(surface, self.base_color, (int(px), int(py)), 3)

        # Pulse shockwave ring
        if self.pulse_ring_timer > 0:
            prog = 1.0 - (self.pulse_ring_timer / 0.4)
            ring_r = int(self.radius + prog * 40.0)
            alpha = int(255 * (1.0 - prog))
            temp_s = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp_s, (*self.base_color[:3], alpha), (ring_r + 2, ring_r + 2), ring_r, 2)
            surface.blit(temp_s, (sx - ring_r - 2, sy - ring_r - 2), special_flags=pygame.BLEND_ADD)


class Strand:
    """The Celestial String connecting two anchors. Oscillates with physical acoustic harmonics."""
    def __init__(self, anchor_a, anchor_b):
        self.anchor_a = anchor_a
        self.anchor_b = anchor_b
        self.length = distance((anchor_a.x, anchor_a.y), (anchor_b.x, anchor_b.y))
        self.vibration = HarmonicVibration(self.length)
        # Note pitch indexed by length (short = high, long = low)
        # Lengths typically 180 to 900
        norm_len = max(0.0, min(1.0, (self.length - 150) / 750.0))
        self.pitch_index = int(11 - norm_len * 11) # 11 down to 0
        self.color = anchor_a.base_color
        self.last_pluck_time = -999.0

    def pluck(self, velocity_mag=300.0, sound_engine=None):
        self.vibration.pluck(velocity_mag)
        if sound_engine:
            sound_engine.play_harp_note(self.pitch_index, volume=0.85)

    def update(self, dt):
        self.vibration.update(dt)

    def draw(self, surface, cam_x, cam_y):
        ax = self.anchor_a.x - cam_x
        ay = self.anchor_a.y - cam_y
        bx = self.anchor_b.x - cam_x
        by = self.anchor_b.y - cam_y

        offsets = self.vibration.get_displacement_samples(num_points=14)
        if not offsets:
            # Straight neon line with core and glow
            pygame.draw.line(surface, self.color, (int(ax), int(ay)), (int(bx), int(by)), 3)
            pygame.draw.line(surface, COLOR_WHITE, (int(ax), int(ay)), (int(bx), int(by)), 1)
        else:
            # Draw vibrating harmonic sine wave
            dx = bx - ax
            dy = by - ay
            dist = math.hypot(dx, dy)
            if dist == 0:
                return
            nx = -dy / dist
            ny = dx / dist

            pts = []
            num_pts = len(offsets)
            for i in range(num_pts):
                t = i / (num_pts - 1)
                px = ax + dx * t + nx * offsets[i]
                py = ay + dy * t + ny * offsets[i]
                pts.append((int(px), int(py)))

            if len(pts) > 1:
                pygame.draw.lines(surface, self.color, False, pts, 4)
                pygame.draw.lines(surface, COLOR_WHITE, False, pts, 2)


class ResonanceField:
    """Enclosed polygon loop that purifies trapped enemies into star motes."""
    def __init__(self, anchors):
        self.anchors = anchors # list of ResonanceAnchor
        self.color = anchors[0].base_color
        self.pulse = 0.0

    @property
    def points(self):
        return [(a.x, a.y) for a in self.anchors]

    def contains_point(self, px, py):
        return is_point_in_polygon(px, py, self.points)

    def update(self, dt):
        self.pulse += dt * 3.5

    def draw(self, surface, cam_x, cam_y):
        pts = [(int(a.x - cam_x), int(a.y - cam_y)) for a in self.anchors]
        if len(pts) < 3:
            return

        # Semi-transparent glowing fill
        min_x = min(p[0] for p in pts)
        max_x = max(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        max_y = max(p[1] for p in pts)
        w = max(10, max_x - min_x + 10)
        h = max(10, max_y - min_y + 10)

        poly_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        local_pts = [(p[0] - min_x + 5, p[1] - min_y + 5) for p in pts]
        
        # Pulsing opacity
        alpha = int(45 + 25 * math.sin(self.pulse))
        pygame.draw.polygon(poly_surf, (*self.color[:3], alpha), local_pts)
        pygame.draw.polygon(poly_surf, (*COLOR_WHITE, int(alpha * 1.5)), local_pts, 2)
        surface.blit(poly_surf, (min_x - 5, min_y - 5), special_flags=pygame.BLEND_ADD)


class StarMote:
    """Luminous collectible motes that gravitate towards player and fill Supernova gauge."""
    def __init__(self, x, y, value=1):
        self.x = x
        self.y = y
        self.vx = random.uniform(-60, 60)
        self.vy = random.uniform(-60, 60)
        self.value = value
        self.life = 12.0
        self.radius = 4.0
        self.color = COLOR_GOLD

    def update(self, player_x, player_y, dt):
        self.life -= dt
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)

        # Magnetic attraction towards player
        attract_range = 320.0
        if dist < attract_range and dist > 1.0:
            force = (1.0 - dist / attract_range) * 900.0
            self.vx += (dx / dist) * force * dt
            self.vy += (dy / dist) * force * dt

        self.vx *= 0.94
        self.vy *= 0.94
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        glow = GlowCache.get_glow(12, self.color)
        surface.blit(glow, (sx - glow.get_width() // 2, sy - glow.get_height() // 2), special_flags=pygame.BLEND_ADD)
        pygame.draw.circle(surface, COLOR_WHITE, (sx, sy), 2)


class VoidBullet:
    """Anti-resonance projectile fired by Disruptors."""
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = 5.0
        self.life = 4.0
        self.color = COLOR_CRIMSON

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        glow = GlowCache.get_glow(14, self.color)
        surface.blit(glow, (sx - glow.get_width() // 2, sy - glow.get_height() // 2), special_flags=pygame.BLEND_ADD)
        pygame.draw.circle(surface, COLOR_WHITE, (sx, sy), 3)


# --- Void Enemies ---

class VoidMite:
    """Fast, erratic swarming crystal that hunts the player."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.speed = random.uniform(160, 220)
        self.radius = 12
        self.health = 20.0
        self.color = COLOR_CRIMSON
        self.score_value = 100
        self.angle = 0.0

    def update(self, player_x, player_y, dt):
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            target_vx = (dx / dist) * self.speed
            target_vy = (dy / dist) * self.speed
            self.vx += (target_vx - self.vx) * 3.5 * dt
            self.vy += (target_vy - self.vy) * 3.5 * dt
            self.angle = math.atan2(self.vy, self.vx)

        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        glow = GlowCache.get_glow(22, self.color)
        surface.blit(glow, (sx - glow.get_width() // 2, sy - glow.get_height() // 2), special_flags=pygame.BLEND_ADD)

        # Jagged shard triangle
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        pts = [
            (sx + cos_a * 14, sy + sin_a * 14),
            (sx - sin_a * 8 - cos_a * 8, sy + cos_a * 8 - sin_a * 8),
            (sx + sin_a * 8 - cos_a * 8, sy - cos_a * 8 - sin_a * 8),
        ]
        pygame.draw.polygon(surface, self.color, pts)
        pygame.draw.polygon(surface, COLOR_WHITE, pts, 1)


class DisruptorSphere:
    """Ranged entity that fires anti-resonance void bolts towards strands and player."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.radius = 20
        self.health = 45.0
        self.color = COLOR_VIOLET
        self.shoot_timer = random.uniform(1.8, 3.0)
        self.score_value = 250
        self.pulse = 0.0

    def update(self, player_x, player_y, dt, bullets):
        self.pulse += dt * 4.0
        # Maintain distance from player
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 380:
            self.x += (dx / dist) * 75 * dt
            self.y += (dy / dist) * 75 * dt
        elif dist < 220:
            self.x -= (dx / dist) * 90 * dt
            self.y -= (dy / dist) * 90 * dt

        # Shooting logic
        self.shoot_timer -= dt
        if self.shoot_timer <= 0:
            self.shoot_timer = 2.4
            if dist > 0:
                b_spd = 280.0
                b_vx = (dx / dist) * b_spd
                b_vy = (dy / dist) * b_spd
                bullets.append(VoidBullet(self.x, self.y, b_vx, b_vy))

    def draw(self, surface, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        glow = GlowCache.get_glow(36, self.color)
        surface.blit(glow, (sx - glow.get_width() // 2, sy - glow.get_height() // 2), special_flags=pygame.BLEND_ADD)

        # Concentric rings
        pygame.draw.circle(surface, self.color, (sx, sy), self.radius, 2)
        inner_r = int(self.radius * 0.5 + 3 * math.sin(self.pulse))
        pygame.draw.circle(surface, COLOR_WHITE, (sx, sy), max(2, inner_r))


class ChronoPhantom:
    """Incorporeal phantom that phases through reality. Stunned by vibrating strings."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 18
        self.health = 35.0
        self.color = COLOR_EMERALD
        self.score_value = 300
        self.phase_time = 0.0
        self.is_corporeal = True
        self.stun_timer = 0.0

    def update(self, player_x, player_y, dt):
        self.phase_time += dt
        self.is_corporeal = math.sin(self.phase_time * 2.0) > -0.2

        if self.stun_timer > 0:
            self.stun_timer -= dt
            return

        # Slow inexorable drift towards player
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            spd = 110.0 if self.is_corporeal else 180.0
            self.x += (dx / dist) * spd * dt
            self.y += (dy / dist) * spd * dt

    def draw(self, surface, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        alpha = 230 if self.is_corporeal else 65

        temp_s = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        center = (self.radius * 2, self.radius * 2)
        pygame.draw.circle(temp_s, (*self.color[:3], alpha), center, self.radius)
        pygame.draw.circle(temp_s, (*COLOR_WHITE, alpha), center, self.radius // 2)
        surface.blit(temp_s, (sx - center[0], sy - center[1]), special_flags=pygame.BLEND_ADD)


class SingularityCore:
    """Epic Boss Anomaly (Wave 5 & 10): Hyper-cube core with orbiting shield nodes."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 48
        self.health = 450.0
        self.max_health = 450.0
        self.color = COLOR_MAGENTA
        self.score_value = 2500
        self.pulse = 0.0
        self.orbit_angle = 0.0
        self.attack_timer = 3.0
        self.shield_nodes = 4 # Orbiting shield nodes

    def update(self, player_x, player_y, dt, bullets, sound_engine):
        self.pulse += dt * 3.0
        self.orbit_angle += dt * 1.5

        # Slowly track player
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 260:
            self.x += (dx / dist) * 45 * dt
            self.y += (dy / dist) * 45 * dt

        # Boss radial burst attack
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            self.attack_timer = 3.2
            sound_engine.play_sfx("shockwave", volume=0.7)
            # Emit 8-way spiral bullet pattern
            for i in range(8):
                ang = self.orbit_angle + i * (math.tau / 8)
                b_spd = 210.0
                bullets.append(VoidBullet(self.x, self.y, math.cos(ang) * b_spd, math.sin(ang) * b_spd))

    def draw(self, surface, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        # Huge core aura
        glow = GlowCache.get_glow(80, self.color)
        surface.blit(glow, (sx - glow.get_width() // 2, sy - glow.get_height() // 2), special_flags=pygame.BLEND_ADD)

        # Nested rotating squares
        for s_idx, rot_dir in enumerate([1.0, -1.0]):
            ang_offset = self.orbit_angle * rot_dir + s_idx * (math.pi / 4)
            pts = []
            size = self.radius + s_idx * 12
            for i in range(4):
                a = ang_offset + i * (math.tau / 4)
                pts.append((sx + math.cos(a) * size, sy + math.sin(a) * size))
            pygame.draw.polygon(surface, self.color, pts, 3)

        # Orbiting shield nodes
        for i in range(self.shield_nodes):
            ang = self.orbit_angle * 1.2 + i * (math.tau / self.shield_nodes)
            dist = self.radius + 38.0
            ox = sx + math.cos(ang) * dist
            oy = sy + math.sin(ang) * dist
            pygame.draw.circle(surface, COLOR_CYAN, (int(ox), int(oy)), 8)
            pygame.draw.circle(surface, COLOR_WHITE, (int(ox), int(oy)), 4)
