"""
visuals.py - High-Performance Visual & Particle Effects for Chroma-Strand.
Includes additive blending glows, glowing neon trails, screen shake,
chromatic aberration, floating damage text, and cosmic starfields.
"""

import math
import random
import pygame

# Color Palette (Celestial Neon Spectrum)
COLOR_BG = (8, 9, 22)
COLOR_WHITE = (255, 255, 255)
COLOR_CYAN = (0, 240, 255)
COLOR_MAGENTA = (255, 30, 180)
COLOR_GOLD = (255, 215, 0)
COLOR_VIOLET = (160, 60, 255)
COLOR_EMERALD = (40, 255, 140)
COLOR_CRIMSON = (255, 50, 75)
COLOR_DEEP_BLUE = (15, 25, 60)

class GlowCache:
    """Caches pre-rendered soft radial glow circles for blitting with BLEND_ADD."""
    _cache = {}

    @classmethod
    def get_glow(cls, radius, color):
        key = (int(radius), color[:3])
        if key in cls._cache:
            return cls._cache[key]
        
        diameter = radius * 2
        surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = (radius, radius)
        r, g, b = color[:3]

        # Draw concentric soft circles with exponential alpha decay
        steps = max(8, int(radius // 2))
        for step in range(steps, 0, -1):
            factor = step / steps
            cur_r = radius * factor
            alpha = int(255 * (1.0 - factor) ** 2 * 0.45)
            pygame.draw.circle(surf, (r, g, b, alpha), center, int(cur_r))

        cls._cache[key] = surf
        return surf


class Starfield:
    """Parallax cosmic dust and distant pulsating stars."""
    def __init__(self, width, height, count=180):
        self.width = width
        self.height = height
        self.stars = []
        for _ in range(count):
            self.stars.append({
                "x": random.uniform(-width, width * 2),
                "y": random.uniform(-height, height * 2),
                "size": random.uniform(0.8, 2.6),
                "layer": random.uniform(0.1, 0.45), # parallax depth
                "twinkle_speed": random.uniform(1.5, 4.0),
                "twinkle_offset": random.uniform(0, math.tau),
                "color": random.choice([COLOR_CYAN, COLOR_MAGENTA, COLOR_GOLD, (200, 220, 255), (180, 150, 255)])
            })

    def update(self, dt):
        pass

    def draw(self, surface, cam_x, cam_y, time_sec):
        w, h = surface.get_size()
        for star in self.stars:
            # Parallax displacement
            screen_x = star["x"] - cam_x * star["layer"]
            screen_y = star["y"] - cam_y * star["layer"]

            # Wrap around camera viewport
            screen_x = (screen_x % (self.width * 2.5)) - (self.width * 0.5)
            screen_y = (screen_y % (self.height * 2.5)) - (self.height * 0.5)

            if -10 <= screen_x <= w + 10 and -10 <= screen_y <= h + 10:
                twinkle = 0.5 + 0.5 * math.sin(time_sec * star["twinkle_speed"] + star["twinkle_offset"])
                brightness = max(0.2, twinkle)
                r, g, b = star["color"]
                final_color = (int(r * brightness), int(g * brightness), int(b * brightness))
                pygame.draw.circle(surface, final_color, (int(screen_x), int(screen_y)), int(star["size"]))


class ParticleSystem:
    """Dynamic particles for spark spray, shattered crystalline shards, and shockwaves."""
    def __init__(self):
        self.particles = []
        self.shockwaves = []
        self.floating_texts = []

    def emit_sparks(self, x, y, color, count=14, speed=220, lifespan=0.6):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            spd = random.uniform(speed * 0.3, speed)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * spd,
                "vy": math.sin(angle) * spd,
                "color": color,
                "size": random.uniform(2.0, 4.5),
                "life": lifespan,
                "max_life": lifespan,
                "drag": 0.94,
                "type": "spark"
            })

    def emit_shatter(self, x, y, color, count=24):
        """Geometric shard fragments emitted when an enemy shatters."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            spd = random.uniform(80, 360)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * spd,
                "vy": math.sin(angle) * spd,
                "color": color,
                "size": random.uniform(3.0, 7.0),
                "angle": random.uniform(0, math.tau),
                "v_rot": random.uniform(-10, 10),
                "life": random.uniform(0.5, 0.9),
                "max_life": 0.9,
                "drag": 0.96,
                "type": "shard"
            })

    def emit_shockwave(self, x, y, color, max_radius=180, duration=0.55, width=4):
        self.shockwaves.append({
            "x": x, "y": y,
            "color": color,
            "radius": 10,
            "max_radius": max_radius,
            "duration": duration,
            "timer": duration,
            "width": width
        })

    def add_floating_text(self, text, x, y, color=COLOR_WHITE, font_size=22, duration=0.9):
        self.floating_texts.append({
            "text": text,
            "x": x, "y": y,
            "color": color,
            "font_size": font_size,
            "timer": duration,
            "duration": duration,
            "vy": -55
        })

    def update(self, dt):
        # Update particles
        alive_p = []
        for p in self.particles:
            p["life"] -= dt
            if p["life"] > 0:
                p["vx"] *= p["drag"]
                p["vy"] *= p["drag"]
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                if p["type"] == "shard":
                    p["angle"] += p["v_rot"] * dt
                alive_p.append(p)
        self.particles = alive_p

        # Update shockwaves
        alive_sw = []
        for sw in self.shockwaves:
            sw["timer"] -= dt
            if sw["timer"] > 0:
                prog = 1.0 - (sw["timer"] / sw["duration"])
                sw["radius"] = 10 + (sw["max_radius"] - 10) * (prog ** 0.6)
                alive_sw.append(sw)
        self.shockwaves = alive_sw

        # Update floating texts
        alive_txt = []
        for ft in self.floating_texts:
            ft["timer"] -= dt
            if ft["timer"] > 0:
                ft["y"] += ft["vy"] * dt
                alive_txt.append(ft)
        self.floating_texts = alive_txt

    def draw(self, surface, cam_x, cam_y, font):
        # Draw shockwaves
        for sw in self.shockwaves:
            sx = int(sw["x"] - cam_x)
            sy = int(sw["y"] - cam_y)
            alpha = int(255 * (sw["timer"] / sw["duration"]) ** 1.5)
            r, g, b = sw["color"]
            ring_surf = pygame.Surface((int(sw["radius"] * 2 + 10), int(sw["radius"] * 2 + 10)), pygame.SRCALPHA)
            pygame.draw.circle(
                ring_surf, (r, g, b, alpha),
                (int(sw["radius"] + 5), int(sw["radius"] + 5)),
                int(sw["radius"]), max(1, int(sw["width"] * (sw["timer"] / sw["duration"])))
            )
            surface.blit(ring_surf, (sx - int(sw["radius"] + 5), sy - int(sw["radius"] + 5)), special_flags=pygame.BLEND_ADD)

        # Draw particles
        for p in self.particles:
            sx = int(p["x"] - cam_x)
            sy = int(p["y"] - cam_y)
            fade = p["life"] / p["max_life"]
            alpha = int(255 * fade)
            r, g, b = p["color"]
            if p["type"] == "spark":
                glow = GlowCache.get_glow(int(p["size"] * 2.5), p["color"])
                surface.blit(glow, (sx - glow.get_width() // 2, sy - glow.get_height() // 2), special_flags=pygame.BLEND_ADD)
                pygame.draw.circle(surface, (255, 255, 255), (sx, sy), max(1, int(p["size"] * 0.6)))
            elif p["type"] == "shard":
                size = p["size"] * fade
                # Draw rotating diamond
                ang = p["angle"]
                cos_a, sin_a = math.cos(ang), math.sin(ang)
                points = [
                    (sx + cos_a * size, sy + sin_a * size),
                    (sx - sin_a * (size * 0.5), sy + cos_a * (size * 0.5)),
                    (sx - cos_a * size, sy - sin_a * size),
                    (sx + sin_a * (size * 0.5), sy - cos_a * (size * 0.5)),
                ]
                pygame.draw.polygon(surface, (r, g, b), points)

        # Draw floating texts
        for ft in self.floating_texts:
            fade = ft["timer"] / ft["duration"]
            alpha = int(255 * fade)
            txt_surf = font.render(ft["text"], True, ft["color"])
            txt_surf.set_alpha(alpha)
            sx = int(ft["x"] - cam_x - txt_surf.get_width() // 2)
            sy = int(ft["y"] - cam_y)
            surface.blit(txt_surf, (sx, sy))


class Camera:
    """Dynamic camera with smooth target tracking, lead-ahead velocity, and screen trauma shake."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = 0.0
        self.y = 0.0
        self.trauma = 0.0
        self.shake_x = 0.0
        self.shake_y = 0.0

    def add_trauma(self, amount):
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, target_x, target_y, target_vx, target_vy, dt):
        # Lead target slightly based on speed
        lead_x = target_x + target_vx * 0.35 - self.width / 2
        lead_y = target_y + target_vy * 0.35 - self.height / 2

        # Smooth exponential lerp
        lerp_speed = 6.5
        self.x += (lead_x - self.x) * min(1.0, lerp_speed * dt)
        self.y += (lead_y - self.y) * min(1.0, lerp_speed * dt)

        # Screen shake
        if self.trauma > 0:
            shake_mag = (self.trauma ** 2) * 26.0
            self.shake_x = random.uniform(-shake_mag, shake_mag)
            self.shake_y = random.uniform(-shake_mag, shake_mag)
            self.trauma = max(0.0, self.trauma - 1.6 * dt)
        else:
            self.shake_x = 0.0
            self.shake_y = 0.0

    @property
    def render_x(self):
        return self.x + self.shake_x

    @property
    def render_y(self):
        return self.y + self.shake_y
