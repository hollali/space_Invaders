import math
import random
import sqlite3
from datetime import date
from pathlib import Path

import pygame

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


def load_image(name):
    return pygame.image.load(IMAGE_DIR / name)


def load_sound(name):
    try:
        return pygame.mixer.Sound(SOUND_DIR / name)
    except pygame.error:
        return None


class HighScoreDB:
    def __init__(self, db_path=None):
        self.path = db_path or DB_FILE
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS scores ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "score INTEGER NOT NULL, "
                "name TEXT NOT NULL DEFAULT 'PLAYER', "
                "date TEXT NOT NULL)"
            )
            columns = [row[1] for row in conn.execute("PRAGMA table_info(scores)")]
            if "name" not in columns:
                conn.execute(
                    "ALTER TABLE scores ADD COLUMN name TEXT NOT NULL DEFAULT 'PLAYER'"
                )

    def add_score(self, score, name="PLAYER"):
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT INTO scores (score, name, date) VALUES (?, ?, ?)",
                (score, name, date.today().isoformat()),
            )

    def get_high_score(self):
        with sqlite3.connect(self.path) as conn:
            row = conn.execute("SELECT MAX(score) FROM scores").fetchone()
            return row[0] if row and row[0] is not None else 0

    def get_top_scores(self, limit=5):
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                "SELECT score, name, date FROM scores ORDER BY score DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return rows


class Player:
    SIZE = 32
    SPEED = 4
    INVULNERABLE_FRAMES = 90
    MAX_LIVES = 5

    def __init__(self):
        self.image = load_image("space-invaders.png")
        self.x = WIDTH // 2 - self.SIZE // 2
        self.y = HEIGHT - 120
        self.change = 0
        self.lives = 3
        self.invulnerable_frames = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.change = -self.SPEED
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.change = self.SPEED
        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                self.change = 0

    def update(self):
        self.x += self.change
        self.x = max(0, min(self.x, WIDTH - self.SIZE))
        if self.invulnerable_frames > 0:
            self.invulnerable_frames -= 1

    def draw(self, screen):
        if self.lives <= 0:
            return
        if self.invulnerable_frames > 0 and (self.invulnerable_frames // 8) % 2 == 0:
            return
        screen.blit(self.image, (self.x, self.y))

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.SIZE, self.SIZE)

    @property
    def center_x(self):
        return self.x + self.SIZE // 2


class Enemy:
    SIZE = 32

    def __init__(self, img_name, x, y, points, speed, drop, level):
        self.image = load_image(img_name)
        self.x = x
        self.y = y
        self.points = points
        self.base_speed = speed * (1 + 0.15 * (level - 1))
        self.direction = random.choice([-1, 1])
        self.speed_multiplier = 1.0
        self.drop = drop
        self.alive = True

    def update(self):
        self.x += self.direction * self.base_speed * self.speed_multiplier
        right_edge = WIDTH - self.SIZE
        if self.x <= 0:
            self.x = 0
            self.direction = 1
            self.y += self.drop
        elif self.x >= right_edge:
            self.x = right_edge
            self.direction = -1
            self.y += self.drop

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.SIZE, self.SIZE)

    @property
    def center_x(self):
        return self.x + self.SIZE // 2

    @property
    def center_y(self):
        return self.y + self.SIZE // 2


class Boss:
    SIZE = 128

    def __init__(self, level):
        self.image = pygame.transform.scale(
            load_image("alien11.png"), (self.SIZE, self.SIZE)
        )
        self.x = (WIDTH - self.SIZE) // 2
        self.y = 90
        self.base_speed = 1.2 * (1 + 0.15 * (level - 1))
        self.direction = 1
        self.max_hp = 12
        self.hp = self.max_hp
        self.points = 1000
        self.alive = True
        self.attack_timer = 90
        self.attack_counter = 0

    @property
    def enraged(self):
        return self.hp <= self.max_hp // 3

    @property
    def speed(self):
        return self.base_speed * (1.5 if self.enraged else 1.0)

    def update(self):
        self.x += self.direction * self.speed
        if self.x <= 0:
            self.x = 0
            self.direction = 1
        elif self.x + self.SIZE >= WIDTH:
            self.x = WIDTH - self.SIZE
            self.direction = -1

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.SIZE, self.SIZE)

    @property
    def center_x(self):
        return self.x + self.SIZE // 2

    @property
    def center_y(self):
        return self.y + self.SIZE // 2


