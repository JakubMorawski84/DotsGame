import pygame
import sys

# ustawienia
UI_HEIGHT = 80
GRID_SIZE = 20
CELL_MARGIN = 30
WIDTH = (GRID_SIZE - 1) * CELL_MARGIN + 2 * CELL_MARGIN
HEIGHT = WIDTH + UI_HEIGHT
DOT_RADIUS = 6

# kolory
BG_COLOR = (245, 245, 220)
LINE_COLOR = (210, 210, 210)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
TEXT_BG = (230, 230, 210)
GRAY = (100, 100, 100)

# klasa gry
class KropkiGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Gra w Kropki")
        self.font = pygame.font.SysFont("Arial", 22, bold=True)
        self.turn_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.end_font = pygame.font.SysFont("Arial", 40, bold=True)
        
        self.grid = [[{'owner': 0, 'captured': False} for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.captured_areas = []
        self.turn = 1
        self.score = {1: 0, 2: 0}
        self.running = True
        self.game_over = False

    def get_neighbors(self, r, c, player):
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                if self.grid[nr][nc]['owner'] == player and not self.grid[nr][nc]['captured']:
                    neighbors.append((nr, nc))
        return neighbors

    def find_cycle(self, start_node, player):
        stack = [(start_node, [start_node])]
        while stack:
            (curr_r, curr_c), path = stack.pop()
            for neighbor in self.get_neighbors(curr_r, curr_c, player):
                if len(path) >= 4 and neighbor == start_node:
                    points = self.validate_and_capture(path, player)
                    if points > 0:
                        self.score[player] += points
                        return path
                if neighbor not in path:
                    stack.append((neighbor, path + [neighbor]))
        return None

    def validate_and_capture(self, poly, player):
        enemy = 2 if player == 1 else 1
        captured_count = 0
        captured_points_coords = []
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.is_point_in_poly(r, c, poly):
                    if self.grid[r][c]['owner'] == enemy and not self.grid[r][c]['captured']:
                        captured_count += 1
                        captured_points_coords.append((r, c))
        if captured_count > 0:
            for r, c in captured_points_coords:
                self.grid[r][c]['captured'] = True
            return captured_count
        return 0

    def is_point_in_poly(self, r, c, poly):
        n = len(poly)
        inside = False
        p1r, p1c = poly[0]
        for i in range(n + 1):
            p2r, p2c = poly[i % n]
            if c > min(p1c, p2c) and c <= max(p1c, p2c) and r <= max(p1r, p2r):
                if p1c != p2c:
                    xints = (c - p1c) * (p2r - p1r) / (p2c - p1c) + p1r
                if p1r == p2r or r <= xints:
                    inside = not inside
            p1r, p1c = p2r, p2c
        return inside

    def check_full(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c]['owner'] == 0:
                    return False
        return True

    def draw_game(self):
        self.screen.fill(BG_COLOR)
        for i in range(GRID_SIZE):
            pygame.draw.line(self.screen, LINE_COLOR, 
                             (CELL_MARGIN, UI_HEIGHT + CELL_MARGIN + i*CELL_MARGIN), 
                             (WIDTH-CELL_MARGIN, UI_HEIGHT + CELL_MARGIN + i*CELL_MARGIN))
            pygame.draw.line(self.screen, LINE_COLOR, 
                             (CELL_MARGIN + i*CELL_MARGIN, UI_HEIGHT + CELL_MARGIN), 
                             (CELL_MARGIN + i*CELL_MARGIN, UI_HEIGHT + WIDTH - CELL_MARGIN))

        for area, player in self.captured_areas:
            color = BLUE if player == 1 else RED
            points = [(CELL_MARGIN + c*CELL_MARGIN, UI_HEIGHT + CELL_MARGIN + r*CELL_MARGIN) for r, c in area]
            pygame.draw.lines(self.screen, color, True, points, 3)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                owner = self.grid[r][c]['owner']
                if owner != 0:
                    if self.grid[r][c]['captured']:
                        color = (180, 180, 255) if owner == 1 else (255, 180, 180)
                    else:
                        color = BLUE if owner == 1 else RED
                    pygame.draw.circle(self.screen, color, 
                                       (CELL_MARGIN + c*CELL_MARGIN, UI_HEIGHT + CELL_MARGIN + r*CELL_MARGIN), 
                                       DOT_RADIUS)

    def draw_ui(self):
        pygame.draw.rect(self.screen, TEXT_BG, (0, 0, WIDTH, UI_HEIGHT))
        pygame.draw.line(self.screen, (150, 150, 150), (0, UI_HEIGHT), (WIDTH, UI_HEIGHT), 2)
        
        score_blue = self.font.render(f"Niebieski: {self.score[1]} pkt", True, BLUE)
        score_red = self.font.render(f"Czerwony: {self.score[2]} pkt", True, RED)
        
        if not self.game_over:
            current_color = BLUE if self.turn == 1 else RED
            turn_text = "TURA: " + ("NIEBIESKI" if self.turn == 1 else "CZERWONY")
            turn_surface = self.turn_font.render(turn_text, True, current_color)
            turn_rect = turn_surface.get_rect(center=(WIDTH // 2, UI_HEIGHT // 2 + 15))
            self.screen.blit(turn_surface, turn_rect)
        else:
            if self.score[1] > self.score[2]:
                win_text, win_color = "WYGRAL NIEBIESKI!", BLUE
            elif self.score[2] > self.score[1]:
                win_text, win_color = "WYGRAL CZERWONY!", RED
            else:
                win_text, win_color = "REMIS!", GRAY
            
            end_surf = self.end_font.render(win_text, True, win_color)
            end_rect = end_surf.get_rect(center=(WIDTH // 2, UI_HEIGHT // 2 + 15))
            self.screen.blit(end_surf, end_rect)
        
        self.screen.blit(score_blue, (20, 10))
        self.screen.blit(score_red, (WIDTH - 180, 10))

    def handle_click(self, pos):
        if self.game_over:
            return

        x, y = pos
        col = round((x - CELL_MARGIN) / CELL_MARGIN)
        row = round((y - UI_HEIGHT - CELL_MARGIN) / CELL_MARGIN)

        if 0 <= col < GRID_SIZE and 0 <= row < GRID_SIZE:
            if self.grid[row][col]['owner'] == 0:
                self.grid[row][col]['owner'] = self.turn
                cycle = self.find_cycle((row, col), self.turn)
                if cycle:
                    self.captured_areas.append((cycle, self.turn))
                
                if self.check_full():
                    self.game_over = True
                else:
                    self.turn = 2 if self.turn == 1 else 1

    def run(self):
        while self.running:
            self.draw_game()
            self.draw_ui()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(pygame.mouse.get_pos())
            pygame.display.flip()
        pygame.quit()

if __name__ == "__main__":
    game = KropkiGame()
    game.run()