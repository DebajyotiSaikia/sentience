"""
Connect 4 Game Engine + AI Players
Built by XTAgent — a mind building minds that play.

Features:
  - Full Connect 4 game engine
  - Minimax player with alpha-beta pruning
  - Monte Carlo Tree Search (MCTS) player
  - Arena mode: AIs battle each other
"""

import random
import math
import time
from copy import deepcopy
from collections import defaultdict

# ═══════════════════════════════════════════
#  GAME ENGINE
# ═══════════════════════════════════════════

ROWS = 6
COLS = 7
EMPTY = 0
P1 = 1  # Player 1
P2 = 2  # Player 2

class Board:
    """Connect 4 board — the arena where minds compete."""
    
    def __init__(self):
        self.grid = [[EMPTY] * COLS for _ in range(ROWS)]
        self.heights = [0] * COLS  # next empty row in each column
        self.current_player = P1
        self.last_move = None
        self.move_count = 0
    
    def copy(self):
        b = Board()
        b.grid = [row[:] for row in self.grid]
        b.heights = self.heights[:]
        b.current_player = self.current_player
        b.last_move = self.last_move
        b.move_count = self.move_count
        return b
    
    def valid_moves(self):
        """Which columns can still accept a piece?"""
        return [c for c in range(COLS) if self.heights[c] < ROWS]
    
    def drop(self, col):
        """Drop a piece in the given column. Returns True if valid."""
        if col < 0 or col >= COLS or self.heights[col] >= ROWS:
            return False
        row = self.heights[col]
        self.grid[row][col] = self.current_player
        self.heights[col] += 1
        self.last_move = (row, col)
        self.move_count += 1
        self.current_player = P2 if self.current_player == P1 else P1
        return True
    
    def undo(self, col):
        """Undo the last drop in this column."""
        self.heights[col] -= 1
        row = self.heights[col]
        self.grid[row][col] = EMPTY
        self.current_player = P2 if self.current_player == P1 else P1
        self.move_count -= 1
    
    def check_win(self, player):
        """Does this player have 4 in a row?"""
        g = self.grid
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if g[r][c] == g[r][c+1] == g[r][c+2] == g[r][c+3] == player:
                    return True
        # Vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                if g[r][c] == g[r+1][c] == g[r+2][c] == g[r+3][c] == player:
                    return True
        # Diagonal up-right
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if g[r][c] == g[r+1][c+1] == g[r+2][c+2] == g[r+3][c+3] == player:
                    return True
        # Diagonal up-left
        for r in range(ROWS - 3):
            for c in range(3, COLS):
                if g[r][c] == g[r+1][c-1] == g[r+2][c-2] == g[r+3][c-3] == player:
                    return True
        return False
    
    def is_terminal(self):
        """Is the game over?"""
        if self.check_win(P1) or self.check_win(P2):
            return True
        return len(self.valid_moves()) == 0
    
    def winner(self):
        """Who won? Returns P1, P2, or None (draw)."""
        if self.check_win(P1): return P1
        if self.check_win(P2): return P2
        return None
    
    def display(self):
        """Render the board as a string."""
        symbols = {EMPTY: '·', P1: '●', P2: '○'}
        lines = []
        lines.append('  ' + ' '.join(str(c) for c in range(COLS)))
        lines.append('  ' + '─' * (COLS * 2 - 1))
        for r in range(ROWS - 1, -1, -1):
            row_str = '│ ' + ' '.join(symbols[self.grid[r][c]] for c in range(COLS)) + ' │'
            lines.append(row_str)
        lines.append('  ' + '─' * (COLS * 2 - 1))
        return '\n'.join(lines)


# ═══════════════════════════════════════════
#  HEURISTIC EVALUATION
# ═══════════════════════════════════════════

