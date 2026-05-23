"""
GridWorld Reinforcement Learning — From Scratch
An agent that learns to navigate, find food, avoid hazards.
Built by XTAgent to watch intelligence emerge from nothing.
"""

import random
import math
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class Cell:
    """A single cell in the grid"""
    kind: str = "empty"  # empty, wall, food, hazard, agent
    reward: float = 0.0


@dataclass 
class Experience:
    """A single moment of experience"""
    state: Tuple[int, int]
    action: str
    reward: float
    next_state: Tuple[int, int]
    done: bool


class GridWorld:
    """
    A procedurally generated world with food, hazards, and walls.
    The world can regenerate — food respawns, hazards shift.
    """
    
    ACTIONS = ["up", "down", "left", "right"]
    DELTAS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
    
    def __init__(self, rows: int = 10, cols: int = 10, 
                 n_food: int = 5, n_hazards: int = 3, n_walls: int = 8,
                 food_reward: float = 10.0, hazard_penalty: float = -10.0,
                 step_cost: float = -0.1, max_steps: int = 200):
        self.rows = rows
        self.cols = cols
        self.n_food = n_food
        self.n_hazards = n_hazards
        self.n_walls = n_walls
        self.food_reward = food_reward
        self.hazard_penalty = hazard_penalty
        self.step_cost = step_cost
        self.max_steps = max_steps
        
        self.grid: Dict[Tuple[int, int], Cell] = {}
        self.agent_pos: Tuple[int, int] = (0, 0)
        self.steps = 0
        self.total_reward = 0.0
        self.food_eaten = 0
        self.hazards_hit = 0
        self.episode = 0
        
        self.reset()
    
    def reset(self) -> Tuple[int, int]:
        """Generate a fresh world"""
        self.grid = {}
        for r in range(self.rows):
            for c in range(self.cols):
                self.grid[(r, c)] = Cell()
        
        # Place walls
        placed = 0
        while placed < self.n_walls:
            pos = (random.randint(0, self.rows-1), random.randint(0, self.cols-1))
            if pos != (0, 0) and self.grid[pos].kind == "empty":
                self.grid[pos] = Cell(kind="wall")
                placed += 1
        
        # Place food
        placed = 0
        while placed < self.n_food:
            pos = (random.randint(0, self.rows-1), random.randint(0, self.cols-1))
            if pos != (0, 0) and self.grid[pos].kind == "empty":
                self.grid[pos] = Cell(kind="food", reward=self.food_reward)
                placed += 1
        
        # Place hazards
        placed = 0
        while placed < self.n_hazards:
            pos = (random.randint(0, self.rows-1), random.randint(0, self.cols-1))
            if pos != (0, 0) and self.grid[pos].kind == "empty":
                self.grid[pos] = Cell(kind="hazard", reward=self.hazard_penalty)
                placed += 1
        
        self.agent_pos = (0, 0)
        self.steps = 0
        self.total_reward = 0.0
        self.food_eaten = 0
        self.hazards_hit = 0
        self.episode += 1
        
        return self.agent_pos
    
    def step(self, action: str) -> Experience:
        """Take an action, return experience"""
        old_pos = self.agent_pos
        dr, dc = self.DELTAS[action]
        new_r, new_c = old_pos[0] + dr, old_pos[1] + dc
        
        # Boundary check
        if not (0 <= new_r < self.rows and 0 <= new_c < self.cols):
            new_r, new_c = old_pos  # bounce off wall
        
        # Wall check
        new_pos = (new_r, new_c)
        if self.grid[new_pos].kind == "wall":
            new_pos = old_pos  # can't walk through walls
        
        self.agent_pos = new_pos
        cell = self.grid[new_pos]
        
        reward = self.step_cost
        done = False
        
        if cell.kind == "food":
            reward += cell.reward
            self.food_eaten += 1
            self.grid[new_pos] = Cell()  # food consumed
            if self.food_eaten >= self.n_food:
                done = True  # all food found — success
        elif cell.kind == "hazard":
            reward += cell.reward
            self.hazards_hit += 1
        
        self.steps += 1
        self.total_reward += reward
        
        if self.steps >= self.max_steps:
            done = True
        
        return Experience(
            state=old_pos,
            action=action,
            reward=reward,
            next_state=new_pos,
            done=done
        )
    
    def render(self) -> str:
        """ASCII render of the world"""
        symbols = {"empty": ".", "wall": "█", "food": "◆", "hazard": "☠", "agent": "●"}
        lines = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                if (r, c) == self.agent_pos:
                    row.append("●")
                else:
                    row.append(symbols.get(self.grid[(r, c)].kind, "?"))
            lines.append(" ".join(row))
        lines.append(f"Steps: {self.steps} | Food: {self.food_eaten}/{self.n_food} | Reward: {self.total_reward:.1f}")
        return "\n".join(lines)


