"""
Base entity class for game objects.
"""


class Entity:
    """Base class for all game entities."""
    
    def __init__(self, x, y, size, color):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
    
    def get_position(self):
        """Get entity position."""
        return (self.x, self.y)
    
    def distance_to(self, other):
        """Calculate distance to another entity."""
        dx = self.x - other.x
        dy = self.y - other.y
        return (dx * dx + dy * dy) ** 0.5
    
    def render(self, screen):
        """Render the entity (to be overridden)."""
        pass