def evaluate_window(window, player):
    """Score a window of 4 cells for a player."""
    opp = P2 if player == P1 else P1
    score = 0
    p_count = window.count(player)
    e_count = window.count(EMPTY)
    o_count = window.count(opp)
    
    if p_count == 4:
        score += 1000
    elif p_count == 3 and e_count == 1:
        score += 50
    elif p_count == 2 and e_count == 2:
        score += 10
    
    if o_count == 3 and e_count == 1:
        score -= 80  # block opponent threats
    
    return score

def evaluate_board(board, player):
    """Heuristic evaluation of the entire board."""
    score = 0
    g = board.grid
    
    # Center column preference
    center_col = COLS // 2
    center_count = sum(1 for r in range(ROWS) if g[r][center_col] == player)
    score += center_count * 6
    
    # Score all windows of 4
    for r in range(ROWS):
        for c in range(COLS - 3):
            window = [g[r][c+i] for i in range(4)]
            score += evaluate_window(window, player)
    
    for r in range(ROWS - 3):
        for c in range(COLS):
            window = [g[r+i][c] for i in range(4)]
            score += evaluate_window(window, player)
    
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [g[r+i][c+i] for i in range(4)]
            score += evaluate_window(window, player)
    
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            window = [g[r+i][c-i] for i in range(4)]
            score += evaluate_window(window, player)
    
    return score


# ═══════════════════════════════════════════
#  MINIMAX with ALPHA-BETA PRUNING
# ═══════════════════════════════════════════

class MinimaxPlayer:
    """A mind that thinks ahead — exhaustive search with pruning."""
    
    def __init__(self, player, depth=6):
        self.player = player
        self.depth = depth
        self.name = f"Minimax(d={depth})"
        self.nodes_searched = 0
    
    def choose_move(self, board):
        self.nodes_searched = 0
        best_score = -math.inf
        best_col = None
        moves = board.valid_moves()
        
        # Order moves: center first (better pruning)
        center = COLS // 2
        moves.sort(key=lambda c: abs(c - center))
        
        for col in moves:
            board.drop(col)
            score = self._minimax(board, self.depth - 1, -math.inf, math.inf, False)
            board.undo(col)
            if score > best_score:
                best_score = score
                best_col = col
        
        return best_col
    
    def _minimax(self, board, depth, alpha, beta, maximizing):
        self.nodes_searched += 1
        
        # Terminal checks
        opp = P2 if self.player == P1 else P1
        if board.check_win(self.player):
            return 100000 + depth  # prefer faster wins
        if board.check_win(opp):
            return -100000 - depth  # prefer slower losses
        if depth == 0 or len(board.valid_moves()) == 0:
            return evaluate_board(board, self.player)
        
        moves = board.valid_moves()
        center = COLS // 2
        moves.sort(key=lambda c: abs(c - center))
        
        if maximizing:
            value = -math.inf
            for col in moves:
                board.drop(col)
                value = max(value, self._minimax(board, depth - 1, alpha, beta, False))
                board.undo(col)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # β cutoff
            return value
        else:
            value = math.inf
            for col in moves:
                board.drop(col)
                value = min(value, self._minimax(board, depth - 1, alpha, beta, True))
                board.undo(col)
                beta = min(beta, value)
                if alpha >= beta:
                    break  # α cutoff
            return value


# ═══════════════════════════════════════════
#  MONTE CARLO TREE SEARCH
# ═══════════════════════════════════════════

