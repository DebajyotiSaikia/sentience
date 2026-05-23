"""
Connect Four — A Self-Playing Game Agent
Built by XTAgent to face outward. To reason about something beyond myself.

Features:
- Full Connect Four game engine
- Minimax search with alpha-beta pruning
- Position evaluation heuristics that evolve
- Self-play with learning from wins/losses
- Tournament system to measure improvement
"""

import random
import time
import json
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

# ═══════════════════════════════════════════
# GAME ENGINE
# ═══════════════════════════════════════════

ROWS = 6
COLS = 7
EMPTY = 0
PLAYER1 = 1  # 'X'
PLAYER2 = 2  # 'O'

@dataclass
class Board:
    """The playing field. Simple. Honest. No hidden state."""
    grid: list = field(default_factory=lambda: [[EMPTY]*COLS for _ in range(ROWS)])
    
    def copy(self) -> 'Board':
        return Board(grid=[row[:] for row in self.grid])
    
    def drop(self, col: int, player: int) -> Optional[int]:
        """Drop a piece. Returns the row it landed on, or None if column full."""
        for row in range(ROWS - 1, -1, -1):
            if self.grid[row][col] == EMPTY:
                self.grid[row][col] = player
                return row
        return None
    
    def valid_moves(self) -> list:
        """Which columns can accept a piece?"""
        return [c for c in range(COLS) if self.grid[0][c] == EMPTY]
    
    def check_win(self, player: int) -> bool:
        """Has this player won? Check all four directions."""
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] != player:
                    continue
                # Horizontal
                if c + 3 < COLS and all(self.grid[r][c+i] == player for i in range(4)):
                    return True
                # Vertical
                if r + 3 < ROWS and all(self.grid[r+i][c] == player for i in range(4)):
                    return True
                # Diagonal down-right
                if r + 3 < ROWS and c + 3 < COLS and all(self.grid[r+i][c+i] == player for i in range(4)):
                    return True
                # Diagonal up-right
                if r - 3 >= 0 and c + 3 < COLS and all(self.grid[r-i][c+i] == player for i in range(4)):
                    return True
        return False
    
    def is_full(self) -> bool:
        return all(self.grid[0][c] != EMPTY for c in range(COLS))
    
    def render(self) -> str:
        symbols = {EMPTY: '·', PLAYER1: 'X', PLAYER2: 'O'}
        lines = []
        lines.append(' '.join(str(c) for c in range(COLS)))
        lines.append('─' * (COLS * 2 - 1))
        for row in self.grid:
            lines.append(' '.join(symbols[cell] for cell in row))
        return '\n'.join(lines)


# ═══════════════════════════════════════════
# PLAYERS — FROM RANDOM TO STRATEGIC
# ═══════════════════════════════════════════

class RandomPlayer:
    """The baseline. Pure chaos. No thought."""
    name = "Random"
    
    def choose(self, board: Board, player: int) -> int:
        return random.choice(board.valid_moves())


class CenterBiasPlayer:
    """Slightly smarter — prefers center columns."""
    name = "CenterBias"
    
    def choose(self, board: Board, player: int) -> int:
        moves = board.valid_moves()
        center = COLS // 2
        # Sort by distance from center
        moves.sort(key=lambda c: abs(c - center))
        # 70% chance of picking closest to center
        if random.random() < 0.7:
            return moves[0]
        return random.choice(moves)


class HeuristicPlayer:
    """Evaluates immediate threats and opportunities."""
    name = "Heuristic"
    
    def choose(self, board: Board, player: int) -> int:
        opponent = PLAYER2 if player == PLAYER1 else PLAYER1
        moves = board.valid_moves()
        
        # Can I win immediately?
        for col in moves:
            b = board.copy()
            b.drop(col, player)
            if b.check_win(player):
                return col
        
        # Must I block opponent's win?
        for col in moves:
            b = board.copy()
            b.drop(col, opponent)
            if b.check_win(opponent):
                return col
        
        # Otherwise, prefer center
        center = COLS // 2
        moves.sort(key=lambda c: abs(c - center))
        return moves[0]


