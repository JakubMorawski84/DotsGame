import pygame
import random
import sys

# --- Ustawienia wymiarów ---
WINDOW_GRID_SIZE = 20  
LOGICAL_GRID_SIZE = 5
UI_HEIGHT = 80
CELL_MARGIN = 30

WIDTH = (WINDOW_GRID_SIZE - 1) * CELL_MARGIN + 2 * CELL_MARGIN
HEIGHT = WIDTH + UI_HEIGHT
DOT_RADIUS = 6

OFFSET = ((WINDOW_GRID_SIZE - LOGICAL_GRID_SIZE) * CELL_MARGIN) // 2

# Kolory
BG_COLOR = (245, 245, 220)
LINE_COLOR = (210, 210, 210)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
TEXT_BG = (230, 230, 210)
GRAY = (100, 100, 100)
LAST_MOVE_COLOR = (255, 215, 0) 

class Player:
    def __init__(self, player_id, color, name):
        self.player_id = player_id
        self.color = color
        self.name = name
        self.score = 0
        self.is_ai = False

class AIPlayer(Player):
    def __init__(self, player_id, color, name, depth=2):
        super().__init__(player_id, color, name)
        self.is_ai = True
        self.depth = depth

    def evaluate_board(self, game):
        """Ocena stanu planszy: im wyższa wartość, tym lepiej dla AI."""
        enemy_id = 3 - self.player_id
        score = (game.players[self.player_id].score * 100) - (game.players[enemy_id].score * 110) #gameplay

        #szukanie ruchow przy wlasnych obwodach jest bezpieczniejsze
        for r in range(LOGICAL_GRID_SIZE):
            for c in range(LOGICAL_GRID_SIZE):
                if game.grid[r][c]['owner'] == self.player_id:
                    neighbors = game.get_neighbors(r, c, self.player_id)
                    score += len(neighbors) * 10 
        return score

    def get_move(self, game):
        best_score = float('-inf')
        best_move = None
        
        # sprawdz dostepne ruchy
        possible_moves = []
        for r in range(LOGICAL_GRID_SIZE):
            for c in range(LOGICAL_GRID_SIZE):
                if game.grid[r][c]['owner'] == 0 and not game.grid[r][c]['captured']:
                    possible_moves.append((r, c))
        
        #tylko w okolicy kropek jak za duzo mozliwych ruchow
        if len(possible_moves) > (LOGICAL_GRID_SIZE**2) * 0.8:
            random.shuffle(possible_moves)
            return possible_moves[0]

        for r, c in possible_moves:
            game.grid[r][c]['owner'] = self.player_id
            score = self.minimax(game, self.depth - 1, float('-inf'), float('inf'), False)
            game.grid[r][c]['owner'] = 0
            
            if score > best_score:
                best_score = score
                best_move = (r, c)
        
        return best_move

    def minimax(self, game, depth, alpha, beta, maximizing_player):
        if depth == 0 or game.check_full():
            return self.evaluate_board(game)

        enemy_id = 3 - self.player_id
        
        if maximizing_player:
            max_eval = float('-inf')
            for r in range(LOGICAL_GRID_SIZE):
                for c in range(LOGICAL_GRID_SIZE):
                    if game.grid[r][c]['owner'] == 0 and not game.grid[r][c]['captured']:
                        game.grid[r][c]['owner'] = self.player_id
                        eval = self.minimax(game, depth - 1, alpha, beta, False)
                        game.grid[r][c]['owner'] = 0
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)
                        if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            for r in range(LOGICAL_GRID_SIZE):
                for c in range(LOGICAL_GRID_SIZE):
                    if game.grid[r][c]['owner'] == 0 and not game.grid[r][c]['captured']:
                        game.grid[r][c]['owner'] = enemy_id
                        eval = self.minimax(game, depth - 1, alpha, beta, True)
                        game.grid[r][c]['owner'] = 0
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha: break
            return min_eval

class KropkiGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Kropki z Implementacja AI")
        self.font = pygame.font.SysFont("Arial", 22, bold=True)
        self.turn_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.end_font = pygame.font.SysFont("Arial", 40, bold=True)
        
        self.grid = [[{'owner': 0, 'captured': False} for _ in range(LOGICAL_GRID_SIZE)] for _ in range(LOGICAL_GRID_SIZE)]
        self.captured_areas = [] 
        self.last_move = None 
        
        self.player1 = Player(1, BLUE, "Niebieski")
        self.player2 = AIPlayer(2, RED, "Czerwony") #human or clanker
        
        self.players = {1: self.player1, 2: self.player2}
        self.turn = 1
        self.running = True
        self.game_over = False

    def get_neighbors(self, r, c, player_id):
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < LOGICAL_GRID_SIZE and 0 <= nc < LOGICAL_GRID_SIZE:
                if self.grid[nr][nc]['owner'] == player_id and not self.grid[nr][nc]['captured']:
                    neighbors.append((nr, nc))
        return neighbors

    def find_cycle(self, start_node, player_id):
        stack = [(start_node, [start_node])]
        while stack:
            (curr_r, curr_c), path = stack.pop()
            for neighbor in self.get_neighbors(curr_r, curr_c, player_id):
                if len(path) >= 4 and neighbor == start_node:
                    if self.is_cycle_already_captured(path):
                        continue
                    points = self.validate_and_capture(path, player_id)
                    if points > 0:
                        self.players[player_id].score += points
                        return path
                if neighbor not in path:
                    stack.append((neighbor, path + [neighbor]))
        return None

    def is_cycle_already_captured(self, path):
        path_set = set(path)
        for existing_area, _ in self.captured_areas:
            if set(existing_area) == path_set:
                return True
        return False

    def validate_and_capture(self, poly, player_id):
        enemy_id = 3 - player_id
        captured_count = 0
        poly_set = set(poly)
        
        has_enemy_dot = False
        for r in range(LOGICAL_GRID_SIZE):
            for c in range(LOGICAL_GRID_SIZE):
                if (r, c) not in poly_set and self.is_point_in_poly(r, c, poly):
                    if self.grid[r][c]['owner'] == enemy_id and not self.grid[r][c]['captured']:
                        has_enemy_dot = True
                        break
            if has_enemy_dot: break
            
        if not has_enemy_dot:
            return 0

        for r in range(LOGICAL_GRID_SIZE):
            for c in range(LOGICAL_GRID_SIZE):
                if (r, c) not in poly_set and self.is_point_in_poly(r, c, poly):
                    if not self.grid[r][c]['captured']:
                        if self.grid[r][c]['owner'] == enemy_id:
                            captured_count += 1
                        self.grid[r][c]['captured'] = True
        return captured_count

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

    def check_for_cycles_around(self, r, c):
        """Optymalizacja: szukaj cykli tylko w otoczeniu punktu (r, c)"""
        owner_of_last_move = self.grid[r][c]['owner']
        cycle = self.find_cycle((r, c), owner_of_last_move)
        if cycle:
            self.captured_areas.append((cycle, owner_of_last_move))
        
        enemy_id = 3 - owner_of_last_move
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = r + dr, c + dc
                if 0 <= nr < LOGICAL_GRID_SIZE and 0 <= nc < LOGICAL_GRID_SIZE:
                    if self.grid[nr][nc]['owner'] == enemy_id and not self.grid[nr][nc]['captured']:
                        cycle = self.find_cycle((nr, nc), enemy_id)
                        if cycle:
                            self.captured_areas.append((cycle, enemy_id))

    def check_full(self):
        for r in range(LOGICAL_GRID_SIZE):
            for c in range(LOGICAL_GRID_SIZE):
                if self.grid[r][c]['owner'] == 0 and not self.grid[r][c]['captured']:
                    return False
        return True

    def draw_game(self):
        self.screen.fill(BG_COLOR)
        for i in range(LOGICAL_GRID_SIZE):
            pygame.draw.line(self.screen, LINE_COLOR, 
                             (CELL_MARGIN + OFFSET, UI_HEIGHT + CELL_MARGIN + i*CELL_MARGIN + OFFSET), 
                             (CELL_MARGIN + (LOGICAL_GRID_SIZE-1)*CELL_MARGIN + OFFSET, UI_HEIGHT + CELL_MARGIN + i*CELL_MARGIN + OFFSET))
            pygame.draw.line(self.screen, LINE_COLOR, 
                             (CELL_MARGIN + i*CELL_MARGIN + OFFSET, UI_HEIGHT + CELL_MARGIN + OFFSET), 
                             (CELL_MARGIN + i*CELL_MARGIN + OFFSET, UI_HEIGHT + CELL_MARGIN + (LOGICAL_GRID_SIZE-1)*CELL_MARGIN + OFFSET))

        all_fence_points = set()
        for area, _ in self.captured_areas:
            for p in area: all_fence_points.add(p)

        for area, player_id in self.captured_areas:
            color = self.players[player_id].color
            points = [(CELL_MARGIN + c*CELL_MARGIN + OFFSET, UI_HEIGHT + CELL_MARGIN + r*CELL_MARGIN + OFFSET) for r, c in area]
            pygame.draw.lines(self.screen, color, True, points, 3)

        for r in range(LOGICAL_GRID_SIZE):
            for c in range(LOGICAL_GRID_SIZE):
                owner_id = self.grid[r][c]['owner']
                pos = (CELL_MARGIN + c*CELL_MARGIN + OFFSET, UI_HEIGHT + CELL_MARGIN + r*CELL_MARGIN + OFFSET)
                if owner_id != 0:
                    if self.grid[r][c]['captured'] and (r, c) not in all_fence_points:
                        orig_color = self.players[owner_id].color
                        color = tuple(min(255, x + 160) for x in orig_color)
                    else:
                        color = self.players[owner_id].color
                    pygame.draw.circle(self.screen, color, pos, DOT_RADIUS)
                    if self.last_move == (r, c):
                        pygame.draw.circle(self.screen, LAST_MOVE_COLOR, pos, DOT_RADIUS + 2, 2)
                elif self.grid[r][c]['captured']:
                    pygame.draw.circle(self.screen, (200, 200, 180), pos, 2)

    def draw_ui(self):
        pygame.draw.rect(self.screen, TEXT_BG, (0, 0, WIDTH, UI_HEIGHT))
        pygame.draw.line(self.screen, (150, 150, 150), (0, UI_HEIGHT), (WIDTH, UI_HEIGHT), 2)
        score_p1 = self.font.render(f"{self.player1.name}: {self.player1.score} pkt", True, self.player1.color)
        score_p2 = self.font.render(f"{self.player2.name}: {self.player2.score} pkt", True, self.player2.color)
        self.screen.blit(score_p1, (20, 10))
        self.screen.blit(score_p2, (WIDTH - 220, 10))
        
        if not self.game_over:
            curr = self.players[self.turn]
            t_surf = self.turn_font.render(f"TURA: {curr.name.upper()}", True, curr.color)
            self.screen.blit(t_surf, t_surf.get_rect(center=(WIDTH // 2, UI_HEIGHT // 2 + 15)))
        else:
            msg = "REMIS!"
            col = GRAY
            if self.player1.score > self.player2.score: msg, col = f"WYGRAŁ {self.player1.name}!", self.player1.color
            elif self.player2.score > self.player1.score: msg, col = f"WYGRAŁ {self.player2.name}!", self.player2.color
            e_surf = self.end_font.render(msg, True, col)
            self.screen.blit(e_surf, e_surf.get_rect(center=(WIDTH // 2, UI_HEIGHT // 2 + 15)))

    def make_move(self, row, col):
        if self.grid[row][col]['owner'] == 0 and not self.grid[row][col]['captured']:
            self.grid[row][col]['owner'] = self.turn
            self.last_move = (row, col)
            
            self.check_for_cycles_around(row, col)
            
            if self.check_full(): self.game_over = True
            else: self.turn = 3 - self.turn
            return True
        return False

    def handle_click(self, pos):
        if self.game_over: return
        x, y = pos
        col = round((x - CELL_MARGIN - OFFSET) / CELL_MARGIN)
        row = round((y - UI_HEIGHT - CELL_MARGIN - OFFSET) / CELL_MARGIN)
        if 0 <= col < LOGICAL_GRID_SIZE and 0 <= row < LOGICAL_GRID_SIZE:
            self.make_move(row, col)

    def run(self):
        while self.running:
            self.draw_game()
            self.draw_ui()
            #turn off
            if not self.game_over and self.players[self.turn].is_ai:
                pygame.display.flip()
                move = self.players[self.turn].get_move(self)
                if move:
                    self.make_move(move[0], move[1])
            #till here
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.running = False
                if event.type == pygame.MOUSEBUTTONDOWN: self.handle_click(pygame.mouse.get_pos())
            pygame.display.flip()
        pygame.quit()

if __name__ == "__main__":
    game = KropkiGame()
    game.run()