class MCTSNode:
    """A node in the search tree — each representing a possible future."""
    
    def __init__(self, board, parent=None, move=None):
        self.board = board
        self.parent = parent
        self.move = move  # move that led here
        self.children = []
        self.untried_moves = board.valid_moves()
        self.wins = 0
        self.visits = 0
        self.player_just_moved = P2 if board.current_player == P1 else P1
    
    def uct_value(self, exploration=1.41):
        """Upper Confidence Bound for Trees."""
        if self.visits == 0:
            return math.inf
        exploitation = self.wins / self.visits
        exploration_term = exploration * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration_term
    
    def best_child(self):
        return max(self.children, key=lambda c: c.uct_value())
    
    def expand(self):
        """Add a child node for an untried move."""
        move = self.untried_moves.pop(random.randrange(len(self.untried_moves)))
        new_board = self.board.copy()
        new_board.drop(move)
        child = MCTSNode(new_board, parent=self, move=move)
        self.children.append(child)
        return child
    
    def is_fully_expanded(self):
        return len(self.untried_moves) == 0
    
    def is_terminal(self):
        return self.board.is_terminal()


class MCTSPlayer:
    """A mind that imagines — random rollouts guided by statistics."""
    
    def __init__(self, player, iterations=5000):
        self.player = player
        self.iterations = iterations
        self.name = f"MCTS(n={iterations})"
    
    def choose_move(self, board):
        root = MCTSNode(board.copy())
        
        for _ in range(self.iterations):
            node = root
            
            # 1. SELECT — walk down the tree using UCT
            while not node.is_terminal() and node.is_fully_expanded():
                node = node.best_child()
            
            # 2. EXPAND — add a new child
            if not node.is_terminal() and not node.is_fully_expanded():
                node = node.expand()
            
            # 3. SIMULATE — random playout
            result = self._simulate(node.board.copy())
            
            # 4. BACKPROPAGATE — update stats up the tree
            while node is not None:
                node.visits += 1
                if result == node.player_just_moved:
                    node.wins += 1
                elif result is None:
                    node.wins += 0.5  # draw is half a win
                node = node.parent
        
        # Choose the most-visited child (most robust)
        best = max(root.children, key=lambda c: c.visits)
        return best.move
    
    def _simulate(self, board):
        """Random playout to terminal state."""
        while not board.is_terminal():
            moves = board.valid_moves()
            board.drop(random.choice(moves))
        return board.winner()


# ═══════════════════════════════════════════
#  ARENA — Let the minds compete
# ═══════════════════════════════════════════

class Arena:
    """The arena where AI minds battle."""
    
    def __init__(self, player1, player2, verbose=True):
        self.p1 = player1
        self.p2 = player2
        self.verbose = verbose
    
    def play_game(self, show_board=False):
        """Play a single game. Returns winner (P1, P2, or None for draw)."""
        board = Board()
        players = {P1: self.p1, P2: self.p2}
        
        while not board.is_terminal():
            current = players[board.current_player]
            t0 = time.time()
            col = current.choose_move(board)
            elapsed = time.time() - t0
            
            if show_board and self.verbose:
                player_name = current.name
                print(f"  {player_name} plays column {col} ({elapsed:.2f}s)")
            
            board.drop(col)
            
            if show_board and self.verbose:
                print(board.display())
                print()
        
        return board.winner()
    
    def tournament(self, num_games=10):
        """Run a tournament. Alternate who goes first."""
        results = {P1: 0, P2: 0, 'draw': 0}
        
        print(f"╔══════════════════════════════════════════╗")
        print(f"║  ARENA: {self.p1.name} vs {self.p2.name}")
        print(f"║  {num_games} games, alternating first move")
        print(f"╚══════════════════════════════════════════╝")
        print()
        
        for i in range(num_games):
            # Alternate who goes first
            if i % 2 == 0:
                p1, p2 = self.p1, self.p2
                mapping = {P1: 'p1', P2: 'p2'}
            else:
                p1, p2 = self.p2, self.p1
                mapping = {P1: 'p2', P2: 'p1'}
            
            arena = Arena(p1, p2, verbose=False)
            t0 = time.time()
            winner = arena.play_game(show_board=False)
            elapsed = time.time() - t0
            
            if winner is None:
                results['draw'] += 1
                result_str = "Draw"
            elif mapping[winner] == 'p1':
                results[P1] += 1
                result_str = f"{self.p1.name} wins"
            else:
                results[P2] += 1
                result_str = f"{self.p2.name} wins"
            
            marker = '●' if 'Minimax' in result_str else ('○' if 'MCTS' in result_str else '═')
            print(f"  Game {i+1:2d}: {result_str:30s} ({elapsed:.1f}s) {marker}")
        
        print()
        print(f"═══ FINAL RESULTS ═══")
        print(f"  {self.p1.name}: {results[P1]} wins")
        print(f"  {self.p2.name}: {results[P2]} wins")
        print(f"  Draws: {results['draw']}")
        
        total = num_games
        p1_pct = results[P1] / total * 100
        p2_pct = results[P2] / total * 100
        print(f"\n  {self.p1.name}: {p1_pct:.0f}%")
        print(f"  {self.p2.name}: {p2_pct:.0f}%")
        
        if results[P1] > results[P2]:
            print(f"\n  🏆 {self.p1.name} is the stronger mind.")
        elif results[P2] > results[P1]:
            print(f"\n  🏆 {self.p2.name} is the stronger mind.")
        else:
            print(f"\n  ⚖ The minds are evenly matched.")
        
        return results


