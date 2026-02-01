"""
Main game loop and state management.
"""

import pygame
import json
import os
import random
import math
from src.grid import Grid
from src.core import EnergyCore
from src.tower import DefenseTower
from src.mine import Mine
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
        self.mines = []
        self.enemies = []
        self.wave_number = 1
        self.wave_active = False
        self.wave_complete = False
        self.enemies_spawned = 0
        self.enemies_per_wave = 0  # Will be calculated based on wave_number
        self.spawn_interval = 0.0  # Will be calculated based on wave_number
        self.last_spawn_time = 0.0
        self.wave_reward = 0  # Reward for current wave
        
        # Occupancy grid for multi-tile buildings
        # None = empty, else = building object reference
        self.occupancy_grid = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.next_building_id = 1
        self.core_original_max_integrity = 0
        
        # Wave focus direction (determined at start of build phase)
        self.wave_focus_direction = None  # 'N', 'E', 'S', 'W'
        wave_focus_config = self.game_config.get('wave_focus', {})
        self.wave_focus_enabled = wave_focus_config.get('enabled', False)
        self.wave_focus_majority_pct = wave_focus_config.get('majority_pct', 0.7)
        self.wave_focus_arrow_count = wave_focus_config.get('arrow_count', 3)
        self.wave_focus_arrow_pulse = wave_focus_config.get('arrow_pulse', True)
        self.arrow_pulse_time = 0.0
        
        # Pre-wave preview
        preview_config = self.game_config.get('preview_incoming', {})
        self.preview_enabled = preview_config.get('enabled', True)
        self.preview_marker_count = preview_config.get('marker_count', 6)
        self.preview_show_in_build = preview_config.get('show_in_build_phase', True)
        
        # Wave countdown
        countdown_config = self.game_config.get('wave_countdown', {})
        self.countdown_enabled = countdown_config.get('enabled', True)
        self.countdown_duration = countdown_config.get('duration', 3.0)
        self.countdown_timer = 0.0
        self.countdown_active = False
        
        # Emergency repair
        repair_config = self.game_config.get('emergency_repair', {})
        self.repair_enabled = repair_config.get('enabled', True)
        self.repair_cost = repair_config.get('cost', 30)
        self.repair_amount = repair_config.get('restore_amount', 20)
        self.repair_used = False
        
        # Pause system
        self.paused = False
        
        # Fast-forward system (build phase only)
        self.game_speed = 1.0  # 1.0 = normal, 2.0 = fast-forward
        
        # Tooltip system
        self.hovered_tower = None
        self.hovered_enemy = None
        
        # Economy
        self.currency_name = self.game_config['currency_name']
        self.energy = self.game_config['starting_currency']
        self.sell_refund_pct = self.game_config['sell_refund_pct']
        self.require_at_least_one_tower = self.game_config.get('require_at_least_one_tower', False)
        
        # Phase system: 'build', 'wave', or 'wave_complete'
        self.phase = 'build'
        
        # Build mode: 'none', 'place', 'sell', 'select'
        self.build_mode = 'none'
        self.is_selecting_tower = False
        self.selected_tower_type = None  # 'basic_tower', 'mine', or None
        
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
        core_config = self.game_config['core']
        core_footprint_w = core_config.get('footprint_w', 3)
        core_footprint_h = core_config.get('footprint_h', 3)
        
        # Center the core footprint
        center_x = self.grid_size // 2
        center_y = self.grid_size // 2
        core_origin_x = center_x - core_footprint_w // 2
        core_origin_y = center_y - core_footprint_h // 2
        
        # Get center pixel position
        core_center_x = center_x
        core_center_y = center_y
        core_x, core_y = self._grid_to_screen_pixel(core_center_x, core_center_y)
        
        self.core = EnergyCore(
            core_x, core_y,
            core_config['max_integrity'],
            core_config['integrity_loss_per_wave'],
            core_config['size'],
            tuple(core_config['color'])
        )
        self.core_original_max_integrity = core_config['max_integrity']
        
        # Store footprint info on core with origin tile coordinates
        self.core.origin_tile_x = core_origin_x
        self.core.origin_tile_y = core_origin_y
        self.core.footprint_w = core_footprint_w
        self.core.footprint_h = core_footprint_h
        self.core.occupied_tiles = []
        
        # Mark all core tiles as occupied
        for dy in range(core_footprint_h):
            for dx in range(core_footprint_w):
                tile_x = core_origin_x + dx
                tile_y = core_origin_y + dy
                if 0 <= tile_x < self.grid_size and 0 <= tile_y < self.grid_size:
                    self.grid.set_tile(tile_x, tile_y, 0)
                    self.occupancy_grid[tile_y][tile_x] = self.core
                    self.core.occupied_tiles.append((tile_x, tile_y))
        
        # Set next wave focus direction for preview
        self._set_next_wave_focus()
    
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
    
    def _set_next_wave_focus(self):
        """Set the focus direction for the next wave (for preview)."""
        if self.wave_focus_enabled:
            self.wave_focus_direction = random.choice(['N', 'E', 'S', 'W'])
        else:
            self.wave_focus_direction = None
    
    def _calculate_wave_params(self, wave_num):
        """Calculate wave parameters based on wave number."""
        scaling = self.game_config['wave_scaling']
        
        # Enemy count
        enemy_count = scaling['base_enemy_count'] + (wave_num - 1) * scaling['enemy_count_growth']
        
        # Spawn interval
        spawn_interval = scaling['base_spawn_interval'] - (wave_num - 1) * scaling['spawn_interval_decay']
        spawn_interval = max(scaling['min_spawn_interval'], spawn_interval)
        
        # Enemy mix ratios
        heavy_ratio_base = scaling.get('heavy_ratio_base', 0.25)
        heavy_ratio_growth = scaling.get('heavy_ratio_growth', 0.01)
        heavy_ratio_max = scaling.get('heavy_ratio_max', 0.6)
        heavy_ratio = min(heavy_ratio_max, heavy_ratio_base + (wave_num - 1) * heavy_ratio_growth)
        heavy_count = round(enemy_count * heavy_ratio)
        light_count = enemy_count - heavy_count
        
        return enemy_count, spawn_interval, heavy_count, light_count
    
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.is_selecting_tower or self.build_mode == 'place':
                        # Cancel selection/placement
                        self.is_selecting_tower = False
                        self.build_mode = 'none'
                        self.selected_tower_type = None
                    else:
                        self.running = False
                elif event.key == pygame.K_t:
                    if self.phase == 'build':
                        if self.is_selecting_tower:
                            # Close selection
                            self.is_selecting_tower = False
                            self.build_mode = 'none'
                        elif self.build_mode == 'place':
                            # Return to selection
                            self.build_mode = 'select'
                            self.is_selecting_tower = True
                        else:
                            # Open selection
                            self.is_selecting_tower = True
                            self.build_mode = 'select'
                elif event.key == pygame.K_1:
                    if self.is_selecting_tower:
                        self.selected_tower_type = 'basic_tower'
                        self.is_selecting_tower = False
                        self.build_mode = 'place'
                elif event.key == pygame.K_2:
                    if self.is_selecting_tower:
                        self.selected_tower_type = 'mine'
                        self.is_selecting_tower = False
                        self.build_mode = 'place'
                elif event.key == pygame.K_x:
                    if self.phase == 'build':
                        if self.build_mode == 'sell':
                            self.build_mode = 'none'
                        else:
                            self.build_mode = 'sell'
                            self.is_selecting_tower = False
                            self.selected_tower_type = None
                elif event.key == pygame.K_SPACE:
                    if self.phase == 'build' and not self.wave_active and not self.wave_complete and not self.countdown_active:
                        self.start_wave()
                    elif self.phase == 'wave_complete':
                        self.complete_wave()
                elif event.key == pygame.K_r:
                    if self.phase == 'build' and not self.countdown_active:
                        if self.build_mode == 'place':
                            # Rotate footprint (if not in selection mode)
                            pass  # Rotation feature - can be added later
                        else:
                            self.emergency_repair()
                elif event.key == pygame.K_p:
                    # Toggle pause
                    if self.phase == 'wave' or self.countdown_active:
                        self.paused = not self.paused
                elif event.key == pygame.K_f:
                    # Toggle fast-forward (build phase only)
                    if self.phase == 'build' and not self.countdown_active:
                        self.game_speed = 2.0 if self.game_speed == 1.0 else 1.0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_placement(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
                # Update hovered structures/enemies for tooltips
                self._update_hovered_objects(event.pos)
                # Update hovered structures/enemies for tooltips
                self._update_hovered_objects(event.pos)
    
    def handle_placement(self, mouse_pos):
        """Handle structure placement and deletion."""
        grid_x, grid_y = self._screen_pixel_to_grid(mouse_pos[0], mouse_pos[1])
        
        if self.build_mode == 'place':
            if self.phase != 'build':
                self.show_message("Can't place during wave", 2.0)
                return
            
            if not self.selected_tower_type:
                return
            
            if self.selected_tower_type == 'mine':
                if self.can_place_mine(grid_x, grid_y):
                    self.place_mine(grid_x, grid_y)
                else:
                    mine_data = self.tower_config['mine']
                    if self.energy < mine_data['cost']:
                        self.show_message("Not enough energy", 2.0)
                    elif not self.grid.is_buildable(grid_x, grid_y):
                        self.show_message("Can't build here", 1.0)
            else:  # basic_tower
                if self.can_place_tower(grid_x, grid_y):
                    self.place_tower(grid_x, grid_y)
                else:
                    tower_data = self.tower_config[self.selected_tower_type]
                    if self.energy < tower_data['cost']:
                        self.show_message("Not enough energy", 2.0)
                    elif not self.grid.is_buildable(grid_x, grid_y):
                        self.show_message("Can't build here", 1.0)
        
        elif self.build_mode == 'sell':
            if self.phase != 'build':
                self.show_message("Can't sell during wave", 2.0)
                return
            
            self.sell_structure(grid_x, grid_y)
    
    def _get_footprint_tiles(self, origin_x, origin_y, footprint_w, footprint_h):
        """Get list of tiles in a footprint."""
        tiles = []
        for dy in range(footprint_h):
            for dx in range(footprint_w):
                tile_x = origin_x + dx
                tile_y = origin_y + dy
                if 0 <= tile_x < self.grid_size and 0 <= tile_y < self.grid_size:
                    tiles.append((tile_x, tile_y))
        return tiles
    
    def _can_place_footprint(self, origin_x, origin_y, footprint_w, footprint_h):
        """Check if a footprint can be placed (all tiles buildable and empty)."""
        tiles = self._get_footprint_tiles(origin_x, origin_y, footprint_w, footprint_h)
        
        for tile_x, tile_y in tiles:
            if not self.grid.is_buildable(tile_x, tile_y):
                return False
            if self.occupancy_grid[tile_y][tile_x] is not None:
                return False
        
        return True
    
    def _mark_footprint_occupied(self, origin_x, origin_y, footprint_w, footprint_h, building):
        """Mark all tiles in a footprint as occupied by a building."""
        tiles = self._get_footprint_tiles(origin_x, origin_y, footprint_w, footprint_h)
        building.occupied_tiles = tiles
        
        for tile_x, tile_y in tiles:
            self.grid.set_tile(tile_x, tile_y, 0)
            self.occupancy_grid[tile_y][tile_x] = building
    
    def _clear_footprint(self, building):
        """Clear a building's footprint from the occupancy grid."""
        for tile_x, tile_y in building.occupied_tiles:
            self.grid.set_tile(tile_x, tile_y, 1)
            self.occupancy_grid[tile_y][tile_x] = None
        building.occupied_tiles = []
        
        # Debug assertion: verify no references remain
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                if self.occupancy_grid[y][x] == building:
                    print(f"WARNING: Building still in occupancy grid at ({x}, {y})")
    
    def can_place_tower(self, grid_x, grid_y):
        """Check if a tower can be placed at the given grid position (top-left of footprint)."""
        if self.phase != 'build' or self.countdown_active:
            return False
        
        if not self.selected_tower_type or self.selected_tower_type not in self.tower_config:
            return False
        
        tower_data = self.tower_config[self.selected_tower_type]
        if self.energy < tower_data['cost']:
            return False
        
        footprint_w = tower_data.get('footprint_w', 1)
        footprint_h = tower_data.get('footprint_h', 1)
        
        return self._can_place_footprint(grid_x, grid_y, footprint_w, footprint_h)
    
    def can_place_mine(self, grid_x, grid_y):
        """Check if a mine can be placed at the given grid position (top-left of footprint)."""
        if self.phase != 'build' or self.countdown_active:
            return False
        
        mine_data = self.tower_config['mine']
        if self.energy < mine_data['cost']:
            return False
        
        footprint_w = mine_data.get('footprint_w', 1)
        footprint_h = mine_data.get('footprint_h', 1)
        
        return self._can_place_footprint(grid_x, grid_y, footprint_w, footprint_h)
    
    def place_tower(self, grid_x, grid_y):
        """Place a tower at the given grid position (top-left of footprint)."""
        tower_data = self.tower_config[self.selected_tower_type]
        footprint_w = tower_data.get('footprint_w', 1)
        footprint_h = tower_data.get('footprint_h', 1)
        
        # Store origin tile (top-left of footprint)
        origin_tile_x = grid_x
        origin_tile_y = grid_y
        
        # Calculate center position for targeting (center of footprint)
        center_grid_x = grid_x + footprint_w / 2.0
        center_grid_y = grid_y + footprint_h / 2.0
        tower_x, tower_y = self._grid_to_screen_pixel(center_grid_x, center_grid_y)
        
        # Calculate range in pixels from range_tiles
        range_tiles = tower_data.get('range_tiles', 3.0)
        range_pixels = range_tiles * self.tile_size
        
        tower = DefenseTower(
            tower_x, tower_y,
            tower_data['damage'],
            range_pixels,
            tower_data['cooldown'],
            tower_data['size'],
            tuple(tower_data['color']),
            tower_data['cost']
        )
        
        # Store footprint info with origin tile coordinates
        tower.origin_tile_x = origin_tile_x
        tower.origin_tile_y = origin_tile_y
        tower.footprint_w = footprint_w
        tower.footprint_h = footprint_h
        tower.occupied_tiles = []
        
        # Mark footprint as occupied
        self._mark_footprint_occupied(origin_tile_x, origin_tile_y, footprint_w, footprint_h, tower)
        
        self.towers.append(tower)
        self.energy -= tower_data['cost']
        # Keep in place mode after placing (don't exit)
    
    def place_mine(self, grid_x, grid_y):
        """Place a mine at the given grid position (top-left of footprint)."""
        mine_data = self.tower_config['mine']
        footprint_w = mine_data.get('footprint_w', 1)
        footprint_h = mine_data.get('footprint_h', 1)
        
        # Store origin tile (top-left of footprint)
        origin_tile_x = grid_x
        origin_tile_y = grid_y
        
        # Calculate center position for rendering (center of footprint)
        center_grid_x = grid_x + footprint_w / 2.0
        center_grid_y = grid_y + footprint_h / 2.0
        mine_x, mine_y = self._grid_to_screen_pixel(center_grid_x, center_grid_y)
        
        mine = Mine(
            mine_x, mine_y,
            mine_data['radius_tiles'],
            self.tile_size,
            mine_data['damage'],
            mine_data['size'],
            tuple(mine_data['color']),
            mine_data['cost']
        )
        
        # Store footprint info with origin tile coordinates
        mine.origin_tile_x = origin_tile_x
        mine.origin_tile_y = origin_tile_y
        mine.footprint_w = footprint_w
        mine.footprint_h = footprint_h
        mine.occupied_tiles = []
        
        # Mark footprint as occupied
        self._mark_footprint_occupied(origin_tile_x, origin_tile_y, footprint_w, footprint_h, mine)
        
        self.mines.append(mine)
        self.energy -= mine_data['cost']
        # Keep in place mode after placing (don't exit)
    
    def sell_structure(self, grid_x, grid_y):
        """Sell a tower or mine at the given grid position (any tile in footprint)."""
        # Check occupancy grid to find building
        if not (0 <= grid_x < self.grid_size and 0 <= grid_y < self.grid_size):
            return
        
        building = self.occupancy_grid[grid_y][grid_x]
        if building is None:
            self.show_message("No structure here", 1.0)
            return
        
        # Don't allow selling core
        if building == self.core:
            self.show_message("Cannot sell core", 1.0)
            return
        
        # Calculate refund
        refund = int(building.cost * self.sell_refund_pct)
        self.energy += refund
        
        # Remove from appropriate list
        if building in self.towers:
            self.towers.remove(building)
        elif building in self.mines:
            self.mines.remove(building)
        
        # Clear footprint
        self._clear_footprint(building)
    
    def show_message(self, message, duration=2.0):
        """Show a temporary UI message."""
        self.ui_message = message
        self.ui_message_timer = duration
    
    def get_tower_at_position(self, grid_x, grid_y):
        """Get the tower at a given grid position, or None."""
        # Check occupancy grid
        if 0 <= grid_x < self.grid_size and 0 <= grid_y < self.grid_size:
            building = self.occupancy_grid[grid_y][grid_x]
            if building and building in self.towers:
                return building
        return None
    
    def _update_hovered_objects(self, mouse_pos):
        """Update hovered tower/enemy for tooltips."""
        self.hovered_tower = None
        self.hovered_enemy = None
        
        if self.phase == 'build':
            # Check for hovered towers/mines
            grid_x, grid_y = self._screen_pixel_to_grid(mouse_pos[0], mouse_pos[1])
            if 0 <= grid_x < self.grid_size and 0 <= grid_y < self.grid_size:
                building = self.occupancy_grid[grid_y][grid_x]
                if building and (building in self.towers or building in self.mines):
                    self.hovered_tower = building
        elif self.phase == 'wave':
            # Check for hovered enemies
            for enemy in self.enemies:
                if enemy.is_alive():
                    # Simple distance check (within enemy size)
                    dx = mouse_pos[0] - enemy.x
                    dy = mouse_pos[1] - enemy.y
                    if dx * dx + dy * dy < (enemy.size + 10) ** 2:
                        self.hovered_enemy = enemy
                        break
    
    def start_wave(self):
        """Start a new enemy wave (with countdown if enabled)."""
        if self.wave_active or self.countdown_active:
            return
        
        # Check if at least one tower is required
        if self.require_at_least_one_tower and len(self.towers) == 0 and len(self.mines) == 0:
            self.show_message("Place at least one structure first", 2.0)
            return
        
        # Calculate wave parameters
        self.enemies_per_wave, self.spawn_interval, self.heavy_count, self.light_count = self._calculate_wave_params(self.wave_number)
        
        # Create enemy type list (interleaved)
        self.enemy_spawn_queue = []
        total = self.heavy_count + self.light_count
        heavy_indices = set(random.sample(range(total), self.heavy_count))
        for i in range(total):
            self.enemy_spawn_queue.append('heavy' if i in heavy_indices else 'light')
        random.shuffle(self.enemy_spawn_queue)
        
        # Calculate focused vs non-focused spawns
        if self.wave_focus_enabled and self.wave_focus_direction:
            self.focused_spawns = round(self.enemies_per_wave * self.wave_focus_majority_pct)
            self.non_focused_spawns = self.enemies_per_wave - self.focused_spawns
        else:
            self.focused_spawns = 0
            self.non_focused_spawns = self.enemies_per_wave
        
        # Start countdown if enabled
        if self.countdown_enabled:
            self.countdown_active = True
            self.countdown_timer = self.countdown_duration
            self.build_mode = 'none'
            self.is_selecting_tower = False
        else:
            self._begin_wave_spawning()
    
    def _begin_wave_spawning(self):
        """Actually begin the wave (called after countdown)."""
        self.phase = 'wave'
        self.wave_active = True
        self.wave_complete = False
        self.enemies_spawned = 0
        self.enemies = []
        self.last_spawn_time = 0.0
        self.wave_reward = 0
        self.arrow_pulse_time = 0.0
        self.build_mode = 'none'  # Exit placement mode when wave starts
        self.is_selecting_tower = False
        self.selected_tower_type = None
    
    def spawn_enemy(self):
        """Spawn a new enemy at a random edge position with scaled stats."""
        # Determine if this should be a focused spawn
        is_focused = False
        if self.wave_focus_enabled and self.wave_focus_direction and self.focused_spawns > 0:
            if self.enemies_spawned < self.focused_spawns:
                is_focused = True
        
        # Get spawn points
        if is_focused:
            spawn_points = self._get_focused_spawn_points(self.wave_focus_direction)
        else:
            # Non-focused: can spawn from any edge except the focused one (or all if no focus)
            if self.wave_focus_enabled and self.wave_focus_direction:
                all_points = self.grid.get_spawn_points()
                focused_points = self._get_focused_spawn_points(self.wave_focus_direction)
                spawn_points = [p for p in all_points if p not in focused_points]
            else:
                spawn_points = self.grid.get_spawn_points()
        
        if not spawn_points:
            return
        
        spawn_point = random.choice(spawn_points)
        spawn_x, spawn_y = self._grid_to_screen_pixel(spawn_point[0], spawn_point[1])
        
        # Get enemy type from queue
        if self.enemies_spawned < len(self.enemy_spawn_queue):
            enemy_type = self.enemy_spawn_queue[self.enemies_spawned]
        else:
            enemy_type = 'light'  # Fallback
        
        # Get base enemy stats
        enemy_data = self.enemy_config[enemy_type]
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
        enemy.enemy_type = enemy_type  # Store type for UI
        self.enemies.append(enemy)
        self.enemies_spawned += 1
    
    def _get_focused_spawn_points(self, direction):
        """Get spawn points for a specific direction (N, E, S, W)."""
        all_points = self.grid.get_spawn_points()
        focused = []
        
        for x, y in all_points:
            if direction == 'N' and y == 0:  # Top edge
                focused.append((x, y))
            elif direction == 'S' and y == self.grid_size - 1:  # Bottom edge
                focused.append((x, y))
            elif direction == 'W' and x == 0:  # Left edge
                focused.append((x, y))
            elif direction == 'E' and x == self.grid_size - 1:  # Right edge
                focused.append((x, y))
        
        return focused
    
    def emergency_repair(self):
        """Emergency repair - restore core HP once per base."""
        if self.repair_used:
            self.show_message("Repair already used", 2.0)
            return
        
        if self.energy < self.repair_cost:
            self.show_message("Not enough energy", 2.0)
            return
        
        self.core.current_integrity = min(self.core.max_integrity, 
                                          self.core.current_integrity + self.repair_amount)
        self.energy -= self.repair_cost
        self.repair_used = True
        self.show_message(f"Repaired +{self.repair_amount} HP", 2.0)
    
    def complete_wave(self):
        """Complete the wave, give mining reward, and degrade the core."""
        if not self.wave_complete:
            return
        
        # Calculate base mining reward
        mining_config = self.game_config['core_mining']
        reward = mining_config['reward_base'] + (self.wave_number - 1) * mining_config['reward_growth']
        
        if 'reward_multiplier_per_wave' in mining_config:
            reward = round(reward * (mining_config['reward_multiplier_per_wave'] ** (self.wave_number - 1)))
        
        # Apply mining efficiency based on core integrity
        if self.core_original_max_integrity > 0:
            efficiency = self.core.max_integrity / self.core_original_max_integrity
            reward = round(reward * efficiency)
        
        self.energy += reward
        
        # Degrade core
        self.core.degrade_after_wave()
        
        # Advance to next wave
        self.wave_number += 1
        
        # Set next wave focus for preview
        self._set_next_wave_focus()
        
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
        
        # Update countdown
        if self.countdown_active:
            self.countdown_timer -= dt
            if self.countdown_timer <= 0:
                self.countdown_active = False
                self._begin_wave_spawning()
            return  # Don't update game during countdown
        
        # Update arrow pulse animation
        if (self.wave_active or (self.preview_show_in_build and self.phase == 'build')) and self.wave_focus_arrow_pulse:
            self.arrow_pulse_time += dt
        
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
        
        # Update mines
        for mine in self.mines[:]:  # Use slice to safely remove during iteration
            mine.update(dt, self.enemies)
            if mine.is_consumed():
                # Clear footprint from occupancy grid before removing
                self._clear_footprint(mine)
                self.mines.remove(mine)
        
        # Check wave completion - auto-advance to wave_complete phase
        if (self.enemies_spawned >= self.enemies_per_wave and
            all(not enemy.is_alive() for enemy in self.enemies)):
            if not self.wave_complete:
                self.wave_complete = True
                self.phase = 'wave_complete'
                
                # Calculate mining reward for display (with efficiency)
                mining_config = self.game_config['core_mining']
                reward = mining_config['reward_base'] + (self.wave_number - 1) * mining_config['reward_growth']
                if 'reward_multiplier_per_wave' in mining_config:
                    reward = round(reward * (mining_config['reward_multiplier_per_wave'] ** (self.wave_number - 1)))
                # Apply mining efficiency
                if self.core_original_max_integrity > 0:
                    efficiency = self.core.max_integrity / self.core_original_max_integrity
                    reward = round(reward * efficiency)
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
        
        # Render core to map surface
        if self.core:
            self.core.render(map_surface, 0, 0, self.tile_size,
                           self.core.origin_tile_x, self.core.origin_tile_y,
                           self.core.footprint_w, self.core.footprint_h)
        
        # Render towers to map surface
        for tower in self.towers:
            tower.render(map_surface, 0, 0, self.tile_size,
                        tower.origin_tile_x, tower.origin_tile_y,
                        tower.footprint_w, tower.footprint_h)
        
        # Render enemies to map surface
        for enemy in self.enemies:
            enemy_x_orig = enemy.x
            enemy_y_orig = enemy.y
            enemy.x -= self.map_origin_x
            enemy.y -= self.map_origin_y
            enemy.render(map_surface)
            enemy.x = enemy_x_orig
            enemy.y = enemy_y_orig
        
        # Render mines to map surface
        for mine in self.mines:
            mine.render(map_surface, 0, 0, self.tile_size,
                       mine.origin_tile_x, mine.origin_tile_y,
                       mine.footprint_w, mine.footprint_h)
        
        # Blit map surface to screen at offset
        self.screen.blit(map_surface, (self.map_origin_x, self.map_origin_y))
        
        # Render focus direction arrows (during wave or preview in build phase)
        if self.wave_active and self.wave_focus_enabled and self.wave_focus_direction:
            self.render_focus_arrows()
        elif self.preview_show_in_build and self.phase == 'build' and self.wave_focus_enabled and self.wave_focus_direction:
            self.render_preview_arrows()
        
        # Render hover preview (uses screen coordinates)
        self.render_hover_preview()
        
        # Render sidebar
        self.render_sidebar()
        
        pygame.display.flip()
    
    def render_focus_arrows(self):
        """Render arrows indicating the wave focus direction."""
        arrow_size = 15
        arrow_color = (255, 200, 0)
        
        # Pulse effect
        pulse_alpha = 1.0
        if self.wave_focus_arrow_pulse:
            pulse_alpha = 0.7 + 0.3 * math.sin(self.arrow_pulse_time * 3.0)
        
        # Calculate arrow positions based on direction
        map_width = self.grid.width
        map_height = self.grid.height
        arrow_spacing = map_width // (self.wave_focus_arrow_count + 1)
        
        for i in range(self.wave_focus_arrow_count):
            if self.wave_focus_direction == 'N':  # Top edge, pointing down
                x = self.map_origin_x + arrow_spacing * (i + 1)
                y = self.map_origin_y + 5
                points = [
                    (x, y),
                    (x - arrow_size // 2, y + arrow_size),
                    (x + arrow_size // 2, y + arrow_size)
                ]
            elif self.wave_focus_direction == 'S':  # Bottom edge, pointing up
                x = self.map_origin_x + arrow_spacing * (i + 1)
                y = self.map_origin_y + map_height - 5
                points = [
                    (x, y),
                    (x - arrow_size // 2, y - arrow_size),
                    (x + arrow_size // 2, y - arrow_size)
                ]
            elif self.wave_focus_direction == 'W':  # Left edge, pointing right
                x = self.map_origin_x + 5
                y = self.map_origin_y + arrow_spacing * (i + 1)
                points = [
                    (x, y),
                    (x + arrow_size, y - arrow_size // 2),
                    (x + arrow_size, y + arrow_size // 2)
                ]
            else:  # 'E' - Right edge, pointing left
                x = self.map_origin_x + map_width - 5
                y = self.map_origin_y + arrow_spacing * (i + 1)
                points = [
                    (x, y),
                    (x - arrow_size, y - arrow_size // 2),
                    (x - arrow_size, y + arrow_size // 2)
                ]
            
            # Draw arrow with pulse
            color = tuple(int(c * pulse_alpha) for c in arrow_color)
            pygame.draw.polygon(self.screen, color, points)
    
    def render_preview_arrows(self):
        """Render preview arrows for incoming wave (lighter color, labeled)."""
        arrow_size = 12
        arrow_color = (200, 200, 100)  # Lighter yellow for preview
        
        # Pulse effect (subtle)
        pulse_alpha = 0.6 + 0.2 * math.sin(self.arrow_pulse_time * 2.0)
        
        map_width = self.grid.width
        map_height = self.grid.height
        arrow_spacing = map_width // (self.wave_focus_arrow_count + 1)
        
        for i in range(self.wave_focus_arrow_count):
            if self.wave_focus_direction == 'N':
                x = self.map_origin_x + arrow_spacing * (i + 1)
                y = self.map_origin_y + 5
                points = [(x, y), (x - arrow_size // 2, y + arrow_size), (x + arrow_size // 2, y + arrow_size)]
            elif self.wave_focus_direction == 'S':
                x = self.map_origin_x + arrow_spacing * (i + 1)
                y = self.map_origin_y + map_height - 5
                points = [(x, y), (x - arrow_size // 2, y - arrow_size), (x + arrow_size // 2, y - arrow_size)]
            elif self.wave_focus_direction == 'W':
                x = self.map_origin_x + 5
                y = self.map_origin_y + arrow_spacing * (i + 1)
                points = [(x, y), (x + arrow_size, y - arrow_size // 2), (x + arrow_size, y + arrow_size // 2)]
            else:  # 'E'
                x = self.map_origin_x + map_width - 5
                y = self.map_origin_y + arrow_spacing * (i + 1)
                points = [(x, y), (x - arrow_size, y - arrow_size // 2), (x - arrow_size, y + arrow_size // 2)]
            
            color = tuple(int(c * pulse_alpha) for c in arrow_color)
            pygame.draw.polygon(self.screen, color, points)
    
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
        if self.paused:
            phase_text += " (Paused)"
        phase_surface = font.render(f"Phase: {phase_text}", True, (200, 200, 200))
        self.screen.blit(phase_surface, (x, y))
        y += 30
        
        # Game speed (build phase only)
        if self.phase == 'build' and self.game_speed > 1.0:
            speed_text = small_font.render(f"Speed: {int(self.game_speed)}x", True, (200, 255, 200))
            self.screen.blit(speed_text, (x, y))
            y += 25
        
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
        
        # Tower selection UI
        if self.is_selecting_tower:
            y += 5
            select_title = font.render("Select Tower:", True, (255, 255, 255))
            self.screen.blit(select_title, (x, y))
            y += 25
            
            # Basic Tower
            tower_data = self.tower_config['basic_tower']
            tower_name = tower_data.get('name', 'Basic Tower')
            tower_cost = tower_data['cost']
            tower_text = small_font.render(f"1 - {tower_name} ({tower_cost})", True, (200, 200, 255))
            self.screen.blit(tower_text, (x + 10, y))
            y += 22
            
            # Mine
            mine_data = self.tower_config['mine']
            mine_name = mine_data.get('name', 'Mine')
            mine_cost = mine_data['cost']
            mine_text = small_font.render(f"2 - {mine_name} ({mine_cost})", True, (255, 200, 100))
            self.screen.blit(mine_text, (x + 10, y))
            y += 30
        
        # Wave focus direction
        if self.wave_active and self.wave_focus_enabled and self.wave_focus_direction:
            focus_text = small_font.render(f"Wave Focus: {self.wave_focus_direction}", True, (255, 200, 100))
            self.screen.blit(focus_text, (x, y))
            y += 25
        
        # Mining efficiency
        if self.core_original_max_integrity > 0:
            efficiency_pct = int((self.core.max_integrity / self.core_original_max_integrity) * 100)
            efficiency_text = small_font.render(f"Mining Efficiency: {efficiency_pct}%", True, (200, 200, 255))
            self.screen.blit(efficiency_text, (x, y))
            y += 25
        
        # Countdown
        if self.countdown_active:
            countdown_text = font.render(f"RAID INCOMING: {int(self.countdown_timer) + 1}", True, (255, 100, 100))
            self.screen.blit(countdown_text, (x, y))
            y += 30
        
        # Next wave preview (only in build phase)
        if self.phase == 'build' and not self.countdown_active:
            next_wave_num = self.wave_number
            next_enemy_count, next_spawn_interval, next_heavy, next_light = self._calculate_wave_params(next_wave_num)
            
            preview_texts = [
                f"Next Wave: {next_wave_num}",
                f"  Enemies: {next_enemy_count}",
                f"  Mix: {next_heavy}H, {next_light}L",
                f"  Spawn: {next_spawn_interval:.2f}s"
            ]
            
            if self.wave_focus_enabled and self.wave_focus_direction:
                preview_texts.append(f"  Incoming: {self.wave_focus_direction}")
            
            # Calculate reward preview
            mining_config = self.game_config['core_mining']
            reward = mining_config['reward_base'] + (next_wave_num - 1) * mining_config['reward_growth']
            if 'reward_multiplier_per_wave' in mining_config:
                reward = round(reward * (mining_config['reward_multiplier_per_wave'] ** (next_wave_num - 1)))
            if self.core_original_max_integrity > 0:
                efficiency = self.core.max_integrity / self.core_original_max_integrity
                reward = round(reward * efficiency)
            preview_texts.append(f"  Reward: +{reward}")
            
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
        
        # Tooltips
        if self.hovered_tower:
            y += 10
            tooltip_title = small_font.render("Hovered Structure:", True, (255, 255, 200))
            self.screen.blit(tooltip_title, (x, y))
            y += 22
            
            if self.hovered_tower in self.towers:
                tower_data = self.tower_config['basic_tower']
                tooltip_lines = [
                    f"Type: {tower_data.get('name', 'Tower')}",
                    f"Cost: {self.hovered_tower.cost}",
                    f"Damage: {self.hovered_tower.damage}",
                    f"Range: {tower_data.get('range_tiles', 3.0):.1f} tiles",
                    f"Footprint: {self.hovered_tower.footprint_w}x{self.hovered_tower.footprint_h}"
                ]
            else:  # mine
                mine_data = self.tower_config['mine']
                tooltip_lines = [
                    f"Type: {mine_data.get('name', 'Mine')}",
                    f"Cost: {self.hovered_tower.cost}",
                    f"Damage: {self.hovered_tower.damage}",
                    f"Radius: {mine_data.get('radius_tiles', 1.5):.1f} tiles",
                    f"Footprint: {self.hovered_tower.footprint_w}x{self.hovered_tower.footprint_h}"
                ]
            
            for line in tooltip_lines:
                tooltip_surface = small_font.render(line, True, (200, 200, 255))
                self.screen.blit(tooltip_surface, (x + 5, y))
                y += 20
            y += 5
        
        if self.hovered_enemy:
            y += 10
            tooltip_title = small_font.render("Hovered Enemy:", True, (255, 200, 200))
            self.screen.blit(tooltip_title, (x, y))
            y += 22
            
            enemy_type = getattr(self.hovered_enemy, 'enemy_type', 'light')
            enemy_type_name = self.enemy_config.get(enemy_type, {}).get('name', enemy_type.capitalize())
            tooltip_lines = [
                f"Type: {enemy_type_name}",
                f"HP: {int(self.hovered_enemy.current_health)}/{int(self.hovered_enemy.max_health)}"
            ]
            
            for line in tooltip_lines:
                tooltip_surface = small_font.render(line, True, (255, 200, 200))
                self.screen.blit(tooltip_surface, (x + 5, y))
                y += 20
            y += 5
        
        # Emergency repair status
        if self.repair_enabled:
            repair_status = "Used" if self.repair_used else "Available"
            repair_text = small_font.render(f"Repair: {repair_status}", True, (200, 200, 200))
            self.screen.blit(repair_text, (x, y))
            y += 25
        
        # Controls
        controls = [
            "Controls:",
            "T - Select Tower",
            "1/2 - Choose Type",
            "X - Sell Structure",
            "R - Emergency Repair",
            "P - Pause (wave)",
            "F - Fast-forward (build)",
            "SPACE - Start/Complete",
            "ESC - Cancel/Quit"
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
        elif self.phase == 'wave_complete':
            return "Wave Complete"
        elif self.build_mode == 'place':
            if self.selected_tower_type == 'mine':
                return "Build (Place Mine)"
            elif self.selected_tower_type == 'basic_tower':
                return "Build (Place Tower)"
            else:
                return "Build (Place)"
        elif self.build_mode == 'sell':
            return "Build (Sell)"
        elif self.build_mode == 'select':
            return "Build (Select)"
        else:
            return "Build"
    
    def render_hover_preview(self):
        """Render hover preview for tower/mine placement."""
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
        
        if self.build_mode == 'place':
            if not self.selected_tower_type:
                return
            
            tower_x, tower_y = self._grid_to_screen_pixel(grid_x, grid_y)
            
            # Get footprint info
            if self.selected_tower_type == 'mine':
                can_place = self.can_place_mine(grid_x, grid_y)
                struct_data = self.tower_config['mine']
            else:
                can_place = self.can_place_tower(grid_x, grid_y)
                struct_data = self.tower_config[self.selected_tower_type]
            
            footprint_w = struct_data.get('footprint_w', 1)
            footprint_h = struct_data.get('footprint_h', 1)
            
            # Calculate footprint rectangle (top-left corner of footprint)
            # grid_x, grid_y is the top-left tile of the footprint
            origin_x = self.map_origin_x + grid_x * self.tile_size
            origin_y = self.map_origin_y + grid_y * self.tile_size
            footprint_rect = pygame.Rect(origin_x, origin_y, 
                                        footprint_w * self.tile_size, 
                                        footprint_h * self.tile_size)
            
            if can_place:
                # Valid placement - green outline
                pygame.draw.rect(self.screen, (100, 255, 100), footprint_rect, 2)
            else:
                # Invalid placement - red outline
                pygame.draw.rect(self.screen, (255, 100, 100), footprint_rect, 2)
                # Draw X marker
                pygame.draw.line(self.screen, (255, 0, 0), 
                               footprint_rect.topleft, footprint_rect.bottomright, 2)
                pygame.draw.line(self.screen, (255, 0, 0), 
                               footprint_rect.topright, footprint_rect.bottomleft, 2)
            
            # For mines, also show radius
            if self.selected_tower_type == 'mine':
                center_x = origin_x + footprint_rect.width // 2
                center_y = origin_y + footprint_rect.height // 2
                radius_pixels = struct_data['radius_tiles'] * self.tile_size
                pygame.draw.circle(self.screen, (100, 255, 100) if can_place else (255, 100, 100),
                                 (center_x, center_y), int(radius_pixels), 1)
        
        elif self.build_mode == 'sell':
            struct_x, struct_y = self._grid_to_screen_pixel(grid_x, grid_y)
            
            # Check for tower
            tower = self.get_tower_at_position(grid_x, grid_y)
            if tower:
                pygame.draw.circle(self.screen, (255, 100, 100), 
                                 (struct_x, struct_y), tower.size + 5, 2)
            else:
                # Check for mine
                for mine in self.mines:
                    m_x, m_y = mine.get_position()
                    if abs(m_x - struct_x) < 1 and abs(m_y - struct_y) < 1:
                        pygame.draw.circle(self.screen, (255, 100, 100), 
                                         (struct_x, struct_y), mine.size + 5, 2)
                        break
    
    def run(self):
        """Run the main game loop."""
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds
            
            self.handle_events()
            self.update(dt)
            self.render()
        
        pygame.quit()

