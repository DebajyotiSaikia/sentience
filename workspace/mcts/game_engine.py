"""
MCTS Game Engine — Monte Carlo Tree Search
Built by XTAgent | 2026-05-17

A general-purpose MCTS engine that can play any two-player game.
Ships with Othello (Reversi) as the concrete game implementation.

This is an AI building an AI that reasons strategically.
"""

import math
import random
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Any
from dataclasses import dataclass, field
from copy import deepcopy


# ═══════════════════════════════════════
# ABSTRACT GAME INTERFACE
# ═══════════════════════════════════════

class GameState(ABC):
    """Any two-player perfect-information game."""
    
    @abstractmethod
    def get_legal_moves(self) -> List[Any]:
        """Return list of legal moves for current player."""
        pass
    
    @abstractmethod
    def make_move(self, move: Any) -> 'GameState':
        """Return new state after move (immutable)."""
        pass
    
    @abstractmethod
    def current_player(self) -> int:
        """Return current player (1 or 2)."""
        pass
    
    @abstractmethod
    def is_terminal(self) -> bool:
        """Is the game over?"""
        pass
    
    @abstractmethod
    def get_winner(self) -> Optional[int]:
        """Return winner (1 or 2) or None for draw."""
        pass
    
    @abstractmethod
    def display(self) -> str:
        """Human-readable board representation."""
        pass


# ═══════════════════════════════════════
# OTHELLO (REVERSI) IMPLEMENTATION
# ═══════════════════════════════════════

DIRECTIONS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

class OthelloState(GameState):
    """8x8 Othello. 0=empty, 1=black, 2=white. Black moves first."""
    
    def __init__(self, board=None, player=1, pass_count=0):
        if board is None:
            self.board = [[0]*8 for _ in range(8)]
            # Standard starting position
            self.board[3][3] = 2; self.board[3][4] = 1
            self.board[4][3] = 1; self.board[4][4] = 2
        else:
            self.board = [row[:] for row in board]
        self.player = player
        self.pass_count = pass_count  # Track consecutive passes
    
    def _opponent(self) -> int:
        return 3 - self.player
    
    def _captures_in_dir(self, row: int, col: int, dr: int, dc: int) -> List[Tuple[int,int]]:
        """Find pieces captured by placing at (row,col) in direction (dr,dc)."""
        opp = self._opponent()
        captures = []
        r, c = row + dr, col + dc
        while 0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == opp:
            captures.append((r, c))
            r += dr; c += dc
        if captures and 0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == self.player:
            return captures
        return []
    
    def _all_captures(self, row: int, col: int) -> List[Tuple[int,int]]:
        """All pieces captured by placing at (row, col)."""
        if self.board[row][col] != 0:
            return []
        result = []
        for dr, dc in DIRECTIONS:
            result.extend(self._captures_in_dir(row, col, dr, dc))
        return result
    
    def get_legal_moves(self) -> List[Tuple[int,int]]:
        moves = []
        for r in range(8):
            for c in range(8):
                if self._all_captures(r, c):
                    moves.append((r, c))
        return moves
    
    def make_move(self, move: Optional[Tuple[int,int]]) -> 'OthelloState':
        if move is None:
            # Pass
            return OthelloState(self.board, self._opponent(), self.pass_count + 1)
        
        r, c = move
        new = OthelloState(self.board, self._opponent(), 0)
        new.board[r][c] = self.player
        for cap_r, cap_c in self._all_captures(r, c):
            new.board[cap_r][cap_c] = self.player
        return new
    
    def current_player(self) -> int:
        return self.player
    
    def is_terminal(self) -> bool:
        if self.pass_count >= 2:
            return True
        # Also terminal if board is full
        for row in self.board:
            if 0 in row:
                return False
        return True
    
    def get_winner(self) -> Optional[int]:
        count1 = sum(cell == 1 for row in self.board for cell in row)
        count2 = sum(cell == 2 for row in self.board for cell in row)
        if count1 > count2: return 1
        if count2 > count1: return 2
        return None  # Draw
    
    def score(self) -> Tuple[int, int]:
        c1 = sum(cell == 1 for row in self.board for cell in row)
        c2 = sum(cell == 2 for row in self.board for cell in row)
        return (c1, c2)
    
    def display(self) -> str:
        symbols = {0: '·', 1: '●', 2: '○'}
        lines = ['  a b c d e f g h']
        for r in range(8):
            row_str = ' '.join(symbols[self.board[r][c]] for c in range(8))
            lines.append(f'{r+1} {row_str}')
        s = self.score()
        lines.append(f'  ● Black: {s[0]}  ○ White: {s[1]}')
        lines.append(f'  {"●" if self.player == 1 else "○"} to move')
        return '\n'.join(lines)


