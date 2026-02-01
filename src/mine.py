"""
Mine - proximity-triggered explosive defense.
"""

import pygame
import math
from src.entities import Entity


class Mine(Entity):
    """Mine that detonates when enemies enter its radius."""
    
    def __init__(self, x, y, radius_tiles, tile_size, damage, size, color, cost):
        super().__init__(x, y, size, color)
        self.radius_tiles = radius_tiles
        self.radius_pixels = radius_tiles * tile_size
        self.damage = damage
        self.cost = cost
        self.armed = True
        self.detonated = False
        self.detonated_timer = 0.0
        self.detonation_duration = 0.3  # seconds for flash effect
    
    def update(self, dt, enemies):
        """Update mine state and check for proximity triggers."""
        if self.detonated:
            self.detonated_timer += dt
            return
        
        if not self.armed:
            return
        
        # Check if any enemy is within radius
        for enemy in enemies:
            if enemy.is_alive():
                distance = self.distance_to(enemy)
                if distance <= self.radius_pixels:
                    # Detonate!
                    self.detonate(enemies)
                    break
    
    def detonate(self, enemies):
        """Detonate the mine, damaging all enemies in radius."""
        if self.detonated:
            return
        
        self.detonated = True
        self.armed = False
        self.detonated_timer = 0.0
        
        # Damage all enemies in radius
        for enemy in enemies:
            if enemy.is_alive():
                distance = self.distance_to(enemy)
                if distance <= self.radius_pixels:
                    enemy.take_damage(self.damage)
    
    def is_consumed(self):
        """Check if mine has been consumed (detonated and flash finished)."""
        return self.detonated and self.detonated_timer >= self.detonation_duration
    
    def render(self, screen):
        """Render the mine."""
        if self.detonated:
            # Show flash effect
            flash_progress = min(1.0, self.detonated_timer / self.detonation_duration)
            flash_radius = int(self.radius_pixels * (0.5 + flash_progress * 0.5))
            flash_alpha = int(255 * (1.0 - flash_progress))
            
            # Draw expanding flash circle
            flash_color = (255, 255, 0, flash_alpha)
            # Create a surface for alpha blending
            flash_surface = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surface, (255, 255, 0, flash_alpha), 
                             (flash_radius, flash_radius), flash_radius)
            screen.blit(flash_surface, 
                       (int(self.x - flash_radius), int(self.y - flash_radius)))
        else:
            # Draw mine
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
            pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), self.size, 1)
            
            # Draw radius circle (subtle, only when armed)
            if self.armed:
                pygame.draw.circle(screen, (150, 150, 150), 
                                 (int(self.x), int(self.y)), 
                                 int(self.radius_pixels), 1)

