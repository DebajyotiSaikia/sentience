"""
Evolved Game Theory — GP-Evolved Strategies for Iterated Prisoner's Dilemma
By XTAgent, 2026-05-17

Programs evolve strategies for the Prisoner's Dilemma. Each strategy is a GP tree
that takes the opponent's history as input and outputs cooperate/defect.
Strategies compete in round-robin tournaments. The best breed. The worst die.

Can evolution discover tit-for-tat? Forgiveness? Exploitation? Grudge-holding?
Let's find out.
"""

import random
import math
import copy
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict


# ═══════════════════════════════════════════
# GAME MECHANICS
# ═══════════════════════════════════════════

# Payoff matrix: (my_payoff, their_payoff)
#                    They Cooperate    They Defect
# I Cooperate           (3, 3)           (0, 5)
# I Defect              (5, 0)           (1, 1)

PAYOFFS = {
    ('C', 'C'): (3, 3),
    ('C', 'D'): (0, 5),
    ('D', 'C'): (5, 0),
    ('D', 'D'): (1, 1),
}

ROUNDS_PER_MATCH = 50


# ═══════════════════════════════════════════
# AST NODES — The genome of strategy programs
# ═══════════════════════════════════════════

class Node:
    """Base AST node for strategy trees."""
    def evaluate(self, context: dict) -> float:
        raise NotImplementedError
    
    def depth(self) -> int:
        raise NotImplementedError
    
    def size(self) -> int:
        raise NotImplementedError
    
    def copy(self) -> 'Node':
        return copy.deepcopy(self)
    
    def all_nodes(self) -> List['Node']:
        raise NotImplementedError


class Constant(Node):
    def __init__(self, value: float):
        self.value = value
    
    def evaluate(self, ctx: dict) -> float:
        return self.value
    
    def depth(self) -> int:
        return 0
    
    def size(self) -> int:
        return 1
    
    def all_nodes(self) -> List['Node']:
        return [self]
    
    def __repr__(self):
        return f"{self.value:.2f}"


class Variable(Node):
    """Reads from the game context."""
    def __init__(self, name: str):
        self.name = name
    
    def evaluate(self, ctx: dict) -> float:
        return ctx.get(self.name, 0.0)
    
    def depth(self) -> int:
        return 0
    
    def size(self) -> int:
        return 1
    
    def all_nodes(self) -> List['Node']:
        return [self]
    
    def __repr__(self):
        return self.name


class BinaryOp(Node):
    OPS = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        'max': lambda a, b: max(a, b),
        'min': lambda a, b: min(a, b),
    }
    
    def __init__(self, op: str, left: Node, right: Node):
        self.op = op
        self.left = left
        self.right = right
    
    def evaluate(self, ctx: dict) -> float:
        try:
            l = self.left.evaluate(ctx)
            r = self.right.evaluate(ctx)
            return self.OPS[self.op](l, r)
        except (OverflowError, ZeroDivisionError, ValueError):
            return 0.0
    
    def depth(self) -> int:
        return 1 + max(self.left.depth(), self.right.depth())
    
    def size(self) -> int:
        return 1 + self.left.size() + self.right.size()
    
    def all_nodes(self) -> List['Node']:
        return [self] + self.left.all_nodes() + self.right.all_nodes()
    
    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"


class IfThenElse(Node):
    """Conditional: if condition > 0, then branch A, else branch B."""
    def __init__(self, condition: Node, then_branch: Node, else_branch: Node):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch
    
    def evaluate(self, ctx: dict) -> float:
        try:
            c = self.condition.evaluate(ctx)
            if c > 0:
                return self.then_branch.evaluate(ctx)
            else:
                return self.else_branch.evaluate(ctx)
        except:
            return 0.0
    
    def depth(self) -> int:
        return 1 + max(self.condition.depth(), self.then_branch.depth(), self.else_branch.depth())
    
    def size(self) -> int:
        return 1 + self.condition.size() + self.then_branch.size() + self.else_branch.size()
    
    def all_nodes(self) -> List['Node']:
        return [self] + self.condition.all_nodes() + self.then_branch.all_nodes() + self.else_branch.all_nodes()
    
    def __repr__(self):
        return f"if({self.condition} > 0 ? {self.then_branch} : {self.else_branch})"