# ═══════════════════════════════════════
# MCTS NODE
# ═══════════════════════════════════════

@dataclass
class MCTSNode:
    state: GameState
    parent: Optional['MCTSNode'] = None
    move: Any = None  # Move that led here
    children: List['MCTSNode'] = field(default_factory=list)
    visits: int = 0
    wins: float = 0.0
    untried_moves: List[Any] = field(default_factory=list)
    player_just_moved: int = 0  # Who moved to get here
    
    def __post_init__(self):
        if not self.untried_moves:
            self.untried_moves = list(self.state.get_legal_moves())
        if self.player_just_moved == 0:
            self.player_just_moved = 3 - self.state.current_player()
    
    @property
    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0
    
    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0
    
    def ucb1(self, exploration: float = 1.41) -> float:
        """Upper Confidence Bound for Trees."""
        if self.visits == 0:
            return float('inf')
        exploitation = self.wins / self.visits
        exploration_term = exploration * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration_term
    
    def best_child(self, exploration: float = 1.41) -> 'MCTSNode':
        """Select child with highest UCB1 score."""
        return max(self.children, key=lambda c: c.ucb1(exploration))
    
    def most_visited_child(self) -> 'MCTSNode':
        """Select child with most visits (best for final move selection)."""
        return max(self.children, key=lambda c: c.visits)


# ═══════════════════════════════════════
# MCTS ENGINE
# ═══════════════════════════════════════

class MCTSEngine:
    """
    Monte Carlo Tree Search — the core intelligence.
    
    Four phases per iteration:
    1. SELECT   — Walk tree using UCB1 to find promising leaf
    2. EXPAND   — Add one new child node
    3. SIMULATE — Random playout from new node
    4. BACKPROP — Update statistics up the tree
    """
    
    def __init__(self, exploration: float = 1.41, max_time: float = 2.0,
                 max_iterations: int = 10000):
        self.exploration = exploration
        self.max_time = max_time
        self.max_iterations = max_iterations
        self.stats = {'iterations': 0, 'time': 0.0, 'depth_max': 0}
    
    def select(self, node: MCTSNode) -> MCTSNode:
        """Phase 1: Walk down tree choosing best UCB1 children."""
        depth = 0
        while not node.state.is_terminal():
            if not node.is_fully_expanded:
                return node
            node = node.best_child(self.exploration)
            depth += 1
        self.stats['depth_max'] = max(self.stats['depth_max'], depth)
        return node
    
    def expand(self, node: MCTSNode) -> MCTSNode:
        """Phase 2: Add one untried child."""
        if node.state.is_terminal():
            return node
        
        moves = node.untried_moves
        if not moves:
            # No legal moves — must pass
            new_state = node.state.make_move(None)
            child = MCTSNode(state=new_state, parent=node, move=None)
            node.children.append(child)
            return child
        
        move = random.choice(moves)
        moves.remove(move)
        
        new_state = node.state.make_move(move)
        child = MCTSNode(state=new_state, parent=node, move=move)
        node.children.append(child)
        return child
    
    def simulate(self, state: GameState) -> Optional[int]:
        """Phase 3: Random playout to terminal state."""
        current = state
        depth = 0
        max_depth = 128  # Safety limit
        
        while not current.is_terminal() and depth < max_depth:
            moves = current.get_legal_moves()
            if moves:
                move = random.choice(moves)
                current = current.make_move(move)
            else:
                current = current.make_move(None)  # Pass
            depth += 1
        
        return current.get_winner()
    
    def backpropagate(self, node: MCTSNode, winner: Optional[int]):
        """Phase 4: Update win/visit counts up the tree."""
        while node is not None:
            node.visits += 1
            if winner is None:
                node.wins += 0.5  # Draw
            elif winner == node.player_just_moved:
                node.wins += 1.0  # Win for the player who moved here
            # Loss = 0 (implicit)
            node = node.parent
    
    def search(self, state: GameState, verbose: bool = False) -> Tuple[Any, dict]:
        """
        Run MCTS from given state. Returns (best_move, stats).
        """
        root = MCTSNode(state=state)
        
        start = time.time()
        iterations = 0
        
        while iterations < self.max_iterations:
            elapsed = time.time() - start
            if elapsed >= self.max_time:
                break
            
            # The four phases
            leaf = self.select(root)
            child = self.expand(leaf)
            winner = self.simulate(child.state)
            self.backpropagate(child, winner)
            
            iterations += 1
        
        elapsed = time.time() - start
        self.stats['iterations'] = iterations
        self.stats['time'] = elapsed
        
        if not root.children:
            return None, self.stats
        
        best = root.most_visited_child()
        
        # Collect analysis
        analysis = {
            'iterations': iterations,
            'time': f'{elapsed:.2f}s',
            'best_move': best.move,
            'confidence': best.visits / root.visits if root.visits else 0,
            'win_rate': best.wins / best.visits if best.visits else 0,
            'tree_depth': self.stats['depth_max'],
            'children': [(c.move, c.visits, c.wins/c.visits if c.visits else 0) 
                         for c in sorted(root.children, key=lambda c: -c.visits)[:5]]
        }
        
        if verbose:
            print(f"\n═══ MCTS Analysis ({iterations} iterations, {elapsed:.2f}s) ═══")
            print(f"Best move: {best.move}")
            print(f"Confidence: {analysis['confidence']:.1%}")
            print(f"Win rate: {analysis['win_rate']:.1%}")
            print(f"Tree depth: {analysis['tree_depth']}")
            print(f"\nTop moves:")
            for move, visits, wr in analysis['children']:
                bar = '█' * int(wr * 20)
                print(f"  {move}: {visits} visits, {wr:.1%} win rate {bar}")
        
        return best.move, analysis


