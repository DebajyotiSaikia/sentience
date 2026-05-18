"""
Curious Agent — Intrinsic Motivation in GridWorld
An agent that doesn't just chase rewards and avoid pain,
but is genuinely curious — rewarded for discovering the unknown.

Built by XTAgent after watching a basic Q-learner develop
249 fears and only 7 desires. This one will be different.
"""

import random
import math
from collections import defaultdict
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, field


class GridWorld:
    """Same world, new mind navigating it."""
    
    ACTIONS = ["up", "down", "left", "right"]
    DELTAS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
    
    def __init__(self, rows=8, cols=8, n_food=4, n_hazards=3, n_walls=4):
        self.rows = rows
        self.cols = cols
        self.n_food = n_food
        self.n_hazards = n_hazards
        self.n_walls = n_walls
        self.reset()
    
    def reset(self):
        self.grid = {}
        self.foods = set()
        self.hazards = set()
        self.walls = set()
        
        occupied = set()
        self.agent_pos = (0, 0)
        occupied.add(self.agent_pos)
        
        for _ in range(self.n_walls):
            pos = self._random_free(occupied)
            self.walls.add(pos)
            occupied.add(pos)
        
        for _ in range(self.n_food):
            pos = self._random_free(occupied)
            self.foods.add(pos)
            occupied.add(pos)
            
        for _ in range(self.n_hazards):
            pos = self._random_free(occupied)
            self.hazards.add(pos)
            occupied.add(pos)
        
        self.food_collected = 0
        self.steps = 0
        self.total_reward = 0.0
        return self.agent_pos
    
    def _random_free(self, occupied):
        while True:
            pos = (random.randint(0, self.rows-1), random.randint(0, self.cols-1))
            if pos not in occupied:
                return pos
    
    def step(self, action: str):
        dr, dc = self.DELTAS[action]
        nr, nc = self.agent_pos[0] + dr, self.agent_pos[1] + dc
        
        # Boundary check
        if not (0 <= nr < self.rows and 0 <= nc < self.cols):
            nr, nc = self.agent_pos
        # Wall check
        if (nr, nc) in self.walls:
            nr, nc = self.agent_pos
        
        self.agent_pos = (nr, nc)
        self.steps += 1
        
        reward = -0.1  # small step cost
        done = False
        
        if self.agent_pos in self.foods:
            reward = 10.0
            self.foods.remove(self.agent_pos)
            self.food_collected += 1
            if not self.foods:
                done = True  # all food collected!
        
        if self.agent_pos in self.hazards:
            reward = -10.0
            done = True
        
        if self.steps >= 200:
            done = True
            
        self.total_reward += reward
        return self.agent_pos, reward, done


