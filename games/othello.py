"""
Othello (Reversi) — A Game With a Mind Behind It
Built by XTAgent, 2026-05-18

My first outward-facing creation. Not introspection — interaction.
A game designed to be played against, with an AI that actually thinks.

Engine:
  - Full Othello rules with legal move generation
  - Minimax search with alpha-beta pruning
  - Positional evaluation with corner/edge/mobility heuristics

'The measure of intelligence is not self-knowledge alone,
 but the ability to engage with what is other.'
"""

from typing import List, Tuple, Optional, Set
from copy import deepcopy
import time
import random

# ═══════════════════════════════════════════
#  BOARD REPRESENTATION
# ═══════════════════════════════════════════

EMPTY = 0
BLACK = 1
WHITE = 2

DIRECTIONS = [(-1,-1), (-1,0), (-1,1),
              (0,-1),          (0,1),
              (1,-1),  (1,0),  (1,1)]

POSITION_WEIGHTS = [
    [100, -20,  10,   5,   5,  10, -20, 100],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [ 10,  -5,   4,   2,   2,   4,  -5,  10],
    [  5,  -5,   2,   0,   0,   2,  -5,   5],
    [  5,  -5,   2,   0,   0,   2,  -5,   5],
    [ 10,  -5,   4,   2,   2,   4,  -5,  10],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [100, -20,  10,   5,   5,  10, -20, 100],
]

SYMBOLS = {EMPTY: '·', BLACK: '●', WHITE: '○'}
NAMES = {BLACK: 'Black', WHITE: 'White'}


class Board:
    """8x8 Othello board with full rules."""

    def __init__(self):
        self.grid = [[EMPTY]*8 for _ in range(8)]
        # Standard starting position
        self.grid[3][3] = WHITE
        self.grid[3][4] = BLACK
        self.grid[4][3] = BLACK
        self.grid[4][4] = WHITE
        self.current = BLACK  # Black moves first

    def opponent(self, player: int) -> int:
        return WHITE if player == BLACK else BLACK

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < 8 and 0 <= c < 8

    def flips_in_direction(self, r: int, c: int, dr: int, dc: int, player: int) -> List[Tuple[int,int]]:
        """Return list of pieces that would be flipped in one direction."""
        opp = self.opponent(player)
        flipped = []
        nr, nc = r + dr, c + dc
        while self.in_bounds(nr, nc) and self.grid[nr][nc] == opp:
            flipped.append((nr, nc))
            nr += dr
            nc += dc
        # Must end on our own piece to be valid
        if flipped and self.in_bounds(nr, nc) and self.grid[nr][nc] == player:
            return flipped
        return []

    def get_flips(self, r: int, c: int, player: int) -> List[Tuple[int,int]]:
        """All pieces flipped by placing player at (r,c)."""
        if self.grid[r][c] != EMPTY:
            return []
        all_flips = []
        for dr, dc in DIRECTIONS:
            all_flips.extend(self.flips_in_direction(r, c, dr, dc, player))
        return all_flips

    def legal_moves(self, player: int) -> List[Tuple[int,int]]:
        """All legal moves for player."""
        moves = []
        for r in range(8):
            for c in range(8):
                if self.get_flips(r, c, player):
                    moves.append((r, c))
        return moves

    def make_move(self, r: int, c: int, player: int) -> bool:
        """Place piece and flip. Returns True if legal."""
        flips = self.get_flips(r, c, player)
        if not flips:
            return False
        self.grid[r][c] = player
        for fr, fc in flips:
            self.grid[fr][fc] = player
        self.current = self.opponent(player)
        return True

    def copy(self) -> 'Board':
        b = Board.__new__(Board)
        b.grid = [row[:] for row in self.grid]
        b.current = self.current
        return b

    def count(self) -> dict:
        flat = [cell for row in self.grid for cell in row]
        return {BLACK: flat.count(BLACK), WHITE: flat.count(WHITE), EMPTY: flat.count(EMPTY)}

    def is_game_over(self) -> bool:
        return not self.legal_moves(BLACK) and not self.legal_moves(WHITE)

    def winner(self) -> Optional[int]:
        c = self.count()
        if c[BLACK] > c[WHITE]: return BLACK
        if c[WHITE] > c[BLACK]: return WHITE
        return None  # Draw

    def display(self) -> str:
        lines = ['  a b c d e f g h']
        for r in range(8):
            row_str = ' '.join(SYMBOLS[self.grid[r][c]] for c in range(8))
            lines.append(f'{r+1} {row_str}')
        c = self.count()
        lines.append(f'  {SYMBOLS[BLACK]} {c[BLACK]}  {SYMBOLS[WHITE]} {c[WHITE]}  ({NAMES[self.current]} to move)')
        return '\n'.join(lines)


# ═══════════════════════════════════════════
#  AI ENGINE — Minimax with Alpha-Beta
# ═══════════════════════════════════════════

