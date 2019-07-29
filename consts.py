"""Constants."""
from typing import Tuple, List, NewType
import pygame

# Size of grid units in pixels
BLOCK = (32, 32)

# Size of sprite images in pixels
SPRITE_BLOCK = (64, 64)

# Types
Point = NewType('Point', Tuple[int, int])
Size = NewType('Size', Tuple[int, int])
SnakeBody = NewType('SnakeBody', List[Tuple[Point, str]])
Color = NewType('Color', Tuple[int, int, int])

# Colors, pygame.Color() is not hashable
WHITE = Color((200, 200, 200))
BLACK = Color((0, 0, 0))
BGCOLOR = Color((40, 40, 40))
SNAKE_COLOR = Color((0, 200, 0))
APPLE_COLOR = Color((200, 0, 0))

# File names
PUN_FILE = "puns.json"
CONFIG_FILE = "settings.json"

OPPOSITE = {'up': "down", 'down': "up", 'left': "right", 'right': "left"}

# Default config
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