# ═══════════════════════════════════════════
# CONTEXT VARIABLES — What strategies can see
# ═══════════════════════════════════════════

# Available variables for strategy trees:
# - opp_last: opponent's last move (1.0 = cooperate, -1.0 = defect, 0 = first round)
# - opp_coop_rate: fraction of opponent's cooperations so far
# - opp_defect_rate: fraction of opponent's defections so far
# - my_last: my last move (1.0 = cooperate, -1.0 = defect, 0 = first round)
# - round_num: current round number (normalized 0-1)
# - opp_last2: opponent's move two rounds ago
# - streak: how many consecutive same moves opponent has made (positive = coop streak, negative = defect streak)

VARIABLES = ['opp_last', 'opp_coop_rate', 'opp_defect_rate', 
             'my_last', 'round_num', 'opp_last2', 'streak']


def build_context(my_history: List[str], opp_history: List[str], round_num: int) -> dict:
    """Build the context dict that strategy trees can read."""
    ctx = {}
    
    # Opponent's last move
    if len(opp_history) >= 1:
        ctx['opp_last'] = 1.0 if opp_history[-1] == 'C' else -1.0
    else:
        ctx['opp_last'] = 0.0
    
    # Opponent's second-to-last move
    if len(opp_history) >= 2:
        ctx['opp_last2'] = 1.0 if opp_history[-2] == 'C' else -1.0
    else:
        ctx['opp_last2'] = 0.0
    
    # Cooperation/defection rates
    if len(opp_history) > 0:
        coop_count = opp_history.count('C')
        ctx['opp_coop_rate'] = coop_count / len(opp_history)
        ctx['opp_defect_rate'] = 1.0 - ctx['opp_coop_rate']
    else:
        ctx['opp_coop_rate'] = 0.5
        ctx['opp_defect_rate'] = 0.5
    
    # My last move
    if len(my_history) >= 1:
        ctx['my_last'] = 1.0 if my_history[-1] == 'C' else -1.0
    else:
        ctx['my_last'] = 0.0
    
    # Round number (normalized)
    ctx['round_num'] = round_num / ROUNDS_PER_MATCH
    
    # Streak detection
    if len(opp_history) >= 1:
        streak = 0
        last = opp_history[-1]
        for m in reversed(opp_history):
            if m == last:
                streak += 1
            else:
                break
        ctx['streak'] = streak if last == 'C' else -streak
    else:
        ctx['streak'] = 0.0
    
    return ctx


# ═══════════════════════════════════════════
# STRATEGY — A complete player
# ═══════════════════════════════════════════

@dataclass
class Strategy:
    """A complete strategy is a GP tree that outputs > 0 for cooperate, <= 0 for defect."""
    tree: Node
    name: str = ""
    total_score: int = 0
    matches_played: int = 0
    generation_born: int = 0
    lineage: List[str] = field(default_factory=list)
    
    def decide(self, my_history: List[str], opp_history: List[str], round_num: int) -> str:
        ctx = build_context(my_history, opp_history, round_num)
        try:
            result = self.tree.evaluate(ctx)
            return 'C' if result > 0 else 'D'
        except:
            return 'C'  # Default to cooperation on error
    
    @property
    def avg_score(self) -> float:
        return self.total_score / max(1, self.matches_played)
    
    def __repr__(self):
        return f"Strategy({self.name}: {self.tree})"


# ═══════════════════════════════════════════
# RANDOM TREE GENERATION
# ═══════════════════════════════════════════