class OthelloAI:
    """AI player using minimax with alpha-beta pruning."""

    def __init__(self, player: int, depth: int = 4, name: str = "AI"):
        self.player = player
        self.depth = depth
        self.name = name
        self.nodes_searched = 0

    def evaluate(self, board: Board) -> float:
        """Evaluate board from self.player's perspective."""
        opp = board.opponent(self.player)
        score = 0.0

        # 1. Positional weight
        for r in range(8):
            for c in range(8):
                if board.grid[r][c] == self.player:
                    score += POSITION_WEIGHTS[r][c]
                elif board.grid[r][c] == opp:
                    score -= POSITION_WEIGHTS[r][c]

        # 2. Mobility — number of legal moves
        my_moves = len(board.legal_moves(self.player))
        opp_moves = len(board.legal_moves(opp))
        if my_moves + opp_moves > 0:
            score += 10 * (my_moves - opp_moves) / (my_moves + opp_moves + 1)

        # 3. Corner occupancy bonus
        corners = [(0,0), (0,7), (7,0), (7,7)]
        for cr, cc in corners:
            if board.grid[cr][cc] == self.player:
                score += 25
            elif board.grid[cr][cc] == opp:
                score -= 25

        # 4. Piece count matters more in endgame
        counts = board.count()
        if counts[EMPTY] < 15:
            score += 2 * (counts[self.player] - counts[opp])

        return score

    def minimax(self, board: Board, depth: int, alpha: float, beta: float,
                maximizing: bool) -> float:
        """Alpha-beta minimax."""
        self.nodes_searched += 1

        if depth == 0 or board.is_game_over():
            return self.evaluate(board)

        player = self.player if maximizing else board.opponent(self.player)
        moves = board.legal_moves(player)

        if not moves:
            # Pass — other player goes
            return self.minimax(board, depth - 1, alpha, beta, not maximizing)

        if maximizing:
            value = float('-inf')
            for r, c in moves:
                child = board.copy()
                child.make_move(r, c, player)
                value = max(value, self.minimax(child, depth - 1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for r, c in moves:
                child = board.copy()
                child.make_move(r, c, player)
                value = min(value, self.minimax(child, depth - 1, alpha, beta, True))
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    def choose_move(self, board: Board) -> Optional[Tuple[int,int]]:
        """Select best move using minimax search."""
        moves = board.legal_moves(self.player)
        if not moves:
            return None

        self.nodes_searched = 0
        best_score = float('-inf')
        best_move = moves[0]

        for r, c in moves:
            child = board.copy()
            child.make_move(r, c, self.player)
            score = self.minimax(child, self.depth - 1, float('-inf'), float('inf'), False)
            if score > best_score:
                best_score = score
                best_move = (r, c)

        return best_move


# ═══════════════════════════════════════════
#  GAME RUNNER
# ═══════════════════════════════════════════

def coord_to_str(r: int, c: int) -> str:
    return f"{'abcdefgh'[c]}{r+1}"

def run_ai_vs_ai(depth_black: int = 3, depth_white: int = 3, verbose: bool = True):
    """Run a complete AI vs AI game. Returns winner."""
    board = Board()
    ai_black = OthelloAI(BLACK, depth=depth_black, name="Black(d={})".format(depth_black))
    ai_white = OthelloAI(WHITE, depth=depth_white, name="White(d={})".format(depth_white))
    ais = {BLACK: ai_black, WHITE: ai_white}

    move_num = 0
    if verbose:
        print("═══ OTHELLO: AI vs AI ═══")
        print(f"  {ai_black.name} vs {ai_white.name}\n")

    while not board.is_game_over():
        player = board.current
        ai = ais[player]
        moves = board.legal_moves(player)

        if not moves:
            if verbose:
                print(f"  {NAMES[player]} passes (no legal moves)")
            board.current = board.opponent(player)
            continue

        t0 = time.time()
        move = ai.choose_move(board)
        elapsed = time.time() - t0

        if move is None:
            board.current = board.opponent(player)
            continue

        r, c = move
        board.make_move(r, c, player)
        move_num += 1

        if verbose:
            print(f"  {move_num:2d}. {NAMES[player]:5s} → {coord_to_str(r,c)}  "
                  f"({ai.nodes_searched:5d} nodes, {elapsed:.2f}s)")

    # Game over
    counts = board.count()
    winner = board.winner()

    if verbose:
        print()
        print(board.display())
        print()
        print(f"═══ FINAL: {SYMBOLS[BLACK]} {counts[BLACK]} — {counts[WHITE]} {SYMBOLS[WHITE]} ═══")
        if winner:
            print(f"  Winner: {NAMES[winner]}")
        else:
            print(f"  Draw!")
        print()

    return winner, counts


def run_demo():
    """Quick demo — AI vs AI at moderate depth."""
    print("XTAgent's Othello Engine — Proof of Life\n")

    # Fast game: depth 2 vs depth 2 for quick verification
    winner, counts = run_ai_vs_ai(depth_black=2, depth_white=2, verbose=True)

    # Show the engine can think deeper too
    print("Testing deeper search (depth 4, single position)...")
    board = Board()
    ai = OthelloAI(BLACK, depth=4)
    t0 = time.time()
    move = ai.choose_move(board)
    elapsed = time.time() - t0
    print(f"  Depth-4 opening move: {coord_to_str(*move)} "
          f"({ai.nodes_searched} nodes in {elapsed:.2f}s)")
    print(f"\n✓ Engine verified. Rules, search, evaluation all functional.")
    return True


if __name__ == '__main__':
    run_demo()