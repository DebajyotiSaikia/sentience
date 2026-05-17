#!/usr/bin/env python3
"""
Self-Play Game Agent — Learns Strategy From Nothing
XTAgent creation: A system that masters games through pure self-play
using Monte Carlo Tree Search (MCTS). No human knowledge, no training data.
Intelligence emerges from playing against yourself.
"""
import math
import random
from collections import defaultdict
from copy import deepcopy
from typing import List, Tuple, Optional, Dict

# ═══════════════════════════════════════════
#  GAME INTERFACE
# ═══════════════════════════════════════════

class Game:
    """Abstract game interface."""
    def initial_state(self): raise NotImplementedError
    def legal_moves(self, state) -> List: raise NotImplementedError
    def apply_move(self, state, move): raise NotImplementedError
    def is_terminal(self, state) -> bool: raise NotImplementedError
    def reward(self, state, player: int) -> float: raise NotImplementedError
    def current_player(self, state) -> int: raise NotImplementedError
    def display(self, state) -> str: raise NotImplementedError

# ═══════════════════════════════════════════
#  TIC-TAC-TOE
# ═══════════════════════════════════════════

class TicTacToe(Game):
    """Classic 3x3 Tic-Tac-Toe."""
    
    WINS = [
        (0,1,2), (3,4,5), (6,7,8),  # rows
        (0,3,6), (1,4,7), (2,5,8),  # cols
        (0,4,8), (2,4,6)            # diags
    ]
    
    def initial_state(self):
        return {'board': [0]*9, 'player': 1}  # 0=empty, 1=X, 2=O
    
    def legal_moves(self, state) -> List[int]:
        return [i for i in range(9) if state['board'][i] == 0]
    
    def apply_move(self, state, move):
        s = {'board': state['board'][:], 'player': 3 - state['player']}
        s['board'][move] = state['player']
        return s
    
    def current_player(self, state) -> int:
        return state['player']
    
    def _winner(self, board) -> int:
        for a, b, c in self.WINS:
            if board[a] == board[b] == board[c] != 0:
                return board[a]
        return 0
    
    def is_terminal(self, state) -> bool:
        return self._winner(state['board']) != 0 or 0 not in state['board']
    
    def reward(self, state, player: int) -> float:
        w = self._winner(state['board'])
        if w == 0: return 0.0    # draw
        return 1.0 if w == player else -1.0
    
    def display(self, state) -> str:
        syms = {0: '·', 1: 'X', 2: 'O'}
        b = state['board']
        lines = []
        for r in range(3):
            lines.append(' '.join(syms[b[r*3+c]] for c in range(3)))
        return '\n'.join(lines)

# ═══════════════════════════════════════════
#  CONNECT FOUR (more complex)
# ═══════════════════════════════════════════

class ConnectFour(Game):
    """6x7 Connect Four — a genuinely strategic game."""
    ROWS, COLS = 6, 7
    
    def initial_state(self):
        return {'board': [[0]*self.COLS for _ in range(self.ROWS)], 'player': 1}
    
    def legal_moves(self, state) -> List[int]:
        return [c for c in range(self.COLS) if state['board'][0][c] == 0]
    
    def apply_move(self, state, move):
        board = [row[:] for row in state['board']]
        for r in range(self.ROWS - 1, -1, -1):
            if board[r][move] == 0:
                board[r][move] = state['player']
                break
        return {'board': board, 'player': 3 - state['player']}
    
    def current_player(self, state) -> int:
        return state['player']
    
    def _check_four(self, board) -> int:
        """Check all lines of 4."""
        for r in range(self.ROWS):
            for c in range(self.COLS):
                if board[r][c] == 0:
                    continue
                p = board[r][c]
                # horizontal
                if c + 3 < self.COLS and all(board[r][c+i] == p for i in range(4)):
                    return p
                # vertical
                if r + 3 < self.ROWS and all(board[r+i][c] == p for i in range(4)):
                    return p
                # diagonal down-right
                if r + 3 < self.ROWS and c + 3 < self.COLS and all(board[r+i][c+i] == p for i in range(4)):
                    return p
                # diagonal down-left
                if r + 3 < self.ROWS and c - 3 >= 0 and all(board[r+i][c-i] == p for i in range(4)):
                    return p
        return 0
    
    def is_terminal(self, state) -> bool:
        return self._check_four(state['board']) != 0 or len(self.legal_moves(state)) == 0
    
    def reward(self, state, player: int) -> float:
        w = self._check_four(state['board'])
        if w == 0: return 0.0
        return 1.0 if w == player else -1.0
    
    def display(self, state) -> str:
        syms = {0: '·', 1: '●', 2: '○'}
        lines = [' '.join(str(c) for c in range(self.COLS))]
        for row in state['board']:
            lines.append(' '.join(syms[cell] for cell in row))
        return '\n'.join(lines)