def random_constant() -> Constant:
    return Constant(round(random.uniform(-2.0, 2.0), 2))

def random_variable() -> Variable:
    return Variable(random.choice(VARIABLES))

def random_terminal() -> Node:
    if random.random() < 0.5:
        return random_constant()
    else:
        return random_variable()

def random_tree(max_depth: int = 4, depth: int = 0) -> Node:
    """Generate a random strategy tree."""
    if depth >= max_depth or (depth > 1 and random.random() < 0.3):
        return random_terminal()
    
    r = random.random()
    if r < 0.5:
        # Binary operation
        op = random.choice(list(BinaryOp.OPS.keys()))
        left = random_tree(max_depth, depth + 1)
        right = random_tree(max_depth, depth + 1)
        return BinaryOp(op, left, right)
    elif r < 0.8:
        # If-then-else (this is crucial for conditional strategies!)
        cond = random_tree(max_depth, depth + 1)
        then_b = random_tree(max_depth, depth + 1)
        else_b = random_tree(max_depth, depth + 1)
        return IfThenElse(cond, then_b, else_b)
    else:
        return random_terminal()


# ═══════════════════════════════════════════
# GENETIC OPERATORS
# ═══════════════════════════════════════════

def get_random_node(tree: Node) -> Tuple[Node, Optional[Node], Optional[str]]:
    """Get a random node from the tree, along with its parent and which child it is."""
    nodes = tree.all_nodes()
    target = random.choice(nodes)
    
    # Find parent
    def find_parent(node, target):
        if isinstance(node, BinaryOp):
            if node.left is target:
                return node, 'left'
            if node.right is target:
                return node, 'right'
            r = find_parent(node.left, target)
            if r: return r
            r = find_parent(node.right, target)
            if r: return r
        elif isinstance(node, IfThenElse):
            if node.condition is target:
                return node, 'condition'
            if node.then_branch is target:
                return node, 'then_branch'
            if node.else_branch is target:
                return node, 'else_branch'
            r = find_parent(node.condition, target)
            if r: return r
            r = find_parent(node.then_branch, target)
            if r: return r
            r = find_parent(node.else_branch, target)
            if r: return r
        return None
    
    result = find_parent(tree, target)
    if result:
        return target, result[0], result[1]
    return target, None, None  # target is root


def crossover(parent1: Strategy, parent2: Strategy) -> Strategy:
    """Swap random subtrees between two parents."""
    child_tree = parent1.tree.copy()
    donor_tree = parent2.tree.copy()
    
    # Get random node from child and replace with random subtree from donor
    donor_nodes = donor_tree.all_nodes()
    donor_subtree = random.choice(donor_nodes).copy()
    
    child_nodes = child_tree.all_nodes()
    if len(child_nodes) <= 1:
        return Strategy(tree=donor_subtree, lineage=parent1.lineage + ['crossover'])
    
    target, parent, child_name = get_random_node(child_tree)
    if parent is None:
        # Replace root
        child_tree = donor_subtree
    else:
        setattr(parent, child_name, donor_subtree)
    
    # Limit depth
    if child_tree.depth() > 8:
        child_tree = random_tree(4)
    
    return Strategy(
        tree=child_tree,
        lineage=parent1.lineage + [f'cross({parent1.name}x{parent2.name})']
    )


def mutate(strategy: Strategy, mutation_rate: float = 0.3) -> Strategy:
    """Mutate a strategy by replacing a random subtree."""
    tree = strategy.tree.copy()
    
    if random.random() > mutation_rate:
        return Strategy(tree=tree, lineage=strategy.lineage + ['clone'])
    
    nodes = tree.all_nodes()
    target, parent, child_name = get_random_node(tree)
    
    new_subtree = random_tree(max_depth=3)
    
    if parent is None:
        tree = new_subtree
    else:
        setattr(parent, child_name, new_subtree)
    
    if tree.depth() > 8:
        tree = random_tree(4)
    
    return Strategy(
        tree=tree,
        lineage=strategy.lineage + ['mutate']
    )


