"""
ui.py - Futuristic HUD, Celestial Minimap, Interactive Menus,
and Tutorial Overlays for Chroma-Strand.
"""

import math
import pygame
from visuals import (
    COLOR_CYAN, COLOR_MAGENTA, COLOR_GOLD, COLOR_WHITE,
    COLOR_CRIMSON, COLOR_VIOLET, COLOR_EMERALD, GlowCache
)

class HUD:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font_large = pygame.font.SysFont("segoeui, arial, helvetica", 32, bold=True)
        self.font_med = pygame.font.SysFont("segoeui, arial, helvetica", 20, bold=True)
        self.font_small = pygame.font.SysFont("segoeui, arial, helvetica", 14)
        self.font_title = pygame.font.SysFont("segoeui, arial, helvetica", 54, bold=True)
        self.combo_pulse = 0.0

    def trigger_combo_pulse(self):
        self.combo_pulse = 1.0

    def update(self, dt):
        if self.combo_pulse > 0:
            self.combo_pulse = max(0.0, self.combo_pulse - 3.0 * dt)

    def draw_game_hud(self, surface, player, score, combo, wave, boss, hint_text=""):
        # --- 1. Health Bar (Top Left) ---
        bar_x = 24
        bar_y = 24
        bar_w = 220
        bar_h = 16

        # Outer box
        pygame.draw.rect(surface, (20, 25, 45), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        health_pct = max(0.0, player.health / player.max_health)
        h_color = COLOR_CYAN if health_pct > 0.35 else COLOR_CRIMSON
        if health_pct > 0:
            pygame.draw.rect(surface, h_color, (bar_x, bar_y, int(bar_w * health_pct), bar_h), border_radius=4)
        pygame.draw.rect(surface, COLOR_WHITE, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)

        lbl_hp = self.font_small.render(f"HULL INTEGRITY  {int(player.health)}%", True, COLOR_WHITE)
        surface.blit(lbl_hp, (bar_x, bar_y - 18))

        # --- 2. Resonance / Supernova Bar ---
        sn_y = bar_y + 36
        pygame.draw.rect(surface, (20, 25, 45), (bar_x, sn_y, bar_w, bar_h), border_radius=4)
        sn_pct = max(0.0, min(1.0, player.resonance_energy / 100.0))
        sn_color = COLOR_GOLD
        if sn_pct > 0:
            pygame.draw.rect(surface, sn_color, (bar_x, sn_y, int(bar_w * sn_pct), bar_h), border_radius=4)
        pygame.draw.rect(surface, COLOR_WHITE, (bar_x, sn_y, bar_w, bar_h), 1, border_radius=4)

        if player.supernova_active:
            lbl_sn = self.font_small.render(f"SUPERNOVA ACTIVE! ({player.supernova_timer:.1f}s)", True, COLOR_GOLD)
        elif sn_pct >= 1.0:
            lbl_sn = self.font_small.render("SUPERNOVA READY! [PRESS F]", True, COLOR_GOLD)
        else:
            lbl_sn = self.font_small.render(f"RESONANCE HARMONY  {int(player.resonance_energy)}%", True, (180, 200, 240))
        surface.blit(lbl_sn, (bar_x, sn_y - 18))

        # --- 3. Score & Combo Multiplier (Top Right) ---
        score_surf = self.font_large.render(f"{score:,}", True, COLOR_WHITE)
        surface.blit(score_surf, (self.width - score_surf.get_width() - 24, 20))
        lbl_sc = self.font_small.render("HARMONIC RESONANCE SCORE", True, (140, 160, 200))
        surface.blit(lbl_sc, (self.width - lbl_sc.get_width() - 24, 60))

        if combo > 1:
            scale_pulse = 1.0 + self.combo_pulse * 0.4
            combo_surf = self.font_med.render(f"x{combo} HARMONY COMBO!", True, COLOR_GOLD)
            surface.blit(combo_surf, (self.width - combo_surf.get_width() - 24, 82))

        # --- 4. Wave Indicator (Top Center) ---
        wave_str = f"HARMONIC FREQUENCY: WAVE {wave}" if not boss else "ANOMALY SINGULARITY CORE"
        wave_surf = self.font_med.render(wave_str, True, COLOR_CYAN if not boss else COLOR_MAGENTA)
        surface.blit(wave_surf, (self.width // 2 - wave_surf.get_width() // 2, 20))

        if boss:
            # Boss Health Bar
            boss_w = 400
            boss_h = 12
            boss_x = self.width // 2 - boss_w // 2
            boss_y = 52
            pygame.draw.rect(surface, (20, 20, 40), (boss_x, boss_y, boss_w, boss_h), border_radius=3)
            b_pct = max(0.0, boss.health / boss.max_health)
            pygame.draw.rect(surface, COLOR_MAGENTA, (boss_x, boss_y, int(boss_w * b_pct), boss_h), border_radius=3)
            pygame.draw.rect(surface, COLOR_WHITE, (boss_x, boss_y, boss_w, boss_h), 1, border_radius=3)

        # --- 5. Interactive Tutorial / Hint Box (Bottom Center) ---
        if hint_text:
            hint_surf = self.font_med.render(hint_text, True, COLOR_WHITE)
            box_w = hint_surf.get_width() + 40
            box_h = 44
            box_x = self.width // 2 - box_w // 2
            box_y = self.height - 72

            bg_s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            pygame.draw.rect(bg_s, (10, 15, 35, 210), (0, 0, box_w, box_h), border_radius=8)
            pygame.draw.rect(bg_s, (*COLOR_CYAN[:3], 180), (0, 0, box_w, box_h), 2, border_radius=8)
            surface.blit(bg_s, (box_x, box_y))
            surface.blit(hint_surf, (box_x + 20, box_y + 10))

    def draw_audio_visualizer(self, surface, time_sec, combo):
        """12-band reactive frequency equalizer on the HUD."""
        vis_x = self.width - 160
        vis_y = self.height - 42
        bar_w = 7
        gap = 3

        for i in range(12):
            freq = (i + 1) * 1.3
            height_mod = math.sin(time_sec * 3.5 + i * 0.5) * 0.4 + math.cos(time_sec * 5.2 - i * 0.3) * 0.3 + 0.5
            bar_h = max(4, int(height_mod * 24 * (1.0 + combo * 0.15)))
            bx = vis_x + i * (bar_w + gap)
            by = vis_y - bar_h

            color = COLOR_GOLD if i % 3 == 0 else (COLOR_CYAN if i % 2 == 0 else COLOR_MAGENTA)
            pygame.draw.rect(surface, color, (bx, by, bar_w, bar_h), border_radius=2)
            pygame.draw.rect(surface, COLOR_WHITE, (bx, by, bar_w, 2), border_radius=1)

        lbl = self.font_small.render("ACOUSTIC SPECTRUM", True, (120, 140, 180))
        surface.blit(lbl, (vis_x - 10, vis_y + 8))

    def draw_crosshair(self, surface, mouse_pos, time_sec):
        mx, my = mouse_pos
        ang = time_sec * 2.0
        r = 12
        # Rotating reticle ticks
        for i in range(4):
            a = ang + i * (math.pi / 2)
            p1 = (mx + math.cos(a) * (r - 3), my + math.sin(a) * (r - 3))
            p2 = (mx + math.cos(a) * (r + 4), my + math.sin(a) * (r + 4))
            pygame.draw.line(surface, COLOR_CYAN, p1, p2, 1)
        pygame.draw.circle(surface, COLOR_WHITE, (mx, my), 2)

    def draw_minimap(self, surface, player, anchors, enemies, arena_size=3600):
        """Mini radar at bottom-left corner showing tactical cosmic overview."""
        map_size = 130
        map_x = 24
        map_y = self.height - map_size - 24

        # Background panel
        radar_s = pygame.Surface((map_size, map_size), pygame.SRCALPHA)
        pygame.draw.rect(radar_s, (10, 15, 30, 200), (0, 0, map_size, map_size), border_radius=6)
        pygame.draw.rect(radar_s, (*COLOR_CYAN[:3], 120), (0, 0, map_size, map_size), 1, border_radius=6)

        scale = map_size / arena_size
        center = map_size // 2

        # Draw anchors
        for a in anchors:
            mx = int(center + a.x * scale)
            my = int(center + a.y * scale)
            if 0 <= mx < map_size and 0 <= my < map_size:
                pygame.draw.circle(radar_s, a.base_color, (mx, my), 2)

        # Draw enemies
        for e in enemies:
            mx = int(center + e.x * scale)
            my = int(center + e.y * scale)
            if 0 <= mx < map_size and 0 <= my < map_size:
                pygame.draw.circle(radar_s, COLOR_CRIMSON, (mx, my), 1)

        # Draw player
        px = int(center + player.x * scale)
        py = int(center + player.y * scale)
        if 0 <= px < map_size and 0 <= py < map_size:
            pygame.draw.circle(radar_s, COLOR_GOLD, (px, py), 3)

        surface.blit(radar_s, (map_x, map_y))

    def get_menu_button_at(self, mouse_pos):
        w, h = self.width, self.height
        btn_w, btn_h = 260, 52
        buttons = [
            ("BEGIN WEAVING", h // 2 - 10, "start"),
            ("HOW TO PLAY", h // 2 + 56, "tutorial"),
            ("EXIT TO DESKTOP", h // 2 + 122, "exit")
        ]
        for _, btn_y, action in buttons:
            btn_x = w // 2 - btn_w // 2
            if btn_x <= mouse_pos[0] <= btn_x + btn_w and btn_y <= mouse_pos[1] <= btn_y + btn_h:
                return action
        return None

    def draw_main_menu(self, surface, mouse_pos):
        w, h = self.width, self.height
        # Title Glow
        title_txt = "CHROMA-STRAND"
        sub_txt = "RESONANCE OF THE CELESTIAL STRINGS"
        desc_txt = "Acoustic-Kinetic Celestial Weaving Odyssey"

        t_surf = self.font_title.render(title_txt, True, COLOR_CYAN)
        sub_surf = self.font_med.render(sub_txt, True, COLOR_GOLD)
        desc_surf = self.font_small.render(desc_txt, True, (180, 200, 240))

        surface.blit(t_surf, (w // 2 - t_surf.get_width() // 2, h // 2 - 170))
        surface.blit(sub_surf, (w // 2 - sub_surf.get_width() // 2, h // 2 - 105))
        surface.blit(desc_surf, (w // 2 - desc_surf.get_width() // 2, h // 2 - 75))

        # Buttons
        btn_w, btn_h = 260, 52
        buttons = [
            ("BEGIN WEAVING", h // 2 - 10, "start"),
            ("HOW TO PLAY", h // 2 + 56, "tutorial"),
            ("EXIT TO DESKTOP", h // 2 + 122, "exit")
        ]

        hovered_action = None
        for text, btn_y, action in buttons:
            btn_x = w // 2 - btn_w // 2
            is_hover = (btn_x <= mouse_pos[0] <= btn_x + btn_w and btn_y <= mouse_pos[1] <= btn_y + btn_h)
            if is_hover:
                hovered_action = action

            col = COLOR_CYAN if is_hover else (40, 60, 100)
            fill_col = (20, 35, 70, 220) if is_hover else (12, 18, 38, 200)

            btn_s = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            pygame.draw.rect(btn_s, fill_col, (0, 0, btn_w, btn_h), border_radius=8)
            pygame.draw.rect(btn_s, col, (0, 0, btn_w, btn_h), 2 if not is_hover else 3, border_radius=8)
            surface.blit(btn_s, (btn_x, btn_y))

            txt_col = COLOR_WHITE if is_hover else (190, 210, 240)
            b_txt = self.font_med.render(text, True, txt_col)
            surface.blit(b_txt, (btn_x + btn_w // 2 - b_txt.get_width() // 2, btn_y + btn_h // 2 - b_txt.get_height() // 2))

        # Footer
        footer = self.font_small.render("[M] Toggle Music  |  [N] Toggle SFX  |  [F11] Fullscreen", True, (120, 140, 170))
        surface.blit(footer, (w // 2 - footer.get_width() // 2, h - 36))

        return hovered_action

    def draw_instructions_modal(self, surface):
        w, h = self.width, self.height
        modal_w, modal_h = 760, 500
        modal_x = w // 2 - modal_w // 2
        modal_y = h // 2 - modal_h // 2

        modal_s = pygame.Surface((modal_w, modal_h), pygame.SRCALPHA)
        pygame.draw.rect(modal_s, (10, 14, 30, 245), (0, 0, modal_w, modal_h), border_radius=12)
        pygame.draw.rect(modal_s, (*COLOR_CYAN[:3], 200), (0, 0, modal_w, modal_h), 2, border_radius=12)
        surface.blit(modal_s, (modal_x, modal_y))

        title = self.font_large.render("HARMONIC WEAVING MECHANICS", True, COLOR_CYAN)
        surface.blit(title, (modal_x + modal_w // 2 - title.get_width() // 2, modal_y + 24))

        instructions = [
            ("1. FLIGHT & TETHERING", "Fly Lumina with WASD or Arrows. Click or drag between Anchors to weave acoustic strings."),
            ("2. KINETIC SLINGSBOMB", "Click an Anchor to tether Lumina. Pull back like a bowstring & RELEASE or press SPACEBAR to slingshot!"),
            ("3. HARMONIC CLEAVE", "Slingshotting puts Lumina into hyper-resonance, allowing you to slice & shatter Void Entities."),
            ("4. ACOUSTIC PLUCKING", "Flying through strings plucks celestial notes and emits radial shockwaves that stun swarms."),
            ("5. RESONANCE ENCLOSURES", "Connect 3+ Anchors into a closed polygon. Trapped Void Entities instantly combust into Star Motes!"),
            ("6. OVERDRIVE SUPERNOVA", "Collect golden Star Motes to fill the Resonance meter. Press [F] for screen-clearing invulnerability!")
        ]

        curr_y = modal_y + 75
        for header, body in instructions:
            h_surf = self.font_med.render(header, True, COLOR_GOLD)
            surface.blit(h_surf, (modal_x + 36, curr_y))
            b_surf = self.font_small.render(body, True, (210, 225, 255))
            surface.blit(b_surf, (modal_x + 36, curr_y + 24))
            curr_y += 58

        close_hint = self.font_med.render("[ CLICK ANYWHERE OR PRESS ESC TO RETURN ]", True, COLOR_CYAN)
        surface.blit(close_hint, (modal_x + modal_w // 2 - close_hint.get_width() // 2, modal_y + modal_h - 44))

    def draw_game_over(self, surface, score, high_score, wave, stats):
        w, h = self.width, self.height
        over_s = pygame.Surface((w, h), pygame.SRCALPHA)
        over_s.fill((6, 8, 18, 225))
        surface.blit(over_s, (0, 0))

        title = self.font_title.render("RESONANCE FRACTURED", True, COLOR_CRIMSON)
        surface.blit(title, (w // 2 - title.get_width() // 2, h // 2 - 160))

        score_txt = self.font_large.render(f"Final Score: {score:,}", True, COLOR_GOLD)
        surface.blit(score_txt, (w // 2 - score_txt.get_width() // 2, h // 2 - 95))

        if score >= high_score and score > 0:
            hs_txt = self.font_med.render("★ NEW COSMIC HIGH SCORE! ★", True, COLOR_EMERALD)
        else:
            hs_txt = self.font_med.render(f"High Score: {high_score:,}", True, (160, 180, 220))
        surface.blit(hs_txt, (w // 2 - hs_txt.get_width() // 2, h // 2 - 58))

        # Stats Breakdown
        stats_lines = [
            f"Wave Reached: {wave}",
            f"Strings Plucked: {stats.get('plucks', 0)}",
            f"Void Entities Cleaved: {stats.get('kills', 0)}",
            f"Resonance Fields Formed: {stats.get('fields', 0)}",
            f"Maximum Harmony Combo: x{stats.get('max_combo', 1)}"
        ]
        stat_y = h // 2 - 12
        for line in stats_lines:
            st = self.font_small.render(line, True, (200, 215, 245))
            surface.blit(st, (w // 2 - st.get_width() // 2, stat_y))
            stat_y += 24

        restart_txt = self.font_med.render("PRESS [R] TO REWEAVE THE STRANDS  |  [ESC] FOR MAIN MENU", True, COLOR_CYAN)
        surface.blit(restart_txt, (w // 2 - restart_txt.get_width() // 2, h // 2 + 130))
