"""Classic Snake game implemented in Python.

TODO:
- highscores screen, enter initials if highscore and save to file.
- intro screen with settings (volume, classic mode, rebind keys).
- add win condition.
- joystick support.
- online mode.
"""
import os
import json
import queue
import random
import datetime
import pygame
import pygame.freetype

WIDTH = 800  # Divisible by BLOCK[0]
HEIGHT = 640  # Divisible by BLOCK[1]
BLOCK = (32, 32)  # Size of grid units in pixels
SPRITE_BLOCK = (64, 64)  # Size of sprite images in pixels
BGCOLOR = pygame.Color("grey13")
FGCOLOR = pygame.Color("gray82")
SNAKE_COLOR = pygame.Color("green3")
APPLE_COLOR = pygame.Color("red3")
BLACK = pygame.Color("black")
FPS = 10  # Lower value for lower speed
OPPOSITE = {'up': "down", 'down': "up", 'left': "right", 'right': "left"}
PUN_FILE = "puns.json"
CONFIG_FILE = "settings.json"
DEFAULT_SETTINGS = {
    'sound': 1.0,
    'music': 0.8,
    'classic': False
}
DEFAULT_KEYMAPPING = {
    'direction':
    {
        pygame.K_UP: "up",
        pygame.K_DOWN: "down",
        pygame.K_LEFT: "left",
        pygame.K_RIGHT: "right"
    },
    'grid': pygame.K_g,
    'pause': pygame.K_p,
    'exit': pygame.K_ESCAPE,
    'accept': pygame.K_RETURN
}