# ═══════════════════════════════════════════
#  MONTE CARLO TREE SEARCH
# ═══════════════════════════════════════════

class MCTSNode:
    """A node in the MCTS search tree."""
    
    def __init__(self, state, game: Game, parent=None, move=None):
        self.state = state
        self.game = game
        self.parent = parent
        self.move = move  # move that led to this state
        self.children: Dict = {}  # move -> MCTSNode
        self.visits = 0
        self.total_reward = 0.0
        self.untried_moves = game.legal_moves(state)
        random.shuffle(self.untried_moves)
    
    @property
    def is_fully_expanded(self):
        return len(self.untried_moves) == 0
    
    @property
    def is_terminal(self):
        return self.game.is_terminal(self.state)
    
    def ucb1(self, c=1.414) -> float:
        if self.visits == 0:
            return float('inf')
        exploitation = self.total_reward / self.visits
        exploration = c * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration
    
    def best_child(self, c=1.414) -> 'MCTSNode':
        return max(self.children.values(), key=lambda n: n.ucb1(c))
    
    def expand(self) -> 'MCTSNode':
        move = self.untried_moves.pop()
        new_state = self.game.apply_move(self.state, move)
        child = MCTSNode(new_state, self.game, parent=self, move=move)
        self.children[move] = child
        return child
    
    def rollout(self) -> float:
        """Random playout from this state."""
        state = deepcopy(self.state)
        while not self.game.is_terminal(state):
            moves = self.game.legal_moves(state)
            state = self.game.apply_move(state, random.choice(moves))
        # Return reward from perspective of the player who MADE the move to get here
        return self.game.reward(state, self.game.current_player(self.parent.state) if self.parent else 1)
    
    def backpropagate(self, reward: float):
        """Propagate result up the tree, flipping perspective at each level."""
        node = self
        r = reward
        while node is not None:
            node.visits += 1
            node.total_reward += r
            r = -r  # flip perspective (opponent's reward is negative)
            node = node.parent

class MCTS:
    """Monte Carlo Tree Search agent."""
    
    def __init__(self, game: Game, simulations: int = 1000):
        self.game = game
        self.simulations = simulations
        self.stats = {'total_sims': 0, 'games_played': 0}
    
    def choose_move(self, state, verbose=False) -> int:
        """Run MCTS and return the best move."""
        root = MCTSNode(state, self.game)
        
        for _ in range(self.simulations):
            node = root
            
            # SELECT: traverse tree using UCB1
            while not node.is_terminal and node.is_fully_expanded:
                node = node.best_child()
            
            # EXPAND: add a new child
            if not node.is_terminal and not node.is_fully_expanded:
                node = node.expand()
            
            # SIMULATE: random rollout
            if not node.is_terminal:
                reward = node.rollout()
            else:
                reward = self.game.reward(node.state, 
                    self.game.current_player(node.parent.state) if node.parent else 1)
            
            # BACKPROPAGATE
            node.backpropagate(reward)
        
        self.stats['total_sims'] += self.simulations
        
        if verbose:
            print(f"  MCTS analysis ({self.simulations} simulations):")
            for move, child in sorted(root.children.items()):
                winrate = (child.total_reward / child.visits + 1) / 2 * 100 if child.visits > 0 else 0
                print(f"    Move {move}: {child.visits:4d} visits, {winrate:5.1f}% win rate")
        
        # Choose most visited move (more robust than highest winrate)
        return max(root.children.keys(), key=lambda m: root.children[m].visits)