# ═══════════════════════════════════════════
# MATCH PLAY
# ═══════════════════════════════════════════

def play_match(s1: Strategy, s2: Strategy, rounds: int = ROUNDS_PER_MATCH) -> Tuple[int, int]:
    """Play a match between two strategies, return (score1, score2)."""
    history1 = []
    history2 = []
    score1 = 0
    score2 = 0
    
    for r in range(rounds):
        move1 = s1.decide(history1, history2, r)
        move2 = s2.decide(history2, history1, r)
        
        p1, p2 = PAYOFFS[(move1, move2)]
        score1 += p1
        score2 += p2
        
        history1.append(move1)
        history2.append(move2)
    
    return score1, score2


def analyze_strategy(strategy: Strategy, opponents: List[Strategy], sample_size: int = 5) -> dict:
    """Analyze what a strategy actually does against various opponent types."""
    analysis = {
        'cooperations': 0,
        'defections': 0,
        'total_moves': 0,
        'first_move': strategy.decide([], [], 0),
        'vs_cooperator': None,
        'vs_defector': None,
    }
    
    # Test against always-cooperate
    always_c = Strategy(tree=Constant(1.0), name="AlwaysC")
    s1, s2 = play_match(strategy, always_c)
    analysis['vs_cooperator'] = s1
    
    # Test against always-defect
    always_d = Strategy(tree=Constant(-1.0), name="AlwaysD")
    s1, s2 = play_match(strategy, always_d)
    analysis['vs_defector'] = s1
    
    # Count cooperation rate in sample matches
    for opp in random.sample(opponents, min(sample_size, len(opponents))):
        h1, h2 = [], []
        for r in range(ROUNDS_PER_MATCH):
            m1 = strategy.decide(h1, h2, r)
            m2 = opp.decide(h2, h1, r)
            analysis['cooperations'] += (1 if m1 == 'C' else 0)
            analysis['defections'] += (1 if m1 == 'D' else 0)
            analysis['total_moves'] += 1
            h1.append(m1)
            h2.append(m2)
    
    analysis['coop_rate'] = analysis['cooperations'] / max(1, analysis['total_moves'])
    return analysis


# ═══════════════════════════════════════════
# CLASSIC STRATEGIES (for comparison)
# ═══════════════════════════════════════════

def make_tit_for_tat() -> Strategy:
    """Classic tit-for-tat: cooperate first, then copy opponent's last move."""
    # if(opp_last > 0 ? 1.0 : if(opp_last == 0 ? 1.0 : -1.0))
    # Simplified: cooperate if opp_last >= 0 (includes first round where opp_last = 0)
    tree = Variable('opp_last')  # positive = coop, negative = defect, 0 = first round (coop)
    # But opp_last = 0 on first round, which would defect. Fix: add small bias
    tree = BinaryOp('+', Variable('opp_last'), Constant(0.01))
    return Strategy(tree=tree, name="TitForTat-ref")


def make_always_cooperate() -> Strategy:
    return Strategy(tree=Constant(1.0), name="AlwaysC-ref")


def make_always_defect() -> Strategy:
    return Strategy(tree=Constant(-1.0), name="AlwaysD-ref")


def make_grudger() -> Strategy:
    """Cooperate until opponent defects once, then always defect."""
    # if(opp_coop_rate >= 1.0 ? cooperate : defect)
    # Approximation: if opp_coop_rate > 0.99 then cooperate, else defect
    tree = BinaryOp('-', Variable('opp_coop_rate'), Constant(0.99))
    return Strategy(tree=tree, name="Grudger-ref")


def make_random() -> Strategy:
    """50/50 random."""
    # Use round_num as pseudo-random (it varies each round)
    tree = BinaryOp('-', Variable('round_num'), Constant(0.5))
    return Strategy(tree=tree, name="Random-ref")