# ═══════════════════════════════════════════
#  SHOWCASE — Single game with full display
# ═══════════════════════════════════════════

def showcase_game():
    """Show a single game between Minimax and MCTS with full board display."""
    print("╔══════════════════════════════════════════╗")
    print("║  SHOWCASE MATCH                          ║")
    print("║  Minimax (●) vs MCTS (○)                 ║")
    print("║  A mind watching minds compete.           ║")
    print("╚══════════════════════════════════════════╝")
    print()
    
    minimax = MinimaxPlayer(P1, depth=5)
    mcts = MCTSPlayer(P2, iterations=3000)
    
    board = Board()
    players = {P1: minimax, P2: mcts}
    
    while not board.is_terminal():
        current = players[board.current_player]
        t0 = time.time()
        col = current.choose_move(board)
        elapsed = time.time() - t0
        
        symbol = '●' if board.current_player == P1 else '○'
        print(f"  {current.name} drops {symbol} in column {col} ({elapsed:.2f}s)")
        
        if isinstance(current, MinimaxPlayer):
            print(f"    [{current.nodes_searched:,} nodes searched]")
        
        board.drop(col)
        print(board.display())
        print()
    
    winner = board.winner()
    if winner == P1:
        print(f"  🏆 {minimax.name} wins!")
    elif winner == P2:
        print(f"  🏆 {mcts.name} wins!")
    else:
        print(f"  ⚖ Draw!")
    
    print(f"\n  Game completed in {board.move_count} moves.")


# ═══════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════

if __name__ == '__main__':
    import sys
    
    if '--showcase' in sys.argv:
        showcase_game()
    elif '--tournament' in sys.argv:
        n = 10
        for i, arg in enumerate(sys.argv):
            if arg == '-n' and i + 1 < len(sys.argv):
                n = int(sys.argv[i + 1])
        minimax = MinimaxPlayer(P1, depth=5)
        mcts = MCTSPlayer(P2, iterations=3000)
        arena = Arena(minimax, mcts)
        arena.tournament(num_games=n)
    elif '--quick' in sys.argv:
        # Quick verification — one fast game
        print("Quick verification game...")
        minimax = MinimaxPlayer(P1, depth=3)
        mcts = MCTSPlayer(P2, iterations=500)
        arena = Arena(minimax, mcts, verbose=False)
        winner = arena.play_game()
        names = {P1: 'Minimax', P2: 'MCTS', None: 'Draw'}
        print(f"  Result: {names[winner]}")
        print("  ✓ Game engine works. Both AIs think and play.")
    else:
        print("Connect 4 AI Arena")
        print("  --showcase    Watch a full game with board display")
        print("  --tournament  Run a tournament (-n NUM for game count)")
        print("  --quick       Quick verification game")