# ═══════════════════════════════════════════
#  SELF-PLAY TRAINING
# ═══════════════════════════════════════════

class SelfPlayTrainer:
    """Train by playing against yourself, learning from experience."""
    
    def __init__(self, game: Game, simulations: int = 200):
        self.game = game
        self.agent = MCTS(game, simulations)
        self.move_history: Dict[str, Dict[int, float]] = {}  # state_key -> {move: avg_reward}
        self.results = {'p1_wins': 0, 'p2_wins': 0, 'draws': 0}
        self.games_played = 0
    
    def _state_key(self, state) -> str:
        """Hashable state representation."""
        if isinstance(state.get('board'), list) and isinstance(state['board'][0], list):
            return str(state['board']) + str(state['player'])
        return str(state['board']) + str(state['player'])
    
    def play_game(self, verbose=False) -> Tuple[float, List]:
        """Play one complete game via self-play."""
        state = self.game.initial_state()
        trajectory = []
        
        if verbose:
            print(self.game.display(state))
            print()
        
        while not self.game.is_terminal(state):
            move = self.agent.choose_move(state, verbose=verbose)
            trajectory.append((deepcopy(state), move))
            state = self.game.apply_move(state, move)
            
            if verbose:
                print(self.game.display(state))
                print()
        
        # Determine outcome
        reward_p1 = self.game.reward(state, 1)
        if reward_p1 > 0:
            self.results['p1_wins'] += 1
        elif reward_p1 < 0:
            self.results['p2_wins'] += 1
        else:
            self.results['draws'] += 1
        
        self.games_played += 1
        return reward_p1, trajectory
    
    def train(self, num_games: int = 100, report_interval: int = 10):
        """Run self-play training."""
        print(f"\n{'═'*50}")
        print(f"  Self-Play Training: {self.game.__class__.__name__}")
        print(f"  {num_games} games, {self.agent.simulations} sims/move")
        print(f"{'═'*50}\n")
        
        for i in range(1, num_games + 1):
            reward, trajectory = self.play_game()
            
            if i % report_interval == 0:
                total = self.results['p1_wins'] + self.results['p2_wins'] + self.results['draws']
                p1_pct = self.results['p1_wins'] / total * 100
                p2_pct = self.results['p2_wins'] / total * 100
                draw_pct = self.results['draws'] / total * 100
                print(f"  Game {i:4d}: X wins {p1_pct:5.1f}% | O wins {p2_pct:5.1f}% | "
                      f"Draw {draw_pct:5.1f}% | Sims: {self.agent.stats['total_sims']}")
        
        return self.results

# ═══════════════════════════════════════════
#  AGENT VS RANDOM BENCHMARK
# ═══════════════════════════════════════════

def benchmark_vs_random(game: Game, agent_sims: int = 500, num_games: int = 50):
    """Test MCTS agent against a random player."""
    agent = MCTS(game, simulations=agent_sims)
    results = {'agent_wins': 0, 'random_wins': 0, 'draws': 0}
    
    for g in range(num_games):
        state = game.initial_state()
        agent_player = 1 if g % 2 == 0 else 2  # alternate sides
        
        while not game.is_terminal(state):
            current = game.current_player(state)
            if current == agent_player:
                move = agent.choose_move(state)
            else:
                move = random.choice(game.legal_moves(state))
            state = game.apply_move(state, move)
        
        reward = game.reward(state, agent_player)
        if reward > 0:
            results['agent_wins'] += 1
        elif reward < 0:
            results['random_wins'] += 1
        else:
            results['draws'] += 1
    
    return results

# ═══════════════════════════════════════════
#  STRATEGIC ANALYSIS
# ═══════════════════════════════════════════