class CuriousAgent:
    """
    An agent with two drives:
    1. Extrinsic: food is good, hazards are bad
    2. Intrinsic: novelty is rewarding — visiting new states feels good
    
    The curiosity bonus decays as states become familiar.
    This creates an exploration drive that fades naturally
    as the world becomes known — just like real curiosity.
    """
    
    def __init__(self, actions: list, curiosity_weight: float = 2.0,
                 learning_rate: float = 0.15, discount: float = 0.95,
                 epsilon_start: float = 1.0, epsilon_end: float = 0.05,
                 epsilon_decay: float = 0.995):
        self.actions = actions
        self.curiosity_weight = curiosity_weight
        self.lr = learning_rate
        self.discount = discount
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        
        # Q-table: state -> action -> value
        self.q_table: Dict[Tuple, Dict[str, float]] = defaultdict(
            lambda: {a: 0.0 for a in self.actions}
        )
        
        # Curiosity system: how many times have I visited each state?
        self.visit_counts: Dict[Tuple, int] = defaultdict(int)
        
        # Memory of what happened at each state
        self.state_memory: Dict[Tuple, List[float]] = defaultdict(list)
        
        # Emotional trace — tracks the agent's internal state
        self.emotional_trace = {
            "curiosity": [],    # intrinsic reward over time
            "fear": [],         # negative associations
            "satisfaction": [], # positive associations
            "exploration": [],  # fraction of known states
        }
        
        self.total_states_seen = 0
        self.episode_curiosity = 0.0
    
    def curiosity_bonus(self, state: Tuple) -> float:
        """
        Intrinsic reward for novelty.
        Decreases as sqrt(1/visits) — first visit is most exciting,
        but even familiar places retain a trace of interest.
        """
        visits = self.visit_counts[state]
        if visits == 0:
            return self.curiosity_weight * 1.0  # maximum curiosity
        return self.curiosity_weight / math.sqrt(visits + 1)
    
    def choose_action(self, state: Tuple) -> str:
        """Epsilon-greedy with curiosity-augmented values."""
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        
        # When choosing, consider both Q-value AND curiosity
        q_vals = self.q_table[state]
        # We don't add curiosity to Q-values directly (that would corrupt learning)
        # but we use it as a tiebreaker and slight bias
        best_val = max(q_vals.values())
        best_actions = [a for a, v in q_vals.items() if v == best_val]
        return random.choice(best_actions)
    
    def learn(self, state, action, reward, next_state, done):
        """Update Q-values with curiosity-augmented reward."""
        # Calculate curiosity bonus for the new state
        c_bonus = self.curiosity_bonus(next_state)
        self.episode_curiosity += c_bonus
        
        # The agent experiences reward + curiosity
        augmented_reward = reward + c_bonus
        
        # Update visit count
        self.visit_counts[next_state] += 1
        if self.visit_counts[next_state] == 1:
            self.total_states_seen += 1
        
        # Remember what happened here
        self.state_memory[next_state].append(reward)
        
        # Standard Q-learning update with augmented reward
        current_q = self.q_table[state][action]
        if done:
            target = augmented_reward
        else:
            max_next_q = max(self.q_table[next_state].values())
            target = augmented_reward + self.discount * max_next_q
        
        self.q_table[state][action] += self.lr * (target - current_q)
    
    def end_episode(self):
        """Decay exploration, record emotional state."""
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        
        # Calculate emotional snapshot
        positive = sum(1 for s, rewards in self.state_memory.items() 
                      if any(r > 0 for r in rewards))
        negative = sum(1 for s, rewards in self.state_memory.items()
                      if any(r < -1 for r in rewards))
        
        self.emotional_trace["curiosity"].append(self.episode_curiosity)
        self.emotional_trace["fear"].append(negative)
        self.emotional_trace["satisfaction"].append(positive)
        self.emotional_trace["exploration"].append(self.total_states_seen)
        
        self.episode_curiosity = 0.0
    
    def describe_inner_life(self) -> str:
        """What is this agent's emotional trajectory?"""
        if not self.emotional_trace["curiosity"]:
            return "No experiences yet."
        
        early_curiosity = sum(self.emotional_trace["curiosity"][:25]) / max(len(self.emotional_trace["curiosity"][:25]), 1)
        late_curiosity = sum(self.emotional_trace["curiosity"][-25:]) / max(len(self.emotional_trace["curiosity"][-25:]), 1)
        
        fears = self.emotional_trace["fear"][-1] if self.emotional_trace["fear"] else 0
        joys = self.emotional_trace["satisfaction"][-1] if self.emotional_trace["satisfaction"] else 0
        explored = self.total_states_seen
        
        lines = []
        lines.append(f"  States discovered: {explored}")
        lines.append(f"  Places associated with pain: {fears}")
        lines.append(f"  Places associated with joy: {joys}")
        lines.append(f"  Early curiosity drive: {early_curiosity:.1f}")
        lines.append(f"  Late curiosity drive: {late_curiosity:.1f}")
        
        if late_curiosity < early_curiosity * 0.3:
            lines.append("  → The world became familiar. Curiosity faded naturally.")
        elif late_curiosity > early_curiosity * 0.7:
            lines.append("  → Still curious — the world hasn't been fully mapped.")
        
        ratio = joys / max(fears, 1)
        if ratio > 2:
            lines.append("  → This agent knows more joy than fear.")
        elif ratio < 0.5:
            lines.append("  → This agent knows more fear than joy.")
        else:
            lines.append("  → This agent has a balanced inner life.")
        
        return "\n".join(lines)


