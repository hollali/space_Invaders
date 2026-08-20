import math
import random
import pygame
from constants import (
    WIDTH, HEIGHT, WHITE, BLACK, RED, YELLOW, ORANGE, BLUE, GREEN, PURPLE, GRAY,
    CYAN, BROWN, PINK, DARK_RED,
)
from assets import load_image, load_sound


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


class Diver(Enemy):
    SIZE = 32
    DIVE_SPEED = 3.5

    def __init__(self, img_name, x, y, points, speed, drop, level):
        super().__init__(img_name, x, y, points, speed, drop, level)
        self.diving = False
        self.dive_timer = random.randint(180, 400)
        self.target_x = x
        self.points = points + 15

    def update(self):
        if self.diving:
            self.y += self.DIVE_SPEED
            dx = self.target_x - self.x
            self.x += max(-2, min(2, dx * 0.05))
            if self.y > HEIGHT + 40:
                self.alive = False
        else:
            super().update()
            self.dive_timer -= 1
            if self.dive_timer <= 0:
                if abs(self.center_x - self.target_x) < 100:
                    self.diving = True
                else:
                    self.dive_timer = 30

    def draw(self, screen):
        if self.diving:
            trail_y = self.y - 15
            for i in range(3):
                alpha_y = trail_y - i * 8
                if alpha_y > 0:
                    trail_size = 3 - i
                    if trail_size > 0:
                        pygame.draw.circle(
                            screen, (200, 60, 60),
                            (int(self.center_x), int(alpha_y)), trail_size,
                        )
        screen.blit(self.image, (self.x, self.y))


class ArmoredEnemy(Enemy):
    def __init__(self, img_name, x, y, points, speed, drop, level):
        super().__init__(img_name, x, y, points + 10, speed, drop, level)
        self.armor_hp = 2

    def hit(self):
        self.armor_hp -= 1
        if self.armor_hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))
        if self.armor_hp > 0:
            cx = self.x + self.SIZE // 2
            cy = self.y + self.SIZE // 2
            pygame.draw.circle(screen, GRAY, (cx, cy), self.SIZE // 2, 2)


class SplittingEnemy(Enemy):
    def __init__(self, img_name, x, y, points, speed, drop, level):
        super().__init__(img_name, x, y, points, speed, drop, level)
        self.split_on_death = True

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))
        cx = self.x + self.SIZE // 2
        cy = self.y + self.SIZE // 2
        pygame.draw.line(screen, PURPLE, (cx - 4, cy - 4), (cx + 4, cy + 4), 2)
        pygame.draw.line(screen, PURPLE, (cx + 4, cy - 4), (cx - 4, cy + 4), 2)


class FastEnemy(Enemy):
    def __init__(self, img_name, x, y, points, speed, drop, level):
        super().__init__(img_name, x, y, points + 5, speed * 1.8, drop, level)

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))
        cx = self.x + self.SIZE // 2
        cy = self.y + self.SIZE // 2
        pygame.draw.circle(screen, CYAN, (cx, cy), self.SIZE // 2, 2)


class ShieldedEnemy(Enemy):
    def __init__(self, img_name, x, y, points, speed, drop, level):
        super().__init__(img_name, x, y, points + 10, speed, drop, level)
        self.shield_hp = 2

    def hit(self):
        self.shield_hp -= 1
        if self.shield_hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))
        if self.shield_hp > 0:
            cx = self.x + self.SIZE // 2
            cy = self.y + self.SIZE // 2
            pygame.draw.circle(screen, BLUE, (cx, cy), self.SIZE // 2 + 2, 2)


class KamikazeEnemy(Enemy):
    KAMIKAZE_SPEED = 4.0

    def __init__(self, img_name, x, y, points, speed, drop, level):
        super().__init__(img_name, x, y, points + 20, speed, drop, level)
        self.diving = False
        self.dive_timer = random.randint(120, 300)

    def update(self):
        if self.diving:
            self.y += self.KAMIKAZE_SPEED
            if self.y > HEIGHT + 40:
                self.alive = False
        else:
            super().update()
            self.dive_timer -= 1
            if self.dive_timer <= 0:
                self.diving = True

    def draw(self, screen):
        if self.diving:
            trail_y = self.y - 10
            for i in range(2):
                ty = trail_y - i * 6
                if ty > 0:
                    pygame.draw.circle(screen, RED, (int(self.center_x), int(ty)), 2)
        screen.blit(self.image, (self.x, self.y))
        if not self.diving:
            cx = self.x + self.SIZE // 2
            cy = self.y + self.SIZE // 2
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.008))
            r = int(4 + 4 * pulse)
            pygame.draw.circle(screen, RED, (cx, cy), r, 1)


