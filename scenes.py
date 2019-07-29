"""Scenes of the Game."""
import random
import datetime
from typing import Tuple, List

import pygame
import pygame.freetype

import settings
import resources
from objects import Apple, Snake, ParaBackground
from helpers import render_text, render_wrapped_text, get_surface
from consts import BGCOLOR, WHITE, BLACK, APPLE_COLOR, BLOCK, SPRITE_BLOCK


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
        self.load_assets()
        pygame.display.set_mode((480, 320), pygame.NOFRAME)

    @staticmethod
    def load_assets():
        """Load stuff that we will need later."""
        resources.load_font("HanSrf.ttf", 30, "mini")
        resources.load_font("Jacked.ttf", 80, "big")

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

        font = resources.get_font("big")
        rd_text, rd_rect = render_wrapped_text("Thanks for playing", font,
                                               WHITE, True, 10, width-50)
        rd_rect.centerx, rd_rect.centery = width//2, height//2-20
        screen.blit(rd_text, rd_rect)

        font = resources.get_font("mini")
        rd_text, rd_rect = render_text("A game by @Alucebur", font, WHITE)
        rd_rect.x, rd_rect.y = 30, height-40
        screen.blit(rd_text, rd_rect)


class SceneGame(SceneBase):
    """Scene with snakes biting things."""

    def __init__(self):
        super().__init__()
        self.load_assets()
        self.timer = 0
        self.is_paused = False
        self.has_crashed = False
        self.event_painted = False
        self.show_grid = False

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
    def load_assets():
        """Load stuff that we will need later and play epic music."""
        resources.load_font("HanSrf.ttf", 25, "mini")
        resources.load_font("Excalibur Nouveau.ttf", 30, "small")
        resources.load_font("Jacked.ttf", 100, "big")

        resources.load_image("bg-game1.png", "snake-bg")

        # Don't load sprites if classic mode is selected
        if not settings.get_setting("classic"):
            resources.load_sprite("snake-sprites.png", "sheet")

        resources.load_sound("snake-bite.wav", "eat")
        resources.load_sound("snake-crash.wav", "crash")
        resources.load_sound("menu-select.wav", "menu-select")
        resources.set_volume(settings.get_setting("sound"))

        pygame.mixer.music.load("assets/audio/snake-music-Rafael_Krux.ogg")
        pygame.mixer.music.set_volume(settings.get_setting("music"))
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
                screen.blit(resources.get_image("snake-bg"), (0, 0))
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
            font = resources.get_font("big")
            text_surf, text_rect = render_text("Paused", font, WHITE)
            text_rect.center = width//2, 250
            screen.blit(text_surf, text_rect)

            font = resources.get_font("small")
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
        self.load_assets()
        self.joke = settings.get_joke()

    @staticmethod
    def load_assets():
        """Load stuff that we will need later."""
        resources.load_font("HanSrf.ttf", 25, "mini")
        resources.load_font("Excalibur Nouveau.ttf", 30, "small")
        resources.load_font("Jacked.ttf", 100, "big")

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
                                           resources.get_font("big"), WHITE)
        text_rect.centerx, text_rect.y = width//2, 110
        screen.blit(text_surf, text_rect)

        text_surf, text_rect = render_text(f"Your score was {self.score}",
                                           resources.get_font("small"), WHITE)
        text_rect.centerx, text_rect.y = width//2, 270
        screen.blit(text_surf, text_rect)

        if not self.record:
            accept = pygame.key.name(settings.get_key("accept"))
            finish = pygame.key.name(settings.get_key("pause"))
            text = (f"({accept.upper()} to replay,"
                    f" {finish.upper()} to exit menu)")
            text_surf, text_rect = render_text(text,
                                               resources.get_font("small"),
                                               WHITE)
            text_rect.centerx, text_rect.y = width//2, 325
            screen.blit(text_surf, text_rect)
        else:
            # Highscore message
            text_surf, text_rect = render_text("New record!",
                                               resources.get_font("small"),
                                               WHITE)
            text_rect.centerx, text_rect.y = width//2, 345
            screen.blit(text_surf, text_rect)

            text_surf, text_rect = render_text("Enter your initials: ",
                                               resources.get_font("small"),
                                               WHITE)
            text_rect.centerx, text_rect.y = width//2-58, 420
            screen.blit(text_surf, text_rect)

            # Textbox
            input_box = pygame.Rect(width//2+82, 415, 100, 35)
            screen.fill(BLACK, input_box)
            resources.get_font("small").render_to(
                screen, (input_box.x+15, input_box.y+5), self.initials, WHITE)

        # Pun
        text_surf, text_rect = render_wrapped_text(
            self.joke, resources.get_font("mini"), WHITE, True, 10, width-150)
        text_rect.centerx, text_rect.y = width//2, height-130
        screen.blit(text_surf, text_rect)


class SceneSettings(SceneBase):  # TODO
    """Settings scene."""

    def __init__(self):
        super().__init__()
        self.load_assets()

    @staticmethod
    def load_assets():
        """Load stuff that we will need later."""

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
        self.load_assets()

    @staticmethod
    def load_assets():
        """Load stuff that we will need later."""
        resources.load_font("Excalibur Nouveau.ttf", 50, "round")
        resources.load_font("Excalibur Nouveau.ttf", 30, "small")
        resources.load_font("AurulentSansMono-Regular.otf", 30, "mono")

    def process_input(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == settings.get_key("accept"):
                    self.switch_to_scene(SceneMenu)

    def update(self, now: int):
        pass

    def render(self, screen: pygame.Surface):
        width, height = pygame.display.get_surface().get_size()

        screen.fill(BGCOLOR)

        text_surf, text_rect = render_text(f"Highscores",
                                           resources.get_font("round"), WHITE)
        text_rect.centerx, text_rect.y = width//2, 50
        screen.blit(text_surf, text_rect)

        # Display highscore list
        highscores = settings.get_highscores()
        for i, highscore in enumerate(highscores):
            color = (200 - i*30, 200 - i*20, 200 - i*30)
            text = (f"{i+1} ___ {highscore['name']:>3} _____ "
                    f"{highscore['score']:3} _____ {highscore['date']} ")
            text_surf, text_rect = render_text(
                text, resources.get_font("mono"), color)
            text_rect.x, text_rect.y = 75, 150+i*50
            screen.blit(text_surf, text_rect)

        accept = pygame.key.name(settings.get_key("accept"))
        text = f"({accept.upper()} to exit menu)"
        text_surf, text_rect = render_text(text, resources.get_font("small"),
                                           WHITE)
        text_rect.centerx, text_rect.y = width//2, height - 120
        screen.blit(text_surf, text_rect)


class SceneMenu(SceneBase):
    """Scene index of scenes."""

    def __init__(self):
        super().__init__()
        self.options = [("Play", lambda: SceneTransition(SceneGame)),
                        ("Settings", lambda: SceneTransition(SceneMenu)),
                        ("Highscores",
                         lambda: SceneTransition(SceneHighScores)),
                        ("Quit", SceneExit)]
        self.selected = False
        self.index = 0
        self.load_assets()
        i = random.getrandbits(1) + 1
        i = 1
        self.background = ParaBackground(resources.get_image(f"menu-bg{i}"),
                                         resources.get_image(f"menu-bg{i}b"))

    @staticmethod
    def load_assets():
        """Load stuff that we will need later and play annoying music."""
        resources.load_font("Jacked.ttf", 175, "menu-title")
        resources.load_font("Jacked.ttf", 150, "artdeco150")
        resources.load_font("Excalibur Nouveau.ttf", 40, "hippy40")
        resources.load_font("Excalibur Nouveau.ttf", 50, "hippy50")

        resources.load_image("bg-menu1.png", "menu-bg1")
        resources.load_image("bg-menu1b.png", "menu-bg1b", alpha=True)
        resources.load_image("bg-menu2.png", "menu-bg2")
        resources.load_image("bg-menu2b.png", "menu-bg2b", alpha=True)

        resources.load_sound("menu-select.wav", "menu-sel")
        resources.load_sound("menu-accept.wav", "menu-accept")
        resources.set_volume(settings.get_setting("sound"))

        pygame.mixer.music.load("assets/audio/menu-music.ogg")
        pygame.mixer.music.set_volume(settings.get_setting("music"))
        pygame.mixer.music.play(-1)

    def process_input(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.index = (len(self.options)-1 if self.index == 0
                                  else self.index-1)
                    resources.get_sound("menu-sel").stop()
                    resources.get_sound("menu-sel").play()
                elif event.key == pygame.K_DOWN:
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
        font = resources.get_font("menu-title")
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
                font = resources.get_font("hippy50")
            else:
                # Inactive
                color = BLACK
                font = resources.get_font("hippy40")

            rd_text, rd_rect = render_text(option[0], font, color)
            rd_rect.centerx, rd_rect.centery = (width//2, pos_y+60*i)
            screen.blit(rd_text, rd_rect)