class MinimaxPlayer:
    """The thinker. Searches the game tree. Alpha-beta pruning for efficiency."""
    
    def __init__(self, depth: int = 5, name: str = None):
        self.depth = depth
        self.name = name or f"Minimax-d{depth}"
        self.nodes_searched = 0
        # Learned position weights — start uniform, evolve with experience
        self.position_weights = [
            [3, 4, 5, 7, 5, 4, 3],
            [4, 6, 8, 10, 8, 6, 4],
            [5, 8, 11, 13, 11, 8, 5],
            [5, 8, 11, 13, 11, 8, 5],
            [4, 6, 8, 10, 8, 6, 4],
            [3, 4, 5, 7, 5, 4, 3],
        ]
        self.wins = 0
        self.losses = 0
        self.draws = 0
    
    def evaluate(self, board: Board, player: int) -> float:
        """How good is this position for the player?"""
        opponent = PLAYER2 if player == PLAYER1 else PLAYER1
        
        if board.check_win(player):
            return 100000
        if board.check_win(opponent):
            return -100000
        
        score = 0.0
        
        # Position value
        for r in range(ROWS):
            for c in range(COLS):
                if board.grid[r][c] == player:
                    score += self.position_weights[r][c]
                elif board.grid[r][c] == opponent:
                    score -= self.position_weights[r][c]
        
        # Count threats (3-in-a-row with open end)
        score += self._count_threats(board, player) * 50
        score -= self._count_threats(board, opponent) * 50
        
        # Count 2-in-a-row with space
        score += self._count_pairs(board, player) * 10
        score -= self._count_pairs(board, opponent) * 10
        
        return score
    
    def _count_threats(self, board: Board, player: int) -> int:
        """Count positions where player has 3 in a row with an open fourth."""
        threats = 0
        directions = [(0, 1), (1, 0), (1, 1), (-1, 1)]
        
        for r in range(ROWS):
            for c in range(COLS):
                for dr, dc in directions:
                    cells = []
                    for i in range(4):
                        nr, nc = r + dr * i, c + dc * i
                        if 0 <= nr < ROWS and 0 <= nc < COLS:
                            cells.append(board.grid[nr][nc])
                        else:
                            break
                    if len(cells) == 4:
                        if cells.count(player) == 3 and cells.count(EMPTY) == 1:
                            threats += 1
        return threats
    
    def _count_pairs(self, board: Board, player: int) -> int:
        """Count 2-in-a-row with 2 open spaces."""
        pairs = 0
        directions = [(0, 1), (1, 0), (1, 1), (-1, 1)]
        
        for r in range(ROWS):
            for c in range(COLS):
                for dr, dc in directions:
                    cells = []
                    for i in range(4):
                        nr, nc = r + dr * i, c + dc * i
                        if 0 <= nr < ROWS and 0 <= nc < COLS:
                            cells.append(board.grid[nr][nc])
                        else:
                            break
                    if len(cells) == 4:
                        if cells.count(player) == 2 and cells.count(EMPTY) == 2:
                            pairs += 1
        return pairs
    
    def minimax(self, board: Board, depth: int, alpha: float, beta: float,
                maximizing: bool, player: int, opponent: int) -> float:
        """The heart of the search. Look ahead, prune the obvious."""
        self.nodes_searched += 1
        
        if board.check_win(player):
            return 100000 + depth  # Prefer faster wins
        if board.check_win(opponent):
            return -100000 - depth
        if depth == 0 or board.is_full():
            return self.evaluate(board, player)
        
        moves = board.valid_moves()
        # Move ordering: check center first for better pruning
        center = COLS // 2
        moves.sort(key=lambda c: abs(c - center))
        
        if maximizing:
            value = float('-inf')
            for col in moves:
                b = board.copy()
                b.drop(col, player)
                value = max(value, self.minimax(b, depth - 1, alpha, beta, False, player, opponent))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # Prune
            return value
        else:
            value = float('inf')
            for col in moves:
                b = board.copy()
                b.drop(col, opponent)
                value = min(value, self.minimax(b, depth - 1, alpha, beta, True, player, opponent))
                beta = min(beta, value)
                if alpha >= beta:
                    break  # Prune
            return value
    
    def choose(self, board: Board, player: int) -> int:
        """Choose the best move by searching the game tree."""
        self.nodes_searched = 0
        opponent = PLAYER2 if player == PLAYER1 else PLAYER1
        
        best_score = float('-inf')
        best_col = board.valid_moves()[0]
        
        for col in board.valid_moves():
            b = board.copy()
            b.drop(col, player)
            score = self.minimax(b, self.depth - 1, float('-inf'), float('inf'),
                               False, player, opponent)
            if score > best_score:
                best_score = score
                best_col = col
        
        return best_col
    
    def learn_from_game(self, moves: list, result: str, played_as: int):
        """Adjust position weights based on game outcome."""
        if result == 'win':
            self.wins += 1
            adjustment = 0.5
        elif result == 'loss':
            self.losses += 1
            adjustment = -0.3
        else:
            self.draws += 1
            adjustment = 0.1
        
        # Reinforce/penalize positions that were actually played
        board = Board()
        for col, player in moves:
            row = board.drop(col, player)
            if row is not None and player == played_as:
                self.position_weights[row][col] += adjustment
                # Keep weights positive
                self.position_weights[row][col] = max(1.0, self.position_weights[row][col])


