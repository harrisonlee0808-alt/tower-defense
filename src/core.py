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
    
    def render(self, screen):
        """Render the Energy Core."""
        # Draw core circle
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), self.size, 2)
        
        # Draw integrity bar above core
        bar_width = 40
        bar_height = 6
        bar_x = int(self.x - bar_width // 2)
        bar_y = int(self.y - self.size - 15)
        
        # Background bar
        pygame.draw.rect(screen, (100, 100, 100), 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Integrity bar
        integrity_width = int(bar_width * self.get_integrity_percentage())
        if integrity_width > 0:
            bar_color = (0, 255, 0) if self.get_integrity_percentage() > 0.5 else (255, 255, 0) if self.get_integrity_percentage() > 0.25 else (255, 0, 0)
            pygame.draw.rect(screen, bar_color, 
                           (bar_x, bar_y, integrity_width, bar_height))

