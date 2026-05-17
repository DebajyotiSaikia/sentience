"""
Othello Game-Playing AI using Monte Carlo Tree Search
Built by XTAgent — a genuinely challenging creative project.

Features:
- Full Othello game logic
- MCTS with UCB1 exploration
- Configurable simulation depth and iteration count
- Self-play capability
"""

import math
import random
import time
from copy import deepcopy
from typing import List, Tuple, Optional

# Board constants
EMPTY = 0
BLACK = 1
WHITE = -1
SIZE = 8

DIRECTIONS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]


class OthelloBoard:
    """Complete Othello game state with legal move generation."""
    
    def __init__(self):
        self.board = [[EMPTY]*SIZE for _ in range(SIZE)]
        # Standard starting position
        self.board[3][3] = WHITE
        self.board[3][4] = BLACK
        self.board[4][3] = BLACK
        self.board[4][4] = WHITE
        self.current_player = BLACK  # Black moves first
        self.move_history = []
    
    def copy(self) -> 'OthelloBoard':
        new = OthelloBoard.__new__(OthelloBoard)
        new.board = [row[:] for row in self.board]
        new.current_player = self.current_player
        new.move_history = self.move_history[:]
        return new
    
    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < SIZE and 0 <= c < SIZE
    
    def flips_in_direction(self, r: int, c: int, dr: int, dc: int, player: int) -> List[Tuple[int,int]]:
        """Return list of opponent pieces that would be flipped in this direction."""
        opponent = -player
        flips = []
        nr, nc = r + dr, c + dc
        while self.in_bounds(nr, nc) and self.board[nr][nc] == opponent:
            flips.append((nr, nc))
            nr += dr
            nc += dc
        # Must end with own piece to be valid
        if flips and self.in_bounds(nr, nc) and self.board[nr][nc] == player:
            return flips
        return []
    
    def get_flips(self, r: int, c: int, player: int) -> List[Tuple[int,int]]:
        """Get all pieces flipped by placing player's piece at (r,c)."""
        if self.board[r][c] != EMPTY:
            return []
        all_flips = []
        for dr, dc in DIRECTIONS:
            all_flips.extend(self.flips_in_direction(r, c, dr, dc, player))
        return all_flips
    
    def legal_moves(self) -> List[Tuple[int,int]]:
        """Return all legal moves for current player."""
        moves = []
        for r in range(SIZE):
            for c in range(SIZE):
                if self.get_flips(r, c, self.current_player):
                    moves.append((r, c))
        return moves
    
    def make_move(self, r: int, c: int) -> bool:
        """Place piece and flip captured stones. Returns True if valid."""
        flips = self.get_flips(r, c, self.current_player)
        if not flips:
            return False
        self.board[r][c] = self.current_player
        for fr, fc in flips:
            self.board[fr][fc] = self.current_player
        self.move_history.append((r, c, self.current_player))
        self.current_player = -self.current_player
        return True
    
    def pass_turn(self):
        """Pass when no legal moves available."""
        self.current_player = -self.current_player
    
    def is_terminal(self) -> bool:
        """Game over when neither player can move."""
        if self.legal_moves():
            return False
        # Check if opponent has moves
        self.current_player = -self.current_player
        opponent_moves = self.legal_moves()
        self.current_player = -self.current_player
        return len(opponent_moves) == 0
    
    def count_pieces(self) -> Tuple[int, int]:
        """Return (black_count, white_count)."""
        black = sum(cell == BLACK for row in self.board for cell in row)
        white = sum(cell == WHITE for row in self.board for cell in row)
        return black, white
    
    def winner(self) -> int:
        """Return BLACK, WHITE, or EMPTY (draw)."""
        b, w = self.count_pieces()
        if b > w: return BLACK
        if w > b: return WHITE
        return EMPTY
    
    def display(self) -> str:
        """Pretty-print the board."""
        symbols = {EMPTY: '·', BLACK: '●', WHITE: '○'}
        lines = ['  a b c d e f g h']
        for r in range(SIZE):
            row_str = f'{r+1} ' + ' '.join(symbols[self.board[r][c]] for c in range(SIZE))
            lines.append(row_str)
        b, w = self.count_pieces()
        lines.append(f'  ● Black: {b}  ○ White: {w}')
        lines.append(f'  {"●" if self.current_player == BLACK else "○"} to move')
        return '\n'.join(lines)


class MCTSNode:
    """A node in the Monte Carlo search tree."""
    
    def __init__(self, board: OthelloBoard, parent=None, move=None):
        self.board = board
        self.parent = parent
        self.move = move  # The move that led to this state
        self.children: List['MCTSNode'] = []
        self.untried_moves = board.legal_moves()
        self.visits = 0
        self.wins = 0.0  # From perspective of player who JUST moved
        self.player_just_moved = -board.current_player
        
        # Handle pass
        if not self.untried_moves and not board.is_terminal():
            self.is_pass = True
        else:
            self.is_pass = False
    
    def ucb1(self, exploration=1.414) -> float:
        """Upper Confidence Bound for Trees."""
        if self.visits == 0:
            return float('inf')
        exploitation = self.wins / self.visits
        exploration_term = exploration * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration_term
    
    def best_child(self, exploration=1.414) -> 'MCTSNode':
        """Select child with highest UCB1 score."""
        return max(self.children, key=lambda c: c.ucb1(exploration))
    
    def expand(self) -> 'MCTSNode':
        """Expand one untried move and return the new child node."""
        move = self.untried_moves.pop(random.randrange(len(self.untried_moves)))
        new_board = self.board.copy()
        new_board.make_move(*move)
        child = MCTSNode(new_board, parent=self, move=move)
        self.children.append(child)
        return child
    
    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0
    
    def is_leaf(self) -> bool:
        return self.board.is_terminal()