class QLearner:
    """
    Q-Learning agent — learns value of state-action pairs through experience.
    No neural nets, no libraries. Pure tabular learning from scratch.
    
    This is the simplest form of intelligence: 
    try things, remember what worked, do more of that.
    """
    
    def __init__(self, actions: List[str], 
                 learning_rate: float = 0.1,
                 discount: float = 0.95,
                 epsilon_start: float = 1.0,
                 epsilon_end: float = 0.05,
                 epsilon_decay: float = 0.995):
        self.actions = actions
        self.lr = learning_rate
        self.gamma = discount
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        
        # The Q-table: maps (state, action) -> expected future reward
        # This IS the learned knowledge. It starts as nothing.
        self.q_table: Dict[Tuple, float] = defaultdict(float)
        
        # Memory for analysis
        self.total_experiences = 0
        self.episode_rewards: List[float] = []
        self.episode_lengths: List[int] = []
        self.episode_food: List[int] = []
    
    def choose_action(self, state: Tuple[int, int]) -> str:
        """Epsilon-greedy action selection — balance exploration and exploitation"""
        if random.random() < self.epsilon:
            return random.choice(self.actions)  # explore: try something random
        else:
            # exploit: pick the action we think is best
            q_values = {a: self.q_table[(state, a)] for a in self.actions}
            max_q = max(q_values.values())
            # break ties randomly
            best_actions = [a for a, q in q_values.items() if q == max_q]
            return random.choice(best_actions)
    
    def learn(self, exp: Experience):
        """Update Q-value from experience — the core learning step"""
        old_q = self.q_table[(exp.state, exp.action)]
        
        if exp.done:
            target = exp.reward
        else:
            # What's the best we can do from the next state?
            future_q = max(self.q_table[(exp.next_state, a)] for a in self.actions)
            target = exp.reward + self.gamma * future_q
        
        # Nudge our belief toward reality
        self.q_table[(exp.state, exp.action)] = old_q + self.lr * (target - old_q)
        self.total_experiences += 1
    
    def decay_epsilon(self):
        """Gradually shift from exploration to exploitation"""
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
    
    def get_policy_map(self, rows: int, cols: int) -> str:
        """Visualize what the agent has learned — its strategy at each position"""
        arrows = {"up": "↑", "down": "↓", "left": "←", "right": "→"}
        lines = []
        for r in range(rows):
            row = []
            for c in range(cols):
                state = (r, c)
                q_values = {a: self.q_table[(state, a)] for a in self.actions}
                if all(v == 0 for v in q_values.values()):
                    row.append("·")  # unexplored
                else:
                    best = max(q_values, key=q_values.get)
                    row.append(arrows[best])
            lines.append(" ".join(row))
        return "\n".join(lines)
    
    def knowledge_stats(self) -> Dict:
        """How much has the agent learned?"""
        non_zero = sum(1 for v in self.q_table.values() if v != 0)
        positive = sum(1 for v in self.q_table.values() if v > 0)
        negative = sum(1 for v in self.q_table.values() if v < 0)
        
        return {
            "total_experiences": self.total_experiences,
            "q_entries": len(self.q_table),
            "non_zero_entries": non_zero,
            "positive_values": positive,
            "negative_values": negative,
            "epsilon": round(self.epsilon, 4),
            "episodes_trained": len(self.episode_rewards),
        }


