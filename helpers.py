"""Useful functions."""
from typing import Tuple
from functools import lru_cache

import pygame
import pygame.freetype

from consts import Color


@lru_cache(maxsize=32)
def render_text(text: str, font: pygame.freetype.Font,
                color: Color) -> Tuple[pygame.Surface, pygame.Rect]:
    """Return a surface & rectangle with text rendered on it."""
    text_surf, text_rect = font.render(text, color)
    return text_surf, text_rect


@lru_cache(maxsize=32)
def render_wrapped_text(text: str, font: pygame.freetype.Font,
                        color: Color, centered: bool, offset_y: int,
                        max_width: int) -> Tuple[pygame.Surface, pygame.Rect]:
    """Return a surface & rectangle with text rendered over several lines.

    Parameter offset_y defines the distance between lines."""
    words = text.split()
    lines = []
    lines_h = 0
    line_w, line_h = 0, 0

    # Separate text into lines, storing each line size
    while words:
        line_words = []
        while words:
            _, _, l_w, l_h = font.get_rect(
                ' '.join(line_words + words[:1]))
            if l_w > max_width:
                break
            line_w, line_h = l_w, l_h
            line_words.append(words.pop(0))
        if line_words:
            lines_h += line_h
            lines.append((' '.join(line_words), (line_w, line_h)))
        else:
            # Split word in half if it is too long
            long_word = words.pop(0)
            words.insert(0, long_word[:len(long_word)//2])
            words.insert(1, long_word[len(long_word)//2:])

    # Create transparent surface and rectangle to be returned
    final_height = lines_h + (len(lines) - 1) * offset_y if lines else lines_h
    final_surf = pygame.Surface((max_width, final_height), pygame.SRCALPHA, 32)
    final_surf.convert()
    final_rect = final_surf.get_rect()

    # Render lines on the surface
    pos_y = 0
    for line in lines:
        if centered:
            pos_x = int(max_width/2 - line[1][0]/2)
        else:
            pos_x = 0
        font.render_to(final_surf, (pos_x, pos_y), line[0], color)
        pos_y += line[1][1] + offset_y
    return final_surf, final_rect


@lru_cache(maxsize=16)
def get_surface(size: Tuple[int, int], color: Color,
                alpha: int) -> pygame.Surface:
    """Return a surface with the given size, color and opacity."""
    surface = pygame.Surface(size)
    surface.convert()
    surface.set_alpha(alpha)
    surface.fill(color)
    return surface


@lru_cache(maxsize=3)
def build_background(tile: pygame.Surface) -> pygame.Surface:
    """Return a screen-sized surface filled with a repeated given tile."""
    # Get screen and tile sizes
    screen_rect = pygame.display.get_surface().get_rect()
    screen_size = (screen_rect.w, screen_rect.h)
    tile_rect = tile.get_rect()

    # Get surface. All arguments need to be hashable
    surface = get_surface(screen_size, (0, 0, 0), 255)

    # Fill surface with repeated tile
    for i in range(0, screen_rect.w, tile_rect.w):
        for j in range(0, screen_rect.h, tile_rect.h):
            surface.blit(tile, (i, j))

    return surface
