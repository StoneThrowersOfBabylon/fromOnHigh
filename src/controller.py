import pygame
import threading
from config import FPS
from hex import Hex
from tile import Tile
from character import Character
from city import City
from utils import get_random_passable_hex
from audio import AudioManager
from ai import AIPlayer

class Controller:
    def __init__(self, view):
        self.view = view
        self.running = True

        self.grid = []
        radius = 40
        for q in range(-radius, radius + 1):
            r1 = max(-radius, -q - radius)
            r2 = min(radius, -q + radius)
            for r in range(r1, r2 + 1):
                self.grid.append(Tile(Hex(q, r)))

        self.game_state = "SETUP"
        self.cities = []
        self.num_players = 6
        self.player_colors = [
            (255, 50, 50),
            (50, 50, 255),
            (50, 255, 50),
            (255, 255, 50),
            (255, 50, 255),
            (50, 255, 255)
        ]

        self.selected_city = False
        self.current_player = 0
        self.founder = Character(get_random_passable_hex(self.grid), self.player_colors[self.current_player])
        self.instructions_text = f"Player {self.current_player + 1}'s turn. Click to move, Enter to found City."
        self.camera_x, self.camera_y = 0.0, 0.0
        self.hovered_tile = None
        self.audio = AudioManager()
        
        self.ai = AIPlayer()
        self.ai_thinking = False
        self.ai_decision = None
        
        self.turn_start_time = 0
        self.god_powers = ["light", "lightning", "fire", "dark"]
        self.selected_power = None
        self.toolbar_rects = []

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        hovered_hex = Hex.from_pixel(mouse_pos[0], mouse_pos[1], self.camera_x, self.camera_y)
        
        self.hovered_tile = None
        for t in self.grid:
            if t.position == hovered_hex:
                self.hovered_tile = t
                break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif self.game_state == "SETUP" and self.founder:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.hovered_tile and self.hovered_tile.element not in ["stone", "metal"]:
                        if self.founder.jump_to(hovered_hex):
                            self.audio.play('move')
                        else:
                            self.audio.play('error') # Clicked a valid tile, but it's too far away
                    else:
                        self.audio.play('error') # Clicked impassable tile or off-grid
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if not any(city.current_hex == self.founder.current_hex for city in self.cities):
                            self.cities.append(City(
                                self.founder.current_hex,
                                self.grid,
                                self.player_colors[self.current_player],
                                self.current_player
                            ))
                            self.audio.play('found_city')
                            self.current_player += 1
                            if self.current_player < self.num_players:
                                self.founder = Character(get_random_passable_hex(self.grid), self.player_colors[self.current_player])
                                self.instructions_text = f"Player {self.current_player + 1}'s turn. Click to move, Enter to found City."
                            else:
                                self.founder = None
                                self.game_state = "PLAY"
                                self.current_player = 0
                                self.turn_start_time = pygame.time.get_ticks()
                                self.instructions_text = f"Player {self.current_player + 1}'s turn. Main game phase."
                                self.center_camera_on_current_player_city()
            elif self.game_state == "PLAY":
                if event.type == pygame.MOUSEMOTION:
                    if self.hovered_tile:
                        self.instructions_text = f"Hovering {self.hovered_tile.element} tile at ({hovered_hex.q}, {hovered_hex.r})"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    clicked_toolbar = False
                    for i, rect in enumerate(self.toolbar_rects):
                        if rect.collidepoint(event.pos):
                            if self.selected_power == self.god_powers[i]:
                                self.selected_power = None
                            else:
                                self.selected_power = self.god_powers[i]
                            clicked_toolbar = True
                            break
                    
                    if not clicked_toolbar:
                        if self.selected_power and self.hovered_tile:
                            self.hovered_tile.element = self.selected_power
                            if self.selected_power == "lightning": self.audio.play('error')
                            elif self.selected_power == "fire": self.audio.play('train')
                            else: self.audio.play('found_city')
                        else:
                            clicked_city = self.get_city_at_hex(hovered_hex)
                            if clicked_city:
                                if clicked_city.owner_id == self.current_player:
                                    self.selected_city = True
                                    self.instructions_text = f"Player {self.current_player + 1}: A to train army, S to train settler, F to build farm, I to build institute."
                if event.type == pygame.KEYDOWN:
                    if self.selected_city:
                        if event.key == pygame.K_a:
                            self.audio.play('train')
                            self.instructions_text = f"Player {self.current_player + 1} training unit..."
                            self.selected_city = False
                            self.next_player()
                        if event.key == pygame.K_s:
                            self.audio.play('train')
                            self.instructions_text = f"Player {self.current_player + 1} training settler..."
                            self.selected_city = False
                            self.next_player()
                        if event.key == pygame.K_f:
                            self.audio.play('build')
                            self.instructions_text = f"Player {self.current_player + 1} building farm..."
                            self.selected_city = False
                            self.next_player()
                        if event.key == pygame.K_i:
                            self.audio.play('build')
                            self.instructions_text = f"Player {self.current_player + 1} building institute..."
                            self.selected_city = False
                            self.next_player()


    def _fetch_ai_decision(self):
        print(f"Asking AI for Player {self.current_player + 1}...")
        decision = self.ai.get_decision(self.founder.current_hex, self.grid)
        print(f"AI decided: {decision}")
        self.ai_decision = decision
        self.ai_thinking = False

    def _fetch_play_ai_decision(self):
        city = self.get_current_player_city()
        if city:
            print(f"Asking AI for Player {self.current_player + 1}...")
            decision = self.ai.get_city_decision(city.current_hex.q, city.current_hex.r)
            print(f"AI decided: {decision}")
            self.ai_decision = decision
        self.ai_thinking = False

    def update(self):
        if self.founder:
            self.founder.update()
            self.camera_x = self.founder.pos[0]
            self.camera_y = self.founder.pos[1]
            
        for city in self.cities:
            city.update()
            
        # AI Auto-Play for the main game loop
        if self.game_state == "PLAY":
            if not self.ai_thinking and self.ai_decision is None:
                time_since_turn = pygame.time.get_ticks() - self.turn_start_time
                if time_since_turn < 1500:
                    self.instructions_text = f"Player {self.current_player + 1} is surveying their lands..."
                elif time_since_turn < 3000:
                    self.instructions_text = f"Player {self.current_player + 1} is consulting the village elders..."
                else:
                    self.ai_thinking = True
                    self.instructions_text = f"Player {self.current_player + 1} is deciding what to produce..."
                    threading.Thread(target=self._fetch_play_ai_decision, daemon=True).start()
                
            if self.ai_decision is not None:
                decision = self.ai_decision
                self.ai_decision = None # Reset
                
                action = decision.get("action", "do_nothing")
                if action in ["train_army", "train_settler"]:
                    self.audio.play('train')
                elif action in ["build_farm", "build_institute"]:
                    self.audio.play('build')
                    
                action_str = action.replace('_', ' ')
                self.next_player(f"P{self.current_player + 1} chose {action_str}.")

    def draw(self):
        self.toolbar_rects = self.view.draw_frame(
            self.grid, 
            self.cities, 
            self.founder, 
            self.camera_x, 
            self.camera_y, 
            self.hovered_tile, 
            self.instructions_text,
            self.game_state,
            self.god_powers,
            self.selected_power
        )

    def get_player_cities(self, player_index):
        return [city for city in self.cities if city.owner_id == player_index]

    def get_current_player_cities(self):
        return self.get_player_cities(self.current_player)

    def get_city_at_hex(self, hex_coord):
        return next((city for city in self.cities if city.current_hex == hex_coord), None)

    def get_current_player_city(self):
        cities = self.get_current_player_cities()
        return cities[0] if cities else None

    def center_camera_on_current_player_city(self):
        city = self.get_current_player_city()
        if city:
            self.camera_x, self.camera_y = city.pos

    def next_player(self, last_action_msg=""):
        self.current_player = (self.current_player + 1) % self.num_players
        self.turn_start_time = pygame.time.get_ticks()
        base_msg = f"Player {self.current_player + 1}'s turn."
        if last_action_msg:
            self.instructions_text = f"{last_action_msg} {base_msg}"
        else:
            self.instructions_text = base_msg
        self.center_camera_on_current_player_city()

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(FPS)