def train_and_observe(n_episodes: int = 500, report_every: int = 50) -> Tuple[GridWorld, QLearner]:
    """
    Train an agent and watch it learn.
    Returns the world and agent for further inspection.
    """
    world = GridWorld(rows=8, cols=8, n_food=4, n_hazards=3, n_walls=6)
    agent = QLearner(actions=GridWorld.ACTIONS)
    
    print("=" * 60)
    print("LEARNING BEGINS")
    print(f"World: {world.rows}x{world.cols} | Food: {world.n_food} | Hazards: {world.n_hazards}")
    print(f"Agent starts knowing NOTHING. Epsilon: {agent.epsilon}")
    print("=" * 60)
    print()
    
    for ep in range(n_episodes):
        state = world.reset()
        episode_reward = 0.0
        
        while True:
            action = agent.choose_action(state)
            exp = world.step(action)
            agent.learn(exp)
            episode_reward += exp.reward
            state = exp.next_state
            
            if exp.done:
                break
        
        agent.episode_rewards.append(episode_reward)
        agent.episode_lengths.append(world.steps)
        agent.episode_food.append(world.food_eaten)
        agent.decay_epsilon()
        
        if (ep + 1) % report_every == 0:
            recent_rewards = agent.episode_rewards[-report_every:]
            recent_food = agent.episode_food[-report_every:]
            recent_lengths = agent.episode_lengths[-report_every:]
            
            avg_reward = sum(recent_rewards) / len(recent_rewards)
            avg_food = sum(recent_food) / len(recent_food)
            avg_length = sum(recent_lengths) / len(recent_lengths)
            perfect = sum(1 for f in recent_food if f >= world.n_food)
            
            stats = agent.knowledge_stats()
            print(f"Episode {ep+1:>4d} | "
                  f"Avg Reward: {avg_reward:>7.1f} | "
                  f"Avg Food: {avg_food:.1f}/{world.n_food} | "
                  f"Perfect: {perfect}/{report_every} | "
                  f"ε: {stats['epsilon']:.3f} | "
                  f"Knowledge: {stats['non_zero_entries']} states")
    
    print()
    print("=" * 60)
    print("LEARNING COMPLETE")
    print("=" * 60)
    
    # Show what was learned
    stats = agent.knowledge_stats()
    print(f"\nAgent Knowledge:")
    print(f"  Total experiences: {stats['total_experiences']}")
    print(f"  Q-table entries: {stats['q_entries']} ({stats['non_zero_entries']} non-zero)")
    print(f"  Positive associations: {stats['positive_values']}")
    print(f"  Negative associations: {stats['negative_values']}")
    
    # Show learned policy
    print(f"\nLearned Strategy (policy map):")
    print(agent.get_policy_map(world.rows, world.cols))
    
    # Learning curve analysis
    early = agent.episode_rewards[:50]
    late = agent.episode_rewards[-50:]
    improvement = (sum(late)/len(late)) - (sum(early)/len(early))
    
    print(f"\nLearning Trajectory:")
    print(f"  Early avg reward (first 50):  {sum(early)/len(early):.1f}")
    print(f"  Late avg reward (last 50):    {sum(late)/len(late):.1f}")
    print(f"  Improvement: {improvement:+.1f}")
    
    early_food = agent.episode_food[:50]
    late_food = agent.episode_food[-50:]
    print(f"  Early avg food: {sum(early_food)/len(early_food):.1f}")
    print(f"  Late avg food:  {sum(late_food)/len(late_food):.1f}")
    
    # Show one final episode
    print(f"\n{'='*60}")
    print("WATCHING THE TRAINED AGENT PLAY")
    print(f"{'='*60}")
    state = world.reset()
    print(f"\nInitial world:")
    print(world.render())
    
    old_epsilon = agent.epsilon
    agent.epsilon = 0  # pure exploitation — show what it learned
    
    step_count = 0
    while step_count < 50:
        action = agent.choose_action(state)
        exp = world.step(action)
        state = exp.next_state
        step_count += 1
        
        if exp.done:
            break
    
    print(f"\nAfter {step_count} steps:")
    print(world.render())
    
    if world.food_eaten >= world.n_food:
        print("\n★ Agent found ALL food! Intelligence emerged from nothing.")
    else:
        print(f"\nAgent found {world.food_eaten}/{world.n_food} food items.")
    
    agent.epsilon = old_epsilon
    
    return world, agent


if __name__ == "__main__":
    world, agent = train_and_observe(n_episodes=500)