class Bullet:
    SPEED = 12

    def __init__(self, center_x, y):
        self.image = load_image("bullet.png")
        self.x = center_x - self.image.get_width() // 2
        self.y = y
        self.active = True

    def update(self):
        self.y -= self.SPEED
        if self.y <= -self.image.get_height():
            self.active = False

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

    @property
    def rect(self):
        return self.image.get_rect(topleft=(self.x, self.y))

    @property
    def center_x(self):
        return self.x + self.image.get_width() // 2

    @property
    def center_y(self):
        return self.y + self.image.get_height() // 2


class EnemyBullet:
    def __init__(self, dx=0, dy=6):
        self.image = pygame.transform.flip(load_image("bullet.png"), False, True)
        self.x = 0
        self.y = -100
        self.vx = dx
        self.vy = dy
        self.active = False

    def fire(self, x, y):
        self.x = x
        self.y = y
        self.active = True

    def update(self):
        if self.active:
            self.x += self.vx
            self.y += self.vy
            if (
                self.y > HEIGHT + 20
                or self.y < -20
                or self.x < -20
                or self.x > WIDTH + 20
            ):
                self.active = False

    def draw(self, screen):
        if self.active:
            screen.blit(self.image, (self.x, self.y))

    @property
    def rect(self):
        return self.image.get_rect(topleft=(self.x, self.y))

    @property
    def center_x(self):
        return self.x + self.image.get_width() // 2

    @property
    def center_y(self):
        return self.y + self.image.get_height() // 2


class UFO:
    SIZE = 32

    def __init__(self):
        self.image = load_image("ufo.png")
        self.x = -40
        self.y = 60
        self.speed = 2
        self.points = 100
        self.active = False

    def spawn(self):
        self.active = True
        self.x = -40
        self.speed = random.choice([-1, 1]) * 2.5
        self.points = random.choice([100, 200, 300])

    def update(self):
        if self.active:
            self.x += self.speed
            if self.x < -40 or self.x > WIDTH + 40:
                self.active = False

    def draw(self, screen):
        if self.active:
            screen.blit(self.image, (self.x, self.y))

    @property
    def rect(self):
        return self.image.get_rect(topleft=(self.x, self.y))


class Explosion:
    DURATION = 16

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.frame = 0

    def update(self):
        self.frame += 1

    @property
    def done(self):
        return self.frame >= self.DURATION

    def draw(self, screen):
        for i, color in enumerate((YELLOW, ORANGE, RED)):
            radius = 8 + self.frame - i * 4
            if radius > 2:
                pygame.draw.circle(screen, color, (int(self.x), int(self.y)), radius, 2)


class PowerUp:
    SIZE = 20
    FALL_SPEED = 3

    TYPES = {
        "rapid": {"color": ORANGE, "label": "R"},
        "shield": {"color": BLUE, "label": "S"},
        "life": {"color": GREEN, "label": "+"},
        "bomb": {"color": RED, "label": "B"},
        "multi": {"color": PURPLE, "label": "M"},
    }

    def __init__(self, kind, x, y, font):
        self.kind = kind
        self.x = x
        self.y = y
        self.font = font
        self.color = self.TYPES[kind]["color"]
        self.label = self.TYPES[kind]["label"]
        self.active = True

    def update(self):
        self.y += self.FALL_SPEED
        if self.y > HEIGHT:
            self.active = False

    def draw(self, screen):
        pygame.draw.circle(
            screen, self.color, (int(self.x), int(self.y)), self.SIZE // 2, 2
        )
        text = self.font.render(self.label, True, self.color)
        screen.blit(text, text.get_rect(center=(int(self.x), int(self.y))))

    @property
    def rect(self):
        half = self.SIZE // 2
        return pygame.Rect(self.x - half, self.y - half, self.SIZE, self.SIZE)


