# Gameplay Documentation

## Core Mechanics

### Energy Core

The Energy Core is the central structure that must be protected:
- **Starting Integrity**: 100 (configurable)
- **Degradation**: Loses 10 integrity per successful wave (configurable)
- **Damage**: Takes damage when enemies reach it
- **Game Over**: When integrity reaches 0, the base is abandoned

### Defense Towers

Towers automatically defend the base:
- **Placement**: Click on buildable (gray) tiles after pressing T
- **Targeting**: Automatically targets nearest enemy within range
- **Attack**: Fires projectiles (visual line) when cooldown is ready
- **Range**: Visible circle shows attack range
- **Stats**: Damage, range, and cooldown configurable in `config/towers.json`

### Enemies

Enemies spawn from map edges and attack the core:
- **Spawn**: Appear at random edge positions
- **Movement**: Move directly toward Energy Core
- **Attack**: Deal damage to core when they reach it
- **Health**: Displayed as red health bar above enemy
- **Stats**: Health, speed, damage configurable in `config/enemies.json`

### Waves

Waves are the primary challenge:
- **Start**: Press SPACE to begin a wave
- **Spawn Rate**: Enemies spawn every 1 second (configurable)
- **Wave Size**: 5 enemies per wave (configurable)
- **Completion**: All enemies must be defeated
- **Reward**: Core degrades after successful defense

## Game Flow

1. **Setup Phase**
   - Core is placed in center of grid
   - Player can place towers on buildable tiles
   - Press T to enter tower placement mode
   - Click on gray tiles to place towers

2. **Wave Phase**
   - Press SPACE to start wave
   - Enemies spawn from edges
   - Towers automatically attack
   - Enemies move toward core
   - Defeat all enemies to complete wave

3. **Degradation Phase**
   - Press SPACE after wave completion
   - Core integrity permanently decreases
   - Return to setup phase or game over

4. **Game Over**
   - When core integrity reaches 0
   - Base is abandoned
   - (Migration system not yet implemented)

## Strategy Tips

- **Placement**: Place towers near the core for maximum protection
- **Range**: Towers have limited range, consider placement carefully
- **Coverage**: Spread towers to cover multiple approach angles
- **Core Health**: Monitor core integrity - each wave reduces it permanently

## Current Limitations

- Only one tower type available
- Only one enemy type
- No upgrades or improvements
- No resource management
- Simple pathfinding (direct movement)
- No multiple waves in sequence

## Future Gameplay Features

- Multiple tower types with different abilities
- Multiple enemy types with different behaviors
- Tower upgrades
- Resource generation and management
- Complex pathfinding
- Wave progression with increasing difficulty
- Base migration with new layouts
- Biome-specific mechanics