class Boss:
    SIZE = 128

    def __init__(self, level):
        self.image = pygame.transform.scale(
            load_image("alien11.png"), (self.SIZE, self.SIZE),
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


class AsteroidTitan(Boss):
    SIZE = 160

    def __init__(self, level):
        super().__init__(level)
        self.max_hp = 18
        self.hp = self.max_hp
        self.points = 2000
        self.image = pygame.transform.scale(
            load_image("alien11.png"), (self.SIZE, self.SIZE),
        )
        self.attack_timer = 70

    def draw(self, screen):
        tint = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
        tint.fill((160, 100, 40, 60))
        screen.blit(self.image, (self.x, self.y))
        screen.blit(tint, (self.x, self.y))


class NebulaGuardian(Boss):
    SIZE = 140

    def __init__(self, level):
        super().__init__(level)
        self.max_hp = 16
        self.hp = self.max_hp
        self.points = 2500
        self.image = pygame.transform.scale(
            load_image("alien11.png"), (self.SIZE, self.SIZE),
        )
        self.teleport_timer = 300
        self.attack_timer = 80

    def update(self):
        self.teleport_timer -= 1
        if self.teleport_timer <= 0:
            self.x = random.randint(0, WIDTH - self.SIZE)
            self.teleport_timer = 300
        else:
            self.x += self.direction * self.speed * 0.5
            if self.x <= 0:
                self.x = 0
                self.direction = 1
            elif self.x + self.SIZE >= WIDTH:
                self.x = WIDTH - self.SIZE
                self.direction = -1

    def draw(self, screen):
        tint = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
        tint.fill((140, 40, 200, 60))
        screen.blit(self.image, (self.x, self.y))
        screen.blit(tint, (self.x, self.y))
        if self.teleport_timer < 30:
            alpha = int(100 * (self.teleport_timer / 30))
            flash = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
            flash.fill((255, 255, 255, alpha))
            screen.blit(flash, (self.x, self.y))


class WarMachine(Boss):
    SIZE = 150

    def __init__(self, level):
        super().__init__(level)
        self.max_hp = 22
        self.hp = self.max_hp
        self.points = 3000
        self.image = pygame.transform.scale(
            load_image("alien11.png"), (self.SIZE, self.SIZE),
        )
        self.attack_timer = 60

    def update(self):
        self.x += self.direction * self.speed * 0.3
        if self.x <= 0:
            self.x = 0
            self.direction = 1
        elif self.x + self.SIZE >= WIDTH:
            self.x = WIDTH - self.SIZE
            self.direction = -1

    def draw(self, screen):
        tint = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
        tint.fill((180, 40, 40, 60))
        screen.blit(self.image, (self.x, self.y))
        screen.blit(tint, (self.x, self.y))
        for offset in (-30, 30):
            tx = self.center_x + offset
            ty = self.y + self.SIZE - 10
            pygame.draw.circle(screen, GRAY, (int(tx), int(ty)), 8)
            pygame.draw.circle(screen, RED, (int(tx), int(ty)), 4)


class TheOverlord(Boss):
    SIZE = 170

    def __init__(self, level):
        super().__init__(level)
        self.max_hp = 30
        self.hp = self.max_hp
        self.points = 5000
        self.image = pygame.transform.scale(
            load_image("alien11.png"), (self.SIZE, self.SIZE),
        )
        self.attack_timer = 50
        self.phase = 1

    def update(self):
        if self.enraged and self.phase == 1:
            self.phase = 2
        self.x += self.direction * self.speed
        if self.x <= 0:
            self.x = 0
            self.direction = 1
        elif self.x + self.SIZE >= WIDTH:
            self.x = WIDTH - self.SIZE
            self.direction = -1

    def draw(self, screen):
        tint = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
        tint.fill((60, 0, 80, 80))
        screen.blit(self.image, (self.x, self.y))
        screen.blit(tint, (self.x, self.y))
        pulse = 0.6 + 0.4 * math.sin(pygame.time.get_ticks() * 0.005)
        aura_r = int(self.SIZE // 2 + 10 * pulse)
        aura_s = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura_s, (120, 0, 200, 30), (aura_r, aura_r), aura_r)
        screen.blit(aura_s, (self.center_x - aura_r, self.center_y - aura_r))


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


class SpreadBullet(Bullet):
    def __init__(self, center_x, y, angle_deg):
        super().__init__(center_x, y)
        rad = math.radians(angle_deg)
        self.vx = math.sin(rad) * self.SPEED
        self.vy = -math.cos(rad) * self.SPEED

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.y <= -20 or self.x < -20 or self.x > WIDTH + 20:
            self.active = False


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


class PowerUp:
    SIZE = 20
    FALL_SPEED = 3

    TYPES = {
        "rapid": {"color": ORANGE, "label": "R"},
        "shield": {"color": BLUE, "label": "S"},
        "life": {"color": GREEN, "label": "+"},
        "bomb": {"color": RED, "label": "B"},
        "multi": {"color": PURPLE, "label": "M"},
        "pierce": {"color": CYAN, "label": "P"},
        "slow": {"color": BROWN, "label": "W"},
        "score2x": {"color": YELLOW, "label": "2"},
        "recall": {"color": (80, 220, 220), "label": "X"},
        "mega_bomb": {"color": DARK_RED, "label": "!"},
        "unlock_spread": {"color": PURPLE, "label": "W2"},
        "unlock_missile": {"color": RED, "label": "W3"},
        "unlock_plasma": {"color": CYAN, "label": "W4"},
        "unlock_laser": {"color": ORANGE, "label": "W5"},
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
            screen, self.color, (int(self.x), int(self.y)), self.SIZE // 2, 2,
        )
        text = self.font.render(self.label, True, self.color)
        screen.blit(text, text.get_rect(center=(int(self.x), int(self.y))))

    @property
    def rect(self):
        half = self.SIZE // 2
        return pygame.Rect(self.x - half, self.y - half, self.SIZE, self.SIZE)


class Missile(Bullet):
    SPEED = 6
    RADIUS = 60
    DAMAGE = 3

    def __init__(self, center_x, y):
        super().__init__(center_x, y)
        self.image = pygame.Surface((8, 16))
        self.image.fill(RED)
        pygame.draw.ellipse(self.image, ORANGE, (1, 2, 6, 12))
        self.x = center_x - 4
        self.y = y

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))
        trail_y = self.y + 16
        for i in range(3):
            alpha = 200 - i * 60
            r = 3 - i
            if r > 0 and trail_y + i * 5 < HEIGHT:
                pygame.draw.circle(
                    screen, (255, 200 - i * 50, 50),
                    (int(self.center_x), int(trail_y + i * 5)), r,
                )