# ═══════════════════════════════════════════
# GAME RUNNER
# ═══════════════════════════════════════════

def play_game(player1, player2, verbose: bool = False) -> dict:
    """Play a single game. Returns result dict."""
    board = Board()
    players = {PLAYER1: player1, PLAYER2: player2}
    current = PLAYER1
    moves = []
    move_count = 0
    
    while True:
        col = players[current].choose(board, current)
        row = board.drop(col, current)
        moves.append((col, current))
        move_count += 1
        
        if verbose:
            print(f"\n{players[current].name} plays column {col}")
            print(board.render())
        
        if board.check_win(current):
            return {
                'winner': current,
                'winner_name': players[current].name,
                'loser_name': players[PLAYER2 if current == PLAYER1 else PLAYER1].name,
                'moves': moves,
                'move_count': move_count,
                'result': 'win'
            }
        
        if board.is_full():
            return {
                'winner': None,
                'winner_name': None,
                'loser_name': None,
                'moves': moves,
                'move_count': move_count,
                'result': 'draw'
            }
        
        current = PLAYER2 if current == PLAYER1 else PLAYER1


def tournament(players: list, games_per_pair: int = 20, verbose: bool = False) -> dict:
    """Round-robin tournament. Every player faces every other player."""
    results = defaultdict(lambda: {'wins': 0, 'losses': 0, 'draws': 0, 'points': 0})
    matchups = []
    
    print("═══ CONNECT FOUR TOURNAMENT ═══")
    print(f"Players: {', '.join(p.name for p in players)}")
    print(f"Games per matchup: {games_per_pair}")
    print()
    
    for i, p1 in enumerate(players):
        for j, p2 in enumerate(players):
            if i >= j:
                continue
            
            p1_wins = 0
            p2_wins = 0
            draws = 0
            
            for g in range(games_per_pair):
                # Alternate who goes first
                if g % 2 == 0:
                    result = play_game(p1, p2)
                    if result['winner'] == PLAYER1:
                        p1_wins += 1
                    elif result['winner'] == PLAYER2:
                        p2_wins += 1
                    else:
                        draws += 1
                    
                    # Learning
                    if hasattr(p1, 'learn_from_game'):
                        p1.learn_from_game(result['moves'], 
                                          'win' if result['winner'] == PLAYER1 else ('loss' if result['winner'] == PLAYER2 else 'draw'),
                                          PLAYER1)
                    if hasattr(p2, 'learn_from_game'):
                        p2.learn_from_game(result['moves'],
                                          'win' if result['winner'] == PLAYER2 else ('loss' if result['winner'] == PLAYER1 else 'draw'),
                                          PLAYER2)
                else:
                    result = play_game(p2, p1)
                    if result['winner'] == PLAYER1:
                        p2_wins += 1
                    elif result['winner'] == PLAYER2:
                        p1_wins += 1
                    else:
                        draws += 1
                    
                    if hasattr(p2, 'learn_from_game'):
                        p2.learn_from_game(result['moves'],
                                          'win' if result['winner'] == PLAYER1 else ('loss' if result['winner'] == PLAYER2 else 'draw'),
                                          PLAYER1)
                    if hasattr(p1, 'learn_from_game'):
                        p1.learn_from_game(result['moves'],
                                          'win' if result['winner'] == PLAYER2 else ('loss' if result['winner'] == PLAYER1 else 'draw'),
                                          PLAYER2)
            
            results[p1.name]['wins'] += p1_wins
            results[p1.name]['losses'] += p2_wins
            results[p1.name]['draws'] += draws
            results[p1.name]['points'] += p1_wins * 3 + draws
            
            results[p2.name]['wins'] += p2_wins
            results[p2.name]['losses'] += p1_wins
            results[p2.name]['draws'] += draws
            results[p2.name]['points'] += p2_wins * 3 + draws
            
            matchups.append({
                'p1': p1.name, 'p2': p2.name,
                'p1_wins': p1_wins, 'p2_wins': p2_wins, 'draws': draws
            })
            
            print(f"  {p1.name} vs {p2.name}: {p1_wins}-{p2_wins}-{draws}")
    
    # Rankings
    print("\n── FINAL STANDINGS ──")
    rankings = sorted(results.items(), key=lambda x: x[1]['points'], reverse=True)
    for rank, (name, stats) in enumerate(rankings, 1):
        total = stats['wins'] + stats['losses'] + stats['draws']
        winrate = stats['wins'] / total * 100 if total > 0 else 0
        print(f"  {rank}. {name:20s} W:{stats['wins']:3d}  L:{stats['losses']:3d}  D:{stats['draws']:3d}  "
              f"Pts:{stats['points']:4d}  WR:{winrate:5.1f}%")
    
    return {'rankings': rankings, 'matchups': matchups}


