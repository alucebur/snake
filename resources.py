"""Retrieve and serve assets for the game."""
from pathlib import Path

import pygame
import pygame.freetype

fonts = {}
sounds = {}
images = {}
sprites = {}

FONTS_PATH = Path('assets/fonts/')
SOUNDS_PATH = Path('assets/audio/')
IMAGES_PATH = Path('assets/images/')
SPRITES_PATH = Path('assets/sprites/')


# LOADS =====================================================================
def load_font(name: str, size: int, label: str):
    """Load fonts for the game."""
    fonts[label] = pygame.freetype.Font(str(FONTS_PATH / name), size)


def load_sound(name: str, label: str):
    """Load sounds for the game."""
    sounds[label] = pygame.mixer.Sound(str(SOUNDS_PATH / name))


def load_image(name: str, label: str, alpha: bool = False):
    """Load images for the game.

    Use alpha=True when image has transparent pixels."""
    img = pygame.image.load(str(IMAGES_PATH / name))
    images[label] = img.convert_alpha() if alpha else img.convert()


def load_sprite(name: str, label: str):
    """Load sprites for the game."""
    sprites[label] = pygame.image.load(
        str(SPRITES_PATH / name)).convert_alpha()


def load_music(name: str):
    """Load music for the game."""
    pygame.mixer.music.load(str(SOUNDS_PATH / name))


def load_assets():
    """Load stuff that we will need later."""
    # Fonts
    load_font("HanSrf.ttf", 25, "normal25")
    load_font("HanSrf.ttf", 30, "normal30")
    load_font("Excalibur Nouveau.ttf", 30, "round30")
    load_font("Excalibur Nouveau.ttf", 40, "round40")
    load_font("Excalibur Nouveau.ttf", 50, "round50")
    load_font("Jacked.ttf", 80, "title80")
    load_font("Jacked.ttf", 100, "title100")
    load_font("Jacked.ttf", 175, "title175")
    load_font("AurulentSansMono-Regular.otf", 30, "mono30")

    # Images and sprites
    load_image("bg-menu1.png", "menu-bg1")
    load_image("bg-menu1b.png", "menu-bg1b", alpha=True)
    load_image("bg-menu2.png", "menu-bg2")
    load_image("bg-menu2b.png", "menu-bg2b", alpha=True)
    load_image("bg-game1.png", "snake-bg")
    load_sprite("snake-sprites.png", "sheet")

    # Sounds
    load_sound("snake-bite.wav", "eat")
    load_sound("snake-crash.wav", "crash")
    load_sound("menu-select.wav", "menu-sel")
    load_sound("menu-accept.wav", "menu-accept")


# GETS ======================================================================
def get_font(label: str) -> pygame.freetype.Font:
    """Return font object."""
    return fonts[label]


def get_sound(label: str) -> pygame.mixer.Sound:
    """Return sound object."""
    return sounds[label]


def get_image(label: str) -> pygame.Surface:
    """Return surface object."""
    return images[label]


def get_sprite(label: str) -> pygame.Surface:
    """Return surface object."""
    return sprites[label]


# HELPS =====================================================================
def set_volume(volume: float):
    """Set volume of all sounds."""
    for audio in sounds.values():
        audio.set_volume(volume)
