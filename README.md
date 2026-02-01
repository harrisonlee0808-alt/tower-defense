# Tower Defense - Base Defense Game

A single-player, PvE, base-defense game inspired by Clash of Clans. Defend your Energy Core from wave-based enemies on a grid-based open base. The core degrades after each successful defense, eventually forcing you to migrate to a new base.

## Features (Current Foundation)

- **Grid-based Base**: 16x16 tile grid with buildable and blocked terrain
- **Energy Core**: Central structure that must be defended, degrades after each wave
- **Defense Towers**: Auto-targeting towers that attack enemies within range
- **Enemy Waves**: Basic enemies spawn from map edges and move toward the core
- **Core Degradation**: Core permanently loses integrity after each successful wave defense

## Installation

1. Install Python 3.7 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Game

```bash
python main.py
```

## Controls

- **T** - Enter tower placement mode (click on buildable tiles to place)
- **SPACE** - Start a wave / Complete wave after defense
- **ESC** - Quit game

## Gameplay

1. Place defense towers on buildable tiles (gray tiles)
2. Press SPACE to start a wave
3. Enemies spawn from map edges and move toward the Energy Core
4. Towers automatically target and attack enemies in range
5. After all enemies are defeated, press SPACE to complete the wave
6. The Energy Core degrades after each successful defense
7. When the core reaches 0 integrity, the base is abandoned (migration not yet implemented)

## Project Structure

```
TowerDefense/
├── src/              # Source code
│   ├── grid.py      # Grid system and tile management
│   ├── entities.py  # Base entity class
│   ├── core.py      # Energy Core implementation
│   ├── tower.py     # Defense Tower implementation
│   ├── enemy.py     # Enemy implementation
│   └── game.py      # Main game loop
├── config/          # JSON configuration files
│   ├── game.json    # Game settings (grid size, core stats, waves)
│   ├── enemies.json # Enemy definitions
│   ├── towers.json  # Tower definitions
│   └── biomes.json # Biome definitions (for future use)
├── docs/            # Documentation
│   ├── ARCHITECTURE.md
│   ├── GAMEPLAY.md
│   └── CHANGELOG.md
├── main.py          # Entry point
└── requirements.txt # Python dependencies
```

## Configuration

Game parameters can be adjusted in the `config/` directory:

- **game.json**: Grid size, tile size, core stats, wave settings
- **enemies.json**: Enemy health, speed, damage, appearance
- **towers.json**: Tower damage, range, cooldown, appearance

## Current Limitations (Foundation Only)

- No upgrades system
- No animations
- No sound
- No menus
- No save/load
- Single tower type
- Single enemy type
- Base migration not yet implemented
- No biome system active

## Future Development

See `docs/` for detailed architecture and planned features.

## License

This project is for educational purposes.