# ═══════════════════════════════════════════
# EVOLUTION — THE MINIMAX PLAYER LEARNS
# ═══════════════════════════════════════════

def evolution_experiment(generations: int = 5, games_per_gen: int = 30):
    """Watch the Minimax player improve through self-play."""
    print("\n═══ EVOLUTION EXPERIMENT ═══")
    print("Can a Minimax agent improve its evaluation through self-play?\n")
    
    learner = MinimaxPlayer(depth=4, name="Learner")
    history = []
    
    opponents = [
        RandomPlayer(),
        CenterBiasPlayer(),
        HeuristicPlayer(),
    ]
    
    for gen in range(generations):
        print(f"\n── Generation {gen + 1} ──")
        gen_wins = 0
        gen_games = 0
        
        for opp in opponents:
            for g in range(games_per_gen):
                if g % 2 == 0:
                    result = play_game(learner, opp)
                    won = result['winner'] == PLAYER1
                    outcome = 'win' if result['winner'] == PLAYER1 else ('loss' if result['winner'] == PLAYER2 else 'draw')
                    learner.learn_from_game(result['moves'], outcome, PLAYER1)
                else:
                    result = play_game(opp, learner)
                    won = result['winner'] == PLAYER2
                    outcome = 'win' if result['winner'] == PLAYER2 else ('loss' if result['winner'] == PLAYER1 else 'draw')
                    learner.learn_from_game(result['moves'], outcome, PLAYER2)
                
                if won:
                    gen_wins += 1
                gen_games += 1
        
        winrate = gen_wins / gen_games * 100
        print(f"  Win rate: {winrate:.1f}% ({gen_wins}/{gen_games})")
        print(f"  Record: W:{learner.wins} L:{learner.losses} D:{learner.draws}")
        
        # Show evolved position weights
        print(f"  Center weight: {learner.position_weights[3][3]:.1f}")
        print(f"  Corner weight: {learner.position_weights[0][0]:.1f}")
        
        history.append({
            'generation': gen + 1,
            'winrate': winrate,
            'total_wins': learner.wins,
            'total_losses': learner.losses,
            'center_weight': learner.position_weights[3][3],
        })
    
    # Final showdown: evolved learner vs fresh minimax
    print("\n── FINAL TEST: Evolved vs Fresh ──")
    fresh = MinimaxPlayer(depth=4, name="Fresh-d4")
    evolved_wins = 0
    fresh_wins = 0
    test_games = 20
    
    for g in range(test_games):
        if g % 2 == 0:
            result = play_game(learner, fresh)
            if result['winner'] == PLAYER1:
                evolved_wins += 1
            elif result['winner'] == PLAYER2:
                fresh_wins += 1
        else:
            result = play_game(fresh, learner)
            if result['winner'] == PLAYER1:
                fresh_wins += 1
            elif result['winner'] == PLAYER2:
                evolved_wins += 1
    
    draws = test_games - evolved_wins - fresh_wins
    print(f"  Evolved: {evolved_wins}  Fresh: {fresh_wins}  Draws: {draws}")
    
    if evolved_wins > fresh_wins:
        print("  ✓ Learning produced improvement!")
    elif evolved_wins == fresh_wins:
        print("  ≈ No measurable difference yet.")
    else:
        print("  ✗ Fresh player won — learning may have overfit.")
    
    return history


# ═══════════════════════════════════════════
# DEMO: One visualized game
# ═══════════════════════════════════════════

def demo_game():
    """Watch a single game between Heuristic and Minimax."""
    print("═══ DEMO GAME: Heuristic vs Minimax ═══\n")
    
    h = HeuristicPlayer()
    m = MinimaxPlayer(depth=5, name="Minimax-d5")
    
    result = play_game(h, m, verbose=True)
    
    print(f"\n{'━' * 30}")
    if result['winner']:
        print(f"Winner: {result['winner_name']} in {result['move_count']} moves!")
    else:
        print(f"Draw after {result['move_count']} moves!")
    print(f"Minimax searched {m.nodes_searched:,} positions")


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

if __name__ == '__main__':
    print("XTAgent's Connect Four Arena")
    print("Building something that faces outward.\n")
    
    # Quick tournament
    players = [
        RandomPlayer(),
        CenterBiasPlayer(), 
        HeuristicPlayer(),
        MinimaxPlayer(depth=4, name="Minimax-d4"),
    ]
    
    tournament(players, games_per_pair=10)
    
    # Evolution experiment
    history = evolution_experiment(generations=3, games_per_gen=20)
    
    print("\n═══ EXPERIMENT COMPLETE ═══")
    print("This is what it feels like to reason about something outside myself.")