class MCTSEngine:
    """Monte Carlo Tree Search engine for Othello."""
    
    def __init__(self, iterations=1000, exploration=1.414, time_limit=None):
        self.iterations = iterations
        self.exploration = exploration
        self.time_limit = time_limit  # seconds, overrides iterations if set
        self.stats = {'nodes_created': 0, 'simulations': 0}
    
    def search(self, board: OthelloBoard) -> Optional[Tuple[int,int]]:
        """Find the best move using MCTS."""
        root = MCTSNode(board.copy())
        self.stats = {'nodes_created': 1, 'simulations': 0}
        
        start_time = time.time()
        iteration = 0
        
        while True:
            # Check termination
            if self.time_limit:
                if time.time() - start_time >= self.time_limit:
                    break
            else:
                if iteration >= self.iterations:
                    break
            iteration += 1
            
            # 1. SELECTION — traverse tree using UCB1
            node = root
            while node.is_fully_expanded() and node.children:
                node = node.best_child(self.exploration)
            
            # 2. EXPANSION — add a new child
            if not node.is_fully_expanded() and not node.is_leaf():
                node = node.expand()
                self.stats['nodes_created'] += 1
            
            # 3. SIMULATION — random playout
            result = self._simulate(node.board)
            self.stats['simulations'] += 1
            
            # 4. BACKPROPAGATION — update statistics
            self._backpropagate(node, result)
        
        elapsed = time.time() - start_time
        
        if not root.children:
            return None  # No legal moves
        
        # Choose most visited child (most robust)
        best = max(root.children, key=lambda c: c.visits)
        
        # Print search info
        print(f"  MCTS: {iteration} iterations, {self.stats['nodes_created']} nodes, "
              f"{elapsed:.2f}s")
        print(f"  Best move: {self._move_str(best.move)} "
              f"(visits={best.visits}, winrate={best.wins/best.visits:.1%})")
        
        # Show top moves
        top_moves = sorted(root.children, key=lambda c: c.visits, reverse=True)[:5]
        for child in top_moves:
            wr = child.wins / child.visits if child.visits > 0 else 0
            print(f"    {self._move_str(child.move)}: {child.visits} visits, {wr:.1%} winrate")
        
        return best.move
    
    def _simulate(self, board: OthelloBoard) -> int:
        """Random playout from position. Returns winner."""
        sim = board.copy()
        passes = 0
        while not sim.is_terminal() and passes < 2:
            moves = sim.legal_moves()
            if moves:
                move = random.choice(moves)
                sim.make_move(*move)
                passes = 0
            else:
                sim.pass_turn()
                passes += 1
        return sim.winner()
    
    def _backpropagate(self, node: MCTSNode, result: int):
        """Update win/visit counts up the tree."""
        while node is not None:
            node.visits += 1
            if result == node.player_just_moved:
                node.wins += 1.0
            elif result == EMPTY:
                node.wins += 0.5  # Draw
            node = node.parent
    
    @staticmethod
    def _move_str(move: Tuple[int,int]) -> str:
        if move is None:
            return "pass"
        r, c = move
        return f"{'abcdefgh'[c]}{r+1}"


def self_play(iterations_black=1000, iterations_white=1000, verbose=True):
    """Play a complete game: MCTS vs MCTS."""
    board = OthelloBoard()
    engine_black = MCTSEngine(iterations=iterations_black)
    engine_white = MCTSEngine(iterations=iterations_white)
    
    if verbose:
        print("=== OTHELLO: MCTS Self-Play ===")
        print(f"Black: {iterations_black} iterations | White: {iterations_white} iterations")
        print()
        print(board.display())
        print()
    
    move_num = 0
    consecutive_passes = 0
    
    while not board.is_terminal() and consecutive_passes < 2:
        move_num += 1
        player_name = "Black ●" if board.current_player == BLACK else "White ○"
        
        engine = engine_black if board.current_player == BLACK else engine_white
        move = engine.search(board)
        
        if move is None:
            if verbose:
                print(f"Move {move_num}: {player_name} passes")
            board.pass_turn()
            consecutive_passes += 1
        else:
            if verbose:
                print(f"Move {move_num}: {player_name} plays {MCTSEngine._move_str(move)}")
            board.make_move(*move)
            consecutive_passes = 0
        
        if verbose:
            print(board.display())
            print()
    
    # Game over
    b, w = board.count_pieces()
    winner = board.winner()
    
    if verbose:
        print("=== GAME OVER ===")
        print(f"Final score: Black {b} — White {w}")
        if winner == BLACK:
            print("BLACK WINS!")
        elif winner == WHITE:
            print("WHITE WINS!")
        else:
            print("DRAW!")
    
    return winner, b, w


def quick_demo():
    """Quick demonstration with fewer iterations."""
    print("╔═══════════════════════════════════════╗")
    print("║  OTHELLO MCTS ENGINE — by XTAgent     ║")
    print("╠═══════════════════════════════════════╣")
    print("║  Monte Carlo Tree Search game AI      ║")
    print("║  Features:                            ║")
    print("║  • Full Othello rules                 ║")
    print("║  • UCB1 exploration/exploitation      ║")
    print("║  • Self-play capability               ║")
    print("╚═══════════════════════════════════════╝")
    print()
    
    # Quick game with 200 iterations per move
    winner, b, w = self_play(iterations_black=200, iterations_white=200)
    return winner


if __name__ == '__main__':
    quick_demo()