"""
main.py - Application entry point for CHROMA-STRAND: HARMONIC VOID.
An Acoustic-Kinetic Celestial Weaving Odyssey.
"""

import sys
import pygame
from audio_synth import SoundEngine
from game import GameEngine

def main():
    pygame.init()
    pygame.font.init()

    # Window setup
    WINDOW_W = 1280
    WINDOW_H = 720
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
    pygame.display.set_caption("CHROMA-STRAND: HARMONIC VOID")

    # App icon setup (generate procedural celestial icon)
    try:
        icon_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(icon_surf, (0, 240, 255), (16, 16), 14)
        pygame.draw.circle(icon_surf, (255, 255, 255), (16, 16), 6)
        pygame.display.set_icon(icon_surf)
    except Exception:
        pass

    clock = pygame.time.Clock()
    sound_engine = SoundEngine()
    game = GameEngine(WINDOW_W, WINDOW_H)

    # Start ambient celestial soundtrack
    sound_engine.start_music()

    is_fullscreen = False
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        dt = min(0.05, dt) # Clamp dt to prevent physics tunneling on hitch

        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                WINDOW_W, WINDOW_H = event.w, event.h
                screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
                game.width = WINDOW_W
                game.height = WINDOW_H
                game.hud.width = WINDOW_W
                game.hud.height = WINDOW_H
                game.camera.width = WINDOW_W
                game.camera.height = WINDOW_H

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
                    w, h = screen.get_size()
                    game.width, game.height = w, h
                    game.hud.width, game.hud.height = w, h
                    game.camera.width, game.camera.height = w, h

                elif event.key == pygame.K_m:
                    sound_engine.toggle_mute()

                elif event.key == pygame.K_ESCAPE:
                    if game.state == "TUTORIAL":
                        game.state = "MENU"
                    elif game.state == "PLAYING":
                        game.state = "MENU"
                    elif game.state == "GAMEOVER":
                        game.state = "MENU"
                    elif game.state == "MENU":
                        running = False

                elif event.key == pygame.K_r:
                    if game.state == "GAMEOVER":
                        game.reset_game()
                        game.state = "PLAYING"

                else:
                    game.handle_key_down(event.key, sound_engine)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game.state == "MENU":
                    clicked_action = game.hud.get_menu_button_at(event.pos)
                    if clicked_action == "start":
                        game.reset_game()
                        game.state = "PLAYING"
                    elif clicked_action == "tutorial":
                        game.state = "TUTORIAL"
                    elif clicked_action == "exit":
                        running = False
                elif game.state == "TUTORIAL":
                    game.state = "MENU"
                elif game.state == "GAMEOVER":
                    game.reset_game()
                    game.state = "PLAYING"
                elif game.state == "PLAYING":
                    game.handle_mouse_down(event.pos, event.button, sound_engine)

            elif event.type == pygame.MOUSEBUTTONUP:
                if game.state == "PLAYING":
                    game.handle_mouse_up(event.pos, event.button, sound_engine)

        # Update game
        game.update(keys, mouse_pos, dt, sound_engine)

        # Render frame
        game.render(screen)
        pygame.display.flip()

    sound_engine.stop_music()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
