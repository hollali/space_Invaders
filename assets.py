import pygame
from constants import IMAGE_DIR, SOUND_DIR


def load_image(name):
    return pygame.image.load(IMAGE_DIR / name)


def load_sound(name):
    try:
        return pygame.mixer.Sound(SOUND_DIR / name)
    except pygame.error:
        return None