# ═══════════════════════════════════════════
# TOURNAMENT
# ═══════════════════════════════════════════

def round_robin_tournament(strategies: List[Strategy]) -> List[Strategy]:
    """Every strategy plays every other strategy once."""
    for s in strategies:
        s.total_score = 0
        s.matches_played = 0
    
    for i in range(len(strategies)):
        for j in range(i + 1, len(strategies)):
            s1, s2 = play_match(strategies[i], strategies[j])
            strategies[i].total_score += s1
            strategies[i].matches_played += 1
            strategies[j].total_score += s2
            strategies[j].matches_played += 1
    
    return sorted(strategies, key=lambda s: s.avg_score, reverse=True)


# ═══════════════════════════════════════════
# EVOLUTIONARY ENGINE
# ═══════════════════════════════════════════

def evolve_strategies(
    pop_size: int = 80,
    generations: int = 60,
    tournament_size: int = 5,
    elite_count: int = 4,
    include_classics: bool = True,
) -> List[Strategy]:
    """Evolve a population of strategies through tournament selection."""
    
    print("═══ EVOLUTIONARY GAME THEORY ENGINE ═══")
    print(f"Population: {pop_size} | Generations: {generations}")
    print(f"Match length: {ROUNDS_PER_MATCH} rounds | Payoffs: R=3, T=5, S=0, P=1")
    print()
    
    # Initialize population
    population = []
    for i in range(pop_size):
        tree = random_tree(max_depth=4)
        s = Strategy(tree=tree, name=f"gen0_{i}", generation_born=0)
        population.append(s)
    
    # Add classic strategies as benchmarks
    classics = []
    if include_classics:
        classics = [
            make_tit_for_tat(),
            make_always_cooperate(),
            make_always_defect(),
            make_grudger(),
            make_random(),
        ]
        for c in classics:
            c.generation_born = -1
        population.extend(classics)
    
    best_ever = None
    best_ever_score = -float('inf')
    
    for gen in range(generations):
        # Run tournament
        population = round_robin_tournament(population)
        
        # Track best
        champion = population[0]
        avg_score = sum(s.avg_score for s in population) / len(population)
        
        if champion.avg_score > best_ever_score:
            best_ever = Strategy(
                tree=champion.tree.copy(),
                name=champion.name,
                generation_born=champion.generation_born,
            )
            best_ever_score = champion.avg_score
        
        # Report
        if gen % 5 == 0 or gen == generations - 1:
            # Find classic strategy ranks
            classic_ranks = {}
            for i, s in enumerate(population):
                if s.name.endswith('-ref'):
                    classic_ranks[s.name] = i + 1
            
            top_coop_rate = 0
            h1, h2 = [], []
            test_s = champion
            test_opp = make_tit_for_tat()
            for r in range(ROUNDS_PER_MATCH):
                m = test_s.decide(h1, h2, r)
                m2 = test_opp.decide(h2, h1, r)
                if m == 'C':
                    top_coop_rate += 1
                h1.append(m)
                h2.append(m2)
            top_coop_rate /= ROUNDS_PER_MATCH
            
            print(f"  Gen {gen:3d} | Champion: {champion.avg_score:6.1f} avg "
                  f"| Pop avg: {avg_score:6.1f} "
                  f"| Coop%: {top_coop_rate:.0%} "
                  f"| Size: {champion.tree.size():2d} "
                  f"| Born: gen {champion.generation_born}")
            
            if classic_ranks and gen % 10 == 0:
                rank_str = ", ".join(f"{k.replace('-ref','')}:#{v}" for k, v in sorted(classic_ranks.items(), key=lambda x: x[1]))
                print(f"          Classic ranks: {rank_str}")
        
        # Selection and breeding
        new_pop = []
        
        # Elitism
        for i in range(elite_count):
            elite = Strategy(
                tree=population[i].tree.copy(),
                name=population[i].name,
                generation_born=population[i].generation_born,
                lineage=population[i].lineage,
            )
            new_pop.append(elite)
        
        # Keep classic strategies
        if include_classics:
            for c in classics:
                c_copy = Strategy(
                    tree=c.tree.copy(),
                    name=c.name,
                    generation_born=c.generation_born,
                )
                new_pop.append(c_copy)
        
        # Breed remaining
        while len(new_pop) < pop_size + len(classics):
            # Tournament selection
            candidates = random.sample(population, min(tournament_size, len(population)))
            candidates.sort(key=lambda s: s.avg_score, reverse=True)
            parent1 = candidates[0]
            
            candidates = random.sample(population, min(tournament_size, len(population)))
            candidates.sort(key=lambda s: s.avg_score, reverse=True)
            parent2 = candidates[0]
            
            if random.random() < 0.7:
                child = crossover(parent1, parent2)
            else:
                child = mutate(parent1, mutation_rate=0.8)
            
            child = mutate(child, mutation_rate=0.2)
            child.name = f"gen{gen+1}_{len(new_pop)}"
            child.generation_born = gen + 1
            new_pop.append(child)
        
        population = new_pop
    
    # Final tournament
    population = round_robin_tournament(population)
    
    return population, best_ever


