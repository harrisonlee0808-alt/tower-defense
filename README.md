# Tower Defense - Base Defense Game

A single-player, PvE, wave-defense game inspired by Clash of Clans. Defend your Energy Core from wave-based enemies on a grid-based open base. The core degrades after each successful defense, eventually forcing you to migrate to a new base.

## Features

- **Grid-based Base**: Configurable grid with buildable and blocked terrain
- **Build vs Wave Phases**: Strategic planning phase and intense combat phase
- **Energy Core**: Central structure that must be defended, permanently degrades after each wave
- **Tower Selection**: Press T to open selection menu, then 1/2 to choose tower type
- **Defense Towers**: Auto-targeting towers with multi-tile footprints
- **Mine Tower**: Single-use proximity-triggered AOE explosive
- **Enemy Waves**: Two enemy types (Heavy and Light) spawn from map edges
- **Wave Focus Direction**: Each wave has a focus direction with visual arrows and preview
- **Progressive Difficulty**: Waves scale with increasing enemy count, stats, and heavy/light ratio
- **Core Mining Rewards**: Earn currency by surviving waves (reduced by core degradation)
- **Emergency Repair**: One-time repair option to restore core HP
- **Right-Side Sidebar UI**: Comprehensive information panel with wave preview, stats, and controls

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

- **T** - Open tower selection menu
- **1** - Select Basic Tower
- **2** - Select Mine
- **X** - Toggle sell mode (click structures to sell)
- **R** - Emergency repair (once per base, during build phase)
- **SPACE** - Start wave / Complete wave after defense
- **ESC** - Cancel selection/placement or quit game

## Gameplay

1. **Build Phase**: Place towers and mines on buildable tiles
   - Press T, then 1 or 2 to select a structure type
   - Click on buildable tiles to place (footprint preview shown)
   - Press X to enter sell mode, click structures to sell
   - Preview shows incoming wave direction and enemy mix

2. **Wave Phase**: Defend against enemy waves
   - Press SPACE to start wave (3-second countdown)
   - Enemies spawn from edges, with majority from focus direction
   - Towers automatically target and attack enemies
   - Mines detonate when enemies enter their radius
   - Defeat all enemies to complete the wave

3. **Wave Completion**: Earn rewards and prepare for next wave
   - Press SPACE after wave clears
   - Earn mined currency (reduced by core integrity)
   - Core permanently degrades
   - Return to build phase with new wave preview

4. **Base Migration**: (Planned feature)
   - When core integrity reaches 0, base is abandoned
   - Player migrates to new base with different layout

## Project Structure

```
TowerDefense/
├── src/              # Source code
│   ├── grid.py      # Grid system and tile management
│   ├── entities.py  # Base entity class
│   ├── core.py      # Energy Core implementation
│   ├── tower.py     # Defense Tower implementation
│   ├── mine.py      # Mine implementation
│   ├── enemy.py     # Enemy implementation
│   └── game.py      # Main game loop
├── config/          # JSON configuration files
│   ├── game.json    # Game settings (grid, waves, UI, features)
│   ├── enemies.json # Enemy type definitions (heavy/light)
│   ├── towers.json  # Tower type definitions
│   └── biomes.json  # Biome definitions (for future use)
├── docs/            # Documentation
│   ├── ARCHITECTURE.md
│   ├── GAMEPLAY.md
│   └── CHANGELOG.md
├── main.py          # Entry point
└── requirements.txt # Python dependencies
```

## Configuration

Game parameters can be adjusted in the `config/` directory:

### config/game.json
- `grid_size`: Grid dimensions (e.g., 24)
- `tile_size`: Pixel size of each tile
- `starting_currency`: Starting energy amount
- `core`: Core stats, footprint, integrity settings
- `wave_scaling`: Enemy count, spawn intervals, stat multipliers, heavy/light ratios
- `core_mining`: Reward calculation settings
- `wave_focus`: Focus direction settings
- `preview_incoming`: Preview system settings
- `wave_countdown`: Countdown timer settings
- `emergency_repair`: Repair cost and amount

### config/towers.json
- Tower definitions with:
  - `damage`, `range`, `cooldown`: Combat stats
  - `cost`: Placement cost
  - `footprint_w`, `footprint_h`: Multi-tile footprint size
  - `color`, `size`: Visual appearance

### config/enemies.json
- Enemy type definitions (heavy/light):
  - `health`, `speed`, `damage`: Base stats
  - `color`, `size`: Visual appearance

## Current Limitations

- Base migration not yet implemented (planned feature)
- No upgrades system
- No animations
- No sound
- No menus
- No save/load
- No biome system active

## Future Development

See `docs/` for detailed architecture and planned features.

## License

This project is for educational purposes.
