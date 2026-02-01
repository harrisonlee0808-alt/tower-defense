"""
Energy Core - the central structure that must be defended.
"""

import pygame
from src.entities import Entity


class EnergyCore(Entity):
    """The Energy Core that must be protected."""
    
    def __init__(self, x, y, max_integrity, integrity_loss_per_wave, size, color):
        super().__init__(x, y, size, color)
        self.max_integrity = max_integrity
        self.current_integrity = max_integrity
        self.integrity_loss_per_wave = integrity_loss_per_wave
    
    def take_damage(self, damage):
        """Take damage from enemies."""
        self.current_integrity = max(0, self.current_integrity - damage)
    
    def degrade_after_wave(self):
        """Permanently degrade after a successful wave defense."""
        self.max_integrity = max(0, self.max_integrity - self.integrity_loss_per_wave)
        self.current_integrity = min(self.current_integrity, self.max_integrity)
    
    def is_destroyed(self):
        """Check if the core is destroyed."""
        return self.current_integrity <= 0 or self.max_integrity <= 0
    
    def get_integrity_percentage(self):
        """Get current integrity as a percentage of max."""
        if self.max_integrity == 0:
            return 0.0
        return self.current_integrity / self.max_integrity
    
    def render(self, screen, map_origin_x, map_origin_y, tile_size, origin_tile_x, origin_tile_y, footprint_w, footprint_h):
        """Render the Energy Core using exact footprint coordinates."""
        # Calculate pixel position from origin tile (top-left)
        origin_x = map_origin_x + origin_tile_x * tile_size
        origin_y = map_origin_y + origin_tile_y * tile_size
        footprint_rect = pygame.Rect(origin_x, origin_y, 
                                    footprint_w * tile_size, 
                                    footprint_h * tile_size)
        
        # Draw filled rectangle for footprint
        pygame.draw.rect(screen, self.color, footprint_rect)
        pygame.draw.rect(screen, (0, 0, 0), footprint_rect, 2)
        
        # Draw integrity bar above core
        bar_width = 40
        bar_height = 6
        bar_x = int(self.x - bar_width // 2)
        bar_y = int(self.y - (footprint_h * tile_size // 2 if tile_size and footprint_h else self.size) - 15)
        
        # Background bar
        pygame.draw.rect(screen, (100, 100, 100), 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Integrity bar
        integrity_width = int(bar_width * self.get_integrity_percentage())
        if integrity_width > 0:
            bar_color = (0, 255, 0) if self.get_integrity_percentage() > 0.5 else (255, 255, 0) if self.get_integrity_percentage() > 0.25 else (255, 0, 0)
            pygame.draw.rect(screen, bar_color, 
                           (bar_x, bar_y, integrity_width, bar_height))