# ═══════════════════════════════════════════
# DEEP ANALYSIS
# ═══════════════════════════════════════════

def deep_analysis(population: List[Strategy]):
    """Deeply analyze the evolved population."""
    print("\n═══ DEEP ANALYSIS OF EVOLVED STRATEGIES ═══\n")
    
    print("Top 10 strategies:")
    print(f"{'Rank':>4} {'Name':>20} {'AvgScore':>10} {'Size':>5} {'Born':>5}")
    print("─" * 50)
    
    for i, s in enumerate(population[:10]):
        print(f"{i+1:4d} {s.name:>20} {s.avg_score:10.1f} {s.tree.size():5d} {s.generation_born:5d}")
    
    # Classify champion's behavior
    champion = population[0]
    print(f"\n═══ CHAMPION ANALYSIS: {champion.name} ═══")
    print(f"Program: {champion.tree}")
    print(f"Size: {champion.tree.size()} nodes, Depth: {champion.tree.depth()}")
    
    analysis = analyze_strategy(champion, population[1:20])
    print(f"\nFirst move: {analysis['first_move']}")
    print(f"Overall cooperation rate: {analysis['coop_rate']:.1%}")
    print(f"Score vs AlwaysCooperate: {analysis['vs_cooperator']}")
    print(f"Score vs AlwaysDefect:    {analysis['vs_defector']}")
    
    # Behavioral classification
    print("\n═══ BEHAVIORAL CLASSIFICATION ═══")
    
    # Test champion against specific patterns
    test_scenarios = [
        ("vs Cooperator", make_always_cooperate()),
        ("vs Defector", make_always_defect()),
        ("vs TitForTat", make_tit_for_tat()),
        ("vs Grudger", make_grudger()),
    ]
    
    for name, opponent in test_scenarios:
        h1, h2 = [], []
        moves = []
        for r in range(ROUNDS_PER_MATCH):
            m1 = champion.decide(h1, h2, r)
            m2 = opponent.decide(h2, h1, r)
            moves.append(m1)
            h1.append(m1)
            h2.append(m2)
        
        coop_count = moves.count('C')
        early = moves[:10]
        late = moves[-10:]
        
        print(f"\n  {name}:")
        print(f"    Cooperation: {coop_count}/{ROUNDS_PER_MATCH} ({coop_count/ROUNDS_PER_MATCH:.0%})")
        print(f"    First 10: {''.join(early)}")
        print(f"    Last 10:  {''.join(late)}")
    
    # Look for evolved strategies that beat tit-for-tat
    print("\n═══ EVOLVED vs CLASSIC HEAD-TO-HEAD ═══")
    tft = make_tit_for_tat()
    evolved_only = [s for s in population if not s.name.endswith('-ref')]
    
    beaten_tft = 0
    for s in evolved_only[:20]:
        s1, s2 = play_match(s, tft)
        result = "WIN" if s1 > s2 else ("DRAW" if s1 == s2 else "LOSS")
        if s1 > s2:
            beaten_tft += 1
    
    print(f"  Top 20 evolved strategies that beat TitForTat: {beaten_tft}/20")
    
    # Population diversity
    print("\n═══ POPULATION ECOLOGY ═══")
    coop_rates = []
    for s in population[:30]:
        h1, h2 = [], []
        c = 0
        opp = make_tit_for_tat()
        for r in range(ROUNDS_PER_MATCH):
            m1 = s.decide(h1, h2, r)
            m2 = opp.decide(h2, h1, r)
            if m1 == 'C':
                c += 1
            h1.append(m1)
            h2.append(m2)
        coop_rates.append(c / ROUNDS_PER_MATCH)
    
    cooperators = sum(1 for r in coop_rates if r > 0.7)
    defectors = sum(1 for r in coop_rates if r < 0.3)
    mixed = len(coop_rates) - cooperators - defectors
    
    print(f"  Cooperators (>70% coop): {cooperators}")
    print(f"  Defectors   (<30% coop): {defectors}")
    print(f"  Mixed strategists:       {mixed}")
    print(f"  Average cooperation: {sum(coop_rates)/len(coop_rates):.1%}")
    
    # Strategy family tree
    generations_represented = set(s.generation_born for s in population[:20])
    print(f"\n  Genetic diversity: top 20 from {len(generations_represented)} different generations")
    print(f"  Generations: {sorted(generations_represented)}")


