"""
Defense Tower - automatically targets and attacks enemies.
"""

import pygame
import math
from src.entities import Entity


class DefenseTower(Entity):
    """Defense tower that automatically targets enemies."""
    
    def __init__(self, x, y, damage, range_distance, cooldown, size, color, cost):
        super().__init__(x, y, size, color)
        self.damage = damage
        self.range_distance = range_distance
        self.cooldown = cooldown
        self.current_cooldown = 0.0
        self.target = None
        self.cost = cost
    
    def update(self, dt, enemies):
        """Update tower state and attack enemies."""
        # Update cooldown
        if self.current_cooldown > 0:
            self.current_cooldown -= dt
        
        # Find nearest enemy in range
        self.target = None
        nearest_distance = self.range_distance
        
        for enemy in enemies:
            if enemy.is_alive():
                # Calculate distance from tower center (self.x, self.y) to enemy
                dx = self.x - enemy.x
                dy = self.y - enemy.y
                distance = (dx * dx + dy * dy) ** 0.5
                
                if distance <= self.range_distance and distance < nearest_distance:
                    self.target = enemy
                    nearest_distance = distance
        
        # Attack if cooldown is ready and target exists
        if self.target and self.current_cooldown <= 0:
            self.target.take_damage(self.damage)
            self.current_cooldown = self.cooldown
    
    def render(self, screen, map_origin_x, map_origin_y, tile_size, origin_tile_x, origin_tile_y, footprint_w, footprint_h):
        """Render the tower using exact footprint coordinates."""
        # Calculate pixel position from origin tile (top-left)
        origin_x = map_origin_x + origin_tile_x * tile_size
        origin_y = map_origin_y + origin_tile_y * tile_size
        footprint_rect = pygame.Rect(origin_x, origin_y, 
                                    footprint_w * tile_size, 
                                    footprint_h * tile_size)
        
        # Draw filled rectangle for footprint
        pygame.draw.rect(screen, self.color, footprint_rect)
        pygame.draw.rect(screen, (0, 0, 0), footprint_rect, 2)
        
        # Calculate center for range circle and targeting line
        center_x = origin_x + footprint_rect.width // 2
        center_y = origin_y + footprint_rect.height // 2
        
        # Draw range circle (subtle)
        pygame.draw.circle(screen, (100, 100, 100), 
                          (center_x, center_y), 
                          int(self.range_distance), 1)
        
        # Draw line to target if targeting
        if self.target and self.target.is_alive():
            pygame.draw.line(screen, (255, 255, 0), 
                           (center_x, center_y),
                           (int(self.target.x), int(self.target.y)), 2)