class Bunker:
    WIDTH = 96
    HEIGHT = 56
    COLOR = (0, 180, 120)
    COLKEY = (0, 0, 0)

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.surface = self._build_surface()

    def _build_surface(self):
        w, h = self.WIDTH, self.HEIGHT
        surface = pygame.Surface((w, h)).convert()
        surface.fill(self.COLKEY)
        pygame.draw.rect(
            surface, self.COLOR, (8, 18, w - 16, h - 18), border_radius=10
        )
        pygame.draw.rect(surface, self.COLKEY, (w // 2 - 12, 0, 24, 26))
        pygame.draw.rect(surface, self.COLKEY, (14, 0, 24, 16))
        pygame.draw.rect(surface, self.COLKEY, (w - 38, 0, 24, 16))
        surface.set_colorkey(self.COLKEY)
        return surface

    def is_solid(self, x, y):
        if 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT:
            return self.surface.get_at((x, y))[:3] != self.COLKEY
        return False

    def destroy_chunk(self, x, y):
        pygame.draw.circle(self.surface, self.COLKEY, (x, y), 12)

    def draw(self, screen):
        screen.blit(self.surface, (self.x, self.y))

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)


class Game:
    FIRE_COOLDOWN = 15
    MAX_ENEMY_BULLETS = 4
    MAX_LEVEL = 5
    POWERUP_CHANCE = 0.08

    def __init__(self, db_path=None):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Space Invaders")
        pygame.display.set_icon(load_image("space.png"))
        self.clock = pygame.time.Clock()

        self.background = load_image("space_image.jpg")
        self.font = pygame.font.Font("freesansbold.ttf", 32)
        self.small_font = pygame.font.Font("freesansbold.ttf", 24)
        self.title_font = pygame.font.Font("freesansbold.ttf", 64)
        self.over_font = pygame.font.Font("freesansbold.ttf", 64)

        self.laser_sound = load_sound("laser.wav")
        self.explosion_sound = load_sound("explosion.wav")

        try:
            pygame.mixer.music.load(SOUND_DIR / "background.wav")
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

        self.muted = False
        self.db = HighScoreDB(db_path)
        self.high_score = self.db.get_high_score()
        self.state = "menu"
        self.running = True
        self.new_game()

    def new_game(self):
        self.score = 0
        self.level = 1
        self._score_recorded = False
        self.player = Player()
        self.spawn_wave()

    def spawn_wave(self):
        self.bullets = []
        self.enemy_bullets = []
        self.powerups = []
        self.explosions = []
        self.fire_cooldown = 0
        self.rapid_frames = 0
        self.multishot_frames = 0

        if self.level == self.MAX_LEVEL:
            self.boss = Boss(self.level)
            self.enemies = [self.boss]
            self.wave_total = 1
            self.ufo = UFO()
            self.ufo.active = False
            self.ufo_countdown = 10 ** 9
        else:
            self.boss = None
            self.enemies = []
            cols = 8
            rows = min(2 + self.level, 5)
            gap = 48
            start_x = (WIDTH - (cols - 1) * gap - Enemy.SIZE) // 2
            start_y = 70
            for row in range(rows):
                img_name, points, speed = self.enemy_type_for_row(row)
                for col in range(cols):
                    self.enemies.append(
                        Enemy(
                            img_name,
                            start_x + col * gap,
                            start_y + row * gap,
                            points,
                            speed,
                            40,
                            self.level,
                        )
                    )
            self.wave_total = len(self.enemies)
            self.ufo = UFO()
            self.ufo_countdown = random.randint(600, 1200)

        self.bunkers = [
            Bunker(60 + i * (Bunker.WIDTH + 90), 400) for i in range(4)
        ]

    def enemy_type_for_row(self, row):
        if row <= 1:
            return "alien11.png", 30, 1.3
        elif row <= 3:
            return "alien2.png", 20, 0.9
        else:
            return "alien.png", 10, 0.6

    def update_enemy_speeds(self):
        alive = len(self.enemies)
        if alive == 0:
            return
        multiplier = 1 + 1.5 * (1 - alive / self.wave_total)
        for enemy in self.enemies:
            if hasattr(enemy, "speed_multiplier"):
                enemy.speed_multiplier = multiplier

    def advance_level(self):
        if self.level >= self.MAX_LEVEL:
            return
        self.level += 1
        self.spawn_wave()
        self.state = "playing"

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update()
            self.draw()
        pygame.quit()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if getattr(pygame, "WINDOWFOCUSLOST", None) is not None and event.type == pygame.WINDOWFOCUSLOST:
            if self.state == "playing":
                self.state = "paused"
            return
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            if self.state == "playing":
                self.state = "paused"
            elif self.state == "paused":
                self.state = "playing"
            elif self.state == "name_entry":
                self.submit_score_name()
            elif self.state in ("menu", "game_over", "win"):
                self.running = False
            return

        if event.key == pygame.K_m:
            self.toggle_mute()
            return

        if self.state == "menu":
            if event.key == pygame.K_SPACE:
                self.new_game()
                self.state = "playing"
        elif self.state == "paused":
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.state = "playing"
        elif self.state == "name_entry":
            if event.key == pygame.K_RETURN:
                self.submit_score_name()
            elif event.key == pygame.K_BACKSPACE:
                self.entered_name = self.entered_name[:-1]
            elif len(self.entered_name) < 3:
                key_name = pygame.key.name(event.key)
                if key_name.isalpha() and len(key_name) == 1:
                    self.entered_name += key_name.upper()
        elif self.state in ("game_over", "win"):
            if event.key == pygame.K_r:
                self.new_game()
                self.state = "playing"
            elif event.key == pygame.K_SPACE:
                self.state = "menu"
        elif self.state == "level_clear":
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.advance_level()
        elif self.state == "playing":
            self.player.handle_event(event)

    def update(self):
        if self.state == "playing":
            self.update_playing()
        elif self.state == "level_clear":
            self.level_clear_timer -= 1
            if self.level_clear_timer <= 0:
                self.advance_level()

    def update_playing(self):
        keys = pygame.key.get_pressed()
        self.player.update()

        for bullet in self.bullets:
            bullet.update()
        for bullet in self.bullets:
            if bullet.active and self.bullet_hits_bunker(bullet):
                bullet.active = False
        self.bullets = [b for b in self.bullets if b.active]

        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        if self.rapid_frames > 0:
            self.rapid_frames -= 1
        if self.multishot_frames > 0:
            self.multishot_frames -= 1
        cooldown = self.FIRE_COOLDOWN // 2 if self.rapid_frames > 0 else self.FIRE_COOLDOWN
        if keys[pygame.K_SPACE] and self.fire_cooldown <= 0:
            self.fire_bullets()
            self.fire_cooldown = cooldown
            self.play_sound(self.laser_sound)

        for enemy in self.enemies:
            enemy.update()
            if enemy.rect.bottom >= self.player.y:
                self.trigger_game_over()
                return
            if isinstance(enemy, Boss):
                enemy.attack_timer -= 1
                if enemy.attack_timer <= 0:
                    enemy.attack_timer = 90 if not enemy.enraged else 60
                    self.boss_fire(enemy)
            for bullet in self.bullets:
                if bullet.rect.colliderect(enemy.rect):
                    bullet.active = False
                    if isinstance(enemy, Boss):
                        self.on_boss_hit(enemy)
                    else:
                        self.on_enemy_destroyed(enemy)
                    break

        if self.check_wave_cleared():
            return
        self.update_enemy_speeds()

        self.fire_enemy_bullets()
        for eb in self.enemy_bullets:
            eb.update()
        for eb in self.enemy_bullets:
            if eb.active and self.bullet_hits_bunker(eb):
                eb.active = False
        self.enemy_bullets = [eb for eb in self.enemy_bullets if eb.active]

        self.check_player_hit()
        if self.state != "playing":
            return

        for powerup in self.powerups:
            powerup.update()
            if powerup.active and powerup.rect.colliderect(self.player.rect):
                self.apply_powerup(powerup)
                self.play_sound(self.explosion_sound)
                powerup.active = False
        self.powerups = [p for p in self.powerups if p.active]
        if self.check_wave_cleared():
            return

        self.ufo_countdown -= 1
        if not self.ufo.active and self.ufo_countdown <= 0:
            self.ufo.spawn()
            self.ufo_countdown = random.randint(600, 1200)
        if self.ufo.active:
            self.ufo.update()
            for bullet in self.bullets:
                if bullet.rect.colliderect(self.ufo.rect):
                    bullet.active = False
                    self.score += self.ufo.points
                    self.check_high_score()
                    self.explosions.append(
                        Explosion(
                            self.ufo.x + UFO.SIZE // 2, self.ufo.y + UFO.SIZE // 2
                        )
                    )
                    self.play_sound(self.explosion_sound)
                    self.ufo.active = False
                    break

        for ex in self.explosions:
            ex.update()
        self.explosions = [ex for ex in self.explosions if not ex.done]

    def fire_bullets(self):
        offsets = (-12, 0, 12) if self.multishot_frames > 0 else (0,)
        for offset in offsets:
            self.bullets.append(Bullet(self.player.center_x + offset, self.player.y))

    def check_wave_cleared(self):
        self.enemies = [e for e in self.enemies if e.alive]
        if self.enemies:
            return False
        if self.level >= self.MAX_LEVEL:
            self.check_high_score()
            self.begin_score_entry("win")
        else:
            self.state = "level_clear"
            self.level_clear_timer = 120
        return True

    def begin_score_entry(self, final_state):
        if self.score > 0 and self.score_qualifies():
            self.state = "name_entry"
            self.entered_name = ""
            self._pending_final_state = final_state
        else:
            self.finish_game(final_state)

    def score_qualifies(self):
        top = self.db.get_top_scores(5)
        if len(top) < 5:
            return True
        return self.score > top[-1][0]

    def finish_game(self, final_state):
        self._score_recorded = True
        self.high_score = self.db.get_high_score()
        self.state = final_state

    def submit_score_name(self):
        name = (self.entered_name or "AAA").ljust(3, "A")[:3]
        self.db.add_score(self.score, name)
        self.finish_game(self._pending_final_state)

    def fire_enemy_bullets(self):
        if self.boss is not None:
            return
        prob = 0.0005 * (1 + 0.15 * (self.level - 1))
        active = sum(1 for b in self.enemy_bullets if b.active)
        if active >= self.MAX_ENEMY_BULLETS:
            return
        for enemy in self.enemies:
            if random.random() < prob:
                enemy_bullet = EnemyBullet()
                enemy_bullet.fire(enemy.center_x, enemy.y + Enemy.SIZE)
                self.enemy_bullets.append(enemy_bullet)
                self.play_sound(self.laser_sound)
                break

    def boss_fire(self, boss):
        spread = 5 if boss.enraged else 3
        speed = 3.5
        for i in range(spread):
            t = i - (spread - 1) / 2
            bullet = EnemyBullet(dx=t * 1.4, dy=speed)
            bullet.fire(boss.center_x, boss.y + boss.SIZE - 10)
            self.enemy_bullets.append(bullet)
        boss.attack_counter += 1
        if boss.enraged and boss.attack_counter % 3 == 0:
            self.enemy_bullets.append(self.aimed_bullet(boss))
        self.play_sound(self.laser_sound)

    def aimed_bullet(self, boss):
        dx = self.player.center_x - boss.center_x
        dy = self.player.y - (boss.y + boss.SIZE)
        dist = math.hypot(dx, dy) or 1
        bullet = EnemyBullet(dx=dx / dist * 4, dy=dy / dist * 4)
        bullet.fire(boss.center_x, boss.y + boss.SIZE)
        return bullet

    def bullet_hits_bunker(self, bullet):
        for bunker in self.bunkers:
            if bullet.rect.colliderect(bunker.rect):
                local_x = int(bullet.center_x - bunker.x)
                local_y = int(bullet.center_y - bunker.y)
                if bunker.is_solid(local_x, local_y):
                    bunker.destroy_chunk(local_x, local_y)
                    return True
        return False

    def on_boss_hit(self, boss):
        boss.hp -= 1
        self.explosions.append(
            Explosion(boss.center_x + random.randint(-40, 40), boss.center_y + random.randint(-40, 40))
        )
        self.play_sound(self.explosion_sound)
        if boss.hp <= 0:
            boss.alive = False
            self.score += boss.points
            self.check_high_score()
            for _ in range(8):
                self.explosions.append(
                    Explosion(boss.center_x + random.randint(-60, 60), boss.center_y + random.randint(-40, 60))
                )
            self.play_sound(self.explosion_sound)

    def on_enemy_destroyed(self, enemy):
        enemy.alive = False
        self.score += enemy.points
        self.check_high_score()
        self.explosions.append(Explosion(enemy.center_x, enemy.center_y))
        self.play_sound(self.explosion_sound)
        if random.random() < self.POWERUP_CHANCE:
            kind = random.choice(list(PowerUp.TYPES))
            self.powerups.append(
                PowerUp(kind, enemy.center_x, enemy.center_y, self.small_font)
            )

    def apply_powerup(self, powerup):
        kind = powerup.kind
        if kind == "rapid":
            self.rapid_frames = 600
        elif kind == "shield":
            self.player.invulnerable_frames = 300
        elif kind == "life":
            self.player.lives = min(self.player.lives + 1, Player.MAX_LIVES)
        elif kind == "multi":
            self.multishot_frames = 600
        elif kind == "bomb":
            for enemy in self.enemies:
                enemy.alive = False
                self.score += enemy.points
                self.explosions.append(Explosion(enemy.center_x, enemy.center_y))
            self.check_high_score()

    def check_player_hit(self):
        if self.player.invulnerable_frames > 0:
            return
        for eb in self.enemy_bullets:
            if eb.active and eb.rect.colliderect(self.player.rect):
                eb.active = False
                self.explosions.append(Explosion(self.player.center_x, self.player.y))
                self.play_sound(self.explosion_sound)
                self.player.lives -= 1
                if self.player.lives <= 0:
                    self.trigger_game_over()
                else:
                    self.player.invulnerable_frames = Player.INVULNERABLE_FRAMES
                    self.enemy_bullets = []
                break

    def trigger_game_over(self):
        self.check_high_score()
        self.begin_score_entry("game_over")
        self.explosions.append(Explosion(self.player.center_x, self.player.y))
        self.play_sound(self.explosion_sound)

    def check_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score

    def play_sound(self, sound):
        if not self.muted and sound:
            sound.play()

    def toggle_mute(self):
        self.muted = not self.muted
        pygame.mixer.music.set_volume(0.0 if self.muted else 1.0)

    def draw(self):
        self.screen.fill(BLACK)
        self.screen.blit(self.background, (0, 0))

        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_game()
            if self.state == "paused":
                self.draw_center_text("PAUSED", self.over_font, 240)
                self.draw_center_text("Press ESC to resume", self.small_font, 330)
            elif self.state == "level_clear":
                self.draw_center_text(f"LEVEL {self.level} CLEARED!", self.over_font, 240)
                self.draw_center_text("Press SPACE to continue", self.small_font, 330)
            elif self.state == "name_entry":
                self.draw_center_text("NEW HIGH SCORE! Enter your name:", self.font, 210)
                self.draw_center_text(self.entered_name + "_", self.title_font, 275, YELLOW)
                self.draw_center_text(
                    "Type A-Z, BACKSPACE to fix, ENTER to save", self.small_font, 350
                )
            elif self.state == "game_over":
                self.draw_center_text("GAME OVER", self.over_font, 180)
                self.draw_center_text(
                    f"Score: {self.score}    High Score: {self.high_score}",
                    self.font,
                    265,
                    YELLOW,
                )
                self.draw_leaderboard_block(325)
                self.draw_center_text(
                    "Press R to retry, SPACE for menu", self.small_font, 545
                )
            elif self.state == "win":
                self.draw_center_text("YOU WIN!", self.over_font, 220, YELLOW)
                self.draw_center_text(
                    f"Score: {self.score}    High Score: {self.high_score}",
                    self.font,
                    310,
                    YELLOW,
                )
                self.draw_center_text(
                    "Press R to play again, SPACE for menu", self.small_font, 360
                )

        pygame.display.update()

    def draw_game(self):
        self.ufo.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        for bunker in self.bunkers:
            bunker.draw(self.screen)
        for powerup in self.powerups:
            powerup.draw(self.screen)
        self.player.draw(self.screen)
        for bullet in self.bullets:
            bullet.draw(self.screen)
        for eb in self.enemy_bullets:
            eb.draw(self.screen)
        for ex in self.explosions:
            ex.draw(self.screen)
        if self.boss is not None and self.boss.alive:
            self.draw_boss_health(self.boss)
        self.draw_hud()

    def draw_boss_health(self, boss):
        bar_width = boss.SIZE
        bar_height = 10
        x = boss.x
        y = boss.y - 22
        pygame.draw.rect(self.screen, RED, (x, y, bar_width, bar_height))
        pygame.draw.rect(
            self.screen,
            GREEN,
            (x, y, int(bar_width * boss.hp / boss.max_hp), bar_height),
        )
        pygame.draw.rect(self.screen, WHITE, (x, y, bar_width, bar_height), 2)

    def draw_hud(self):
        self.screen.blit(self.font.render(f"Score: {self.score}", True, WHITE), (10, 10))
        self.screen.blit(self.font.render(f"High: {self.high_score}", True, WHITE), (10, 50))
        self.screen.blit(self.font.render(f"Level: {self.level}", True, WHITE), (640, 10))
        self.screen.blit(self.small_font.render(f"Lives: {self.player.lives}", True, WHITE), (640, 50))
        if self.rapid_frames > 0:
            self.screen.blit(self.small_font.render("RAPID", True, ORANGE), (640, 90))
        if self.multishot_frames > 0:
            self.screen.blit(self.small_font.render("MULTI", True, PURPLE), (640, 120))
        if self.muted:
            self.screen.blit(self.small_font.render("MUTED", True, RED), (10, 90))

    def draw_menu(self):
        self.draw_center_text("SPACE INVADERS", self.title_font, 140)
        if self.high_score > 0:
            self.draw_center_text(f"High Score: {self.high_score}", self.font, 230, YELLOW)
        self.draw_center_text("Press SPACE to Start", self.font, 290)
        self.draw_center_text(
            "Arrows/WASD: move   SPACE: shoot   ESC: pause   M: mute",
            self.small_font,
            345,
        )
        self.draw_leaderboard_block(400)

    def draw_leaderboard_block(self, start_y):
        rows = self.db.get_top_scores(5)
        if not rows:
            return
        self.draw_center_text("TOP SCORES", self.small_font, start_y)
        for i, (score, name, when) in enumerate(rows):
            self.draw_center_text(
                f"{i + 1}.  {name}  {score}", self.small_font, start_y + 26 + i * 26, YELLOW
            )

    def draw_center_text(self, text, font, y, color=WHITE):
        surface = font.render(text, True, color)
        self.screen.blit(surface, surface.get_rect(center=(WIDTH // 2, y)))


if __name__ == "__main__":
    Game().run()
