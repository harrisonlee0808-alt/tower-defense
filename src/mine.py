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
    
    def render(self, screen, map_origin_x, map_origin_y, tile_size, origin_tile_x, origin_tile_y, footprint_w, footprint_h):
        """Render the mine using exact footprint coordinates."""
        if self.detonated:
            # Show flash effect
            flash_progress = min(1.0, self.detonated_timer / self.detonation_duration)
            flash_radius = int(self.radius_pixels * (0.5 + flash_progress * 0.5))
            flash_alpha = int(255 * (1.0 - flash_progress))
            
            # Calculate center from origin tile
            center_x = map_origin_x + (origin_tile_x + footprint_w / 2.0) * tile_size
            center_y = map_origin_y + (origin_tile_y + footprint_h / 2.0) * tile_size
            
            # Draw expanding flash circle
            flash_color = (255, 255, 0, flash_alpha)
            # Create a surface for alpha blending
            flash_surface = pygame.Surface((flash_radius * 2, flash_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surface, (255, 255, 0, flash_alpha), 
                             (flash_radius, flash_radius), flash_radius)
            screen.blit(flash_surface, 
                       (int(center_x - flash_radius), int(center_y - flash_radius)))
        else:
            # Calculate pixel position from origin tile (top-left)
            origin_x = map_origin_x + origin_tile_x * tile_size
            origin_y = map_origin_y + origin_tile_y * tile_size
            footprint_rect = pygame.Rect(origin_x, origin_y, 
                                        footprint_w * tile_size, 
                                        footprint_h * tile_size)
            
            # Draw filled rectangle for footprint
            pygame.draw.rect(screen, self.color, footprint_rect)
            pygame.draw.rect(screen, (0, 0, 0), footprint_rect, 1)
            
            # Draw radius circle (subtle, only when armed)
            if self.armed:
                center_x = origin_x + footprint_rect.width // 2
                center_y = origin_y + footprint_rect.height // 2
                pygame.draw.circle(screen, (150, 150, 150), 
                                 (int(center_x), int(center_y)), 
                                 int(self.radius_pixels), 1)

