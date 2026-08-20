import math
import random

import pygame

from constants import (
    WIDTH, HEIGHT, FPS, WHITE, BLACK, RED, YELLOW, ORANGE, BLUE, GREEN, PURPLE,
    CYAN, BROWN, GRAY,
)
from assets import load_image, load_sound, SOUND_DIR
from db import HighScoreDB
from effects import Starfield, Explosion, FloatingText
from entities import (
    Player, Enemy, Diver, ArmoredEnemy, SplittingEnemy,
    FastEnemy, ShieldedEnemy, KamikazeEnemy,
    Boss, Bullet, SpreadBullet, EnemyBullet, UFO, PowerUp,
    Missile, PlasmaBolt, LaserBeam, Weapon,
)
from obstacles import Bunker, AutoTurret, OrganicPod
from worlds import WORLDS, LEVELS_PER_WORLD, TOTAL_LEVELS, TOTAL_WORLDS


class Game:
    FIRE_COOLDOWN = 15
    MAX_ENEMY_BULLETS = 4
    POWERUP_CHANCE = 0.08
    COMBO_TIMEOUT = 90
    MAX_LEVEL = TOTAL_LEVELS
    WORLD_WEAPON_UNLOCK = {
        0: None,
        1: Weapon.SPREAD,
        2: Weapon.MISSILE,
        3: Weapon.PLASMA,
        4: Weapon.LASER,
    }

    @property
    def level(self):
        return self._global_level_number()

    @level.setter
    def level(self, val):
        val = max(1, min(val, TOTAL_LEVELS))
        self.world_index = (val - 1) // LEVELS_PER_WORLD
        self.level_in_world = (val - 1) % LEVELS_PER_WORLD

    @property
    def bunkers(self):
        return [o for o in self.obstacles if isinstance(o, Bunker)]

    @bunkers.setter
    def bunkers(self, value):
        others = [o for o in self.obstacles if not isinstance(o, Bunker)]
        self.obstacles = others + list(value)

    def __init__(self, db_path=None):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Space Invaders")
        pygame.display.set_icon(load_image("space.png"))
        self.clock = pygame.time.Clock()

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

        self.particles = []
        self.floating_texts = []
        self.shake_timer = 0
        self.shake_intensity = 0
        self.shake_x = 0
        self.shake_y = 0

        self.combo_count = 0
        self.combo_timer = 0

        self.new_game()

    def _load_world_background(self):
        world = WORLDS[self.world_index]
        bg = pygame.Surface((WIDTH, HEIGHT))
        bg.fill(world.bg_color)
        for i in range(200):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            r = random.randint(1, 3)
            c = random.choice(world.star_colors)
            pygame.draw.circle(bg, c, (x, y), r)
        self.background = bg
        self.starfield = Starfield(world.star_colors)

    def new_game(self):
        self.score = 0
        self.world_index = 0
        self.level_in_world = 0
        self._score_recorded = False
        self.combo_count = 0
        self.combo_timer = 0
        self.player = Player()
        self.weapon = Weapon()
        self.laser_beams = []
        self._load_world_background()
        self.spawn_wave()

    def _current_world(self):
        return WORLDS[self.world_index]

    def _is_boss_level(self):
        return self.level_in_world == LEVELS_PER_WORLD - 1

    def _global_level_number(self):
        return self.world_index * LEVELS_PER_WORLD + self.level_in_world + 1

    def spawn_wave(self):
        self.bullets = []
        self.enemy_bullets = []
        self.laser_beams = getattr(self, "laser_beams", [])
        self.powerups = []
        self.explosions = []
        self.fire_cooldown = 0
        self.rapid_frames = 0
        self.multishot_frames = 0
        self.pierce_frames = 0
        self.slow_frames = 0
        self.score2x_frames = 0
        self.combo_count = 0
        self.combo_timer = 0

        world = self._current_world()

        if self._is_boss_level():
            boss = world.boss_class(self._global_level_number())
            boss.max_hp = world.boss_hp
            boss.hp = world.boss_hp
            boss.points = world.boss_points
            boss.attack_timer = world.boss_attack_interval
            self.boss = boss
            self.enemies = [self.boss]
            self.wave_total = 1
            self.ufo = UFO()
            self.ufo.active = False
            self.ufo_countdown = 10 ** 9
        else:
            self.boss = None
            self.enemies = []
            ec = world.enemy_config
            cols = 8
            rows = min(2 + self.level_in_world + self.world_index, 5)
            gap = 48
            start_x = (WIDTH - (cols - 1) * gap - Enemy.SIZE) // 2
            start_y = 70
            for row in range(rows):
                img_name, points, speed = self._enemy_type_for_row(row)
                speed *= ec["speed_mult"]
                for col in range(cols):
                    cls = self._pick_enemy_class(row, col, ec)
                    self.enemies.append(
                        cls(
                            img_name,
                            start_x + col * gap,
                            start_y + row * gap,
                            points,
                            speed,
                            40,
                            self._global_level_number(),
                        )
                    )
            self.wave_total = len(self.enemies)
            self.ufo = UFO()
            self.ufo_countdown = random.randint(600, 1200)

        self.obstacles = world.obstacle_factory()
        self.turrets = [o for o in self.obstacles if isinstance(o, AutoTurret)]

    def _pick_enemy_class(self, row, col, ec):
        if ec.get("divers") and row == 0 and col in (1, 3, 5):
            return Diver
        if ec.get("kamikaze") and row == 0 and col in (0, 7):
            return KamikazeEnemy
        if ec.get("splitting") and row == 2 and col in (0, 2, 4, 6):
            return SplittingEnemy
        if ec.get("shielded") and row == 3 and col in (1, 3, 5):
            return ShieldedEnemy
        if ec.get("fast") and row == 4 and col in (0, 2, 4, 6):
            return FastEnemy
        if ec.get("armored") and row <= 1:
            return ArmoredEnemy
        return Enemy

    def _enemy_type_for_row(self, row):
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
        multiplier = 1 + 1.2 * (1 - alive / self.wave_total)
        slow = 0.4 if self.slow_frames > 0 else 1.0
        for enemy in self.enemies:
            if hasattr(enemy, "speed_multiplier"):
                enemy.speed_multiplier = multiplier * slow

    def advance_level(self):
        self.level_in_world += 1
        if self.level_in_world >= LEVELS_PER_WORLD:
            self.world_index += 1
            self.level_in_world = 0
            if self.world_index >= TOTAL_WORLDS:
                self.check_high_score()
                self.begin_score_entry("win")
                return
            self._unlock_world_weapon()
            self.state = "world_clear"
            self._world_clear_timer = 150
            self._load_world_background()
            return
        self._load_world_background()
        self.spawn_wave()
        self.state = "wave_countdown"
        self._wave_countdown = 120

    def _unlock_world_weapon(self):
        weapon = self.WORLD_WEAPON_UNLOCK.get(self.world_index)
        if weapon and weapon not in self.weapon.unlocked:
            self.weapon.unlock(weapon)
            label = Weapon.STATS[weapon]["label"].upper()
            self.floating_texts.append(
                FloatingText(
                    WIDTH // 2, HEIGHT // 2,
                    f"{label} UNLOCKED!", Weapon.STATS[weapon]["color"], 32,
                )
            )

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
        if (
            getattr(pygame, "WINDOWFOCUSLOST", None) is not None
            and event.type == pygame.WINDOWFOCUSLOST
        ):
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

        if self.state == "playing" and event.key in Weapon.KEY_BINDINGS:
            self.weapon.switch_to(Weapon.KEY_BINDINGS[event.key])
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
        elif self.state == "world_clear":
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.spawn_wave()
                self.state = "wave_countdown"
                self._wave_countdown = 120
        elif self.state == "playing":
            self.player.handle_event(event)

    def update(self):
        if self.state == "playing":
            self.update_playing()
        elif self.state == "wave_countdown":
            self._wave_countdown -= 1
            if self._wave_countdown <= 0:
                self.state = "playing"
        elif self.state == "level_clear":
            self.level_clear_timer -= 1
            if self.level_clear_timer <= 0:
                self.advance_level()
        elif self.state == "world_clear":
            self._world_clear_timer -= 1
            if self._world_clear_timer <= 0:
                self.spawn_wave()
                self.state = "wave_countdown"
                self._wave_countdown = 120

        self.starfield.update()
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if not p.done]
        for ft in self.floating_texts:
            ft.update()
        self.floating_texts = [ft for ft in self.floating_texts if not ft.done]

        if self.shake_timer > 0:
            self.shake_timer -= 1
            intensity = int(self.shake_intensity)
            decay = self.shake_timer / max(1, self.shake_timer + 5)
            self.shake_x = random.randint(-intensity, intensity) * decay
            self.shake_y = random.randint(-intensity, intensity) * decay
            self.shake_intensity = max(0, self.shake_intensity - 0.5)
        else:
            self.shake_x = 0
            self.shake_y = 0

    def trigger_shake(self, intensity=6, duration=12):
        self.shake_timer = max(self.shake_timer, duration)
        self.shake_intensity = max(self.shake_intensity, intensity)

    def update_playing(self):
        keys = pygame.key.get_pressed()
        self.player.update()

        for obs in self.obstacles:
            obs.update()
        for turret in self.turrets:
            if turret.should_fire():
                tx, ty = turret.fire()
                eb = EnemyBullet()
                dx = self.player.center_x - tx
                dy = self.player.y - ty
                dist = math.hypot(dx, dy) or 1
                eb.vx = dx / dist * 3
                eb.vy = dy / dist * 3
                eb.fire(tx, ty)
                self.enemy_bullets.append(eb)
                self.play_sound(self.laser_sound)

        for bullet in self.bullets:
            bullet.update()
        for beam in self.laser_beams:
            beam.update()
        self.laser_beams = [b for b in self.laser_beams if b.active]
        for bullet in self.bullets:
            if bullet.active and self.bullet_hits_obstacle(bullet):
                bullet.active = False
        for obs in self.obstacles:
            if isinstance(obs, OrganicPod) and obs.should_spawn:
                obs.mark_spawned()
                diver = Diver(
                    "alien11.png",
                    obs.rect.centerx - Diver.SIZE // 2,
                    obs.rect.centery - Diver.SIZE // 2,
                    40, 2.0, 40, self._global_level_number(),
                )
                diver.diving = True
                self.enemies.append(diver)
        self.bullets = [b for b in self.bullets if b.active]

        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        if self.rapid_frames > 0:
            self.rapid_frames -= 1
        if self.multishot_frames > 0:
            self.multishot_frames -= 1
        if self.pierce_frames > 0:
            self.pierce_frames -= 1
        if self.slow_frames > 0:
            self.slow_frames -= 1
            if self.slow_frames <= 0:
                for enemy in self.enemies:
                    if hasattr(enemy, "speed_multiplier"):
                        enemy.speed_multiplier = 1 + 1.2 * (1 - len(self.enemies) / self.wave_total)
        if self.score2x_frames > 0:
            self.score2x_frames -= 1
        cooldown = max(
            self.weapon.cooldown,
            self.FIRE_COOLDOWN // 2 if self.rapid_frames > 0 else self.FIRE_COOLDOWN,
        )
        if keys[pygame.K_SPACE] and self.fire_cooldown <= 0:
            self.fire_bullets()
            self.fire_cooldown = cooldown
            self.play_sound(self.laser_sound)

        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.combo_count = 0

        for enemy in self.enemies:
            if isinstance(enemy, Diver):
                enemy.target_x = self.player.center_x
            elif isinstance(enemy, KamikazeEnemy) and not enemy.diving:
                enemy.target_x = self.player.center_x
            enemy.update()
            if enemy.alive and enemy.rect.bottom >= self.player.y:
                self.trigger_game_over()
                return
            if isinstance(enemy, Boss):
                enemy.attack_timer -= 1
                if enemy.attack_timer <= 0:
                    enemy.attack_timer = 60 if not enemy.enraged else 40
                    self.boss_fire(enemy)
            for bullet in self.bullets:
                if not bullet.active:
                    continue
                if bullet.rect.colliderect(enemy.rect):
                    if self.pierce_frames <= 0:
                        bullet.active = False
                    if isinstance(enemy, Boss):
                        self.on_boss_hit(enemy, self.weapon.damage)
                    elif isinstance(enemy, (ArmoredEnemy, ShieldedEnemy)):
                        if not enemy.hit():
                            self.trigger_shake(2, 4)
                            self.play_sound(self.laser_sound)
                        else:
                            self.on_enemy_destroyed(enemy)
                    elif isinstance(enemy, SplittingEnemy):
                        self.on_splitting_enemy_destroyed(enemy)
                    else:
                        self.on_enemy_destroyed(enemy)
                    if isinstance(bullet, Missile):
                        self.explosions.append(
                            Explosion(bullet.center_x, bullet.center_y)
                        )
                        self.trigger_shake(6, 10)
                        for other in self.enemies:
                            if other is not enemy and other.alive:
                                dist = math.hypot(
                                    other.center_x - bullet.center_x,
                                    other.center_y - bullet.center_y,
                                )
                                if dist < Missile.RADIUS:
                                    if isinstance(other, Boss):
                                        self.on_boss_hit(other, Missile.DAMAGE)
                                    else:
                                        self.on_enemy_destroyed(other)
                    if self.pierce_frames <= 0:
                        break
            for beam in self.laser_beams:
                if beam.active and beam.rect.colliderect(enemy.rect):
                    if isinstance(enemy, Boss):
                        self.on_boss_hit(enemy, self.weapon.damage)
                    elif isinstance(enemy, (ArmoredEnemy, ShieldedEnemy)):
                        if not enemy.hit():
                            self.trigger_shake(1, 2)
                        else:
                            self.on_enemy_destroyed(enemy)
                    elif isinstance(enemy, SplittingEnemy):
                        self.on_splitting_enemy_destroyed(enemy)
                    else:
                        self.on_enemy_destroyed(enemy)

        if self.check_wave_cleared():
            return
        self.update_enemy_speeds()

        self.fire_enemy_bullets()
        for eb in self.enemy_bullets:
            eb.update()
        for eb in self.enemy_bullets:
            if eb.active and self.bullet_hits_obstacle(eb):
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
                    self.floating_texts.append(
                        FloatingText(
                            self.ufo.x + UFO.SIZE // 2,
                            self.ufo.y,
                            f"+{self.ufo.points}",
                            YELLOW, 28,
                        )
                    )
                    self.check_high_score()
                    self.explosions.append(
                        Explosion(
                            self.ufo.x + UFO.SIZE // 2,
                            self.ufo.y + UFO.SIZE // 2,
                        )
                    )
                    self.play_sound(self.explosion_sound)
                    self.ufo.active = False
                    break

        for ex in self.explosions:
            ex.update()
        self.explosions = [ex for ex in self.explosions if not ex.done]

    def fire_bullets(self):
        w = self.weapon.current
        cx = self.player.center_x
        py = self.player.y
        offsets = (-12, 0, 12) if self.multishot_frames > 0 else (0,)
        if w == Weapon.BLASTER:
            for offset in offsets:
                self.bullets.append(Bullet(cx + offset, py))
        elif w == Weapon.SPREAD:
            for angle in (-15, 0, 15):
                self.bullets.append(SpreadBullet(cx, py, angle))
        elif w == Weapon.MISSILE:
            self.bullets.append(Missile(cx, py))
        elif w == Weapon.PLASMA:
            for offset in offsets:
                self.bullets.append(PlasmaBolt(cx + offset, py))
        elif w == Weapon.LASER:
            beam = LaserBeam(cx, py)
            self.laser_beams.append(beam)

    def check_wave_cleared(self):
        self.enemies = [e for e in self.enemies if e.alive]
        if self.enemies:
            return False
        if self._is_boss_level():
            self.check_high_score()
            self.begin_score_entry("world_boss_defeated")
        else:
            self.state = "level_clear"
            self.level_clear_timer = 120
        return True

    def begin_score_entry(self, final_state):
        self._pending_final_state = final_state
        if self.score > 0 and self.score_qualifies():
            self.state = "name_entry"
            self.entered_name = ""
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
        if final_state == "world_boss_defeated":
            if self.world_index >= TOTAL_WORLDS - 1:
                self.state = "win"
            else:
                self.advance_level()
        else:
            self.state = final_state

    def submit_score_name(self):
        name = (self.entered_name or "AAA").ljust(3, "A")[:3]
        self.db.add_score(self.score, name)
        self.finish_game(self._pending_final_state)

    def fire_enemy_bullets(self):
        if self.boss is not None:
            return
        prob = 0.0005 * (1 + 0.15 * self._global_level_number())
        active = sum(1 for b in self.enemy_bullets if b.active)
        if active >= self.MAX_ENEMY_BULLETS:
            return
        for enemy in self.enemies:
            if random.random() < prob:
                aimed_chance = min(0.35, 0.10 + 0.05 * self._global_level_number())
                if random.random() < aimed_chance:
                    dx = self.player.center_x - enemy.center_x
                    dy = self.player.y - (enemy.y + Enemy.SIZE)
                    dist = math.hypot(dx, dy) or 1
                    enemy_bullet = EnemyBullet(dx=dx / dist * 4, dy=dy / dist * 4)
                else:
                    enemy_bullet = EnemyBullet()
                enemy_bullet.fire(enemy.center_x, enemy.y + Enemy.SIZE)
                self.enemy_bullets.append(enemy_bullet)
                self.play_sound(self.laser_sound)
                break

    def boss_fire(self, boss):
        from entities import AsteroidTitan, NebulaGuardian, WarMachine, TheOverlord

        if isinstance(boss, TheOverlord):
            spread = 7 if boss.enraged else 4
            speed = 4.0
            for i in range(spread):
                t = i - (spread - 1) / 2
                bullet = EnemyBullet(dx=t * 1.2, dy=speed)
                bullet.fire(boss.center_x, boss.y + boss.SIZE - 10)
                self.enemy_bullets.append(bullet)
            boss.attack_counter += 1
            if boss.enraged and boss.attack_counter % 2 == 0:
                self.enemy_bullets.append(self.aimed_bullet(boss))
        elif isinstance(boss, AsteroidTitan):
            spread = 5 if boss.enraged else 3
            speed = 3.5
            for i in range(spread):
                t = i - (spread - 1) / 2
                bullet = EnemyBullet(dx=t * 1.4, dy=speed)
                bullet.fire(boss.center_x, boss.y + boss.SIZE - 10)
                self.enemy_bullets.append(bullet)
            if boss.enraged and boss.attack_counter % 2 == 0:
                self.enemy_bullets.append(self.aimed_bullet(boss))
        elif isinstance(boss, WarMachine):
            for offset in (-40, 0, 40):
                bullet = EnemyBullet(dx=offset * 0.05, dy=5)
                bullet.fire(boss.center_x + offset, boss.y + boss.SIZE - 10)
                self.enemy_bullets.append(bullet)
            boss.attack_counter += 1
            if boss.enraged:
                self.enemy_bullets.append(self.aimed_bullet(boss))
        elif isinstance(boss, NebulaGuardian):
            for i in range(6):
                angle = (i / 6) * 2 * math.pi
                bullet = EnemyBullet(dx=math.cos(angle) * 3, dy=math.sin(angle) * 3)
                bullet.fire(boss.center_x, boss.center_y)
                self.enemy_bullets.append(bullet)
            if boss.enraged:
                self.enemy_bullets.append(self.aimed_bullet(boss))
        else:
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

        boss.attack_counter += 1
        self.play_sound(self.laser_sound)

    def aimed_bullet(self, boss):
        dx = self.player.center_x - boss.center_x
        dy = self.player.y - (boss.y + boss.SIZE)
        dist = math.hypot(dx, dy) or 1
        bullet = EnemyBullet(dx=dx / dist * 4, dy=dy / dist * 4)
        bullet.fire(boss.center_x, boss.y + boss.SIZE)
        return bullet

    def bullet_hits_obstacle(self, bullet):
        for obs in self.obstacles:
            if not hasattr(obs, "is_solid"):
                continue
            if bullet.rect.colliderect(obs.rect):
                local_x = int(bullet.center_x - obs.x)
                local_y = int(bullet.center_y - obs.y)
                if obs.is_solid(local_x, local_y):
                    obs.destroy_chunk(local_x, local_y)
                    return True
        return False

    def bullet_hits_bunker(self, bullet):
        return self.bullet_hits_obstacle(bullet)

    def _award_score(self, base, label, color, y_offset=0):
        multiplier = 2 if self.score2x_frames > 0 else 1
        earned = base * multiplier
        self.score += earned
        text = f"+{earned}"
        if multiplier > 1:
            text += " x2"
        self.floating_texts.append(
            FloatingText(
                self.player.center_x if y_offset == 0 else 0,
                self.player.y if y_offset == 0 else 0,
                text, color,
            )
        )
        self.check_high_score()
        return earned

    def on_boss_hit(self, boss, damage=1):
        boss.hp -= damage
        self.trigger_shake(4, 10)
        self.explosions.append(
            Explosion(
                boss.center_x + random.randint(-40, 40),
                boss.center_y + random.randint(-40, 40),
            )
        )
        self.play_sound(self.explosion_sound)
        if boss.hp <= 0:
            boss.alive = False
            self._award_score(boss.points, f"+{boss.points}", YELLOW)
            self.trigger_shake(12, 20)
            for _ in range(12):
                self.explosions.append(
                    Explosion(
                        boss.center_x + random.randint(-60, 60),
                        boss.center_y + random.randint(-40, 60),
                    )
                )
            self.play_sound(self.explosion_sound)

    def on_enemy_destroyed(self, enemy):
        enemy.alive = False
        self.combo_count += 1
        self.combo_timer = self.COMBO_TIMEOUT
        combo_mult = min(self.combo_count, 5)
        base = enemy.points * combo_mult
        score_mult = 2 if self.score2x_frames > 0 else 1
        earned = base * score_mult
        self.score += earned

        color = YELLOW if combo_mult > 1 or score_mult > 1 else WHITE
        text = f"+{earned}"
        if combo_mult > 1:
            text += f" x{combo_mult}"
        if score_mult > 1:
            text += " x2"
        self.floating_texts.append(
            FloatingText(enemy.center_x, enemy.center_y - 10, text, color)
        )

        self.check_high_score()
        exp_color = RED if isinstance(enemy, Diver) else None
        self.explosions.append(
            Explosion(enemy.center_x, enemy.center_y, color=exp_color)
        )
        self.play_sound(self.explosion_sound)
        if random.random() < self.POWERUP_CHANCE:
            kind = random.choice(list(PowerUp.TYPES))
            self.powerups.append(
                PowerUp(kind, enemy.center_x, enemy.center_y, self.small_font)
            )
        locked = [
            w for w in Weapon.ALL
            if w not in self.weapon.unlocked
        ]
        if locked and random.random() < 0.04:
            weapon_name = random.choice(locked)
            self.powerups.append(
                PowerUp(
                    f"unlock_{weapon_name}",
                    enemy.center_x, enemy.center_y, self.small_font,
                )
            )

    def on_splitting_enemy_destroyed(self, enemy):
        enemy.alive = False
        self.score += enemy.points
        self.check_high_score()
        self.explosions.append(Explosion(enemy.center_x, enemy.center_y))
        self.play_sound(self.explosion_sound)
        self.floating_texts.append(
            FloatingText(enemy.center_x, enemy.center_y - 10, f"+{enemy.points}", PURPLE)
        )
        for i in range(2):
            offset = 16 if i == 0 else -16
            mini = Enemy(
                "alien.png",
                enemy.center_x + offset - Enemy.SIZE // 2,
                enemy.y,
                enemy.points // 2,
                enemy.base_speed * 1.3,
                enemy.drop,
                self._global_level_number(),
            )
            mini.direction = 1 if i == 0 else -1
            self.enemies.append(mini)
        self.wave_total = len(self.enemies)

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
        elif kind == "pierce":
            self.pierce_frames = 600
        elif kind == "slow":
            self.slow_frames = 600
            for enemy in self.enemies:
                enemy.speed_multiplier *= 0.4
        elif kind == "score2x":
            self.score2x_frames = 600
        elif kind == "recall":
            for eb in self.enemy_bullets:
                eb.active = False
            self.enemy_bullets = []
            self.floating_texts.append(
                FloatingText(WIDTH // 2, HEIGHT // 2, "RECALL!", CYAN, 36)
            )
        elif kind == "mega_bomb":
            if self.boss is not None and self.boss.alive:
                self.boss.hp -= 5
                if self.boss.hp <= 0:
                    self.boss.alive = False
                    self.score += self.boss.points
                self.trigger_shake(10, 18)
            for enemy in self.enemies:
                enemy.alive = False
                self.score += enemy.points
                self.explosions.append(Explosion(enemy.center_x, enemy.center_y))
            self.floating_texts.append(
                FloatingText(WIDTH // 2, HEIGHT // 2, "MEGA BOMB!", RED, 40)
            )
            self.trigger_shake(12, 20)
            self.check_high_score()
        elif kind == "bomb":
            for enemy in self.enemies:
                enemy.alive = False
                self.score += enemy.points
                self.explosions.append(Explosion(enemy.center_x, enemy.center_y))
            self.floating_texts.append(
                FloatingText(WIDTH // 2, HEIGHT // 2, "BOMB!", RED, 36)
            )
            self.trigger_shake(8, 15)
            self.check_high_score()
        elif kind.startswith("unlock_"):
            weapon_name = kind.replace("unlock_", "")
            if weapon_name not in self.weapon.unlocked:
                self.weapon.unlock(weapon_name)
                self.weapon.switch_to(weapon_name)
                label = Weapon.STATS[weapon_name]["label"].upper()
                self.floating_texts.append(
                    FloatingText(
                        WIDTH // 2, HEIGHT // 2,
                        f"{label} UNLOCKED!", Weapon.STATS[weapon_name]["color"], 32,
                    )
                )
        self.play_sound(self.explosion_sound)

    def check_player_hit(self):
        if self.player.invulnerable_frames > 0:
            return
        for eb in self.enemy_bullets:
            if eb.active and eb.rect.colliderect(self.player.rect):
                eb.active = False
                self.trigger_shake(8, 15)
                self.explosions.append(
                    Explosion(self.player.center_x, self.player.y)
                )
                self.play_sound(self.explosion_sound)
                self.player.lives -= 1
                if self.player.lives <= 0:
                    self.trigger_game_over()
                else:
                    self.player.invulnerable_frames = Player.INVULNERABLE_FRAMES
                    self.enemy_bullets = []
                break

    def trigger_game_over(self):
        self.trigger_shake(10, 18)
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
        sx = int(self.shake_x)
        sy = int(self.shake_y)
        self.screen.blit(self.background, (sx, sy))
        self.starfield.draw(self.screen)

        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_game(sx, sy)
            if self.state == "paused":
                self.draw_center_text("PAUSED", self.over_font, 240)
                self.draw_center_text("Press ESC to resume", self.small_font, 330)
            elif self.state == "wave_countdown":
                world = self._current_world()
                seconds_left = self._wave_countdown // 60 + 1
                self.draw_center_text(
                    f"WAVE {self._global_level_number()}",
                    self.over_font, 220, world.accent_color,
                )
                self.draw_center_text(
                    f"Starting in {seconds_left}...", self.small_font, 310, WHITE,
                )
            elif self.state == "level_clear":
                self.draw_center_text(
                    f"LEVEL {self._global_level_number()} CLEARED!",
                    self.over_font, 240,
                )
                self.draw_center_text(
                    "Press SPACE to continue", self.small_font, 330,
                )
            elif self.state == "world_clear":
                world = self._current_world()
                self.draw_center_text(
                    f"WORLD {self.world_index + 1}: {world.name.upper()}",
                    self.over_font, 220, world.accent_color,
                )
                self.draw_center_text(
                    "Press SPACE to begin", self.small_font, 310,
                )
            elif self.state == "name_entry":
                self.draw_center_text(
                    "NEW HIGH SCORE! Enter your name:", self.font, 210,
                )
                self.draw_center_text(
                    self.entered_name + "_", self.title_font, 275, YELLOW,
                )
                self.draw_center_text(
                    "Type A-Z, BACKSPACE to fix, ENTER to save",
                    self.small_font, 350,
                )
            elif self.state == "game_over":
                self.draw_center_text("GAME OVER", self.over_font, 180)
                self.draw_center_text(
                    f"Score: {self.score}    High Score: {self.high_score}",
                    self.font, 265, YELLOW,
                )
                self.draw_leaderboard_block(325)
                self.draw_center_text(
                    "Press R to retry, SPACE for menu", self.small_font, 545,
                )
            elif self.state == "win":
                self.draw_center_text("YOU WIN!", self.over_font, 180, YELLOW)
                self.draw_center_text(
                    "All worlds conquered!", self.font, 250, GREEN,
                )
                self.draw_center_text(
                    f"Score: {self.score}    High Score: {self.high_score}",
                    self.font, 300, YELLOW,
                )
                self.draw_leaderboard_block(355)
                self.draw_center_text(
                    "Press R to play again, SPACE for menu",
                    self.small_font, 545,
                )

        pygame.display.update()

    def draw_game(self, sx=0, sy=0):
        self.ufo.draw(self.screen)
        for obs in self.obstacles:
            obs.draw(self.screen)
        for beam in self.laser_beams:
            beam.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        self.player.draw(self.screen)
        for bullet in self.bullets:
            bullet.draw(self.screen)
        for eb in self.enemy_bullets:
            eb.draw(self.screen)
        for ex in self.explosions:
            ex.draw(self.screen)
        for p in self.particles:
            p.draw(self.screen)
        for ft in self.floating_texts:
            ft.draw(self.screen)
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
            self.screen, GREEN,
            (x, y, int(bar_width * boss.hp / boss.max_hp), bar_height),
        )
        pygame.draw.rect(self.screen, WHITE, (x, y, bar_width, bar_height), 2)
        hp_text = f"BOSS  {boss.hp}/{boss.max_hp}"
        if boss.enraged:
            hp_text += "  ENRAGED!"
        hp_color = RED if boss.enraged else WHITE
        hp_surface = self.small_font.render(hp_text, True, hp_color)
        self.screen.blit(
            hp_surface,
            hp_surface.get_rect(centerx=boss.center_x, bottom=y - 4),
        )

    def draw_hud(self):
        world = self._current_world()
        world_label = f"W{self.world_index + 1}: {world.name}"
        level_label = f"Level {self.level_in_world + 1}/{LEVELS_PER_WORLD}"
        self.screen.blit(
            self.small_font.render(world_label, True, world.accent_color), (10, 10),
        )
        self.screen.blit(
            self.font.render(f"Score: {self.score}", True, WHITE), (10, 35),
        )
        self.screen.blit(
            self.font.render(f"High: {self.high_score}", True, WHITE), (10, 65),
        )
        self.screen.blit(
            self.small_font.render(level_label, True, WHITE), (10, 95),
        )
        self.screen.blit(
            self.font.render(
                f"Lives: {self.player.lives}", True, WHITE,
            ), (640, 10),
        )
        self.screen.blit(
            self.font.render(
                f"World {self.world_index + 1}/{TOTAL_WORLDS}", True, WHITE,
            ), (640, 45),
        )

        if self.combo_count > 1:
            combo_color = (
                YELLOW if self.combo_count < 4
                else ORANGE if self.combo_count < 5
                else RED
            )
            combo_text = f"COMBO x{min(self.combo_count, 5)}"
            combo_surface = self.font.render(combo_text, True, combo_color)
            combo_rect = combo_surface.get_rect(centerx=WIDTH // 2, top=10)
            self.screen.blit(combo_surface, combo_rect)

        bar_y = 80
        if self.rapid_frames > 0:
            self.draw_powerup_bar("RAPID", ORANGE, self.rapid_frames, 600, 640, bar_y)
            bar_y += 20
        if self.multishot_frames > 0:
            self.draw_powerup_bar("MULTI", PURPLE, self.multishot_frames, 600, 640, bar_y)
            bar_y += 20
        if self.pierce_frames > 0:
            self.draw_powerup_bar("PIERCE", CYAN, self.pierce_frames, 600, 640, bar_y)
            bar_y += 20
        if self.slow_frames > 0:
            self.draw_powerup_bar("SLOW", BROWN, self.slow_frames, 600, 640, bar_y)
            bar_y += 20
        if self.score2x_frames > 0:
            self.draw_powerup_bar("SCORE x2", YELLOW, self.score2x_frames, 600, 640, bar_y)

        if self.muted:
            self.screen.blit(
                self.small_font.render("MUTED", True, RED), (10, 120),
            )

        weapon_y = HEIGHT - 35
        for i, name in enumerate(Weapon.ALL):
            stat = Weapon.STATS[name]
            x = 10 + i * 140
            is_current = name == self.weapon.current
            is_unlocked = name in self.weapon.unlocked
            if is_unlocked:
                color = stat["color"] if is_current else GRAY
                prefix = ">" if is_current else " "
                key_num = str(Weapon.ALL.index(name) + 1)
                label = f"{prefix}{key_num}:{stat['label']}"
            else:
                color = (60, 60, 70)
                key_num = str(Weapon.ALL.index(name) + 1)
                label = f" {key_num}:???"
            self.screen.blit(
                self.small_font.render(label, True, color), (x, weapon_y),
            )

    def draw_powerup_bar(self, label, color, remaining, total, x, y):
        bar_width = 80
        bar_height = 8
        ratio = remaining / total
        self.screen.blit(self.small_font.render(label, True, color), (x, y))
        bar_x = x + 55
        pygame.draw.rect(
            self.screen, (40, 40, 40), (bar_x, y + 4, bar_width, bar_height),
        )
        pygame.draw.rect(
            self.screen, color,
            (bar_x, y + 4, int(bar_width * ratio), bar_height),
        )
        pygame.draw.rect(
            self.screen, WHITE, (bar_x, y + 4, bar_width, bar_height), 1,
        )

    def draw_menu(self):
        t = pygame.time.get_ticks() / 1000.0
        pulse = 0.85 + 0.15 * math.sin(t * 3)
        title_color = (int(255 * pulse), int(220 * pulse), int(80 * pulse))
        title_surface = self.title_font.render("SPACE INVADERS", True, title_color)
        title_rect = title_surface.get_rect(center=(WIDTH // 2, 120))
        self.screen.blit(title_surface, title_rect)

        self.draw_center_text(
            f"{TOTAL_WORLDS} Worlds  {TOTAL_LEVELS} Levels",
            self.small_font, 170, GREEN,
        )

        if self.high_score > 0:
            self.draw_center_text(
                f"High Score: {self.high_score}", self.font, 210, YELLOW,
            )

        start_alpha = int(180 + 75 * math.sin(t * 4))
        start_surface = self.font.render("Press SPACE to Start", True, WHITE)
        start_surface.set_alpha(start_alpha)
        start_rect = start_surface.get_rect(center=(WIDTH // 2, 265))
        self.screen.blit(start_surface, start_rect)

        self.draw_center_text(
            "Arrows/WASD: move   SPACE: shoot   ESC: pause   M: mute",
            self.small_font, 315,
        )

        self.draw_world_preview(355)
        self.draw_leaderboard_block(490)

    def draw_world_preview(self, start_y):
        self.draw_center_text("WORLDS", self.small_font, start_y)
        for i, world in enumerate(WORLDS):
            y = start_y + 22 + i * 20
            marker = ">" if i == 0 else " "
            self.screen.blit(
                self.small_font.render(
                    f"{marker} {i + 1}. {world.name}", True, world.accent_color,
                ),
                (260, y),
            )

    def draw_leaderboard_block(self, start_y):
        rows = self.db.get_top_scores(5)
        if not rows:
            return
        self.draw_center_text("TOP SCORES", self.small_font, start_y)
        for i, (score, name, when) in enumerate(rows):
            self.draw_center_text(
                f"{i + 1}.  {name}  {score}",
                self.small_font, start_y + 24 + i * 24, YELLOW,
            )

    def draw_center_text(self, text, font, y, color=WHITE):
        surface = font.render(text, True, color)
        self.screen.blit(surface, surface.get_rect(center=(WIDTH // 2, y)))
