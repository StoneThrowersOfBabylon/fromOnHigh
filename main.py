import pygame
import math
import random

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
HEX_SIZE = 40
FPS = 60

# Colors (from docs/elements.md; Lightning/Creature had no color in doc — see comments)
COLOR_BG = (30, 30, 30)
COLOR_PLAYER = (50, 150, 255)
COLOR_SWORD = (200, 200, 200)
COLOR_SWORD_HILT = (139, 69, 19)

class Hex:
    def __init__(self, q, r):
        self.q = q
        self.r = r

    def __eq__(self, other):
        return self.q == other.q and self.r == other.r

    def __hash__(self):
        return hash((self.q, self.r))

    def to_pixel(self):
        x = HEX_SIZE * 3/2 * self.q
        y = HEX_SIZE * math.sqrt(3) * (self.r + self.q/2)
        return (x, y)

    @staticmethod
    def from_pixel(x, y, camera_x=0, camera_y=0):
        x_adj = x - SCREEN_WIDTH // 2 + camera_x
        y_adj = y - SCREEN_HEIGHT // 2 + camera_y
        q = (2/3 * x_adj) / HEX_SIZE
        r = (-1/3 * x_adj + math.sqrt(3)/3 * y_adj) / HEX_SIZE
        return Hex.round(q, r)

    @staticmethod
    def round(q, r):
        s = -q - r
        rq = round(q)
        rr = round(r)
        rs = round(s)

        dq = abs(rq - q)
        dr = abs(rr - r)
        ds = abs(rs - s)

        if dq > dr and dq > ds:
            rq = -rr - rs
        elif dr > ds:
            rr = -rq - rs
        
        return Hex(rq, rr)

ELEMENT_COLORS = {
    "light": (255, 255, 255),
    "lightning": (255, 245, 120),  # doc blank — electric yellow
    "fire": (220, 45, 45),
    "wind": (255, 218, 228),  # pale pink
    "creature": (175, 130, 95),  # doc "t" — tan / organic
    "water": (45, 95, 195),
    "plant": (45, 145, 55),
    "earth": (75, 48, 28),
    "stone": (68, 68, 72),
    "metal": (178, 182, 188),
    "ice": (175, 225, 255),
    "dark": (18, 18, 18),
}

ELEMENTS = tuple(ELEMENT_COLORS.keys())

def element_hover_color(element):
    r, g, b = ELEMENT_COLORS[element]
    return (min(255, r + 45), min(255, g + 45), min(255, b + 45))

class Tile:
    def __init__(self, position):
        self.position = position
        self.element = random.choice(ELEMENTS)
        self.food = random.randint(0, 5)
        self.gold = random.randint(0, 3)
        self.has_city = False
        self.owner = None
        self.deco_seed = random.randint(0, 2**31 - 1)

    def __str__(self):
        return (
            f"Tile(hex=({self.position.q}, {self.position.r}), "
            f"element={self.element!r}, food={self.food}, gold={self.gold}, "
            f"has_city={self.has_city}, owner={self.owner!r})"
        )

def get_hex_corners(center):
    corners = []
    for i in range(6):
        angle_deg = 60 * i
        angle_rad = math.pi / 180 * angle_deg
        corners.append((center[0] + HEX_SIZE * math.cos(angle_rad),
                        center[1] + HEX_SIZE * math.sin(angle_rad)))
    return corners

def draw_tile_hex(surface, tile, center, corners, base_color):
    """Fill hex, draw element-specific interior style, then black outline."""
    cx, cy = center
    cx, cy = float(cx), float(cy)

    elem = tile.element
    outline_w = 2

    def outline():
        pygame.draw.polygon(surface, (0, 0, 0), corners, outline_w)

    # Fill the tile with its base color
    pygame.draw.polygon(surface, base_color, corners)

    # Draw orange circle for fire and lightning
    if elem in ["fire", "lightning"]:
        pygame.draw.circle(surface, (255, 140, 0), (int(cx), int(cy)), int(HEX_SIZE * 0.2))

    outline()

