import math
import random
import pygame
from constants import WIDTH, HEIGHT, WHITE, YELLOW, ORANGE, RED


class Particle:
    def __init__(self, x, y, color=None):
        self.x = float(x)
        self.y = float(y)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color or random.choice([YELLOW, ORANGE, RED, WHITE])
        self.size = random.uniform(2, 5)
        self.lifetime = random.randint(15, 30)
        self.frame = 0

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.08
        self.vx *= 0.97
        self.frame += 1

    @property
    def done(self):
        return self.frame >= self.lifetime

    def draw(self, screen):
        progress = self.frame / self.lifetime
        size = max(1, int(self.size * (1 - progress * 0.6)))
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)


class FloatingText:
    def __init__(self, x, y, text, color=WHITE, size=20):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.font = pygame.font.Font("freesansbold.ttf", size)
        self.lifetime = 50
        self.frame = 0

    def update(self):
        self.y -= 1.2
        self.frame += 1

    @property
    def done(self):
        return self.frame >= self.lifetime

    def draw(self, screen):
        progress = self.frame / self.lifetime
        alpha = max(0, int(255 * (1 - progress)))
        surface = self.font.render(self.text, True, self.color)
        surface.set_alpha(alpha)
        screen.blit(surface, surface.get_rect(center=(int(self.x), int(self.y))))


class Starfield:
    def __init__(self, colors=None):
        layers = [
            {"count": 50, "speed": 0.2, "size_range": (1, 1),
             "colors": colors or [(80, 80, 100)]},
            {"count": 30, "speed": 0.5, "size_range": (1, 1),
             "colors": colors or [(130, 130, 160)]},
            {"count": 15, "speed": 1.0, "size_range": (1, 2),
             "colors": (colors or [(200, 200, 230)]) + [WHITE]},
        ]
        self.stars = []
        for layer in layers:
            for _ in range(layer["count"]):
                self.stars.append({
                    "x": random.uniform(0, WIDTH),
                    "y": random.uniform(0, HEIGHT),
                    "speed": layer["speed"],
                    "size": random.randint(*layer["size_range"]),
                    "color": random.choice(layer["colors"]),
                })

    def update(self):
        for star in self.stars:
            star["y"] += star["speed"]
            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.uniform(0, WIDTH)

    def draw(self, screen):
        for star in self.stars:
            pygame.draw.circle(
                screen, star["color"],
                (int(star["x"]), int(star["y"])), star["size"],
            )


class Explosion:
    DURATION = 16

    def __init__(self, x, y, particles=True, color=None):
        self.x = x
        self.y = y
        self.frame = 0
        self.particles = []
        if particles:
            for _ in range(random.randint(10, 18)):
                self.particles.append(Particle(x, y, color))

    def update(self):
        self.frame += 1
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if not p.done]

    @property
    def done(self):
        return self.frame >= self.DURATION and not self.particles

    def draw(self, screen):
        for i, color in enumerate((YELLOW, ORANGE, RED)):
            radius = 8 + self.frame - i * 4
            if radius > 2:
                pygame.draw.circle(
                    screen, color, (int(self.x), int(self.y)), radius, 2,
                )
        for p in self.particles:
            p.draw(screen)