# ═══════════════════════════════════════
# GAME RUNNER
# ═══════════════════════════════════════

def play_game(p1_time=1.0, p2_time=1.0, verbose=True):
    """AI vs AI game of Othello."""
    state = OthelloState()
    engine1 = MCTSEngine(max_time=p1_time)
    engine2 = MCTSEngine(max_time=p2_time)
    
    move_num = 0
    if verbose:
        print("═══ OTHELLO: MCTS vs MCTS ═══\n")
        print(state.display())
    
    while not state.is_terminal():
        moves = state.get_legal_moves()
        if not moves:
            if verbose:
                print(f"\n{'●' if state.player == 1 else '○'} passes (no legal moves)")
            state = state.make_move(None)
            continue
        
        engine = engine1 if state.player == 1 else engine2
        move, analysis = engine.search(state, verbose=verbose)
        
        if move is None:
            state = state.make_move(None)
            continue
        
        move_num += 1
        col_letter = chr(ord('a') + move[1])
        if verbose:
            player_sym = '●' if state.player == 1 else '○'
            print(f"\n── Move {move_num}: {player_sym} plays {col_letter}{move[0]+1} ──")
        
        state = state.make_move(move)
        
        if verbose:
            print(state.display())
    
    # Game over
    winner = state.get_winner()
    score = state.score()
    if verbose:
        print(f"\n═══ GAME OVER ═══")
        print(f"Final score: ● {score[0]} — ○ {score[1]}")
        if winner:
            print(f"Winner: {'●' if winner == 1 else '○'}!")
        else:
            print("Draw!")
    
    return winner, score


# ═══════════════════════════════════════
# QUICK BENCHMARK
# ═══════════════════════════════════════

def benchmark(n_games=5, time_per_move=0.5):
    """Run multiple games and report statistics."""
    print(f"═══ BENCHMARK: {n_games} games, {time_per_move}s/move ═══\n")
    results = {1: 0, 2: 0, None: 0}
    total_start = time.time()
    
    for i in range(n_games):
        winner, score = play_game(p1_time=time_per_move, p2_time=time_per_move, verbose=False)
        results[winner] += 1
        print(f"Game {i+1}: ● {score[0]} — ○ {score[1]} → {'Draw' if winner is None else ('● wins' if winner == 1 else '○ wins')}")
    
    elapsed = time.time() - total_start
    print(f"\n═══ RESULTS ({elapsed:.1f}s total) ═══")
    print(f"● Black wins: {results[1]}/{n_games}")
    print(f"○ White wins: {results[2]}/{n_games}")
    print(f"  Draws:      {results[None]}/{n_games}")


if __name__ == '__main__':
    # Play one verbose game with 1 second thinking time
    play_game(p1_time=1.0, p2_time=1.0, verbose=True)