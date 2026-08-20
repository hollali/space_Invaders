import math
import random
import pygame
from constants import WIDTH, HEIGHT, GREEN, BROWN, GRAY, BLUE, CYAN, RED, PURPLE, WHITE, BLACK


class Bunker:
    WIDTH = 96
    HEIGHT = 56
    COLOR = GREEN
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
            surface, self.COLOR, (8, 18, w - 16, h - 18), border_radius=10,
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

    def update(self):
        pass

    def draw(self, screen):
        screen.blit(self.surface, (self.x, self.y))

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)


class Rock:
    WIDTH = 64
    HEIGHT = 48
    COLKEY = (0, 0, 0)

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = 3
        self.surface = self._build_surface()

    def _build_surface(self):
        w, h = self.WIDTH, self.HEIGHT
        surface = pygame.Surface((w, h)).convert()
        surface.fill(self.COLKEY)
        points = [
            (w // 2, 2), (w - 8, h // 4), (w - 4, h * 3 // 4),
            (w // 2 + 10, h - 2), (12, h * 3 // 4), (4, h // 4),
        ]
        pygame.draw.polygon(surface, BROWN, points)
        pygame.draw.polygon(surface, GRAY, points, 2)
        surface.set_colorkey(self.COLKEY)
        return surface

    def is_solid(self, x, y):
        if self.hp <= 0:
            return False
        if 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT:
            return self.surface.get_at((x, y))[:3] != self.COLKEY
        return False

    def destroy_chunk(self, x, y):
        self.hp -= 1
        if self.hp <= 0:
            self.surface.fill(self.COLKEY)
        else:
            pygame.draw.circle(self.surface, (60, 40, 20), (x, y), 8)

    def update(self):
        pass

    def draw(self, screen):
        if self.hp > 0:
            screen.blit(self.surface, (self.x, self.y))

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)


class Crystal:
    WIDTH = 32
    HEIGHT = 64
    COLKEY = (0, 0, 0)

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self._tick = 0

    def is_solid(self, x, y):
        if 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT:
            local = self._render().get_at((x, y))[:3]
            return local != self.COLKEY
        return False

    def destroy_chunk(self, x, y):
        pass

    def update(self):
        self._tick += 1

    def _render(self):
        w, h = self.WIDTH, self.HEIGHT
        surface = pygame.Surface((w, h)).convert()
        surface.fill(self.COLKEY)
        brightness = 180 + int(40 * math.sin(self._tick * 0.05))
        color = (brightness // 2, brightness // 3, brightness)
        points = [(w // 2, 0), (w - 2, h // 3), (w // 2, h), (2, h // 3)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, WHITE, points, 2)
        surface.set_colorkey(self.COLKEY)
        return surface

    def draw(self, screen):
        screen.blit(self._render(), (self.x, self.y))

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)


class ShieldBarrier:
    WIDTH = 80
    HEIGHT = 12
    DOWN_TIME = 300

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.down_timer = 0
        self._tick = 0

    @property
    def active(self):
        return self.down_timer <= 0

    def is_solid(self, x, y):
        if not self.active:
            return False
        if 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT:
            return True
        return False

    def destroy_chunk(self, x, y):
        self.down_timer = self.DOWN_TIME

    def update(self):
        self._tick += 1
        if self.down_timer > 0:
            self.down_timer -= 1

    def draw(self, screen):
        if self.active:
            alpha = 180 + int(50 * math.sin(self._tick * 0.08))
            color = (alpha // 4, alpha // 2 + 60, alpha)
            rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
            s = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
            s.fill((*color, 140))
            screen.blit(s, (self.x, self.y))
            pygame.draw.rect(screen, CYAN, rect, 1)
        else:
            progress = self.down_timer / self.DOWN_TIME
            alpha = int(40 * (1 - progress))
            if alpha > 0:
                s = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
                s.fill((*CYAN, alpha))
                screen.blit(s, (self.x, self.y))

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)


class AutoTurret:
    SIZE = 28
    FIRE_INTERVAL = 180
    HP = 2

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = self.HP
        self.fire_timer = self.FIRE_INTERVAL
        self._flash = 0

    def is_solid(self, x, y):
        if self.hp <= 0:
            return False
        cx, cy = self.SIZE // 2, self.SIZE // 2
        if (x - cx) ** 2 + (y - cy) ** 2 <= (self.SIZE // 2) ** 2:
            return True
        return False

    def destroy_chunk(self, x, y):
        self.hp -= 1

    def should_fire(self):
        return self.hp > 0 and self.fire_timer <= 0

    def fire(self):
        self.fire_timer = self.FIRE_INTERVAL
        self._flash = 8
        cx = self.x + self.SIZE // 2
        cy = self.y + self.SIZE
        return cx, cy

    def update(self):
        if self.fire_timer > 0:
            self.fire_timer -= 1
        if self._flash > 0:
            self._flash -= 1

    def draw(self, screen):
        if self.hp <= 0:
            return
        cx = self.x + self.SIZE // 2
        cy = self.y + self.SIZE // 2
        body_color = RED if self._flash > 0 else (120, 40, 40)
        pygame.draw.rect(
            screen, body_color,
            (self.x + 4, self.y + 8, self.SIZE - 8, self.SIZE - 8),
        )
        pygame.draw.circle(screen, (180, 50, 50), (cx, cy), 6)
        pygame.draw.line(
            screen, GRAY, (cx, cy), (cx, self.y - 4), 3,
        )

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.SIZE, self.SIZE)

    @property
    def center_x(self):
        return self.x + self.SIZE // 2

    @property
    def center_y(self):
        return self.y + self.SIZE // 2


class OrganicPod:
    WIDTH = 28
    HEIGHT = 32
    HP = 2

    def is_solid(self, x, y):
        if self.hp <= 0:
            return False
        if 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT:
            cx, cy = self.WIDTH // 2, self.HEIGHT // 2
            return (x - cx) ** 2 + (y - cy) ** 2 <= (min(self.WIDTH, self.HEIGHT) // 2) ** 2
        return False

    def destroy_chunk(self, x, y):
        self.hp -= 1

    @property
    def dead(self):
        return self.hp <= 0

    @property
    def should_spawn(self):
        return self.hp <= 0 and not self._spawned

    def mark_spawned(self):
        self._spawned = True

    def update(self):
        self._tick += 1

    def draw(self, screen):
        if self.hp <= 0:
            return
        pulse = 0.8 + 0.2 * math.sin(self._tick * 0.1)
        g = int(160 * pulse)
        color = (40, g, 60)
        cx = self.x + self.WIDTH // 2
        cy = self.y + self.HEIGHT // 2
        rx = self.WIDTH // 2 - 2
        ry = self.HEIGHT // 2 - 2
        pygame.draw.ellipse(screen, color, (cx - rx, cy - ry, rx * 2, ry * 2))
        pygame.draw.ellipse(screen, (80, 220, 80), (cx - rx, cy - ry, rx * 2, ry * 2), 2)

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = self.HP
        self._tick = 0
        self._spawned = False


class TeleportBarrier:
    WIDTH = 72
    HEIGHT = 14
    CYCLE = 240

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self._tick = random.randint(0, self.CYCLE)

    @property
    def visible(self):
        return self._tick < self.CYCLE * 3 // 4

    def is_solid(self, x, y):
        if not self.visible:
            return False
        if 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT:
            return True
        return False

    def destroy_chunk(self, x, y):
        pass

    def update(self):
        self._tick = (self._tick + 1) % self.CYCLE

    def draw(self, screen):
        if self.visible:
            phase = self._tick / (self.CYCLE * 3 // 4)
            alpha = int(180 * min(1.0, phase * 4))
            s = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
            s.fill((*WHITE, alpha))
            screen.blit(s, (self.x, self.y))
            pygame.draw.rect(screen, WHITE, (self.x, self.y, self.WIDTH, self.HEIGHT), 1)
        else:
            phase = self._tick / self.CYCLE
            fade = max(0, 1 - phase * 4)
            if fade > 0:
                alpha = int(30 * fade)
                s = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
                s.fill((*WHITE, alpha))
                screen.blit(s, (self.x, self.y))

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
