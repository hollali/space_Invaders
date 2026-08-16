# Space Invaders Game

A Space Invaders game built with Python and Pygame. Defend Earth across 5 escalating
levels against descending alien waves, bonus UFOs, and enemy fire — including a
boss fight on the final level.

## Features

- Player control with arrows or WASD and hold-space rapid fire
- **5 levels** with difficulty scaling, a victory screen, and a game-over state
- **3 lives** with temporary invulnerability after being hit
- Enemies shoot back; the wave advances toward you and ends the game if it reaches you
- **3 alien types** with different point values and speeds; the wave speeds up as it thins out
- **Bonus UFO** worth 100-300 points crossing the top of the screen
- **Destructible bunkers** — 4 barriers that erode as they absorb fire from both sides
- **Boss fight on level 5** — a large alien with a health bar that fires spread shots,
  aims at you when enraged (below 1/3 HP), and is worth 1000 points
- **Power-ups** dropped by defeated enemies:
  - `R` rapid fire, `S` shield, `+` extra life, `B` bomb (clears the wave), `M` multishot (triple fire)
- **High scores stored in a SQLite database** (`scores.db`) with a top-5 leaderboard
- **Arcade-style name entry** — enter 3-letter initials when you make the leaderboard
- Explosion effects, background music, and sound effects
- Pause (ESC), auto-pause on focus loss, and mute (M) toggles

## Controls

| Key    | Action                      |
| ------ | --------------------------- |
| `←`/`→` or `A`/`D` | Move the player |
| `SPACE` | Fire                       |
| `ESC`  | Pause / resume (or quit from menus) |
| `M`    | Mute / unmute              |
| `R`    | Retry after game over      |

When your score makes the top 5, type `A`-`Z` to enter 3-letter initials,
`BACKSPACE` to correct, and `ENTER` to save.

## Installation

Requires Python 3.x and Pygame.

```bash
pip install -r requirements.txt
```

Or install Pygame directly:

```bash
pip install pygame
```

On Fedora you can install the system package instead:

```bash
sudo dnf install python3-pygame
```

## Usage

```bash
python main.py
```

## Running Tests

```bash
python -m pytest
```

The test suite runs headless (no window) using dummy SDL drivers.

## Project Structure

- `main.py` — game logic (`Player`, `Enemy`, `Boss`, `Bullet`, `EnemyBullet`, `UFO`, `Explosion`, `PowerUp`, `Bunker`, `HighScoreDB`, `Game`)
- `images/`, `sounds/` — game assets
- `scores.db` — SQLite high-score database (created on first run, auto-migrated)
- `tests/` — automated tests

## License

MIT
