# Changelog

All notable changes to the project will be documented in this file.

## [Foundation] - Initial Release

### Added

#### Core Systems
- Grid-based base system (16x16 tiles)
- Tile state management (empty, buildable, blocked)
- Coordinate conversion (grid ↔ pixel)
- Enemy spawn point generation

#### Entities
- Base `Entity` class for all game objects
- `EnergyCore` with integrity and degradation system
- `DefenseTower` with auto-targeting and cooldown system
- `Enemy` with health, movement, and core attack

#### Game Loop
- Main game loop with 60 FPS
- Event handling (keyboard, mouse)
- Structure placement system
- Wave spawning and management
- Core degradation after wave completion

#### Configuration
- JSON-based configuration system
- Game settings (`game.json`)
- Enemy definitions (`enemies.json`)
- Tower definitions (`towers.json`)
- Biome definitions (`biomes.json`) - prepared for future use

#### Rendering
- Grid rendering with tile states
- Core rendering with integrity bar
- Tower rendering with range indicators
- Enemy rendering with health bars
- Targeting visualization (line from tower to enemy)
- Basic UI text display

#### Documentation
- README.md with setup and usage instructions
- Architecture documentation
- Gameplay documentation
- Changelog

### Gameplay Features
- Single Energy Core placement (center)
- Tower placement on buildable tiles
- Single wave system (5 enemies)
- Enemy spawning from map edges
- Automatic tower targeting and attack
- Core damage from enemies
- Core degradation after successful wave
- Game over when core integrity reaches 0

### Technical Details
- Python 3.7+ with Pygame 2.5.2
- Modular file structure (`src/`, `config/`, `docs/`)
- Clean separation of concerns
- Data-driven design
- No global state (except game instance)

### Known Limitations
- No upgrade system
- No animations
- No sound
- No menus
- No save/load
- Single tower type
- Single enemy type
- Base migration not implemented
- Biome system not active
- Simple pathfinding (direct movement)

### Next Steps (Not Yet Implemented)
- Base migration system
- Multiple tower types
- Multiple enemy types
- Resource generation
- Tower upgrades
- Wave progression
- Biome mechanics
- Save/load system
- Menu system
- Animations and polish