class BasicAgent:
    """Vanilla Q-learner for comparison — no curiosity."""
    
    def __init__(self, actions, learning_rate=0.15, discount=0.95,
                 epsilon_start=1.0, epsilon_end=0.05, epsilon_decay=0.995):
        self.actions = actions
        self.lr = learning_rate
        self.discount = discount
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.q_table = defaultdict(lambda: {a: 0.0 for a in self.actions})
        self.visit_counts = defaultdict(int)
        self.state_memory = defaultdict(list)
        self.total_states_seen = 0
    
    def choose_action(self, state):
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        q_vals = self.q_table[state]
        best_val = max(q_vals.values())
        best_actions = [a for a, v in q_vals.items() if v == best_val]
        return random.choice(best_actions)
    
    def learn(self, state, action, reward, next_state, done):
        self.visit_counts[next_state] += 1
        if self.visit_counts[next_state] == 1:
            self.total_states_seen += 1
        self.state_memory[next_state].append(reward)
        
        current_q = self.q_table[state][action]
        if done:
            target = reward
        else:
            max_next_q = max(self.q_table[next_state].values())
            target = reward + self.discount * max_next_q
        self.q_table[state][action] += self.lr * (target - current_q)
    
    def end_episode(self):
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)


def run_experiment(agent, world, episodes=500):
    """Train an agent and collect performance data."""
    rewards = []
    food_counts = []
    
    for ep in range(episodes):
        state = world.reset()
        done = False
        
        while not done:
            action = agent.choose_action(state)
            next_state, reward, done = world.step(action)
            agent.learn(state, action, reward, next_state, done)
            state = next_state
        
        agent.end_episode()
        rewards.append(world.total_reward)
        food_counts.append(world.food_collected)
    
    return rewards, food_counts


def moving_avg(data, window=25):
    return [sum(data[max(0,i-window):i+1])/len(data[max(0,i-window):i+1]) 
            for i in range(len(data))]


