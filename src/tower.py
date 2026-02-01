"""
Defense Tower - automatically targets and attacks enemies.
"""

import pygame
import math
from src.entities import Entity


class DefenseTower(Entity):
    """Defense tower that automatically targets enemies."""
    
    def __init__(self, x, y, damage, range_distance, cooldown, size, color):
        super().__init__(x, y, size, color)
        self.damage = damage
        self.range_distance = range_distance
        self.cooldown = cooldown
        self.current_cooldown = 0.0
        self.target = None
    
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
                distance = self.distance_to(enemy)
                if distance <= self.range_distance and distance < nearest_distance:
                    self.target = enemy
                    nearest_distance = distance
        
        # Attack if cooldown is ready and target exists
        if self.target and self.current_cooldown <= 0:
            self.target.take_damage(self.damage)
            self.current_cooldown = self.cooldown
    
    def render(self, screen):
        """Render the tower."""
        # Draw tower base
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), self.size, 2)
        
        # Draw range circle (subtle)
        pygame.draw.circle(screen, (100, 100, 100), 
                          (int(self.x), int(self.y)), 
                          int(self.range_distance), 1)
        
        # Draw line to target if targeting
        if self.target and self.target.is_alive():
            pygame.draw.line(screen, (255, 255, 0), 
                           (int(self.x), int(self.y)),
                           (int(self.target.x), int(self.target.y)), 2)

