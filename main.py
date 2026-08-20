from datetime import date

from constants import *
from assets import load_image, load_sound
from db import HighScoreDB
from effects import Particle, FloatingText, Starfield, Explosion
from entities import (
    Player, Enemy, Diver, ArmoredEnemy, SplittingEnemy,
    FastEnemy, ShieldedEnemy, KamikazeEnemy,
    Boss, AsteroidTitan, NebulaGuardian, WarMachine, TheOverlord,
    Bullet, EnemyBullet, UFO, PowerUp,
)
from obstacles import (
    Bunker, Rock, Crystal, ShieldBarrier, AutoTurret, OrganicPod, TeleportBarrier,
)
from worlds import WORLDS, LEVELS_PER_WORLD, TOTAL_WORLDS, TOTAL_LEVELS, WorldConfig
from game import Game

__all__ = [
    "Game", "HighScoreDB", "date",
    "Player", "Enemy", "Diver", "ArmoredEnemy", "SplittingEnemy",
    "FastEnemy", "ShieldedEnemy", "KamikazeEnemy",
    "Boss", "AsteroidTitan", "NebulaGuardian", "WarMachine", "TheOverlord",
    "Bullet", "EnemyBullet", "UFO", "PowerUp",
    "Bunker", "Rock", "Crystal", "ShieldBarrier", "AutoTurret",
    "OrganicPod", "TeleportBarrier",
    "Particle", "FloatingText", "Starfield", "Explosion",
    "WORLDS", "LEVELS_PER_WORLD", "TOTAL_WORLDS", "TOTAL_LEVELS", "WorldConfig",
    "load_image", "load_sound",
    "WIDTH", "HEIGHT", "FPS",
    "WHITE", "BLACK", "RED", "YELLOW", "ORANGE", "BLUE", "GREEN", "PURPLE",
]

if __name__ == "__main__":
    Game().run()
