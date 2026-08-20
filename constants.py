from pathlib import Path

WIDTH, HEIGHT = 800, 600
FPS = 60

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "images"
SOUND_DIR = BASE_DIR / "sounds"
DB_FILE = BASE_DIR / "scores.db"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 30, 30)
YELLOW = (255, 220, 80)
ORANGE = (255, 140, 40)
BLUE = (80, 140, 255)
GREEN = (90, 220, 90)
PURPLE = (200, 120, 255)
CYAN = (80, 220, 220)
BROWN = (160, 120, 60)
GRAY = (150, 150, 160)
PINK = (255, 100, 150)
DARK_RED = (120, 20, 20)
