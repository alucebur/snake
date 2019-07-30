"""Objects of the game."""
import math
import queue
import random
from typing import Dict, Tuple

import pygame

from consts import (SnakeBody, BLOCK, APPLE_COLOR,
                    WHITE, SNAKE_COLOR, OPPOSITE)


class Apple:
    """Define snack for snakes. Coordinates are in BLOCK units."""

    def __init__(self, snake_body: SnakeBody, sprite: pygame.Surface = None):
        self.pos = (0, 0)
        self.sprite = sprite
        self.new(snake_body)

    def new(self, obstacles: SnakeBody):
        """Create new random apple. It can't be in obstacles."""
        width, height = pygame.display.get_surface().get_size()
        banned_coordinates = [member[0] for member in obstacles]
        while True:
            self.pos = (random.randint(0, width//BLOCK[0] - 1),
                        random.randint(0, height//BLOCK[1] - 1))
            if self.pos not in banned_coordinates:
                break

    def draw(self, screen: pygame.Surface):
        """Draw an apple on the screen."""
        rectangle = (self.pos[0] * BLOCK[0], self.pos[1] * BLOCK[1],
                     BLOCK[0], BLOCK[1])
        # Classic look
        if not self.sprite:
            pygame.draw.rect(screen, APPLE_COLOR, rectangle)
        # Apple with a peel
        else:
            screen.blit(self.sprite, (self.pos[0] * BLOCK[0],
                                      self.pos[1] * BLOCK[1]))


class Snake:
    """Define player's snake. Body coordinates are in BLOCK units."""
    def __init__(self):
        self.direction = None
        # FIFO queue, buffer of direction changes
        self.direction_queue = queue.Queue(maxsize=3)
        self.timer = 0
        self.vel = 10
        self.growing = False
        self.color = SNAKE_COLOR
        self.body = []
        self.reset()
        self.skin = {}

    def reset(self):
        """Build a new body for the snake (head & tail)."""
        width, height = pygame.display.get_surface().get_size()
        pos_x = random.randint(0, width//BLOCK[0] - 1)
        pos_y = random.randint(0, height//BLOCK[1] - 1)
        self.direction = random.choice(list(OPPOSITE))
        self.body = [((pos_x, pos_y), self.direction),
                     ((pos_x, pos_y), self.direction)]

    def get_head(self) -> Tuple[int, int]:
        """Return head position."""
        return self.body[0][0]

    def queue_direction(self, event: pygame.event.EventType,
                        dir_dict: Dict[int, str]):
        """Add new directions to the queue depending on keys pressed."""
        try:
            self.direction_queue.put_nowait(
                dir_dict[event.key])
        except queue.Full:
            pass

    def move(self, now: int):
        """Move snake according to its speed.

        Movement is done by inserting a new head and removing tail."""
        width, height = pygame.display.get_surface().get_size()
        if now - self.timer >= 1000.0 / self.vel:
            self.timer = now
            head_x, head_y = self.get_head()

            # Try to get new direction from queue
            try:
                new_dir = self.direction_queue.get_nowait()
            except queue.Empty:
                new_dir = self.direction
            # Avoid 180º turns
            if new_dir != OPPOSITE[self.direction]:
                self.direction = new_dir

            # Move according to direction
            if self.direction == "up":
                self.body.insert(0, ((head_x, head_y - 1), self.direction))
            elif self.direction == "down":
                self.body.insert(0, ((head_x, head_y + 1), self.direction))
            elif self.direction == "left":
                self.body.insert(0, ((head_x - 1, head_y), self.direction))
            elif self.direction == "right":
                self.body.insert(0, ((head_x + 1, head_y), self.direction))

            # Don't remove tail if snake ate apple
            if self.growing:
                self.growing = False
            else:
                self.body.pop()

            # Infinite screen, if snake crossses the screen edges,
            # it appears going out of the opposite edge
            head_x, head_y = self.get_head()
            if head_x >= width//BLOCK[0]:
                self.body.insert(0, ((0, head_y), self.direction))
                self.body.pop(1)
            elif head_x < 0:
                self.body.insert(0, ((width//BLOCK[0] - 1, head_y),
                                     self.direction))
                self.body.pop(1)
            elif head_y >= height//BLOCK[1]:
                self.body.insert(0, ((head_x, 0), self.direction))
                self.body.pop(1)
            elif head_y < 0:
                self.body.insert(0, ((head_x, height//BLOCK[1] - 1),
                                     self.direction))
                self.body.pop(1)

    def check_collision(self) -> bool:
        """Check if head has crashed into the body."""
        head = self.get_head()
        for member in self.body[1:]:
            if head == member[0]:
                return True
        return False

    def load_skin(self, skin: pygame.Surface = None):
        """Load sprites to a dictionary.

        Parameter skin must be a surface with 4x3 sprites for straight and
        curved body, tail and head."""
        if skin:
            # Split each image of the sprite
            line_h = skin.subsurface((0, 0, BLOCK[0], BLOCK[1]))
            curve_r = skin.subsurface((BLOCK[0], 0, BLOCK[0], BLOCK[1]))
            tail_d = skin.subsurface((BLOCK[0] * 2, 0, BLOCK[0], BLOCK[1]))
            head_u = skin.subsurface((BLOCK[0] * 3, 0, BLOCK[0], BLOCK[1]))

            line_h2 = skin.subsurface((0, BLOCK[1]*2,
                                       BLOCK[0], BLOCK[1]))
            curve_r2 = skin.subsurface((BLOCK[0], BLOCK[1]*2,
                                        BLOCK[0], BLOCK[1]))
            tail_d2 = skin.subsurface((BLOCK[0] * 2, BLOCK[1]*2,
                                       BLOCK[0], BLOCK[1]))

            line_h_down_blood = skin.subsurface((0, BLOCK[1],
                                                 BLOCK[0], BLOCK[1]))
            curve_r_left_blood = skin.subsurface((BLOCK[0], BLOCK[1],
                                                  BLOCK[0], BLOCK[1]))
            tail_d_left_blood = skin.subsurface((BLOCK[0]*2, BLOCK[1],
                                                 BLOCK[0], BLOCK[1]))
            tail_d_up_blood = skin.subsurface((BLOCK[0]*3, BLOCK[1],
                                               BLOCK[0], BLOCK[1]))

            # Straight body
            self.skin['hor'] = (line_h, line_h2)
            self.skin['ver'] = (pygame.transform.rotate(line_h, 90),
                                pygame.transform.rotate(line_h2, 90))

            # Head (Doesn't have alternate skin, its index is always 0)
            self.skin['head-left'] = (pygame.transform.rotate(head_u, 90),
                                      None)
            self.skin['head-right'] = (pygame.transform.rotate(head_u, -90),
                                       None)
            self.skin['head-up'] = (head_u, None)
            self.skin['head-down'] = (pygame.transform.rotate(head_u, 180),
                                      None)

            # Tail
            self.skin['tail-left'] = (pygame.transform.rotate(tail_d, -90),
                                      pygame.transform.rotate(tail_d2, -90))
            self.skin['tail-right'] = (pygame.transform.rotate(tail_d, 90),
                                       pygame.transform.rotate(tail_d2, 90))
            self.skin['tail-up'] = (pygame.transform.rotate(tail_d, 180),
                                    pygame.transform.rotate(tail_d2, 180))
            self.skin['tail-down'] = (tail_d, tail_d2)

            # Curved body
            self.skin['J'] = (pygame.transform.rotate(curve_r, 180),
                              pygame.transform.rotate(curve_r2, 180))
            self.skin['7'] = (pygame.transform.rotate(curve_r, -90),
                              pygame.transform.rotate(curve_r2, -90))
            self.skin['L'] = (pygame.transform.rotate(curve_r, 90),
                              pygame.transform.rotate(curve_r2, 90))
            self.skin['r'] = (curve_r, curve_r2)

            # Bloody parts
            # Bloody straight body
            self.skin['hor-up-blood'] = pygame.transform.rotate(
                line_h_down_blood, 180)
            self.skin['hor-down-blood'] = line_h_down_blood
            self.skin['ver-left-blood'] = pygame.transform.rotate(
                line_h_down_blood, -90)
            self.skin['ver-right-blood'] = pygame.transform.rotate(
                line_h_down_blood, 90)

            # Bloody tail
            self.skin['tail-down-right-blood'] = pygame.transform.flip(
                tail_d_left_blood, True, False)
            self.skin['tail-down-left-blood'] = tail_d_left_blood
            self.skin['tail-down-up-blood'] = tail_d_up_blood

            self.skin['tail-up-right-blood'] = pygame.transform.rotate(
                tail_d_left_blood, 180)
            self.skin['tail-up-left-blood'] = pygame.transform.rotate(
                self.skin['tail-down-right-blood'], 180)
            self.skin['tail-up-down-blood'] = pygame.transform.rotate(
                tail_d_up_blood, 180)

            self.skin['tail-left-down-blood'] = pygame.transform.rotate(
                self.skin['tail-down-right-blood'], -90)
            self.skin['tail-left-up-blood'] = pygame.transform.rotate(
                tail_d_left_blood, -90)
            self.skin['tail-left-right-blood'] = pygame.transform.rotate(
                tail_d_up_blood, -90)

            self.skin['tail-right-down-blood'] = pygame.transform.rotate(
                tail_d_left_blood, 90)
            self.skin['tail-right-up-blood'] = pygame.transform.rotate(
                self.skin['tail-down-right-blood'], 90)
            self.skin['tail-right-left-blood'] = pygame.transform.rotate(
                tail_d_up_blood, 90)

            # Bloody curved body
            self.skin['7-right-blood'] = pygame.transform.flip(
                curve_r_left_blood, True, False)
            self.skin['7-up-blood'] = pygame.transform.rotate(
                curve_r_left_blood, -90)
            self.skin['J-right-blood'] = pygame.transform.rotate(
                curve_r_left_blood, 180)
            self.skin['J-down-blood'] = pygame.transform.rotate(
                self.skin['7-right-blood'], -90)
            self.skin['L-left-blood'] = pygame.transform.rotate(
                self.skin['7-right-blood'], 180)
            self.skin['L-down-blood'] = pygame.transform.rotate(
                curve_r_left_blood, 90)
            self.skin['r-left-blood'] = curve_r_left_blood
            self.skin['r-up-blood'] = pygame.transform.rotate(
                self.skin['7-right-blood'], 90)

    def get_body_shape(self, index: int) -> str:
        """Return the shape of the given part of the body."""
        current_dir = self.body[index][1]
        previous_dir = self.body[index-1][1]

        # Head
        if index == 0:
            piece = "head-" + current_dir

        # Tail
        elif index == len(self.body) - 1:
            piece = "tail-" + previous_dir

        # Straight body part
        elif current_dir == previous_dir:
            if current_dir in ("up", "down"):
                piece = "ver"
            else:
                piece = "hor"

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

        return piece

    def draw_blood(self, win: pygame.Surface):
        """Draw blood around snake's head."""
        # Center of its head
        head_x, head_y = self.get_head()
        head_x = head_x * BLOCK[0] + BLOCK[0]//2
        head_y = head_y * BLOCK[1] + BLOCK[1]//2

        radius = math.sqrt(random.random())
        alpha = 2 * math.pi * random.random()
        color = (random.randint(50, 250), 0, 0)

        # Draw red rectangle around the center of its head
        pos_x = BLOCK[0] * radius * math.cos(alpha) + head_x
        pos_y = BLOCK[1] * radius * math.sin(alpha) + head_y
        pygame.draw.rect(win, color, (pos_x, pos_y, 2, 2))

        # Draw body to cover blood splashes over the body, and hole on top
        self.draw(win)
        if self.skin:
            self.draw_bloody_piece(win)

    def draw_bloody_piece(self, win: pygame.Surface):
        """Draw a piece of the body with a bloody hole."""
        # Search for collided piece
        head = self.get_head()
        for i in range(1, len(self.body)):
            if head == self.body[i][0]:
                collision_ix = i
                break

        head_direction = self.body[0][1]
        piece_col_type = self.get_body_shape(collision_ix)
        rectangle = (self.body[i][0][0]*BLOCK[0],
                     self.body[i][0][1]*BLOCK[1],
                     BLOCK[0], BLOCK[1])

        bloody_piece = f"{piece_col_type}-{OPPOSITE[head_direction]}-blood"
        win.blit(self.skin[bloody_piece], rectangle)

    def draw(self, win: pygame.Surface):
        """Draw the snake on the screen."""
        for i in range(len(self.body)):
            rectangle = (self.body[i][0][0]*BLOCK[0],
                         self.body[i][0][1]*BLOCK[1],
                         BLOCK[0], BLOCK[1])
            # Classic look
            if not self.skin:
                pygame.draw.rect(win, self.color, rectangle)

            # Paint skin, alternating sprite
            else:
                piece = self.get_body_shape(i)
                win.blit(self.skin[piece][i % 2], rectangle)


class ParaBackground:
    """A moving background with parallax effect."""

    def __init__(self, surface: pygame.Surface, layer: pygame.Surface):
        self.surface = surface
        self.layer = layer
        self.rect_s = surface.get_rect()
        self.rect_l = layer.get_rect()
        width, height = pygame.display.get_surface().get_size()
        self.rect_s.x = 0
        self.rect_s.centery = height // 2
        self.rect_l.x = self.rect_l.w - width
        self.rect_l.centery = height // 2
        self.max_x = self.rect_l.x
        self.timer = 0
        self.vel = 60
        self.moved = False
        self.direction = -1  # Left

    def move(self):
        """Move across the screen.

        Scroll background horizontally, changing its direction when
        left part of image reaches max_x (moving to right) or
        right part of image reaches the screen width (moving to left)."""
        width = pygame.display.get_surface().get_width()

        # Move layer
        self.rect_l.x += self.direction

        # Move surface at half the speed of layer
        if not self.moved:
            self.rect_s.x += self.direction
            self.moved = True
        else:
            self.moved = False

        # Check edges
        if self.rect_l.x + self.rect_l.w <= width:
            self.direction = - self.direction
        elif self.rect_l.x >= self.max_x:
            self.direction = - self.direction

    def draw(self, screen: pygame.surface):
        """Draw on the screen."""
        screen.blit(self.surface, self.rect_s)
        screen.blit(self.layer, self.rect_l)


class Slider:
    """Create a bar object filled at the given percentage."""
    def __init__(self, percent: float):
        self.percent = percent
        self.color = (0, 0, 0)
        self.rect = pygame.Rect(0, 0, 250, 26)
        self.rect.x = 0
        self.rect.y = 0

    def draw(self, screen: pygame.Surface):
        """Draw on the screen."""
        bar_rect = (self.rect.x + 2, self.rect.y + 2,
                    (self.rect.w - 4)*self.percent,
                    self.rect.h - 4)
        pygame.draw.rect(screen, WHITE, self.rect)
        pygame.draw.rect(screen, self.color, bar_rect)
