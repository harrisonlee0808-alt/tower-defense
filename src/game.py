"""
Main game loop and state management.
"""

import pygame
import json
import os
import random
from src.grid import Grid
from src.core import EnergyCore
from src.tower import DefenseTower
from src.enemy import Enemy


class Game:
    """Main game class managing the game loop and state."""
    
    def __init__(self):
        pygame.init()
        
        # Load configs
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        self.game_config = self._load_config('game.json')
        self.enemy_config = self._load_config('enemies.json')
        self.tower_config = self._load_config('towers.json')
        
        # Setup display
        self.grid_size = self.game_config['grid_size']
        self.tile_size = self.game_config['tile_size']
        self.grid = Grid(self.grid_size, self.tile_size)
        
        screen_width = self.grid.width + 200  # Extra space for UI
        screen_height = self.grid.height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Tower Defense - Base Defense")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game state
        self.core = None
        self.towers = []
        self.enemies = []
        self.wave_active = False
        self.wave_complete = False
        self.enemies_spawned = 0
        self.enemies_per_wave = self.game_config['waves']['enemies_per_wave']
        self.spawn_interval = self.game_config['waves']['spawn_interval']
        self.last_spawn_time = 0.0
        
        # Economy
        self.energy = self.game_config['starting_energy']
        self.sell_refund_pct = self.game_config['sell_refund_pct']
        
        # Phase system: 'build' or 'wave'
        self.phase = 'build'
        
        # Placement mode
        self.placement_mode = None  # 'tower', 'delete', or None
        self.selected_tower_type = 'basic_tower'
        
        # UI messages
        self.ui_message = None
        self.ui_message_timer = 0.0
        
        # Hover preview
        self.mouse_pos = (0, 0)
        
        self._initialize_game()
    
    def _load_config(self, filename):
        """Load a JSON config file."""
        filepath = os.path.join(self.config_dir, filename)
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def _initialize_game(self):
        """Initialize the game state."""
        # Place core in center
        center_x = self.grid_size // 2
        center_y = self.grid_size // 2
        core_x, core_y = self.grid.grid_to_pixel(center_x, center_y)
        
        core_config = self.game_config['core']
        self.core = EnergyCore(
            core_x, core_y,
            core_config['max_integrity'],
            core_config['integrity_loss_per_wave'],
            core_config['size'],
            tuple(core_config['color'])
        )
        
        # Mark core tile as occupied
        self.grid.set_tile(center_x, center_y, 0)
    
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_t:
                    if self.phase == 'build':
                        if self.placement_mode == 'tower':
                            self.placement_mode = None
                        else:
                            self.placement_mode = 'tower'
                elif event.key == pygame.K_x:
                    if self.phase == 'build':
                        if self.placement_mode == 'delete':
                            self.placement_mode = None
                        else:
                            self.placement_mode = 'delete'
                elif event.key == pygame.K_SPACE:
                    if self.phase == 'build' and not self.wave_active and not self.wave_complete:
                        self.start_wave()
                    elif self.wave_complete:
                        self.complete_wave()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_placement(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
    
    def handle_placement(self, mouse_pos):
        """Handle structure placement and deletion."""
        grid_x, grid_y = self.grid.pixel_to_grid(mouse_pos[0], mouse_pos[1])
        
        if self.placement_mode == 'tower':
            if self.phase != 'build':
                self.show_message("Can't place during wave", 2.0)
                return
            
            if self.can_place_tower(grid_x, grid_y):
                self.place_tower(grid_x, grid_y)
            else:
                tower_data = self.tower_config[self.selected_tower_type]
                if self.energy < tower_data['cost']:
                    self.show_message("Not enough energy", 2.0)
                elif not self.grid.is_buildable(grid_x, grid_y):
                    self.show_message("Can't build here", 1.0)
        
        elif self.placement_mode == 'delete':
            if self.phase != 'build':
                self.show_message("Can't sell during wave", 2.0)
                return
            
            self.sell_tower(grid_x, grid_y)
    
    def can_place_tower(self, grid_x, grid_y):
        """Check if a tower can be placed at the given grid position."""
        if self.phase != 'build':
            return False
        
        if not self.grid.is_buildable(grid_x, grid_y):
            return False
        
        tower_data = self.tower_config[self.selected_tower_type]
        if self.energy < tower_data['cost']:
            return False
        
        # Check if there's already a tower at this position
        tower_x, tower_y = self.grid.grid_to_pixel(grid_x, grid_y)
        for tower in self.towers:
            t_x, t_y = tower.get_position()
            if abs(t_x - tower_x) < 1 and abs(t_y - tower_y) < 1:
                return False
        
        return True
    
    def place_tower(self, grid_x, grid_y):
        """Place a tower at the given grid position."""
        tower_x, tower_y = self.grid.grid_to_pixel(grid_x, grid_y)
        tower_data = self.tower_config[self.selected_tower_type]
        
        tower = DefenseTower(
            tower_x, tower_y,
            tower_data['damage'],
            tower_data['range'],
            tower_data['cooldown'],
            tower_data['size'],
            tuple(tower_data['color']),
            tower_data['cost']
        )
        self.towers.append(tower)
        self.grid.set_tile(grid_x, grid_y, 0)
        self.energy -= tower_data['cost']
        self.placement_mode = None
    
    def sell_tower(self, grid_x, grid_y):
        """Sell a tower at the given grid position."""
        tower_x, tower_y = self.grid.grid_to_pixel(grid_x, grid_y)
        
        # Find tower at this position
        for i, tower in enumerate(self.towers):
            t_x, t_y = tower.get_position()
            if abs(t_x - tower_x) < 1 and abs(t_y - tower_y) < 1:
                # Calculate refund
                refund = int(tower.cost * self.sell_refund_pct)
                self.energy += refund
                
                # Remove tower
                self.towers.pop(i)
                
                # Free the tile
                self.grid.set_tile(grid_x, grid_y, 1)
                self.placement_mode = None
                return
        
        # No tower found at this position
        self.show_message("No tower here", 1.0)
    
    def show_message(self, message, duration=2.0):
        """Show a temporary UI message."""
        self.ui_message = message
        self.ui_message_timer = duration
    
    def get_tower_at_position(self, grid_x, grid_y):
        """Get the tower at a given grid position, or None."""
        tower_x, tower_y = self.grid.grid_to_pixel(grid_x, grid_y)
        for tower in self.towers:
            t_x, t_y = tower.get_position()
            if abs(t_x - tower_x) < 1 and abs(t_y - tower_y) < 1:
                return tower
        return None
    
    def start_wave(self):
        """Start a new enemy wave."""
        if self.wave_active:
            return
        
        self.phase = 'wave'
        self.wave_active = True
        self.wave_complete = False
        self.enemies_spawned = 0
        self.enemies = []
        self.last_spawn_time = 0.0
        self.placement_mode = None  # Exit placement mode when wave starts
    
    def spawn_enemy(self):
        """Spawn a new enemy at a random edge position."""
        spawn_points = self.grid.get_spawn_points()
        if not spawn_points:
            return
        
        spawn_point = random.choice(spawn_points)
        spawn_x, spawn_y = self.grid.grid_to_pixel(spawn_point[0], spawn_point[1])
        
        enemy_data = self.enemy_config['basic_enemy']
        enemy = Enemy(
            spawn_x, spawn_y,
            enemy_data['health'],
            enemy_data['speed'],
            enemy_data['damage'],
            enemy_data['size'],
            tuple(enemy_data['color'])
        )
        self.enemies.append(enemy)
        self.enemies_spawned += 1
    
    def complete_wave(self):
        """Complete the wave and degrade the core."""
        if not self.wave_complete:
            return
        
        self.core.degrade_after_wave()
        self.phase = 'build'
        self.wave_active = False
        self.wave_complete = False
        
        if self.core.is_destroyed():
            print("Core destroyed! Base abandoned. (Migration not implemented yet)")
            self.running = False
    
    def update(self, dt):
        """Update game state."""
        # Update UI message timer
        if self.ui_message_timer > 0:
            self.ui_message_timer -= dt
            if self.ui_message_timer <= 0:
                self.ui_message = None
        
        if not self.wave_active:
            return
        
        # Spawn enemies
        current_time = pygame.time.get_ticks() / 1000.0
        if (self.enemies_spawned < self.enemies_per_wave and 
            current_time - self.last_spawn_time >= self.spawn_interval):
            self.spawn_enemy()
            self.last_spawn_time = current_time
        
        # Update enemies
        for enemy in self.enemies:
            if enemy.is_alive():
                enemy.update(dt, self.core)
        
        # Update towers
        for tower in self.towers:
            tower.update(dt, self.enemies)
        
        # Check wave completion
        if (self.enemies_spawned >= self.enemies_per_wave and
            all(not enemy.is_alive() for enemy in self.enemies)):
            if not self.wave_complete:
                self.wave_complete = True
                print(f"Wave complete! Core integrity: {self.core.current_integrity}/{self.core.max_integrity}")
    
    def render(self):
        """Render the game."""
        self.screen.fill((50, 50, 50))
        
        # Render grid
        self.grid.render(self.screen)
        
        # Render core
        if self.core:
            self.core.render(self.screen)
        
        # Render towers
        for tower in self.towers:
            tower.render(self.screen)
        
        # Render enemies
        for enemy in self.enemies:
            enemy.render(self.screen)
        
        # Render hover preview
        self.render_hover_preview()
        
        # Render UI text
        font = pygame.font.Font(None, 24)
        ui_x = self.grid.width + 10
        
        y_offset = 20
        texts = [
            f"Energy: {int(self.energy)}",
            f"Core: {int(self.core.current_integrity)}/{int(self.core.max_integrity)}",
            "",
            f"Mode: {self.get_mode_text()}",
            "",
            "Controls:",
            "T - Place Tower",
            "X - Sell Tower",
            "SPACE - Start/Complete Wave",
            "ESC - Quit",
            "",
        ]
        
        if self.wave_active:
            alive_count = sum(1 for e in self.enemies if e.is_alive())
            texts.append(f"Wave Active: {alive_count} enemies")
        elif self.wave_complete:
            texts.append("Wave Complete!")
            texts.append("Press SPACE to continue")
        else:
            texts.append("Press SPACE to start wave")
        
        # Show UI message
        if self.ui_message:
            texts.append("")
            texts.append(f"> {self.ui_message}")
        
        for text in texts:
            if text:
                text_surface = font.render(text, True, (255, 255, 255))
                self.screen.blit(text_surface, (ui_x, y_offset))
            y_offset += 25
        
        pygame.display.flip()
    
    def get_mode_text(self):
        """Get text description of current mode."""
        if self.phase == 'wave':
            return "Wave"
        elif self.placement_mode == 'tower':
            return "Build (Place)"
        elif self.placement_mode == 'delete':
            return "Build (Sell)"
        else:
            return "Build"
    
    def render_hover_preview(self):
        """Render hover preview for tower placement."""
        if self.phase != 'build':
            return
        
        if self.placement_mode == 'tower':
            grid_x, grid_y = self.grid.pixel_to_grid(self.mouse_pos[0], self.mouse_pos[1])
            
            # Check if position is valid
            can_place = self.can_place_tower(grid_x, grid_y)
            tower_data = self.tower_config[self.selected_tower_type]
            
            # Only show preview if mouse is over grid
            if 0 <= grid_x < self.grid_size and 0 <= grid_y < self.grid_size:
                tower_x, tower_y = self.grid.grid_to_pixel(grid_x, grid_y)
                
                # Draw preview circle
                if can_place:
                    # Valid placement - green outline
                    pygame.draw.circle(self.screen, (100, 255, 100), 
                                     (tower_x, tower_y), tower_data['size'], 2)
                else:
                    # Invalid placement - red outline or X
                    pygame.draw.circle(self.screen, (255, 100, 100), 
                                     (tower_x, tower_y), tower_data['size'], 2)
                    
                    # Draw X marker
                    size = tower_data['size']
                    pygame.draw.line(self.screen, (255, 0, 0), 
                                   (tower_x - size, tower_y - size),
                                   (tower_x + size, tower_y + size), 2)
                    pygame.draw.line(self.screen, (255, 0, 0), 
                                   (tower_x - size, tower_y + size),
                                   (tower_x + size, tower_y - size), 2)
        
        elif self.placement_mode == 'delete':
            grid_x, grid_y = self.grid.pixel_to_grid(self.mouse_pos[0], self.mouse_pos[1])
            tower = self.get_tower_at_position(grid_x, grid_y)
            
            # Only show preview if mouse is over grid
            if 0 <= grid_x < self.grid_size and 0 <= grid_y < self.grid_size:
                tower_x, tower_y = self.grid.grid_to_pixel(grid_x, grid_y)
                
                if tower:
                    # Tower found - show sell preview (red highlight)
                    pygame.draw.circle(self.screen, (255, 100, 100), 
                                     (tower_x, tower_y), tower.size + 5, 2)
    
    def run(self):
        """Run the main game loop."""
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds
            
            self.handle_events()
            self.update(dt)
            self.render()
        
        pygame.quit()