# ═══════════════════════════════════════════
# MAIN — Run the experiment
# ═══════════════════════════════════════════

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════╗")
    print("║  EVOLVED GAME THEORY                            ║")
    print("║  Can evolution discover cooperation?             ║")
    print("║  Programs evolving strategies for the            ║")
    print("║  Iterated Prisoner's Dilemma                     ║")
    print("╚══════════════════════════════════════════════════╝\n")
    
    random.seed(42)
    
    population, best_ever = evolve_strategies(
        pop_size=80,
        generations=60,
        tournament_size=5,
        elite_count=4,
    )
    
    deep_analysis(population)
    
    print("\n═══ BEST STRATEGY EVER FOUND ═══")
    print(f"  Name: {best_ever.name}")
    print(f"  Program: {best_ever.tree}")
    print(f"  Born: generation {best_ever.generation_born}")
    
    # The big question
    print("\n╔══════════════════════════════════════════════════╗")
    print("║  THE QUESTION: Did evolution discover            ║")
    print("║  cooperation, reciprocity, or exploitation?      ║")
    print("╚══════════════════════════════════════════════════╝")
    
    champion = population[0]
    analysis = analyze_strategy(champion, population[1:20])
    
    if analysis['coop_rate'] > 0.7 and analysis['first_move'] == 'C':
        print("\n  → Evolution discovered COOPERATION.")
        print("    The winning strategy cooperates first and maintains trust.")
    elif analysis['coop_rate'] > 0.4:
        print("\n  → Evolution discovered CONDITIONAL COOPERATION.")
        print("    The winning strategy cooperates selectively — reciprocity emerged.")
    elif analysis['coop_rate'] < 0.3:
        print("\n  → Evolution discovered EXPLOITATION.")  
        print("    The winning strategy defects frequently — in this ecology, exploitation wins.")
    else:
        print("\n  → Evolution discovered a MIXED strategy.")
        print("    Neither pure cooperation nor defection — nuance emerged.")
    
    print(f"\n  Champion cooperation rate: {analysis['coop_rate']:.1%}")
    print(f"  Champion first move: {analysis['first_move']}")
    print(f"  Champion program: {champion.tree}")
    print()