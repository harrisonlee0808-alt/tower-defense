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
        
        # UI layout config
        ui_config = self.game_config['ui']
        self.sidebar_width = ui_config['sidebar_width']
        self.sidebar_padding = ui_config['sidebar_padding']
        self.window_margin = ui_config['window_margin']
        
        # Calculate window size
        map_width_px = self.grid_size * self.tile_size
        map_height_px = self.grid_size * self.tile_size
        window_width = self.window_margin * 3 + map_width_px + self.sidebar_width
        window_height = self.window_margin * 2 + map_height_px
        
        # Map origin offset
        self.map_origin_x = self.window_margin
        self.map_origin_y = self.window_margin
        
        # Sidebar position
        self.sidebar_x = self.window_margin * 2 + map_width_px
        self.sidebar_y = self.window_margin
        self.sidebar_height = map_height_px
        
        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption("Tower Defense - Base Defense")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game state
        self.core = None
        self.towers = []
        self.enemies = []
        self.wave_number = 1
        self.wave_active = False
        self.wave_complete = False
        self.enemies_spawned = 0
        self.enemies_per_wave = 0  # Will be calculated based on wave_number
        self.spawn_interval = 0.0  # Will be calculated based on wave_number
        self.last_spawn_time = 0.0
        self.wave_reward = 0  # Reward for current wave
        
        # Economy
        self.currency_name = self.game_config['currency_name']
        self.energy = self.game_config['starting_currency']
        self.sell_refund_pct = self.game_config['sell_refund_pct']
        self.require_at_least_one_tower = self.game_config.get('require_at_least_one_tower', False)
        
        # Phase system: 'build', 'wave', or 'wave_complete'
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
        core_x, core_y = self._grid_to_screen_pixel(center_x, center_y)
        
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
    
    def _grid_to_screen_pixel(self, grid_x, grid_y):
        """Convert grid coordinates to screen pixel coordinates (with map offset)."""
        pixel_x, pixel_y = self.grid.grid_to_pixel(grid_x, grid_y)
        return (pixel_x + self.map_origin_x, pixel_y + self.map_origin_y)
    
    def _screen_pixel_to_grid(self, screen_x, screen_y):
        """Convert screen pixel coordinates to grid coordinates (accounting for map offset)."""
        # Adjust for map origin
        map_x = screen_x - self.map_origin_x
        map_y = screen_y - self.map_origin_y
        return self.grid.pixel_to_grid(map_x, map_y)
    
    def _calculate_wave_params(self, wave_num):
        """Calculate wave parameters based on wave number."""
        scaling = self.game_config['wave_scaling']
        
        # Enemy count
        enemy_count = scaling['base_enemy_count'] + (wave_num - 1) * scaling['enemy_count_growth']
        
        # Spawn interval
        spawn_interval = scaling['base_spawn_interval'] - (wave_num - 1) * scaling['spawn_interval_decay']
        spawn_interval = max(scaling['min_spawn_interval'], spawn_interval)
        
        return enemy_count, spawn_interval
    
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
                    elif self.phase == 'wave_complete':
                        self.complete_wave()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_placement(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
    
    def handle_placement(self, mouse_pos):
        """Handle structure placement and deletion."""
        grid_x, grid_y = self._screen_pixel_to_grid(mouse_pos[0], mouse_pos[1])
        
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
        tower_x, tower_y = self._grid_to_screen_pixel(grid_x, grid_y)
        for tower in self.towers:
            t_x, t_y = tower.get_position()
            if abs(t_x - tower_x) < 1 and abs(t_y - tower_y) < 1:
                return False
        
        return True
    
    def place_tower(self, grid_x, grid_y):
        """Place a tower at the given grid position."""
        tower_x, tower_y = self._grid_to_screen_pixel(grid_x, grid_y)
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
        tower_x, tower_y = self._grid_to_screen_pixel(grid_x, grid_y)
        
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
        tower_x, tower_y = self._grid_to_screen_pixel(grid_x, grid_y)
        for tower in self.towers:
            t_x, t_y = tower.get_position()
            if abs(t_x - tower_x) < 1 and abs(t_y - tower_y) < 1:
                return tower
        return None
    
    def start_wave(self):
        """Start a new enemy wave."""
        if self.wave_active:
            return
        
        # Check if at least one tower is required
        if self.require_at_least_one_tower and len(self.towers) == 0:
            self.show_message("Place at least one tower first", 2.0)
            return
        
        # Calculate wave parameters
        self.enemies_per_wave, self.spawn_interval = self._calculate_wave_params(self.wave_number)
        
        self.phase = 'wave'
        self.wave_active = True
        self.wave_complete = False
        self.enemies_spawned = 0
        self.enemies = []
        self.last_spawn_time = 0.0
        self.wave_reward = 0
        self.placement_mode = None  # Exit placement mode when wave starts
    
    def spawn_enemy(self):
        """Spawn a new enemy at a random edge position with scaled stats."""
        spawn_points = self.grid.get_spawn_points()
        if not spawn_points:
            return
        
        spawn_point = random.choice(spawn_points)
        spawn_x, spawn_y = self._grid_to_screen_pixel(spawn_point[0], spawn_point[1])
        
        # Get base enemy stats
        enemy_data = self.enemy_config['basic_enemy']
        base_health = enemy_data['health']
        base_speed = enemy_data['speed']
        base_damage = enemy_data['damage']
        
        # Apply wave scaling
        scaling = self.game_config['wave_scaling']
        wave_num = self.wave_number
        hp_mult = scaling['enemy_hp_multiplier_per_wave']
        speed_mult = scaling['enemy_speed_multiplier_per_wave']
        damage_mult = scaling['enemy_damage_multiplier_per_wave']
        
        scaled_health = round(base_health * (hp_mult ** (wave_num - 1)))
        scaled_speed = base_speed * (speed_mult ** (wave_num - 1))
        scaled_damage = round(base_damage * (damage_mult ** (wave_num - 1)))
        
        enemy = Enemy(
            spawn_x, spawn_y,
            scaled_health,
            scaled_speed,
            scaled_damage,
            enemy_data['size'],
            tuple(enemy_data['color'])
        )
        self.enemies.append(enemy)
        self.enemies_spawned += 1
    
    def complete_wave(self):
        """Complete the wave, give mining reward, and degrade the core."""
        if not self.wave_complete:
            return
        
        # Calculate and give mining reward (for the wave that just completed)
        mining_config = self.game_config['core_mining']
        reward = mining_config['reward_base'] + (self.wave_number - 1) * mining_config['reward_growth']
        
        if 'reward_multiplier_per_wave' in mining_config:
            reward = round(reward * (mining_config['reward_multiplier_per_wave'] ** (self.wave_number - 1)))
        
        self.energy += reward
        
        # Degrade core
        self.core.degrade_after_wave()
        
        # Advance to next wave
        self.wave_number += 1
        
        self.phase = 'build'
        self.wave_active = False
        self.wave_complete = False
        self.wave_reward = 0  # Reset for next wave
        
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
        
        # Check wave completion - auto-advance to wave_complete phase
        if (self.enemies_spawned >= self.enemies_per_wave and
            all(not enemy.is_alive() for enemy in self.enemies)):
            if not self.wave_complete:
                self.wave_complete = True
                self.phase = 'wave_complete'
                
                # Calculate mining reward for display
                mining_config = self.game_config['core_mining']
                reward = mining_config['reward_base'] + (self.wave_number - 1) * mining_config['reward_growth']
                if 'reward_multiplier_per_wave' in mining_config:
                    reward = round(reward * (mining_config['reward_multiplier_per_wave'] ** (self.wave_number - 1)))
                self.wave_reward = reward
                
                print(f"Wave complete! Core integrity: {self.core.current_integrity}/{self.core.max_integrity}")
    
    def render(self):
        """Render the game."""
        self.screen.fill((30, 30, 30))  # Dark background
        
        # Create a surface for the map area
        map_surface = pygame.Surface((self.grid.width, self.grid.height))
        map_surface.fill((50, 50, 50))
        
        # Render grid to map surface
        self.grid.render(map_surface)
        
        # Render core to map surface (temporarily adjust coordinates for rendering)
        if self.core:
            core_x_orig = self.core.x
            core_y_orig = self.core.y
            self.core.x -= self.map_origin_x
            self.core.y -= self.map_origin_y
            self.core.render(map_surface)
            self.core.x = core_x_orig
            self.core.y = core_y_orig
        
        # Render towers to map surface
        for tower in self.towers:
            tower_x_orig = tower.x
            tower_y_orig = tower.y
            tower.x -= self.map_origin_x
            tower.y -= self.map_origin_y
            tower.render(map_surface)
            tower.x = tower_x_orig
            tower.y = tower_y_orig
        
        # Render enemies to map surface
        for enemy in self.enemies:
            enemy_x_orig = enemy.x
            enemy_y_orig = enemy.y
            enemy.x -= self.map_origin_x
            enemy.y -= self.map_origin_y
            enemy.render(map_surface)
            enemy.x = enemy_x_orig
            enemy.y = enemy_y_orig
        
        # Blit map surface to screen at offset
        self.screen.blit(map_surface, (self.map_origin_x, self.map_origin_y))
        
        # Render hover preview (uses screen coordinates)
        self.render_hover_preview()
        
        # Render sidebar
        self.render_sidebar()
        
        pygame.display.flip()
    
    def render_sidebar(self):
        """Render the sidebar panel with all UI text."""
        # Draw sidebar background
        sidebar_rect = pygame.Rect(self.sidebar_x, self.sidebar_y, 
                                  self.sidebar_width, self.sidebar_height)
        pygame.draw.rect(self.screen, (40, 40, 40), sidebar_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), sidebar_rect, 2)  # Border
        
        # Prepare text content
        font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 20)
        
        x = self.sidebar_x + self.sidebar_padding
        y = self.sidebar_y + self.sidebar_padding
        
        # Wave number
        wave_text = font.render(f"Wave: {self.wave_number}", True, (255, 255, 255))
        self.screen.blit(wave_text, (x, y))
        y += 30
        
        # Phase
        phase_text = self.get_phase_text()
        phase_surface = font.render(f"Phase: {phase_text}", True, (200, 200, 200))
        self.screen.blit(phase_surface, (x, y))
        y += 30
        
        # Currency
        currency_text = font.render(f"{self.currency_name}: {int(self.energy)}", True, (255, 255, 100))
        self.screen.blit(currency_text, (x, y))
        y += 30
        
        # Core integrity
        core_text = font.render(f"Core: {int(self.core.current_integrity)}/{int(self.core.max_integrity)}", 
                               True, (255, 255, 255))
        self.screen.blit(core_text, (x, y))
        y += 30
        
        # Current mode
        mode_text = small_font.render(f"Mode: {self.get_mode_text()}", True, (180, 180, 180))
        self.screen.blit(mode_text, (x, y))
        y += 35
        
        # Next wave preview (only in build phase)
        if self.phase == 'build':
            next_wave_num = self.wave_number
            next_enemy_count, next_spawn_interval = self._calculate_wave_params(next_wave_num)
            
            # Get scaling multipliers for preview
            scaling = self.game_config['wave_scaling']
            enemy_data = self.enemy_config['basic_enemy']
            hp_mult = scaling['enemy_hp_multiplier_per_wave']
            base_hp = enemy_data['health']
            preview_hp = round(base_hp * (hp_mult ** (next_wave_num - 1)))
            
            preview_texts = [
                "Next Wave:",
                f"  Enemies: {next_enemy_count}",
                f"  Spawn: {next_spawn_interval:.2f}s",
                f"  Enemy HP: {preview_hp}"
            ]
            
            for text in preview_texts:
                preview_surface = small_font.render(text, True, (150, 150, 200))
                self.screen.blit(preview_surface, (x, y))
                y += 22
            y += 10
        
        # Wave status
        if self.phase == 'wave':
            alive_count = sum(1 for e in self.enemies if e.is_alive())
            status_text = font.render(f"Enemies: {alive_count}/{self.enemies_per_wave}", True, (255, 150, 150))
            self.screen.blit(status_text, (x, y))
            y += 30
        elif self.phase == 'wave_complete':
            status_text = font.render("Wave Cleared!", True, (100, 255, 100))
            self.screen.blit(status_text, (x, y))
            y += 25
            if self.wave_reward > 0:
                reward_text = small_font.render(f"Mined this wave: +{self.wave_reward}", True, (100, 255, 100))
                self.screen.blit(reward_text, (x, y))
                y += 25
            continue_text = small_font.render("Press SPACE to continue", True, (200, 200, 200))
            self.screen.blit(continue_text, (x, y))
            y += 30
        
        y += 10
        
        # Controls
        controls = [
            "Controls:",
            "T - Place Tower",
            "X - Sell Tower",
            "SPACE - Start/Complete",
            "ESC - Quit"
        ]
        
        for control in controls:
            control_surface = small_font.render(control, True, (150, 150, 150))
            self.screen.blit(control_surface, (x, y))
            y += 22
        
        # UI message
        if self.ui_message:
            y += 10
            msg_surface = font.render(f"> {self.ui_message}", True, (255, 200, 100))
            self.screen.blit(msg_surface, (x, y))
    
    def get_phase_text(self):
        """Get text description of current phase."""
        if self.phase == 'build':
            return "Build"
        elif self.phase == 'wave':
            return "Wave"
        elif self.phase == 'wave_complete':
            return "Wave Complete"
        return "Unknown"
    
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
        
        # Convert screen coordinates to grid
        grid_x, grid_y = self._screen_pixel_to_grid(self.mouse_pos[0], self.mouse_pos[1])
        
        # Only show preview if mouse is over grid area
        if not (0 <= grid_x < self.grid_size and 0 <= grid_y < self.grid_size):
            return
        
        # Check if mouse is actually over the map area (not sidebar)
        if not (self.map_origin_x <= self.mouse_pos[0] < self.map_origin_x + self.grid.width and
                self.map_origin_y <= self.mouse_pos[1] < self.map_origin_y + self.grid.height):
            return
        
        if self.placement_mode == 'tower':
            # Check if position is valid
            can_place = self.can_place_tower(grid_x, grid_y)
            tower_data = self.tower_config[self.selected_tower_type]
            tower_x, tower_y = self._grid_to_screen_pixel(grid_x, grid_y)
            
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
            tower = self.get_tower_at_position(grid_x, grid_y)
            tower_x, tower_y = self._grid_to_screen_pixel(grid_x, grid_y)
            
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

