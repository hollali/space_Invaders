from constants import WIDTH, GREEN, BROWN, GRAY, BLUE, CYAN, RED, PURPLE, WHITE, BLACK, ORANGE
from obstacles import Bunker, Rock, Crystal, ShieldBarrier, AutoTurret, OrganicPod, TeleportBarrier
from entities import (
    Boss, AsteroidTitan, NebulaGuardian, WarMachine, TheOverlord,
)


class WorldConfig:
    def __init__(
        self, name, bg_color, star_colors, accent_color,
        obstacle_factory, boss_class, enemy_config,
        boss_hp=12, boss_points=1000, boss_attack_interval=90,
    ):
        self.name = name
        self.bg_color = bg_color
        self.star_colors = star_colors
        self.accent_color = accent_color
        self.obstacle_factory = obstacle_factory
        self.boss_class = boss_class
        self.enemy_config = enemy_config
        self.boss_hp = boss_hp
        self.boss_points = boss_points
        self.boss_attack_interval = boss_attack_interval


def _world1_obstacles():
    return [
        Bunker(60, 400), Bunker(240, 400), Bunker(440, 400), Bunker(640, 400),
    ]


def _world2_obstacles():
    return [
        Rock(100, 410), Rock(300, 410), Rock(500, 410), Rock(660, 410),
        Bunker(200, 380), Bunker(560, 380),
        Crystal(400, 390),
    ]


def _world3_obstacles():
    return [
        ShieldBarrier(80, 420), ShieldBarrier(280, 420),
        ShieldBarrier(480, 420), ShieldBarrier(680, 420),
        OrganicPod(180, 390), OrganicPod(540, 390),
        Bunker(380, 400),
    ]


def _world4_obstacles():
    return [
        AutoTurret(120, 380), AutoTurret(640, 380),
        Rock(280, 410), Rock(500, 410),
        Bunker(380, 420),
        Crystal(60, 400), Crystal(720, 400),
    ]


def _world5_obstacles():
    return [
        TeleportBarrier(100, 420), TeleportBarrier(320, 420),
        TeleportBarrier(540, 420),
        Crystal(200, 400), Crystal(600, 400),
    ]


WORLDS = [
    WorldConfig(
        name="Deep Space",
        bg_color=(5, 5, 20),
        star_colors=[(80, 80, 100), (130, 130, 160), (200, 200, 230)],
        accent_color=GREEN,
        obstacle_factory=_world1_obstacles,
        boss_class=Boss,
        enemy_config={"divers": False, "armored": False, "splitting": False, "speed_mult": 1.0},
    ),
    WorldConfig(
        name="Asteroid Belt",
        bg_color=(20, 12, 5),
        star_colors=[(160, 120, 60), (120, 100, 50), (200, 170, 100)],
        accent_color=BROWN,
        obstacle_factory=_world2_obstacles,
        boss_class=AsteroidTitan,
        enemy_config={"divers": True, "armored": False, "splitting": False, "speed_mult": 1.2},
    ),
    WorldConfig(
        name="Alien Nebula",
        bg_color=(15, 5, 25),
        star_colors=[(140, 60, 200), (100, 40, 180), (200, 100, 255)],
        accent_color=PURPLE,
        obstacle_factory=_world3_obstacles,
        boss_class=NebulaGuardian,
        enemy_config={"divers": True, "armored": False, "splitting": True, "speed_mult": 1.1,
                       "kamikaze": False, "shielded": False, "fast": False},
    ),
    WorldConfig(
        name="Planet Surface",
        bg_color=(25, 10, 8),
        star_colors=[(180, 80, 40), (140, 60, 30), (220, 120, 60)],
        accent_color=RED,
        obstacle_factory=_world4_obstacles,
        boss_class=WarMachine,
        enemy_config={"divers": True, "armored": True, "splitting": False, "speed_mult": 1.3,
                       "kamikaze": True, "shielded": False, "fast": False},
    ),
    WorldConfig(
        name="The Void",
        bg_color=(3, 3, 10),
        star_colors=[(80, 40, 120), (60, 30, 100), (150, 80, 200)],
        accent_color=(120, 0, 200),
        obstacle_factory=_world5_obstacles,
        boss_class=TheOverlord,
        enemy_config={"divers": True, "armored": True, "splitting": True, "speed_mult": 1.5,
                       "kamikaze": True, "shielded": True, "fast": True},
    ),
]

LEVELS_PER_WORLD = 3
TOTAL_WORLDS = len(WORLDS)
TOTAL_LEVELS = TOTAL_WORLDS * LEVELS_PER_WORLD
