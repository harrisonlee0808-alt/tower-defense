# Architecture Documentation

## Overview

The game is built using Python and Pygame, with a modular architecture that separates concerns into distinct modules.

## Core Components

### 1. Grid System (`src/grid.py`)

The `Grid` class manages the game's tile-based world:
- **Tile States**: 0 = empty, 1 = buildable, 2 = blocked
- **Coordinate Conversion**: Grid coordinates ↔ Pixel coordinates
- **Spawn Points**: Generates enemy spawn points along map edges
- **Terrain Generation**: Currently blocks corners and some edges (can be extended)

### 2. Entity System (`src/entities.py`)

Base `Entity` class providing:
- Position management (x, y)
- Distance calculation between entities
- Common rendering interface

All game objects inherit from this base class.

### 3. Energy Core (`src/core.py`)

The `EnergyCore` class represents the central structure:
- **Integrity System**: Current and max integrity
- **Degradation**: Permanent integrity loss after each wave
- **Damage Handling**: Takes damage from enemies that reach it
- **Visual Feedback**: Integrity bar displayed above core

### 4. Defense Tower (`src/tower.py`)

The `DefenseTower` class handles automatic enemy targeting:
- **Range-Based Targeting**: Finds nearest enemy within range
- **Cooldown System**: Attack rate limited by cooldown timer
- **Auto-Attack**: Automatically attacks when cooldown is ready
- **Visual Feedback**: Range circle and targeting line

### 5. Enemy System (`src/enemy.py`)

The `Enemy` class manages enemy behavior:
- **Pathfinding**: Simple direct movement toward Energy Core
- **Health System**: Takes damage from towers
- **Core Attack**: Deals damage to core when reached
- **Visual Feedback**: Health bar displayed above enemy

### 6. Game Loop (`src/game.py`)

The `Game` class orchestrates the entire game:
- **State Management**: Wave state, placement mode, game state
- **Event Handling**: Keyboard and mouse input
- **Update Loop**: Updates all entities each frame
- **Rendering**: Renders grid, entities, and UI
- **Config Loading**: Loads JSON configuration files

## Data Flow

1. **Initialization**: Game loads configs, creates grid, places core
2. **Placement Phase**: Player places towers on buildable tiles
3. **Wave Start**: Player presses SPACE, enemies begin spawning
4. **Combat Phase**: 
   - Enemies move toward core
   - Towers target and attack enemies
   - Enemies attack core if they reach it
5. **Wave Completion**: All enemies defeated, core degrades
6. **Repeat**: Return to placement phase or game over

## Configuration System

All game parameters are stored in JSON files in `config/`:
- **Data-Driven Design**: Easy to modify without code changes
- **Extensible**: New enemy/tower types can be added via JSON
- **Type Safety**: Configs are loaded at runtime (validation can be added)

## Coordinate Systems

- **Grid Coordinates**: Integer tile positions (0 to grid_size-1)
- **Pixel Coordinates**: Screen pixel positions
- **Conversion**: `grid_to_pixel()` and `pixel_to_grid()` methods

## Rendering Pipeline

1. Clear screen
2. Render grid (tiles)
3. Render core
4. Render towers (with range indicators)
5. Render enemies (with health bars)
6. Render UI text
7. Flip display

## Future Extensibility

The architecture supports:
- Multiple tower types (via config)
- Multiple enemy types (via config)
- Biome system (configs ready)
- Base migration (structure in place)
- Upgrade system (can extend tower/core classes)
- Save/load system (can serialize game state)

## Design Patterns

- **Entity Component**: Base Entity class with inheritance
- **Data-Driven**: Configuration files separate from code
- **State Machine**: Game states (placement, wave active, wave complete)
- **Observer Pattern**: (Future) Events for wave completion, core destruction

