"""Classic Snake game implemented in Python.

Classic look:
- snake_game.bg_img = None
- snake_game.sneik.skin = None
- snake_game.apple.sprite = None

TODO:
- add win condition.
- intro screen with settings (volume, classic mode).
- score file, top3 scores.
"""
import os
import random
import pygame
import pygame.freetype

WIDTH = 800  # Divisible by BLOCK[0]
HEIGHT = 640  # Divisible by BLOCK[1]
BLOCK = (32, 32)
SPRITE_BLOCK = (64, 64)
BGCOLOR = (40, 40, 40)
FGCOLOR = (200, 200, 200)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLACK = (0, 0, 0)
FPS = 10  # Lower value for lower speed
DIRS = ("up", "down", "left", "right")


class Game:
    """Game logic."""
    def __init__(self):
        self.win = None
        self.clock = None
        self.running = True
        self.on_pause = False
        self.gameover = False
        self.show_grid = False
        self.fonts = {}
        self.sounds = {}
        self.bg_img = None
        self.sneik = None
        self.apple = None

    @staticmethod
    def split_sprites(image):
        """Return apple and snake skin sprites already resized.
        :param image: Sprite file (with 5 images in a single row)
        :returns: 2-tuple of pygame surfaces"""
        sheet = pygame.image.load(image).convert_alpha()
        snack = sheet.subsurface((0, 0, SPRITE_BLOCK[0], SPRITE_BLOCK[1]))
        snack = pygame.transform.scale(snack, (BLOCK[0], BLOCK[1]))
        snake = sheet.subsurface((SPRITE_BLOCK[0], 0,
                                  SPRITE_BLOCK[0] * 4, SPRITE_BLOCK[1]))
        snake = pygame.transform.scale(snake, (BLOCK[0] * 4, BLOCK[1]))
        return snack, snake

    def on_init(self):
        """Initialize game, set variables, load assets."""
        # Loading pygame
        pygame.mixer.pre_init(22100, -16, 2, 512)
        pygame.init()
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.mouse.set_visible(False)
        pygame.display.set_caption("Snake - the classic game!")

        # Setting game attributes
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Loading assets
        game_icon = pygame.image.load('assets/icon.png')
        pygame.display.set_icon(game_icon)
        self.fonts['small'] = pygame.freetype.Font(
            'assets/fonts/Excalibur Nouveau.ttf', 30)
        self.fonts['big'] = pygame.freetype.Font(
            'assets/fonts/Jacked.ttf', 80)
        self.sounds['eat'] = pygame.mixer.Sound('assets/audio/snake-bite.wav')
        self.sounds['crash'] = pygame.mixer.Sound(
            'assets/audio/snake-crash.wav')
        pygame.mixer.music.load('assets/audio/snake-music-Rafael_Krux.mp3')
        self.bg_img = pygame.image.load('assets/background.png')
        apple_skin, snake_skin = self.split_sprites(
            'assets/sprites/snake-graphics.png')

        # Creating snake and apple instances
        self.sneik = Snake()
        self.sneik.define_skin(snake_skin)
        self.apple = Apple(self.sneik.body, apple_skin)

        # Play music
        pygame.mixer.music.play(-1)

    def on_event(self, event):
        """Check for pygame events.
        :param event: Pygame event from the pool of events."""
        # Exit game
        if (event.type == pygame.QUIT or
                (event.type == pygame.KEYDOWN and
                 event.key == pygame.K_ESCAPE)):
            self.gameover = True
            self.running = False

        # Snake control
        elif event.type == pygame.KEYDOWN and not self.on_pause:
            if (event.key == pygame.K_UP and
                    self.sneik.direction != "down"):
                self.sneik.direction = "up"
            elif (event.key == pygame.K_DOWN and
                  self.sneik.direction != "up"):
                self.sneik.direction = "down"
            elif (event.key == pygame.K_LEFT and
                  self.sneik.direction != "right"):
                self.sneik.direction = "left"
            elif (event.key == pygame.K_RIGHT and
                  self.sneik.direction != "left"):
                self.sneik.direction = "right"

            # Show grid
            elif event.key == pygame.K_g:
                self.show_grid = not self.show_grid
            elif event.key == pygame.K_p:
                self.pause()
        elif event.type == pygame.KEYDOWN and self.on_pause:
            if event.key == pygame.K_p:
                self.unpause()

    def on_loop(self):
        """Move snake and check interactions."""
        if not self.on_pause:
            # Moves snake
            self.sneik.move()

            # Checks if snake crashed into itself
            if self.sneik.check_collision():
                self.sounds['crash'].play()
                self.gameover = True

            # Checks if snake is feeding
            self.check_food()

    def on_render(self):
        """Draw window."""
        if not self.on_pause:
            # Draw background
            if self.bg_img:
                self.win.blit(self.bg_img, (0, 0))
            else:  # Classic look
                self.win.fill(BGCOLOR)

            # Draw snake, apple, grid
            self.sneik.draw(self.win, self.gameover)
            self.apple.draw(self.win)
            if self.show_grid:
                self.draw_grid()

        self.clock.tick(FPS)
        pygame.display.update()

    @staticmethod
    def on_cleanup():
        """Uninitialize pygame."""
        pygame.quit()

    def on_execute(self):
        """Flow of the program."""
        self.on_init()
        while self.running:
            while not self.gameover:
                for event in pygame.event.get():
                    self.on_event(event)
                self.on_loop()
                self.on_render()
            if self.gameover and self.running:
                self.gameover_screen()
        self.on_cleanup()

    def pause(self):
        """Pause game and render pause screen."""
        # Pauses game
        pygame.mixer.music.pause()
        self.on_pause = True

        # Darkens the screen
        surf = pygame.Surface((WIDTH, HEIGHT))
        surf.set_alpha(160)
        surf.fill(BLACK)
        self.win.blit(surf, (0, 0))

        # Show pause message
        text_surf, text_rect = self.fonts['big'].render("Paused", FGCOLOR)
        text_rect.center = (WIDTH//2, HEIGHT//2 - 40)
        self.win.blit(text_surf, text_rect)

        # Show current score
        text_surf, text_rect = self.fonts['small'].render(
            f"Score: {len(self.sneik.body)}", FGCOLOR)
        text_rect.center = (WIDTH//2, HEIGHT//2 + 20)
        self.win.blit(text_surf, text_rect)

    def unpause(self):
        """Unpause game."""
        pygame.mixer.music.unpause()
        self.on_pause = False

    def reset_game(self):
        """Reset stats to start a new game."""
        self.sneik.reset()
        self.apple.new(self.sneik.body)

    def gameover_screen(self):
        """Gameover message."""
        pygame.mixer.music.stop()
        pygame.time.delay(1000)
        choice = False

        # Waits until user decides to play again or exit game
        while not choice:
            for event in pygame.event.get():
                # Play again
                if (event.type == pygame.KEYDOWN and
                        event.key == pygame.K_RETURN):
                    self.gameover = False
                    self.reset_game()
                    choice = True
                    pygame.mixer.music.play(-1)

                # Exit game
                elif (event.type == pygame.QUIT or
                      (event.type == pygame.KEYDOWN and
                       event.key == pygame.K_ESCAPE)):
                    self.running = False
                    choice = True

            # Displays message
            if not choice:
                self.win.fill(BGCOLOR)
                text = "YOU LOST"
                text_surf, text_rect = self.fonts['big'].render(
                    text, FGCOLOR)
                text_rect.center = WIDTH//2, HEIGHT//2 - 60
                self.win.blit(text_surf, text_rect)

                text = f"Your score was {len(self.sneik.body) - 2}"
                text_surf, text_rect = self.fonts['small'].render(
                    text, FGCOLOR)
                text_rect.center = WIDTH//2, HEIGHT//2
                self.win.blit(text_surf, text_rect)

                text = "(ENTER to play again, ESCAPE to exit)"
                text_surf, text_rect = self.fonts['small'].render(
                    text, FGCOLOR)
                text_rect.center = WIDTH//2, HEIGHT//2 + 40
                self.win.blit(text_surf, text_rect)

                self.clock.tick(FPS)
                pygame.display.update()

    def draw_grid(self):
        """Draw grid on screen, BLOCK sized rectangles."""
        # Vertical lines
        for i in range(WIDTH//BLOCK[0]):
            pygame.draw.line(self.win, FGCOLOR,
                             (i * BLOCK[0], 0), (i * BLOCK[0], HEIGHT), 1)
        # Horizontal lines
        for i in range(HEIGHT//BLOCK[1]):
            pygame.draw.line(self.win, FGCOLOR,
                             (0, i * BLOCK[1]), (WIDTH, i * BLOCK[1]), 1)

    def check_food(self):
        """Check if snake eats apple."""
        if self.sneik.get_head() == self.apple.pos:
            self.sounds['eat'].play()
            self.sneik.grow(*self.sneik.get_head())
            self.apple.new(self.sneik.body)


class Snake:
    """Define player's snake. Body coordinates are in BLOCK units."""
    def __init__(self):
        self.direction = None
        self.body = []
        self.color = GREEN
        self.skin = {}
        self.reset()

    def reset(self):
        """Build a new body for the snake (head & tail)."""
        pos_x = random.randint(0, WIDTH//BLOCK[0] - 1)
        pos_y = random.randint(0, HEIGHT//BLOCK[1] - 1)
        self.direction = random.choice(DIRS)
        self.body = [((pos_x, pos_y), self.direction),
                     ((pos_x, pos_y), self.direction)]

    def grow(self, pos_x, pos_y):
        """Grow snake body by adding 1 block at the specified point.
        :param pos_x: x-coordinate for the new block.
        :param pos_y: y-coordinate for the new block."""
        self.body.append(((pos_x, pos_y), self.direction))

    def get_head(self):
        """Return head position.
        :returns: 2-tuple with the position of the head."""
        return self.body[0][0]

    def move(self):
        """Move snake by inserting a new head and removing tail."""
        head_x, head_y = self.get_head()
        if self.direction == 'up':
            self.body.insert(0, ((head_x, head_y - 1), self.direction))
            self.body.pop()
        elif self.direction == 'down':
            self.body.insert(0, ((head_x, head_y + 1), self.direction))
            self.body.pop()
        elif self.direction == 'left':
            self.body.insert(0, ((head_x - 1, head_y), self.direction))
            self.body.pop()
        elif self.direction == 'right':
            self.body.insert(0, ((head_x + 1, head_y), self.direction))
            self.body.pop()

        # Infinite screen, if snake crossses the screen edges,
        # it appears going out of the opposite edge
        head_x, head_y = self.get_head()
        if head_x >= WIDTH//BLOCK[0]:
            self.body.insert(0, ((0, head_y), self.direction))
            self.body.pop(1)
        elif head_x < 0:
            self.body.insert(0, ((WIDTH//BLOCK[0] - 1, head_y),
                                 self.direction))
            self.body.pop(1)
        elif head_y >= HEIGHT//BLOCK[1]:
            self.body.insert(0, ((head_x, 0), self.direction))
            self.body.pop(1)
        elif head_y < 0:
            self.body.insert(0, ((head_x, HEIGHT//BLOCK[1] - 1),
                                 self.direction))
            self.body.pop(1)

    def check_collision(self):
        """Check if head has crashed into the body.
        :returns: Boolean."""
        head = self.get_head()
        for member in self.body[1:]:
            if head == member[0]:
                return True
        return False

    def define_skin(self, skin):
        """Define a skin dictionary from a sprite.
        :param skin: Surface with straight body, head, tail and curved body."""
        # Splits each image of the sprite
        curve_rd = skin.subsurface((0, 0, BLOCK[0], BLOCK[1]))
        line_h = skin.subsurface((BLOCK[0], 0, BLOCK[0], BLOCK[1]))
        head_u = skin.subsurface((BLOCK[0] * 2, 0, BLOCK[0], BLOCK[1]))
        tail_d = skin.subsurface((BLOCK[0] * 3, 0, BLOCK[0], BLOCK[1]))

        # Straight body
        self.skin['horizontal'] = line_h
        self.skin['vertical'] = pygame.transform.rotate(line_h, 90)

        # Head
        self.skin['head-left'] = pygame.transform.rotate(head_u, 90)
        self.skin['head-right'] = pygame.transform.rotate(head_u, -90)
        self.skin['head-up'] = head_u
        self.skin['head-down'] = pygame.transform.rotate(head_u, 180)

        # Tail
        self.skin['tail-left'] = pygame.transform.rotate(tail_d, -90)
        self.skin['tail-right'] = pygame.transform.rotate(tail_d, 90)
        self.skin['tail-up'] = pygame.transform.rotate(tail_d, 180)
        self.skin['tail-down'] = tail_d

        # Curved body
        self.skin['J'] = pygame.transform.rotate(curve_rd, 180)
        self.skin['7'] = pygame.transform.rotate(curve_rd, -90)
        self.skin['L'] = pygame.transform.rotate(curve_rd, 90)
        self.skin['r'] = curve_rd

    @staticmethod
    def get_head_skin(current_dir):
        """Return piece to draw for the head.
        :param current_dir: str.
        :returns: str."""
        return 'head-' + current_dir

    @staticmethod
    def get_tail_skin(previous_dir):
        """Return piece to draw for the head.
        :param previous_dir: str.
        :returns: str."""
        return 'tail-' + previous_dir

    @staticmethod
    def get_body_skin(current_dir, previous_dir):
        """Return piece to draw for the body.
        :param current_dir: str.
        :param previous_dir: str."""
        # Straight body part
        if current_dir == previous_dir:
            if current_dir in ('up', 'down'):
                piece = 'vertical'
            else:
                piece = 'horizontal'

        # Curved body part
        elif ((current_dir == 'right' and previous_dir == 'up') or
              (current_dir == 'down' and previous_dir == 'left')):
            piece = 'J'
        elif ((current_dir == 'left' and previous_dir == 'up') or
              (current_dir == 'down' and previous_dir == 'right')):
            piece = 'L'
        elif ((current_dir == 'left' and previous_dir == 'down') or
              (current_dir == 'up' and previous_dir == 'right')):
            piece = 'r'
        elif ((current_dir == 'right' and previous_dir == 'down') or
              (current_dir == 'up' and previous_dir == 'left')):
            piece = '7'
        else:
            # Head crash with neck, movement too fast
            piece = None

        return piece

    def draw(self, win, gameover):
        """Draw the snake on the screen.
        :param win: Screen surface.
        :param gameover: Boolean, true if snake crashed."""
        false_tail = False
        for i in range(len(self.body)):
            cur_dir = self.body[i][1]
            rectangle = (self.body[i][0][0]*BLOCK[0],
                         self.body[i][0][1]*BLOCK[1],
                         BLOCK[0], BLOCK[1])
            # Classic look
            if not self.skin:
                pygame.draw.rect(win, self.color, rectangle)

            # Paints skin
            else:
                # Head
                prev_dir = self.body[i-1][1]
                if i == 0:
                    piece = self.get_head_skin(cur_dir)

                # Tail
                elif i == len(self.body) - 1:
                    if not false_tail:
                        piece = self.get_tail_skin(prev_dir)
                    else:
                        piece = None

                # Body
                else:
                    # Check if snake just ate an apple, generating a false tail
                    if self.body[i+1][0] == self.get_head() and not gameover:
                        false_tail = True
                        piece = self.get_tail_skin(prev_dir)
                    else:
                        piece = self.get_body_skin(cur_dir, prev_dir)
                if piece:
                    win.blit(self.skin[piece], rectangle)


class Apple:
    """Define snack for snakes. Coordinates are in BLOCK units."""
    def __init__(self, snake_body, sprite=None):
        self.pos = (0, 0)
        self.sprite = sprite
        self.new(snake_body)

    def new(self, snake_body):
        """Create new random apple. It can't be in snake body.
        :param snake: List of 2-tuples (x,y coordinates)."""
        body_coordinates = [member[0] for member in snake_body]
        while True:
            self.pos = (random.randint(0, WIDTH//BLOCK[0] - 1),
                        random.randint(0, HEIGHT//BLOCK[1] - 1))
            if self.pos not in body_coordinates:
                break

    def draw(self, win):
        """Draw an apple on the screen.
        :param win: Screen surface."""
        rectangle = (self.pos[0] * BLOCK[0], self.pos[1] * BLOCK[1],
                     BLOCK[0], BLOCK[1])
        # Classic look
        if not self.sprite:
            pygame.draw.rect(win, RED, rectangle)
        # Apple with a skin
        else:
            win.blit(self.sprite, (self.pos[0] * BLOCK[0],
                                   self.pos[1] * BLOCK[1]))

if __name__ == "__main__":
    snake_game = Game()
    snake_game.on_execute()
