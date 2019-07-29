"""Classic Snake game implemented in Python.

TODO:
- settings scenes.
- win condition (max points = width*height/32/32 - 2 = 498 -> 250 points=win)
- obstacles?
- joystick support.
- online mode."""
import os

import pygame

import settings
from scenes import SceneBase, SceneMenu


def run_game(width: int, height: int, fps: int, starting_scene: SceneBase):
    """Main function that moves everything. Don't delete it."""
    pygame.mixer.pre_init(44100, -16, 2, 1024)
    os.environ['SDL_VIDEO_CENTERED'] = "1"
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    game_icon = pygame.image.load("assets/images/icon.png")
    pygame.display.set_icon(game_icon)
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    # Load data
    settings.load_config()
    settings.load_jokes()

    # Start first scene
    active_scene = starting_scene()

    while active_scene is not None:
        # Handle events
        pressed_keys = pygame.key.get_pressed()

        filtered_events = []
        for event in pygame.event.get():
            quit_attempt = False
            if event.type == pygame.QUIT:
                quit_attempt = True
            elif event.type == pygame.KEYDOWN:
                alt_pressed = (pressed_keys[pygame.K_LALT] or
                               pressed_keys[pygame.K_LALT])
                if event.key == settings.get_key("exit"):
                    quit_attempt = True
                elif event.key == pygame.K_F4 and alt_pressed:
                    quit_attempt = True

            if quit_attempt:
                active_scene.terminate()
            else:
                filtered_events.append(event)

        # Scene does its stuff
        active_scene.process_input(filtered_events, pressed_keys)
        now = pygame.time.get_ticks()
        active_scene.update(now)
        active_scene.render(screen)

        # To next scene or continue in the same
        active_scene = active_scene.next

        pygame.display.flip()
        clock.tick(fps)
        pygame.display.set_caption(f"Snake - {clock.get_fps():2.0f} fps")

if __name__ == "__main__":
    run_game(800, 640, 60, SceneMenu)
    pygame.quit()
