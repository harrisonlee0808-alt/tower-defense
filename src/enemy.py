"""
Enemy - moves toward the Energy Core and attacks it.
"""

import pygame
import math
from src.entities import Entity


class Enemy(Entity):
    """Enemy that moves toward the Energy Core."""
    
    def __init__(self, x, y, health, speed, damage, size, color):
        super().__init__(x, y, size, color)
        self.max_health = health
        self.current_health = health
        self.speed = speed
        self.damage = damage
        self.alive = True
    
    def update(self, dt, core):
        """Update enemy position toward the core."""
        if not self.alive or core is None:
            return
        
        # Calculate direction to core
        dx = core.x - self.x
        dy = core.y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 0:
            # Normalize and move
            move_distance = self.speed * dt * 60  # 60 for frame rate normalization
            if move_distance >= distance:
                # Reached core, attack it
                core.take_damage(self.damage)
                self.alive = False
            else:
                self.x += (dx / distance) * move_distance
                self.y += (dy / distance) * move_distance
    
    def take_damage(self, damage):
        """Take damage from towers."""
        self.current_health -= damage
        if self.current_health <= 0:
            self.alive = False
    
    def is_alive(self):
        """Check if enemy is alive."""
        return self.alive
    
    def get_health_percentage(self):
        """Get current health as percentage."""
        if self.max_health == 0:
            return 0.0
        return self.current_health / self.max_health
    
    def render(self, screen):
        """Render the enemy."""
        if not self.alive:
            return
        
        # Draw enemy circle
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), self.size, 1)
        
        # Draw health bar above enemy
        bar_width = 20
        bar_height = 4
        bar_x = int(self.x - bar_width // 2)
        bar_y = int(self.y - self.size - 8)
        
        # Background bar
        pygame.draw.rect(screen, (100, 100, 100), 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Health bar
        health_width = int(bar_width * self.get_health_percentage())
        if health_width > 0:
            pygame.draw.rect(screen, (255, 0, 0), 
                           (bar_x, bar_y, health_width, bar_height))