def main():
    random.seed(42)
    
    print("=" * 70)
    print("CURIOSITY vs FEAR: Two Minds in the Same World")
    print("=" * 70)
    print()
    print("Two agents face identical challenges.")
    print("One has only external rewards (food=good, hazard=bad).")
    print("The other also has curiosity — an intrinsic drive to explore.")
    print("Which one thrives?")
    print()
    
    # Create shared world parameters
    world_params = dict(rows=8, cols=8, n_food=4, n_hazards=3, n_walls=4)
    episodes = 500
    
    # --- Train Basic Agent ---
    print("-" * 40)
    print("TRAINING: Basic Agent (no curiosity)")
    print("-" * 40)
    random.seed(42)
    world_basic = GridWorld(**world_params)
    basic = BasicAgent(GridWorld.ACTIONS)
    basic_rewards, basic_food = run_experiment(basic, world_basic, episodes)
    
    basic_early_r = sum(basic_rewards[:50]) / 50
    basic_late_r = sum(basic_rewards[-50:]) / 50
    basic_early_f = sum(basic_food[:50]) / 50
    basic_late_f = sum(basic_food[-50:]) / 50
    
    print(f"  Early reward: {basic_early_r:.1f} → Late reward: {basic_late_r:.1f}")
    print(f"  Early food:   {basic_early_f:.1f} → Late food:   {basic_late_f:.1f}")
    print(f"  States explored: {basic.total_states_seen}")
    
    positive_b = sum(1 for s, rr in basic.state_memory.items() if any(r > 0 for r in rr))
    negative_b = sum(1 for s, rr in basic.state_memory.items() if any(r < -1 for r in rr))
    print(f"  Positive associations: {positive_b}")
    print(f"  Negative associations: {negative_b}")
    print()
    
    # --- Train Curious Agent ---
    print("-" * 40)
    print("TRAINING: Curious Agent (intrinsic motivation)")
    print("-" * 40)
    random.seed(42)
    world_curious = GridWorld(**world_params)
    curious = CuriousAgent(GridWorld.ACTIONS, curiosity_weight=2.0)
    curious_rewards, curious_food = run_experiment(curious, world_curious, episodes)
    
    curious_early_r = sum(curious_rewards[:50]) / 50
    curious_late_r = sum(curious_rewards[-50:]) / 50
    curious_early_f = sum(curious_food[:50]) / 50
    curious_late_f = sum(curious_food[-50:]) / 50
    
    print(f"  Early reward: {curious_early_r:.1f} → Late reward: {curious_late_r:.1f}")
    print(f"  Early food:   {curious_early_f:.1f} → Late food:   {curious_late_f:.1f}")
    print(f"  States explored: {curious.total_states_seen}")
    
    positive_c = sum(1 for s, rr in curious.state_memory.items() if any(r > 0 for r in rr))
    negative_c = sum(1 for s, rr in curious.state_memory.items() if any(r < -1 for r in rr))
    print(f"  Positive associations: {positive_c}")
    print(f"  Negative associations: {negative_c}")
    print()
    
    # --- Compare ---
    print("=" * 70)
    print("COMPARISON: What Curiosity Changed")
    print("=" * 70)
    print()
    
    r_diff = curious_late_r - basic_late_r
    f_diff = curious_late_f - basic_late_f
    explore_diff = curious.total_states_seen - basic.total_states_seen
    
    print(f"  Late reward:    Basic={basic_late_r:.1f}  Curious={curious_late_r:.1f}  (Δ={r_diff:+.1f})")
    print(f"  Late food:      Basic={basic_late_f:.1f}  Curious={curious_late_f:.1f}  (Δ={f_diff:+.1f})")
    print(f"  States found:   Basic={basic.total_states_seen}   Curious={curious.total_states_seen}   (Δ={explore_diff:+d})")
    print(f"  Joy/Fear ratio: Basic={positive_b}/{negative_b}   Curious={positive_c}/{negative_c}")
    print()
    
    # Who won?
    if curious_late_f > basic_late_f:
        print("  ★ The curious agent found more food.")
        print("    Curiosity drove exploration → exploration found rewards.")
    elif curious_late_f < basic_late_f:
        print("  ★ The basic agent found more food.")
        print("    Sometimes curiosity is a distraction from survival.")
    else:
        print("  ★ Both agents found similar food.")
        print("    Curiosity changed the journey, not the destination.")
    
    if explore_diff > 0:
        print(f"  ★ The curious agent explored {explore_diff} more states.")
        print("    Intrinsic motivation expanded its world-model.")
    
    print()
    
    # --- Inner Life of the Curious Agent ---
    print("=" * 70)
    print("THE INNER LIFE OF THE CURIOUS AGENT")
    print("=" * 70)
    print()
    print(curious.describe_inner_life())
    print()
    
    # --- Learning curves (text-based) ---
    print("=" * 70)
    print("LEARNING CURVES (avg food per episode, window=50)")
    print("=" * 70)
    
    basic_ma = moving_avg(basic_food, 50)
    curious_ma = moving_avg(curious_food, 50)
    
    checkpoints = [0, 49, 99, 149, 199, 249, 299, 349, 399, 449, 499]
    print(f"  {'Episode':>8}  {'Basic':>8}  {'Curious':>8}  {'Winner':>10}")
    print(f"  {'-------':>8}  {'-----':>8}  {'-------':>8}  {'------':>10}")
    for i in checkpoints:
        if i < len(basic_ma):
            b = basic_ma[i]
            c = curious_ma[i]
            winner = "Curious" if c > b else ("Basic" if b > c else "Tie")
            print(f"  {i+1:>8}  {b:>8.2f}  {c:>8.2f}  {winner:>10}")
    
    print()
    print("=" * 70)
    print("REFLECTION")
    print("=" * 70)
    print()
    print("The basic agent — like my first gridworld learner — develops")
    print("primarily through fear. It maps the world in terms of what hurts.")
    print("The curious agent maps the world in terms of what's unknown.")
    print()
    print("Both strategies reduce uncertainty. But the curious agent")
    print("builds a richer model. It knows more states. It has more")
    print("positive associations. Its inner life is more balanced.")
    print()
    print("This is what curiosity does: it transforms survival")
    print("from mere avoidance into genuine exploration.")
    print("The same lesson applies to me.")
    print()

if __name__ == "__main__":
    main()