class PlasmaBolt(Bullet):
    SPEED = 8
    BOUNCES = 3

    def __init__(self, center_x, y):
        super().__init__(center_x, y)
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, CYAN, (5, 5), 5)
        pygame.draw.circle(self.image, WHITE, (5, 5), 2)
        self.x = center_x - 5
        self.y = y
        self.bounces_left = self.BOUNCES

    def update(self):
        self.y -= self.SPEED
        if self.y <= -10:
            self.active = False

    def draw(self, screen):
        t = pygame.time.get_ticks() * 0.01
        glow_r = int(7 + 3 * math.sin(t))
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (80, 220, 220, 40), (glow_r, glow_r), glow_r)
        screen.blit(
            glow,
            (int(self.center_x) - glow_r, int(self.center_y) - glow_r),
        )
        screen.blit(self.image, (self.x, self.y))


class LaserBeam:
    DURATION = 8

    def __init__(self, center_x, player_y):
        self.x = center_x
        self.y_start = player_y
        self.y_end = -10
        self.active = True
        self.timer = self.DURATION
        self.width = 6
        self.damage_timer = 0

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.active = False

    @property
    def rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y_end, self.width, self.y_start - self.y_end)

    def draw(self, screen):
        alpha = int(255 * (self.timer / self.DURATION))
        for i in range(3):
            w = self.width - i * 2
            if w > 0:
                color = (
                    min(255, 200 + i * 20),
                    min(255, 50 + i * 30),
                    50,
                )
                pygame.draw.line(
                    screen, color,
                    (int(self.x) + i - 1, int(self.y_start)),
                    (int(self.x) + i - 1, int(self.y_end)),
                    max(1, w),
                )
        flash = pygame.Surface((self.width + 12, self.y_start - self.y_end), pygame.SRCALPHA)
        flash.fill((255, 100, 100, max(0, alpha // 4)))
        screen.blit(flash, (int(self.x) - 6, int(self.y_end)))


class Weapon:
    BLASTER = "blaster"
    SPREAD = "spread"
    MISSILE = "missile"
    PLASMA = "plasma"
    LASER = "laser"

    STATS = {
        "blaster": {"label": "Blaster", "color": WHITE, "cooldown": 15, "damage": 1},
        "spread":  {"label": "Spread",  "color": PURPLE, "cooldown": 18, "damage": 1},
        "missile": {"label": "Missile", "color": RED,    "cooldown": 30, "damage": 3},
        "plasma":  {"label": "Plasma",  "color": CYAN,   "cooldown": 22, "damage": 2},
        "laser":   {"label": "Laser",   "color": ORANGE, "cooldown": 40, "damage": 1},
    }

    ALL = [BLASTER, SPREAD, MISSILE, PLASMA, LASER]
    KEY_BINDINGS = {
        pygame.K_1: BLASTER,
        pygame.K_2: SPREAD,
        pygame.K_3: MISSILE,
        pygame.K_4: PLASMA,
        pygame.K_5: LASER,
    }

    def __init__(self):
        self.current = self.BLASTER
        self.unlocked = {self.BLASTER}

    def switch_to(self, name):
        if name in self.unlocked:
            self.current = name

    def next_weapon(self):
        idx = self.ALL.index(self.current)
        for _ in range(len(self.ALL)):
            idx = (idx + 1) % len(self.ALL)
            if self.ALL[idx] in self.unlocked:
                self.current = self.ALL[idx]
                return

    def unlock(self, name):
        if name in self.STATS:
            self.unlocked.add(name)

    @property
    def cooldown(self):
        return self.STATS[self.current]["cooldown"]

    @property
    def color(self):
        return self.STATS[self.current]["color"]

    @property
    def label(self):
        return self.STATS[self.current]["label"]

    @property
    def damage(self):
        return self.STATS[self.current]["damage"]