class Game:
    """Game logic."""
    def __init__(self):
        self.win = None
        self.clock = None
        self.status = "running"  # running, pause, gameover, stopping
        self.show_grid = False
        self.data = {}
        self.sneik = None
        self.apple = None

    @staticmethod
    def split_sprites(image):
        """Return apple and snake sprites already resized.
        :param image: str (file name, sprite with 5 images in a single row)
        :returns: 2-tuple of pygame surfaces"""
        sheet = pygame.image.load(image).convert_alpha()
        apple = sheet.subsurface((0, 0, SPRITE_BLOCK[0], SPRITE_BLOCK[1]))
        apple = pygame.transform.scale(apple, (BLOCK[0], BLOCK[1]))
        snake = sheet.subsurface((SPRITE_BLOCK[0], 0,
                                  SPRITE_BLOCK[0] * 4, SPRITE_BLOCK[1]))
        snake = pygame.transform.scale(snake, (BLOCK[0] * 4, BLOCK[1]))
        return apple, snake

    def write_config(self):
        """Write current configuration to file."""
        print(f"Saving config to {CONFIG_FILE}...", end=" ")
        data = {}
        data['settings'] = self.data['settings']
        data['keymapping'] = self.data['keymapping']
        data['highscores'] = self.data['highscores']
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except EnvironmentError:
            print(f"Could't save config to file.")
        else:
            print("Done.")

    def load_config(self):
        """Load configuration from file.
        :param file: str (file name)."""
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except EnvironmentError:
            print(f"Could't load config from {CONFIG_FILE}.")
            # Load default values
            self.data['settings'] = DEFAULT_SETTINGS
            self.data['keymapping'] = DEFAULT_KEYMAPPING
            self.data['highscores'] = []
            # create config file
            self.write_config()
        else:
            # Load values from file
            self.data['settings'] = config['settings']
            self.data['keymapping'] = {}
            self.data['keymapping']['pause'] = config['keymapping']['pause']
            self.data['keymapping']['grid'] = config['keymapping']['grid']
            self.data['keymapping']['exit'] = config['keymapping']['exit']
            self.data['keymapping']['accept'] = config['keymapping']['accept']
            self.data['keymapping']['direction'] = {}
            for key, value in config['keymapping']['direction'].items():
                self.data['keymapping']['direction'][int(key)] = value
            self.data['highscores'] = config['highscores']

    def load_fonts(self):
        """Load fonts."""
        self.data['fonts'] = {}
        self.data['fonts']['mini'] = pygame.freetype.Font(
            "assets/fonts/HanSrf.ttf", 25)
        self.data['fonts']['small'] = pygame.freetype.Font(
            "assets/fonts/Excalibur Nouveau.ttf", 30)
        self.data['fonts']['big'] = pygame.freetype.Font(
            "assets/fonts/Jacked.ttf", 100)

    def load_sounds(self):
        """Load sounds and set volume."""
        self.data['sounds'] = {}
        self.data['sounds']['eat'] = pygame.mixer.Sound(
            "assets/audio/snake-bite.wav")
        self.data['sounds']['crash'] = pygame.mixer.Sound(
            "assets/audio/snake-crash.wav")
        for audio in self.data['sounds'].values():
            audio.set_volume(self.data['settings']['sound'])

    def on_init(self):
        """Initialize game, set variables, load assets."""
        # Loading pygame
        pygame.mixer.pre_init(22100, -16, 2, 512)
        pygame.init()
        os.environ['SDL_VIDEO_CENTERED'] = "1"
        pygame.mouse.set_visible(False)
        pygame.display.set_caption("Snake - the classic game!")

        # Setting game attributes
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.load_config()

        # Loading assets
        game_icon = pygame.image.load("assets/icon.png")
        pygame.display.set_icon(game_icon)
        self.load_fonts()
        self.load_sounds()
        if not self.data['settings']['classic']:
            self.data['bg_img'] = pygame.image.load("assets/background.png")
            apple_skin, snake_skin = self.split_sprites(
                "assets/sprites/snake-graphics.png")
        else:
            apple_skin, snake_skin = None, None

        # Load jokes
        try:
            with open(PUN_FILE, "r", encoding="utf8") as f:
                self.data.update(json.load(f))
        except EnvironmentError:
            print(f"Couldn't load data from {PUN_FILE}")
            self.data['jokes'] = ["There are no snakes in my boot :("]

        # Creating snake and apple instances
        self.sneik = Snake()
        self.sneik.define_skin(snake_skin)
        self.apple = Apple(self.sneik.body, apple_skin)

        # Load and play music
        pygame.mixer.music.load("assets/audio/snake-music-Rafael_Krux.mp3")
        pygame.mixer.music.set_volume(self.data['settings']['music'])
        pygame.mixer.music.play(-1)

    def on_event(self, event):
        """Check for pygame events.
        :param event: Pygame event."""
        # Exit game
        if (event.type == pygame.QUIT or
                (event.type == pygame.KEYDOWN and
                 event.key == self.data['keymapping']['exit'])):
            self.status = "stopping"

        elif (self.status == "running" and event.type == pygame.KEYDOWN):
            # Snake control, add new direction to queue
            if event.key in self.data['keymapping']['direction']:
                self.sneik.queue_direction(
                    event, self.data['keymapping']['direction'])

            # Game control
            elif event.key == self.data['keymapping']['grid']:
                self.show_grid = not self.show_grid
            elif event.key == self.data['keymapping']['pause']:
                self.pause()

        elif (self.status == "pause" and event.type == pygame.KEYDOWN and
              event.key == self.data['keymapping']['pause']):
            self.unpause()

    def on_loop(self):
        """Move snake and check interactions."""
        if self.status == "running":
            # Moves snake
            self.sneik.move()

            # Checks if snake crashed into itself
            if self.sneik.check_collision():
                self.data['sounds']['crash'].play()
                self.status = "gameover"

            # Checks if snake is feeding
            self.check_food()

    def on_render(self):
        """Draw window."""
        if self.status == "running" or self.status == "gameover":
            # Draw background
            if self.data.get("bg_img"):
                self.win.blit(self.data['bg_img'], (0, 0))
            else:
                # Classic look
                self.win.fill(BGCOLOR)

            # Draw snake, apple, grid
            self.sneik.draw(self.win, self.status == "gameover")
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
        while self.status != "stopping":
            while self.status != "gameover" and self.status != "stopping":
                for event in pygame.event.get():
                    self.on_event(event)
                self.on_loop()
                self.on_render()
            if self.status == "gameover":
                self.gameover_screen()
        self.on_cleanup()

    def pause(self):
        """Pause game and render pause screen."""
        # Pauses game
        pygame.mixer.music.pause()
        self.status = "pause"

        # Darkens the screen
        surf = pygame.Surface((WIDTH, HEIGHT))
        surf.set_alpha(160)
        surf.fill(BLACK)
        self.win.blit(surf, (0, 0))

        # Show pause message
        self.render_centered_text("Paused", "big", FGCOLOR, WIDTH//2, 250)
        self.render_centered_text(f"Score: {len(self.sneik.body) - 2}",
                                  "small", FGCOLOR, WIDTH//2, 330)

    def unpause(self):
        """Unpause game."""
        pygame.mixer.music.unpause()
        self.status = "running"

    def reset_game(self):
        """Reset stats to start a new game."""
        self.sneik.reset()
        self.apple.new(self.sneik.body)

    def add_highscore(self, name):
        """Adds highscore to data and file.
        :param name: str."""
        date = str(datetime.date.today())
        score = len(self.sneik.body) - 2
        new_highscore = {"name": name, "score": score, "date": date}

        new_list = self.data['highscores'].copy()
        new_list.append(new_highscore)
        # Highscore list is sorted by score (desc) and date (asc)
        new_list.sort(key=lambda x: (-x['score'], x['date']))
        if len(new_list) > 5:
            new_list.pop()
        self.data['highscores'] = new_list

        # Save to file
        self.write_config()

    def gameover_screen(self):
        """Gameover message."""
        pygame.mixer.music.stop()
        pygame.time.delay(1000)

        joke = random.choice(self.data['jokes'])
        accept = pygame.key.name(self.data['keymapping']['accept'])
        finish = pygame.key.name(self.data['keymapping']['exit'])
        score = len(self.sneik.body) - 2
        record = (score > min([user['score'] for
                               user in self.data['highscores']],
                              default=-1))
        initials = ""
        input_box = pygame.Rect(WIDTH // 2 + 82, 415, 100, 35)
        choice = False
        # Waits until user decides to play again or exit game
        while not choice:
            for event in pygame.event.get():
                if not record:
                    # Play again
                    if (event.type == pygame.KEYDOWN and
                            event.key == self.data['keymapping']['accept']):
                        self.status = "running"
                        self.reset_game()
                        choice = True
                        pygame.mixer.music.play(-1)
                    # Exit game
                    elif (event.type == pygame.QUIT or
                          (event.type == pygame.KEYDOWN and
                           event.key == self.data['keymapping']['exit'])):
                        self.status = "stopping"
                        choice = True
                else:
                    # Enter initials
                    if event.type == pygame.QUIT:
                        self.status = "stopping"
                        choice = True
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            # confirm
                            self.add_highscore(initials)
                            record = False
                        elif event.key == pygame.K_BACKSPACE:
                            # delete
                            initials = initials[:-1]
                        elif len(initials) < 3 and event.unicode.isalnum():
                            # writing
                            initials += event.unicode.upper()

            # Displays gameover message
            if not choice:
                self.win.fill(BGCOLOR)
                self.render_centered_text("YOU LOST", "big", FGCOLOR,
                                          WIDTH//2, 110)
                self.render_centered_text(f"Your score was {score}",
                                          "small", FGCOLOR, WIDTH//2, 270)
                if not record:
                    text = (f"({accept.upper()} to play again,"
                            f" {finish.upper()} to exit)")
                    self.render_centered_text(text, "small", FGCOLOR,
                                              WIDTH//2, 325)
                else:
                    # Highscore message
                    self.render_centered_text("New record!", "small", FGCOLOR,
                                              WIDTH//2, 345)
                    self.render_centered_text("Enter your initials: ", "small",
                                              FGCOLOR, WIDTH//2-58, 420)
                    # Initials textbox
                    self.win.fill(BLACK, input_box)
                    self.data['fonts']['small'].render_to(
                        self.win, (input_box.x + 15, input_box.y + 5),
                        initials, FGCOLOR)
                # Pun
                self.render_wrapped_centered_text(
                    joke, "mini", FGCOLOR, WIDTH//2, HEIGHT-130, WIDTH-150)

                self.clock.tick(FPS)
                pygame.display.update()

    def render_centered_text(self, text, font, color, center_x, pos_y):
        """Render centered text on the screen.
        :param text: str.
        :param font: str.
        :param color: 3-tuple of int.
        :param center_x: int.
        :param pos_y: int."""
        text_surf, text_rect = self.data['fonts'][font].render(text, color)
        text_rect.centerx, text_rect.y = center_x, pos_y
        self.win.blit(text_surf, text_rect)

    def render_wrapped_centered_text(self, text, font, color,
                                     center_x, pos_y, max_width):
        """Render text using several lines if not fit in surface.
        :param text: str.
        :param font: str.
        :param color: 3-tuple of int.
        :param center_x: int.
        :param pos_y: int.
        :param max_width: int."""
        words = text.split()
        lines = []
        # Separate text into lines
        while words:
            line_words = []
            while words:
                line_words.append(words.pop(0))
                _, _, line_w, _ = self.data['fonts'][font].get_rect(
                    ' '.join(line_words + words[:1]))
                if line_w > max_width:
                    break
            lines.append(' '.join(line_words))

        # Write the lines on the screen
        for line in lines:
            text_surf, text_rect = self.data['fonts'][font].render(
                line, color)
            text_rect.centerx, text_rect.y = center_x, pos_y
            self.win.blit(text_surf, text_rect)
            pos_y = pos_y + text_rect.h + 10

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
            self.data['sounds']['eat'].play()
            self.sneik.grow(*self.sneik.get_head())
            self.apple.new(self.sneik.body)


class Snake:
    """Define player's snake. Body coordinates are in BLOCK units."""
    def __init__(self):
        self.direction = None
        # FIFO queue, buffer of direction changes
        self.direction_queue = queue.Queue(maxsize=3)
        self.body = []
        self.color = SNAKE_COLOR
        self.skin = {}
        self.reset()

    def reset(self):
        """Build a new body for the snake (head & tail)."""
        pos_x = random.randint(0, WIDTH//BLOCK[0] - 1)
        pos_y = random.randint(0, HEIGHT//BLOCK[1] - 1)
        self.direction = random.choice(list(OPPOSITE))
        self.body = [((pos_x, pos_y), self.direction),
                     ((pos_x, pos_y), self.direction)]

    def grow(self, pos_x, pos_y):
        """Grow snake body by adding 1 block at the specified point.
        :param pos_x: int.
        :param pos_y: int."""
        self.body.append(((pos_x, pos_y), self.direction))

    def get_head(self):
        """Return head position.
        :returns: 2-tuple of int (position of the head)."""
        return self.body[0][0]

    def queue_direction(self, event, dir_dict):
        """Add new directions to the queue depending on keys pressed.
        :param event: pygame event."""
        try:
            self.direction_queue.put_nowait(
                dir_dict[event.key])
        except queue.Full:
            pass

    def move(self):
        """Move snake by inserting a new head and removing tail."""
        head_x, head_y = self.get_head()

        # Try to get new direction from queue
        try:
            new_dir = self.direction_queue.get_nowait()
        except queue.Empty:
            new_dir = self.direction
        if new_dir != OPPOSITE[self.direction]:  # Avoid 180º turns
            self.direction = new_dir

        # Move according to direction
        if self.direction == "up":
            self.body.insert(0, ((head_x, head_y - 1), self.direction))
            self.body.pop()
        elif self.direction == "down":
            self.body.insert(0, ((head_x, head_y + 1), self.direction))
            self.body.pop()
        elif self.direction == "left":
            self.body.insert(0, ((head_x - 1, head_y), self.direction))
            self.body.pop()
        elif self.direction == "right":
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

    def define_skin(self, skin=None):
        """Define a skin dictionary from a sprite.
        :param skin: Surface with images of straight body,
                     head, tail and curved body."""
        if skin:
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
        return "head-" + current_dir

    @staticmethod
    def get_tail_skin(previous_dir):
        """Return piece to draw for the head.
        :param previous_dir: str.
        :returns: str."""
        return "tail-" + previous_dir

    @staticmethod
    def get_body_skin(current_dir, previous_dir):
        """Return piece to draw for the body.
        :param current_dir: str.
        :param previous_dir: str."""
        # Straight body part
        if current_dir == previous_dir:
            if current_dir in ("up", "down"):
                piece = "vertical"
            else:
                piece = "horizontal"

        # Curved body part
        elif ((current_dir == "right" and previous_dir == "up") or
              (current_dir == "down" and previous_dir == "left")):
            piece = "J"
        elif ((current_dir == "left" and previous_dir == "up") or
              (current_dir == "down" and previous_dir == "right")):
            piece = "L"
        elif ((current_dir == "left" and previous_dir == "down") or
              (current_dir == "up" and previous_dir == "right")):
            piece = "r"
        elif ((current_dir == "right" and previous_dir == "down") or
              (current_dir == "up" and previous_dir == "left")):
            piece = "7"
        else:
            # Safeguard in case of undetected bug
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

    def new(self, obstacles):
        """Create new random apple. It can't be in obstacles.
        :param obstacles: List of tuples with a 2-tuples of int
                          as first element."""
        banned_coordinates = [member[0] for member in obstacles]
        while True:
            self.pos = (random.randint(0, WIDTH//BLOCK[0] - 1),
                        random.randint(0, HEIGHT//BLOCK[1] - 1))
            if self.pos not in banned_coordinates:
                break

    def draw(self, win):
        """Draw an apple on the screen.
        :param win: Screen surface."""
        rectangle = (self.pos[0] * BLOCK[0], self.pos[1] * BLOCK[1],
                     BLOCK[0], BLOCK[1])
        # Classic look
        if not self.sprite:
            pygame.draw.rect(win, APPLE_COLOR, rectangle)
        # Apple with a peel
        else:
            win.blit(self.sprite, (self.pos[0] * BLOCK[0],
                                   self.pos[1] * BLOCK[1]))

if __name__ == "__main__":
    snake_game = Game()
    snake_game.on_execute()
