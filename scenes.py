"""Scenes of the Game."""
import random
import datetime
from typing import Tuple, List

import pygame
import pygame.freetype

import settings
import resources
from objects import Apple, Snake, ParaBackground, Slider
from helpers import (render_text, render_wrapped_text, get_surface,
                     build_background)
from consts import (BGCOLOR, WHITE, BLACK, APPLE_COLOR,
                    BLOCK, SPRITE_BLOCK)


class SceneBase:
    """Boiler-plate class for game scenes."""

    def __init__(self):
        self.next = self

    def process_input(self, events: List[pygame.event.EventType],
                      pressed_keys: List[bool]):
        """Boiler-plate method for processing events in game scenes."""
        print("Override!", events, pressed_keys)

    def update(self, now: int):
        """Boiler-plate method for stuff happening in game scenes."""
        print("Override!", now)

    def render(self, screen: pygame.Surface):
        """Boiler-plate method for drawing on screen in game scenes."""
        print("Override!", screen)

    def switch_to_scene(self, next_scene: "SceneBase"):
        """Boiler-plate method for switching in between game scenes."""
        pygame.mixer.music.stop()
        self.next = next_scene() if next_scene else None

    def terminate(self):
        """Boiler-plate method for closing the game."""
        self.switch_to_scene(None)


class SceneTransition(SceneBase):
    """Transition between scenes."""
    def __init__(self, next_scene):
        SceneBase.__init__(self)
        self.surface = get_surface(pygame.display.get_surface().get_size(),
                                   BLACK, 15)
        self.rect = self.surface.get_rect()
        self.running = False
        self.timer = 0
        self.when_finished = next_scene

    def process_input(self, events, pressed_keys):
        pass

    def update(self, now: int):
        # Finish transition after 1 second
        if not self.running:
            self.running = True
            self.timer = now
        if now - self.timer > 1000:
            self.switch_to_scene(self.when_finished)

    def render(self, screen: pygame.Surface):
        screen.blit(self.surface, self.rect)


class SceneExit(SceneBase):
    """Final scene aka credits."""

    def __init__(self):
        super().__init__()
        self.timer = 0
        self.started = False
        pygame.display.set_mode((480, 320), pygame.NOFRAME)

    def process_input(self, events, pressed_keys):
        pass

    def update(self, now):
        # Show message for 2,5 seconds
        if not self.started:
            self.timer = now
            self.started = True
        elif now - self.timer >= 2500:
            self.switch_to_scene(None)

    def render(self, screen):
        width, height = pygame.display.get_surface().get_size()
        screen.fill(BGCOLOR)

        font = resources.get_font("title80")
        rd_text, rd_rect = render_wrapped_text("Thanks for playing", font,
                                               WHITE, True, 10, width-50)
        rd_rect.centerx, rd_rect.centery = width//2, height//2-20
        screen.blit(rd_text, rd_rect)

        font = resources.get_font("normal30")
        rd_text, rd_rect = render_text("A game by @Alucebur", font, WHITE)
        rd_rect.x, rd_rect.y = 30, height-40
        screen.blit(rd_text, rd_rect)