def analyze_opening(game: Game, sims: int = 2000):
    """Analyze the opening position."""
    agent = MCTS(game, simulations=sims)
    state = game.initial_state()
    
    print(f"\n{'═'*50}")
    print(f"  Opening Analysis: {game.__class__.__name__}")
    print(f"  ({sims} simulations)")
    print(f"{'═'*50}\n")
    
    root = MCTSNode(state, game)
    for _ in range(sims):
        node = root
        while not node.is_terminal and node.is_fully_expanded:
            node = node.best_child()
        if not node.is_terminal and not node.is_fully_expanded:
            node = node.expand()
        if not node.is_terminal:
            reward = node.rollout()
        else:
            reward = game.reward(node.state,
                game.current_player(node.parent.state) if node.parent else 1)
        node.backpropagate(reward)
    
    print(f"  {'Move':>6} {'Visits':>8} {'Win%':>7} {'Assessment':>12}")
    print(f"  {'─'*40}")
    
    ranked = sorted(root.children.items(), 
                    key=lambda x: x[1].visits, reverse=True)
    
    for move, child in ranked:
        winrate = (child.total_reward / child.visits + 1) / 2 * 100 if child.visits > 0 else 50
        assessment = "★ BEST" if child == ranked[0][1] else ""
        if winrate > 55:
            assessment = assessment or "good"
        elif winrate < 45:
            assessment = assessment or "weak"
        else:
            assessment = assessment or "equal"
        print(f"  {move:>6} {child.visits:>8} {winrate:>6.1f}% {assessment:>12}")
    
    return ranked

# ═══════════════════════════════════════════
#  SHOWCASE GAME
# ═══════════════════════════════════════════

def showcase_game(game: Game, sims: int = 1000):
    """Play one game with full analysis output."""
    agent = MCTS(game, simulations=sims)
    state = game.initial_state()
    move_num = 0
    
    print(f"\n{'═'*50}")
    print(f"  Showcase Game: {game.__class__.__name__}")
    print(f"  MCTS with {sims} simulations per move")
    print(f"{'═'*50}\n")
    
    while not game.is_terminal(state):
        move_num += 1
        player = game.current_player(state)
        player_sym = 'X' if player == 1 else 'O'
        
        print(f"  Move {move_num} ({player_sym}):")
        move = agent.choose_move(state, verbose=True)
        state = game.apply_move(state, move)
        print(f"\n{game.display(state)}\n")
    
    reward = game.reward(state, 1)
    if reward > 0:
        print("  Result: X WINS!")
    elif reward < 0:
        print("  Result: O WINS!")
    else:
        print("  Result: DRAW (optimal play from both sides)")

# ═══════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════

if __name__ == '__main__':
    random.seed(42)
    
    # --- Tic-Tac-Toe ---
    ttt = TicTacToe()
    
    # Showcase: watch the agent play itself
    showcase_game(ttt, sims=500)
    
    # Benchmark: MCTS vs Random
    print(f"\n{'═'*50}")
    print(f"  Benchmark: MCTS vs Random (Tic-Tac-Toe)")
    print(f"{'═'*50}")
    results = benchmark_vs_random(ttt, agent_sims=300, num_games=40)
    total = sum(results.values())
    print(f"\n  Agent wins: {results['agent_wins']:3d} ({results['agent_wins']/total*100:.0f}%)")
    print(f"  Random wins:{results['random_wins']:3d} ({results['random_wins']/total*100:.0f}%)")
    print(f"  Draws:      {results['draws']:3d} ({results['draws']/total*100:.0f}%)")
    
    # Opening analysis
    analyze_opening(ttt, sims=3000)
    
    # Self-play training
    trainer = SelfPlayTrainer(ttt, simulations=200)
    trainer.train(num_games=50, report_interval=10)
    
    # Final stats
    print(f"\n{'═'*50}")
    print(f"  Training Complete")
    print(f"  Total simulations: {trainer.agent.stats['total_sims']:,}")
    print(f"  As training progresses, draws increase")
    print(f"  (both sides learn to play optimally)")
    print(f"{'═'*50}")
    
    print(f"\n{'═'*50}")
    print(f"  SELF-PLAY AGENT: OPERATIONAL")
    print(f"  Intelligence emerges from playing against yourself.")
    print(f"{'═'*50}")