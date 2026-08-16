import random
import sys
from pathlib import Path

import pygame
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main


@pytest.fixture
def game(tmp_path):
    random.seed(7)
    return main.Game(db_path=tmp_path / "scores.db")


@pytest.fixture
def held_keys(monkeypatch):
    keys = set()
    monkeypatch.setattr(
        pygame.key,
        "get_pressed",
        lambda: {k: k in keys for k in range(512)},
    )
    return keys


def keydown(game, key):
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))


def run_frames(game, held_keys, frames):
    for _ in range(frames):
        game.update()
        game.draw()


def start_playing(game):
    keydown(game, pygame.K_SPACE)
    assert game.state == "playing"


def test_menu_start_pause_and_resume(game):
    assert game.state == "menu"
    start_playing(game)
    keydown(game, pygame.K_ESCAPE)
    assert game.state == "paused"
    keydown(game, pygame.K_ESCAPE)
    assert game.state == "playing"


def test_player_movement_arrows_and_wasd(game):
    start_playing(game)
    game.player.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
    assert game.player.change < 0
    game.player.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    assert game.player.change > 0
    game.player.x = 0
    game.player.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT))
    for _ in range(500):
        game.player.update()
    assert game.player.x == 0


def test_firing_kills_enemies_and_scores(game, held_keys):
    start_playing(game)
    held_keys.add(pygame.K_SPACE)
    for _ in range(6000):
        game.update()
        game.draw()
        if game.score > 0:
            break
    assert game.score > 0


def test_level_clear_and_advance(game):
    start_playing(game)
    game.enemies = []
    assert game.check_wave_cleared()
    assert game.state == "level_clear"
    game.advance_level()
    assert game.level == 2
    assert game.state == "playing"


def test_win_at_max_level(game):
    start_playing(game)
    game.level = main.Game.MAX_LEVEL
    game.spawn_wave()
    game.enemies = []
    game.check_wave_cleared()
    assert game.state == "win"


def test_game_over_and_retry(game):
    start_playing(game)
    lives = game.player.lives
    while game.state == "playing":
        game.player.invulnerable_frames = 0
        eb = main.EnemyBullet()
        eb.fire(game.player.x, game.player.y - 4)
        game.enemy_bullets.append(eb)
        game.check_player_hit()
        assert game.player.lives < lives
        lives = game.player.lives
    assert game.state == "game_over"
    keydown(game, pygame.K_r)
    assert game.state == "playing"
    assert game.score == 0
    assert game.level == 1


def test_name_entry_on_qualifying_score(game):
    start_playing(game)
    game.score = 500
    game.check_high_score()
    game.begin_score_entry("game_over")
    assert game.state == "name_entry"
    for letter in (pygame.K_a, pygame.K_b, pygame.K_c):
        keydown(game, letter)
    assert game.entered_name == "ABC"
    keydown(game, pygame.K_RETURN)
    assert game.state == "game_over"
    assert game.db.get_top_scores(1) == [(500, "ABC", main.date.today().isoformat())]


def test_low_score_skips_name_entry(game):
    start_playing(game)
    game.score = 0
    game.begin_score_entry("game_over")
    assert game.state == "game_over"


def test_powerup_life(game):
    start_playing(game)
    game.player.lives = 1
    game.apply_powerup(main.PowerUp("life", 0, 0, game.small_font))
    assert game.player.lives == 2


def test_powerup_rapid(game):
    start_playing(game)
    game.apply_powerup(main.PowerUp("rapid", 0, 0, game.small_font))
    assert game.rapid_frames == 600


def test_powerup_multi_fires_three_bullets(game):
    start_playing(game)
    game.apply_powerup(main.PowerUp("multi", 0, 0, game.small_font))
    assert game.multishot_frames == 600
    game.fire_bullets()
    assert len(game.bullets) == 3


def test_powerup_bomb_clears_wave(game):
    start_playing(game)
    count = len(game.enemies)
    assert count > 0
    score_before = game.score
    game.apply_powerup(main.PowerUp("bomb", 0, 0, game.small_font))
    assert game.check_wave_cleared()
    assert game.state == "level_clear"
    assert game.score > score_before


def test_bunker_blocks_player_bullet(game):
    start_playing(game)
    game.bunkers = [main.Bunker(200, 400)]
    bullet = main.Bullet(224, 420)
    assert game.bullet_hits_bunker(bullet) is True
    assert not game.bunkers[0].is_solid(24, 32)


def test_bunker_lets_bullet_through_after_erosion(game):
    start_playing(game)
    bunker = main.Bunker(200, 400)
    game.bunkers = [bunker]
    bunker.destroy_chunk(24, 32)
    assert bunker.is_solid(24, 32) is False
    bullet = main.Bullet(224, 420)
    assert game.bullet_hits_bunker(bullet) is False


def test_boss_spawns_on_final_level(game):
    game.level = main.Game.MAX_LEVEL
    game.spawn_wave()
    assert isinstance(game.enemies[0], main.Boss)


def test_boss_takes_damage_and_is_defeated(game):
    game.level = main.Game.MAX_LEVEL
    game.spawn_wave()
    boss = game.enemies[0]
    hp = boss.hp
    game.on_boss_hit(boss)
    assert boss.hp == hp - 1
    assert boss.alive
    boss.hp = 1
    score_before = game.score
    game.on_boss_hit(boss)
    assert boss.alive is False
    assert game.score > score_before
    assert game.check_wave_cleared()
    assert game.state == "name_entry"
    keydown(game, pygame.K_RETURN)
    assert game.state == "win"


def test_boss_fires_spread_and_aimed_bullets(game):
    game.level = main.Game.MAX_LEVEL
    game.spawn_wave()
    game.state = "playing"
    boss = game.enemies[0]
    game.boss_fire(boss)
    assert len(game.enemy_bullets) >= 3
    game.boss_fire(boss)
    game.boss_fire(boss)
    assert len(game.enemy_bullets) >= 9
    boss.hp = 1
    game.boss_fire(boss)
    game.boss_fire(boss)
    game.boss_fire(boss)
    assert len(game.enemy_bullets) >= 9 + 15 + 1


def test_boss_fires_angled_bullets(game):
    game.level = main.Game.MAX_LEVEL
    game.spawn_wave()
    bullet = game.aimed_bullet(game.enemies[0])
    assert bullet.active
    assert bullet.vy > 0


def test_enemies_speed_up_as_wave_thins(game):
    start_playing(game)
    game.update_enemy_speeds()
    full_multiplier = game.enemies[0].speed_multiplier
    game.enemies = game.enemies[:1]
    game.update_enemy_speeds()
    assert game.enemies[0].speed_multiplier > full_multiplier


def test_mute_toggle(game):
    assert game.muted is False
    keydown(game, pygame.K_m)
    assert game.muted is True
    keydown(game, pygame.K_m)
    assert game.muted is False


def test_focus_loss_pauses(game):
    start_playing(game)
    game.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert game.state == "paused"


def test_high_score_recorded_to_db(game):
    game.db.add_score(500, "AAA")
    assert game.db.get_high_score() == 500
    assert game.db.get_top_scores(5) == [(500, "AAA", main.date.today().isoformat())]


def test_leaderboard_sorted(game):
    for score, name in ((50, "AAA"), (900, "BBB"), (120, "CCC")):
        game.db.add_score(score, name)
    rows = game.db.get_top_scores(5)
    assert [(r[0], r[1]) for r in rows] == [(900, "BBB"), (120, "CCC"), (50, "AAA")]