class SceneGame(SceneBase):
    """Scene with snakes biting things."""

    def __init__(self):
        super().__init__()
        self.timer = 0
        self.is_paused = False
        self.has_crashed = False
        self.event_painted = False
        self.show_grid = False
        self.play_music()

        # Create background from random texture
        i = random.getrandbits(1) + 1
        self.background = build_background(resources.get_image(
            f"snake-tile{i}"))

        # Create objects snake and apple
        if not settings.get_setting("classic"):
            apple_skin, snake_skin = self.split_sprites(
                resources.get_sprite("sheet"))
        else:
            apple_skin, snake_skin = None, None
        self.sneik = Snake()
        self.sneik.load_skin(snake_skin)
        self.apple = Apple(self.sneik.body, apple_skin)

    @staticmethod
    def play_music():
        """Load and play epic music."""
        resources.load_music("snake-music-Rafael_Krux.ogg")
        pygame.mixer.music.play(-1)

    @staticmethod
    def split_sprites(sheet: pygame.Surface) -> Tuple[pygame.Surface,
                                                      pygame.Surface]:
        """Return apple and snake sprites already resized.

        Parameter sheet should contain 4x3 sprites, with the apple
        in the bottom rigth corner."""
        apple = sheet.subsurface((SPRITE_BLOCK[0] * 3, SPRITE_BLOCK[1] * 2,
                                  SPRITE_BLOCK[0], SPRITE_BLOCK[1]))
        apple = pygame.transform.scale(apple, (BLOCK[0], BLOCK[1]))
        snake = sheet
        snake = pygame.transform.scale(snake, (BLOCK[0]*4, BLOCK[1]*3))
        return apple, snake

    def pause(self):
        """Pause game."""
        pygame.mixer.music.pause()
        self.is_paused = True
        self.event_painted = False

    def unpause(self):
        """Unpause game."""
        pygame.mixer.music.unpause()
        self.is_paused = False

    @staticmethod
    def draw_grid(screen: pygame.Surface):
        """Draw grid on screen, BLOCK sized rectangles."""
        width, height = pygame.display.get_surface().get_size()
        # Vertical lines
        for i in range(width//BLOCK[0]):
            pygame.draw.line(screen, WHITE,
                             (i * BLOCK[0], 0), (i * BLOCK[0], height), 1)
        # Horizontal lines
        for i in range(height//BLOCK[1]):
            pygame.draw.line(screen, WHITE,
                             (0, i * BLOCK[1]), (width, i * BLOCK[1]), 1)

    def process_input(self, events, pressed_keys):
        for event in events:
            if not self.has_crashed:
                if self.is_paused:
                    if (event.type == pygame.KEYDOWN and
                            event.key == settings.get_key("pause")):
                        self.unpause()
                else:
                    if event.type == pygame.KEYDOWN:
                        # Snake control, add new direction to queue
                        if event.key in settings.get_key("direction"):
                            self.sneik.queue_direction(
                                event, settings.get_key("direction"))

                        # UI control
                        elif event.key == settings.get_key("grid"):
                            self.show_grid = not self.show_grid
                        elif event.key == settings.get_key("pause"):
                            self.pause()

    def update(self, now):
        if not self.is_paused and not self.has_crashed:
            # Move snake
            self.sneik.move(now)

            # Check if snake ate apple
            if self.sneik.get_head() == self.apple.pos:
                resources.get_sound("eat").stop()
                resources.get_sound("eat").play()
                self.sneik.growing = True
                self.apple.new(self.sneik.body)

            # Check if snake crashed
            if self.sneik.check_collision():
                resources.get_sound("crash").play()
                self.has_crashed = True
                self.event_painted = False
                self.timer = now
                pygame.mixer.music.stop()

        # Wait for 3 seconds from crash then switch to gameover scene
        elif self.has_crashed and now - self.timer > 3000:
            score = len(self.sneik.body) - 2
            self.switch_to_scene(lambda: SceneGameOver(score))

    def render(self, screen):
        width, height = pygame.display.get_surface().get_size()
        if not self.is_paused and (not self.has_crashed or
                                   (self.has_crashed and
                                    not self.event_painted)):
            # Draw background
            if not settings.get_setting("classic"):
                screen.blit(self.background, (0, 0))
            else:
                # Classic look
                screen.fill(BGCOLOR)

            # Draw snake, apple, grid
            self.sneik.draw(screen)
            self.apple.draw(screen)
            if self.show_grid:
                self.draw_grid(screen)

            if self.has_crashed:
                self.event_painted = True

        elif self.has_crashed:
            # Add snake blood
            self.sneik.draw_blood(screen)

        # Paint pause screen once
        elif not self.event_painted:
            # Darken the screen
            surf = get_surface((width, height), BLACK, 160)
            screen.blit(surf, (0, 0))

            # Show pause message
            font = resources.get_font("title100")
            text_surf, text_rect = render_text("Paused", font, WHITE)
            text_rect.center = width//2, 250
            screen.blit(text_surf, text_rect)

            font = resources.get_font("round30")
            text_surf, text_rect = render_text(
                f"Score: {len(self.sneik.body) - 2}", font, WHITE)
            text_rect.center = width//2, 330
            screen.blit(text_surf, text_rect)
            self.event_painted = True


class SceneGameOver(SceneBase):
    """Game over scene."""

    def __init__(self, score):
        super().__init__()
        self.score = score
        self.record = (self.score > settings.lower_highscore())
        self.initials = ""
        self.joke = settings.get_joke()

    def process_input(self, events: List[pygame.event.EventType],
                      pressed_keys: List[bool]):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if not self.record:
                    if event.key == settings.get_key("accept"):
                        # Replay
                        self.switch_to_scene(SceneGame)
                    elif event.key == settings.get_key("pause"):
                        # To menu
                        self.switch_to_scene(SceneMenu)
                else:
                    if event.key == settings.get_key("accept"):
                        # confirm entered text
                        self.add_highscore()
                        self.record = False
                    elif event.key == pygame.K_BACKSPACE:
                        # delete letter
                        self.initials = self.initials[:-1]
                    elif len(self.initials) < 3 and event.unicode.isalnum():
                        # write letter
                        self.initials += event.unicode.upper()

    def update(self, now: int):
        pass

    def add_highscore(self):
        """Adds highscore to data and file."""
        date = str(datetime.date.today())
        new_highscore = {"name": self.initials,
                         "score": self.score,
                         "date": date}

        top = settings.get_highscores()
        top.append(new_highscore)
        # Highscore list is sorted by score (desc) and date (asc)
        top.sort(key=lambda x: (-x['score'], x['date']))
        if len(top) > 5:
            top.pop()

        # Save to file
        settings.save_config()

    def render(self, screen: pygame.Surface):
        width, height = pygame.display.get_surface().get_size()

        # Display gameover message
        screen.fill(BGCOLOR)
        text_surf, text_rect = render_text("YOU LOST",
                                           resources.get_font("title100"),
                                           WHITE)
        text_rect.centerx, text_rect.y = width//2, 110
        screen.blit(text_surf, text_rect)

        text_surf, text_rect = render_text(f"Your score was {self.score}",
                                           resources.get_font("round30"),
                                           WHITE)
        text_rect.centerx, text_rect.y = width//2, 270
        screen.blit(text_surf, text_rect)

        if not self.record:
            accept = pygame.key.name(settings.get_key("accept"))
            finish = pygame.key.name(settings.get_key("pause"))
            text = (f"({accept.upper()} to replay,"
                    f" {finish.upper()} to exit menu)")
            text_surf, text_rect = render_text(text,
                                               resources.get_font("round30"),
                                               WHITE)
            text_rect.centerx, text_rect.y = width//2, 325
            screen.blit(text_surf, text_rect)
        else:
            # Highscore message
            text_surf, text_rect = render_text("New record!",
                                               resources.get_font("round30"),
                                               WHITE)
            text_rect.centerx, text_rect.y = width//2, 345
            screen.blit(text_surf, text_rect)

            text_surf, text_rect = render_text("Enter your initials: ",
                                               resources.get_font("round30"),
                                               WHITE)
            text_rect.centerx, text_rect.y = width//2-58, 420
            screen.blit(text_surf, text_rect)

            # Textbox
            input_box = pygame.Rect(width//2+82, 415, 100, 35)
            screen.fill(BLACK, input_box)
            resources.get_font("round30").render_to(
                screen, (input_box.x+15, input_box.y+5), self.initials, WHITE)

        # Pun
        text_surf, text_rect = render_wrapped_text(
            self.joke, resources.get_font("normal25"), WHITE, True,
            10, width-150)
        text_rect.centerx, text_rect.y = width//2, height-130
        screen.blit(text_surf, text_rect)


class SceneSettings(SceneBase):
    """Settings scene."""

    def __init__(self):
        super().__init__()
        self.index = 0
        self.sound = settings.get_setting("sound")
        self.music = settings.get_setting("music")
        self.classic = settings.get_setting("classic")
        self.options = ["Sound Effects", "Music", "Graphics",
                        "Change Controls", "Save and Return to Main Menu"]

        # Create sliders
        self.sound_slider = Slider(self.sound, 250)
        self.music_slider = Slider(self.music, 250)

    def process_input(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Select option
                if event.key == settings.get_key("up"):
                    self.index = (len(self.options)-1 if self.index == 0
                                  else self.index-1)
                    resources.get_sound("menu-sel").stop()
                    resources.get_sound("menu-sel").play()
                elif event.key == settings.get_key("down"):
                    self.index = (0 if self.index == len(self.options)-1
                                  else self.index+1)
                    resources.get_sound("menu-sel").stop()
                    resources.get_sound("menu-sel").play()

                # Modify option
                elif event.key == settings.get_key("left"):
                    if self.index == 0:
                        self.sound -= (0.1 if self.sound >= 0.1 else 0)
                        self.test_volume(self.sound)
                    elif self.index == 1:
                        self.music -= (0.1 if self.music >= 0.1 else 0)
                        self.test_volume(self.music)
                    elif self.index == 2:
                        resources.get_sound("menu-sel").stop()
                        resources.get_sound("menu-sel").play()
                        self.classic = not self.classic

                elif event.key == settings.get_key("right"):
                    if self.index == 0:
                        self.sound += (0.1 if self.sound <= 0.9 else 0)
                        self.test_volume(self.sound)
                    elif self.index == 1:
                        self.music += (0.1 if self.music <= 0.9 else 0)
                        self.test_volume(self.music)
                    elif self.index == 2:
                        resources.get_sound("menu-sel").stop()
                        resources.get_sound("menu-sel").play()
                        self.classic = not self.classic

                elif (event.key == settings.get_key("accept") and
                      2 < self.index < 5):
                    resources.get_sound("menu-accept").stop()
                    resources.get_sound("menu-accept").play()
                    # Change controls
                    if self.index == 3:
                        self.switch_to_scene(SceneSettingsControls)

                    # Return to Main Menu
                    elif self.index == 4:
                        self.save_config()
                        self.switch_to_scene(SceneMenu)

    def test_volume(self, option: float):
        """Play a sound at the given volume.."""
        test_audio = resources.get_sound("eat")
        test_audio.stop()
        test_audio.set_volume(option)
        test_audio.play()

    def save_config(self):
        """Apply and save new settings."""
        settings.set_settings("sound", round(self.sound, 1))
        settings.set_settings("music", round(self.music, 1))
        settings.set_settings("classic", self.classic)
        settings.save_config()

        # Set volumes
        resources.set_volume(settings.get_setting("sound"))
        pygame.mixer.music.set_volume(settings.get_setting("music"))

    def update(self, now: int):
        pass

    def render(self, screen: pygame.Surface):
        width = pygame.display.get_surface().get_width()
        screen.fill(BGCOLOR)

        font = resources.get_font("round50")
        text_surf, text_rect = render_text("Settings", font, WHITE)
        text_rect.centerx, text_rect.y = width//2, 50
        screen.blit(text_surf, text_rect)

        pos_y = 180
        for i, option in enumerate(self.options):
            # leave more space for last option
            if i == len(self.options) - 1:
                pos_y += 60

            if i == self.index:
                # Selected
                color = APPLE_COLOR
                font = resources.get_font("round40")
            else:
                # Inactive
                color = WHITE
                font = resources.get_font("round30")

            text_surf, text_rect = render_text(option, font, color)
            text_rect.x, text_rect.y = (150, pos_y+60*i)
            screen.blit(text_surf, text_rect)

        # Sound slider
        self.sound_slider.percent = self.sound
        self.sound_slider.rect.x = 450
        self.sound_slider.rect.y = 180
        if self.index == 0:
            self.sound_slider.color = APPLE_COLOR
        else:
            self.sound_slider.color = BGCOLOR
        self.sound_slider.draw(screen)

        # Music slider
        self.music_slider.percent = self.music
        self.music_slider.rect.x = 450
        self.music_slider.rect.y = 240
        if self.index == 1:
            self.music_slider.color = APPLE_COLOR
        else:
            self.music_slider.color = BGCOLOR
        self.music_slider.draw(screen)

        # Graphics
        font = resources.get_font("round30")
        if self.classic:
            text_surf, text_rect = render_text("Classic /", font, APPLE_COLOR)
            text_rect.x, text_rect.y = 465, 300
        else:
            text_surf, text_rect = render_text("/ Modern", font, APPLE_COLOR)
            text_rect.x, text_rect.y = 564, 300
        screen.blit(text_surf, text_rect)


class SceneSettingsControls(SceneBase):  # TODO
    """Change controls scene."""

    def __init__(self):
        super().__init__()

    def process_input(self, events, pressed_keys):
        pass

    def update(self, now: int):
        pass

    def render(self, screen: pygame.Surface):
        pass


class SceneHighScores(SceneBase):
    """Highscores scene."""

    def __init__(self):
        super().__init__()

    def process_input(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == settings.get_key("accept"):
                    resources.get_sound("menu-accept").stop()
                    resources.get_sound("menu-accept").play()
                    self.switch_to_scene(SceneMenu)

    def update(self, now: int):
        pass

    def render(self, screen: pygame.Surface):
        width, height = pygame.display.get_surface().get_size()

        screen.fill(BGCOLOR)

        text_surf, text_rect = render_text(f"Highscores",
                                           resources.get_font("round50"),
                                           WHITE)
        text_rect.centerx, text_rect.y = width//2, 50
        screen.blit(text_surf, text_rect)

        # Display highscore list
        highscores = settings.get_highscores()
        for i, highscore in enumerate(highscores):
            color = (200 - i*30, 200 - i*20, 200 - i*30)
            text = (f"{i+1} ___ {highscore['name']:>3} _____ "
                    f"{highscore['score']:3} _____ {highscore['date']} ")
            text_surf, text_rect = render_text(
                text, resources.get_font("mono30"), color)
            text_rect.x, text_rect.y = 75, 150+i*50
            screen.blit(text_surf, text_rect)

        text = "Return to Main Menu"
        text_surf, text_rect = render_text(text, resources.get_font("round40"),
                                           APPLE_COLOR)
        text_rect.centerx, text_rect.y = width//2, height - 120
        screen.blit(text_surf, text_rect)


class SceneMenu(SceneBase):
    """Scene index of scenes."""

    def __init__(self):
        super().__init__()
        self.options = [("Play", lambda: SceneTransition(SceneGame)),
                        ("Settings", lambda: SceneTransition(SceneSettings)),
                        ("Highscores",
                         lambda: SceneTransition(SceneHighScores)),
                        ("Quit", SceneExit)]
        self.selected = False
        self.index = 0
        self.play_music()
        i = random.getrandbits(1) + 1
        i = 1
        self.background = ParaBackground(resources.get_image(f"menu-bg{i}"),
                                         resources.get_image(f"menu-bg{i}b"))

    @staticmethod
    def play_music():
        """Play annoying music."""
        resources.load_music("menu-music.ogg")
        pygame.mixer.music.play(-1)

    def process_input(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == settings.get_key("up"):
                    self.index = (len(self.options)-1 if self.index == 0
                                  else self.index-1)
                    resources.get_sound("menu-sel").stop()
                    resources.get_sound("menu-sel").play()
                elif event.key == settings.get_key("down"):
                    self.index = (0 if self.index == len(self.options)-1
                                  else self.index+1)
                    resources.get_sound("menu-sel").stop()
                    resources.get_sound("menu-sel").play()
                elif event.key == settings.get_key("accept"):
                    resources.get_sound("menu-accept").stop()
                    resources.get_sound("menu-accept").play()
                    self.selected = True

    def update(self, now):
        # Wait for sound to stop playing
        if self.selected and not pygame.mixer.get_busy():
            self.switch_to_scene(self.options[self.index][1])
        else:
            # Move background according to its speed
            if now - self.background.timer >= 1000.0/self.background.vel:
                self.background.timer = now
                self.background.move()

    def render(self, screen):
        width = pygame.display.get_surface().get_width()
        screen.fill(BGCOLOR)

        # Draw background
        self.background.draw(screen)

        # Semitransparent surface behind title
        overlay = get_surface((width, 140), WHITE, 120)
        overlay_rect = overlay.get_rect()
        overlay_rect.centerx, overlay_rect.y = width//2, 50
        screen.blit(overlay, overlay_rect)

        # Title
        font = resources.get_font("title175")
        rd_text, rd_rect = render_text("SNAKE", font, BLACK)
        rd_rect.centerx, rd_rect.y = width//2, 60
        screen.blit(rd_text, rd_rect)

        pos_y = 280
        # Semitransparent surface behind selected option
        overlay = get_surface((width, 50), BLACK, 150)
        overlay_rect = overlay.get_rect()
        overlay_rect.centerx = width//2
        overlay_rect.centery = pos_y + 60 * self.index + 60 * (
            self.index == len(self.options) - 1)
        screen.blit(overlay, overlay_rect)

        for i, option in enumerate(self.options):
            # leave more space for last option 'Quit'
            if i == len(self.options) - 1:
                pos_y += 60

            if i == self.index:
                # Selected
                color = APPLE_COLOR
                font = resources.get_font("round50")
            else:
                # Inactive
                color = BLACK
                font = resources.get_font("round40")

            rd_text, rd_rect = render_text(option[0], font, color)
            rd_rect.centerx, rd_rect.centery = (width//2, pos_y+60*i)
            screen.blit(rd_text, rd_rect)