class Character:
    def __init__(self, start_hex, color=(255, 255, 255)):
        self.current_hex = start_hex
        self.target_hex = start_hex
        self.pos = list(start_hex.to_pixel())
        self.start_pos = list(start_hex.to_pixel())
        self.progress = 1.0 # 0.0 to 1.0 during jump
        self.jump_duration = 15 # frames
        self.jump_height = 40
        self.color = color

    def jump_to(self, target_hex):
        if self.current_hex != target_hex and self.progress >= 1.0 and self.is_adjacent(target_hex):
            self.start_pos = list(self.pos)
            self.target_hex = target_hex
            self.progress = 0.0


    def is_adjacent(self, target_hex):
        dq = self.current_hex.q - target_hex.q
        dr = self.current_hex.r - target_hex.r
        return (dq, dr) in [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]

    def update(self):
        if self.progress < 1.0:
            self.progress += 1.0 / self.jump_duration
            if self.progress >= 1.0:
                self.progress = 1.0
                self.current_hex = self.target_hex
            
            target_pos = self.target_hex.to_pixel()
            # Linear horizontal/vertical interpolation
            self.pos[0] = self.start_pos[0] + (target_pos[0] - self.start_pos[0]) * self.progress
            self.pos[1] = self.start_pos[1] + (target_pos[1] - self.start_pos[1]) * self.progress

    def draw(self, surface, camera_x, camera_y):
        # Calculate jump offset (parabola: h * 4 * x * (1-x))
        jump_offset = self.jump_height * 4 * self.progress * (1 - self.progress)
        draw_x = int(self.pos[0] - camera_x + SCREEN_WIDTH // 2)
        draw_y = int(self.pos[1] - jump_offset - camera_y + SCREEN_HEIGHT // 2)

        pygame.draw.circle(surface, self.color, (draw_x, draw_y), int(HEX_SIZE * 0.7), 2)

        # Draw sword icon (centered on the character)
        # Blade (top part)
        pygame.draw.line(surface, COLOR_SWORD, (draw_x, draw_y - 15), (draw_x, draw_y + 5), 4)
        # Hilt/Guard
        pygame.draw.line(surface, COLOR_SWORD_HILT, (draw_x - 8, draw_y + 5), (draw_x + 8, draw_y + 5), 3)
        # Handle
        pygame.draw.line(surface, COLOR_SWORD_HILT, (draw_x, draw_y + 5), (draw_x, draw_y + 12), 3)

class City:
    def __init__(self, start_hex, grid, color=(255, 255, 255)):
        self.current_hex = start_hex
        self.pos = list(start_hex.to_pixel())
        self.color = color
        
        # Turn the tile it is on into a white color (light element)
        for tile in grid:
            if tile.position == self.current_hex:
                tile.element = "light"
                tile.has_city = True
                tile.owner = color
                break

    def update(self):
        pass

    def draw(self, surface, camera_x, camera_y):
        draw_x = int(self.pos[0] - camera_x + SCREEN_WIDTH // 2)
        draw_y = int(self.pos[1] - camera_y + SCREEN_HEIGHT // 2)

        # Border of radius 1 hex
        border_hexes = [
            self.current_hex,
            Hex(self.current_hex.q + 1, self.current_hex.r),
            Hex(self.current_hex.q + 1, self.current_hex.r - 1),
            Hex(self.current_hex.q, self.current_hex.r - 1),
            Hex(self.current_hex.q - 1, self.current_hex.r),
            Hex(self.current_hex.q - 1, self.current_hex.r + 1),
            Hex(self.current_hex.q, self.current_hex.r + 1),
        ]
        
        edges = {}
        for bh in border_hexes:
            world_center = bh.to_pixel()
            screen_center = (world_center[0] - camera_x + SCREEN_WIDTH // 2, 
                             world_center[1] - camera_y + SCREEN_HEIGHT // 2)
            corners = get_hex_corners(screen_center)
            for i in range(6):
                p1 = corners[i]
                p2 = corners[(i + 1) % 6]
                rp1 = (int(round(p1[0])), int(round(p1[1])))
                rp2 = (int(round(p2[0])), int(round(p2[1])))
                edge = tuple(sorted((rp1, rp2)))
                edges[edge] = edges.get(edge, 0) + 1
        
        for edge, count in edges.items():
            if count == 1:
                pygame.draw.line(surface, self.color, edge[0], edge[1], 4)

        # Draw house icon
        pygame.draw.rect(surface, (200, 200, 200), (draw_x - 12, draw_y - 2, 24, 16))
        pygame.draw.rect(surface, (139, 69, 19), (draw_x - 4, draw_y + 6, 8, 8))
        pygame.draw.polygon(surface, (150, 50, 50), [
            (draw_x - 16, draw_y - 2), 
            (draw_x + 16, draw_y - 2), 
            (draw_x, draw_y - 18)
        ])

def get_random_passable_hex(grid):
    valid_tiles = [t for t in grid if t.element not in ["stone", "metal"] and not t.has_city]
    if not valid_tiles:
        return Hex(0, 0)
    return random.choice(valid_tiles).position

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hex Jump Prototype")
    clock = pygame.time.Clock()

    # Create a grid of tiles (radius-based)
    grid = []
    radius = 40  # 10x larger radius
    for q in range(-radius, radius + 1):
        r1 = max(-radius, -q - radius)
        r2 = min(radius, -q + radius)
        for r in range(r1, r2 + 1):
            grid.append(Tile(Hex(q, r)))

    game_state = "SETUP"
    cities = []
    num_players = 6
    player_colors = [
        (255, 50, 50),   # Red
        (50, 50, 255),   # Blue
        (50, 255, 50),   # Green
        (255, 255, 50),  # Yellow
        (255, 50, 255),  # Magenta
        (50, 255, 255)   # Cyan
    ]
    current_player = 0
    founder = Character(get_random_passable_hex(grid), player_colors[current_player])

    font = pygame.font.SysFont(None, 24)
    instructions = font.render(f"Player {current_player + 1}'s turn. Click to move, Enter to found City.", True, (200, 200, 200))
    
    camera_x, camera_y = 0.0, 0.0

    running = True
    while running:
        if founder:
            camera_x = founder.pos[0]
            camera_y = founder.pos[1]

        mouse_pos = pygame.mouse.get_pos()
        hovered_hex = Hex.from_pixel(mouse_pos[0], mouse_pos[1], camera_x, camera_y)
        
        hovered_tile = None
        for t in grid:
            if t.position == hovered_hex:
                hovered_tile = t
                break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game_state == "SETUP" and founder:
                    # Check that the target tile exists and isn't impassable
                    if hovered_tile and hovered_tile.element not in ["stone", "metal"]:
                        founder.jump_to(hovered_hex)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if game_state == "SETUP" and founder:
                        # Prevent founding a city on top of another city
                        if not any(city.current_hex == founder.current_hex for city in cities):
                            cities.append(City(founder.current_hex, grid, player_colors[current_player]))
                            current_player += 1
                            if current_player < num_players:
                                founder = Character(get_random_passable_hex(grid), player_colors[current_player])
                                instructions = font.render(f"Player {current_player + 1}'s turn. Click to move, Enter to found City.", True, (200, 200, 200))
                            else:
                                founder = None
                                game_state = "PLAY"
                                instructions = font.render("All cities founded! Main game phase.", True, (200, 200, 200))

        # Update
        if founder:
            founder.update()
        for city in cities:
            city.update()

        # Draw
        screen.fill(COLOR_BG)
        
        # Draw grid
        for tile in grid:
            world_center = tile.position.to_pixel()
            
            # Viewport culling: skip rendering if the tile is outside the screen bounds
            screen_x = world_center[0] - camera_x + SCREEN_WIDTH // 2
            screen_y = world_center[1] - camera_y + SCREEN_HEIGHT // 2
            if (screen_x + HEX_SIZE < 0 or screen_x - HEX_SIZE > SCREEN_WIDTH or
                screen_y + HEX_SIZE < 0 or screen_y - HEX_SIZE > SCREEN_HEIGHT):
                continue

            corners = get_hex_corners((screen_x, screen_y))
            if tile == hovered_tile:
                color = element_hover_color(tile.element)
            else:
                color = ELEMENT_COLORS[tile.element]
            draw_tile_hex(screen, tile, (screen_x, screen_y), corners, color)

        # Draw entities
        for city in cities:
            city.draw(screen, camera_x, camera_y)
        if founder:
            founder.draw(screen, camera_x, camera_y)
        
        # Draw instructions
        screen.blit(instructions, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
