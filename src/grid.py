"""
Grid system for the base defense game.
Manages tile states and grid rendering.
"""

import pygame
import json
import os


class Grid:
    """Manages the game grid and tile states."""
    
    def __init__(self, grid_size, tile_size):
        self.grid_size = grid_size
        self.tile_size = tile_size
        self.width = grid_size * tile_size
        self.height = grid_size * tile_size
        
        # Tile states: 0 = empty, 1 = buildable, 2 = blocked
        self.tiles = [[1 for _ in range(grid_size)] for _ in range(grid_size)]
        
        # Block some tiles as terrain (random for now, can be config-driven later)
        self._generate_terrain()
    
    def _generate_terrain(self):
        """Generate blocked terrain tiles."""
        # Block corners and some edges for variety
        blocked_positions = [
            (0, 0), (0, 1), (1, 0),
            (self.grid_size - 1, 0), (self.grid_size - 2, 0), (self.grid_size - 1, 1),
            (0, self.grid_size - 1), (0, self.grid_size - 2), (1, self.grid_size - 1),
            (self.grid_size - 1, self.grid_size - 1), 
            (self.grid_size - 1, self.grid_size - 2),
            (self.grid_size - 2, self.grid_size - 1),
        ]
        
        for x, y in blocked_positions:
            if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
                self.tiles[y][x] = 2
    
    def is_buildable(self, grid_x, grid_y):
        """Check if a tile is buildable."""
        if not (0 <= grid_x < self.grid_size and 0 <= grid_y < self.grid_size):
            return False
        return self.tiles[grid_y][grid_x] == 1
    
    def set_tile(self, grid_x, grid_y, state):
        """Set tile state (0=empty, 1=buildable, 2=blocked)."""
        if 0 <= grid_x < self.grid_size and 0 <= grid_y < self.grid_size:
            self.tiles[grid_y][grid_x] = state
    
    def grid_to_pixel(self, grid_x, grid_y):
        """Convert grid coordinates to pixel coordinates."""
        return (grid_x * self.tile_size + self.tile_size // 2,
                grid_y * self.tile_size + self.tile_size // 2)
    
    def pixel_to_grid(self, pixel_x, pixel_y):
        """Convert pixel coordinates to grid coordinates."""
        grid_x = pixel_x // self.tile_size
        grid_y = pixel_y // self.tile_size
        return grid_x, grid_y
    
    def get_spawn_points(self):
        """Get enemy spawn points along the edges."""
        spawn_points = []
        # Top edge
        for x in range(self.grid_size):
            spawn_points.append((x, 0))
        # Bottom edge
        for x in range(self.grid_size):
            spawn_points.append((x, self.grid_size - 1))
        # Left edge
        for y in range(1, self.grid_size - 1):
            spawn_points.append((0, y))
        # Right edge
        for y in range(1, self.grid_size - 1):
            spawn_points.append((self.grid_size - 1, y))
        return spawn_points
    
    def render(self, screen):
        """Render the grid."""
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                rect = pygame.Rect(
                    x * self.tile_size,
                    y * self.tile_size,
                    self.tile_size,
                    self.tile_size
                )
                
                if self.tiles[y][x] == 2:  # Blocked
                    pygame.draw.rect(screen, (50, 50, 50), rect)
                else:  # Empty/Buildable
                    pygame.draw.rect(screen, (200, 200, 200), rect)
                    pygame.draw.rect(screen, (150, 150, 150), rect, 1)

