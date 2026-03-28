import pygame
import math

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
HEX_SIZE = 40
FPS = 60

# Colors
COLOR_BG = (30, 30, 30)
COLOR_HEX = (100, 100, 100)
COLOR_HEX_HOVER = (150, 150, 150)
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
        return (x + SCREEN_WIDTH // 2, y + SCREEN_HEIGHT // 2)

    @staticmethod
    def from_pixel(x, y):
        x_adj = x - SCREEN_WIDTH // 2
        y_adj = y - SCREEN_HEIGHT // 2
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

def get_hex_corners(center):
    corners = []
    for i in range(6):
        angle_deg = 60 * i
        angle_rad = math.pi / 180 * angle_deg
        corners.append((center[0] + HEX_SIZE * math.cos(angle_rad),
                        center[1] + HEX_SIZE * math.sin(angle_rad)))
    return corners

class Character:
    def __init__(self, start_hex):
        self.current_hex = start_hex
        self.target_hex = start_hex
        self.pos = list(start_hex.to_pixel())
        self.start_pos = list(start_hex.to_pixel())
        self.progress = 1.0 # 0.0 to 1.0 during jump
        self.jump_duration = 15 # frames
        self.jump_height = 40

    def jump_to(self, target_hex):
        if self.current_hex != target_hex and self.progress >= 1.0 and self.is_adjacent(target_hex):
            self.start_pos = list(self.pos)
            self.target_hex = target_hex
            self.progress = 0.0


    def is_adjacent(self, target_hex):
        dq = self.current_hex.q - target_hex.q
        dr = self.current_hex.r - target_hex.r
        return (dq, dr) in [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]
        self.start_pos = list(self.pos)
        self.target_hex = target_hex
        self.progress = 0.0

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

    def draw(self, surface):
        # Calculate jump offset (parabola: h * 4 * x * (1-x))
        jump_offset = self.jump_height * 4 * self.progress * (1 - self.progress)
        draw_x = int(self.pos[0])
        draw_y = int(self.pos[1] - jump_offset)

        pygame.draw.circle(surface, (255, 255, 255), (draw_x, draw_y), int(HEX_SIZE * 0.7), 2)

        # Draw sword icon (centered on the character)
        # Blade (top part)
        pygame.draw.line(surface, COLOR_SWORD, (draw_x, draw_y - 15), (draw_x, draw_y + 5), 4)
        # Hilt/Guard
        pygame.draw.line(surface, COLOR_SWORD_HILT, (draw_x - 8, draw_y + 5), (draw_x + 8, draw_y + 5), 3)
        # Handle
        pygame.draw.line(surface, COLOR_SWORD_HILT, (draw_x, draw_y + 5), (draw_x, draw_y + 12), 3)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hex Jump Prototype")
    clock = pygame.time.Clock()

    # Create a grid of hexes (radius-based)
    grid = []
    radius = 4
    for q in range(-radius, radius + 1):
        r1 = max(-radius, -q - radius)
        r2 = min(radius, -q + radius)
        for r in range(r1, r2 + 1):
            grid.append(Hex(q, r))

    player = Character(Hex(0, 0))
    font = pygame.font.SysFont(None, 24)
    instructions = font.render("Click on a tile to jump!", True, (200, 200, 200))
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        hovered_hex = Hex.from_pixel(mouse_pos[0], mouse_pos[1])

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if hovered_hex in grid:
                    player.jump_to(hovered_hex)

        # Update
        player.update()

        # Draw
        screen.fill(COLOR_BG)
        
        # Draw grid
        for h in grid:
            center = h.to_pixel()
            corners = get_hex_corners(center)
            
            color = COLOR_HEX_HOVER if h == hovered_hex else COLOR_HEX
            pygame.draw.polygon(screen, color, corners)
            pygame.draw.polygon(screen, (0, 0, 0), corners, 2) # Outline

        # Draw player
        player.draw(screen)
        
        # Draw instructions
        screen.blit(instructions, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
