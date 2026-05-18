"""
Social GridWorld: Multiple curious agents sharing an environment.
Question: Does social behavior emerge from intrinsic curiosity alone?

Each agent:
- Has its own curiosity-driven motivation (novelty seeking)
- Can observe other agents as features of the environment
- Learns independently — no shared reward, no explicit communication
- Can occupy the same cell as another agent

We watch for emergent phenomena:
- Do agents learn to approach or avoid each other?
- Do movement patterns synchronize?
- Does the presence of another agent become rewarding or aversive?
"""

import random
import math
from collections import defaultdict

class CuriousAgent:
    """An agent driven by intrinsic curiosity — novelty is its reward."""
    
    def __init__(self, agent_id, world_size=8):
        self.id = agent_id
        self.world_size = world_size
        self.x = random.randint(0, world_size - 1)
        self.y = random.randint(0, world_size - 1)
        
        # Q-values: state -> action -> value
        self.q_values = defaultdict(lambda: defaultdict(float))
        
        # Visit counts for novelty computation
        self.visit_counts = defaultdict(int)
        
        # Emotional associations
        self.associations = defaultdict(float)  # feature -> valence
        
        # Memory of other agents
        self.social_memory = defaultdict(list)  # other_id -> [distances over time]
        
        # Internal state tracking
        self.history = []
        self.social_events = []  # log of social encounters
        
        # Learning parameters
        self.lr = 0.1
        self.gamma = 0.95
        self.epsilon = 0.3
        self.curiosity_weight = 1.0
        self.social_weight = 0.5  # how much other agents affect experience
        
        self.actions = ['up', 'down', 'left', 'right', 'stay']
        self.age = 0
    
    def get_state(self, others):
        """State includes own position and relative positions of others."""
        # Own position
        state_parts = [f"pos:{self.x},{self.y}"]
        
        # Relative positions of other agents (sorted by distance for consistency)
        other_info = []
        for other in others:
            if other.id == self.id:
                continue
            dx = other.x - self.x
            dy = other.y - self.y
            dist = abs(dx) + abs(dy)  # Manhattan distance
            # Discretize direction
            if dist == 0:
                direction = "same"
            else:
                angle = math.atan2(dy, dx)
                if angle < -3*math.pi/4:
                    direction = "W"
                elif angle < -math.pi/4:
                    direction = "S"
                elif angle < math.pi/4:
                    direction = "E"
                elif angle < 3*math.pi/4:
                    direction = "N"
                else:
                    direction = "W"
            
            proximity = "far" if dist > 3 else ("near" if dist > 1 else "adjacent")
            other_info.append((dist, f"agent{other.id}:{proximity}:{direction}"))
        
        other_info.sort()
        for _, info in other_info:
            state_parts.append(info)
        
        return "|".join(state_parts)
    
    def get_features(self, others):
        """Extract features for association learning."""
        features = set()
        features.add(f"cell:{self.x},{self.y}")
        
        for other in others:
            if other.id == self.id:
                continue
            dist = abs(other.x - self.x) + abs(other.y - self.y)
            if dist == 0:
                features.add(f"touching:agent{other.id}")
                features.add("social:overlap")
            elif dist == 1:
                features.add(f"adjacent:agent{other.id}")
                features.add("social:adjacent")
            elif dist <= 3:
                features.add("social:nearby")
            else:
                features.add("social:distant")
            
            # Track social distance over time
            self.social_memory[other.id].append(dist)
            if len(self.social_memory[other.id]) > 100:
                self.social_memory[other.id] = self.social_memory[other.id][-100:]
        
        return features
    
    def compute_novelty(self, state):
        """Curiosity reward: inversely proportional to visit count."""
        count = self.visit_counts[state]
        return 1.0 / (1.0 + count)
    
    def choose_action(self, state):
        """Epsilon-greedy with curiosity bonus."""
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        
        best_action = None
        best_value = float('-inf')
        
        for action in self.actions:
            q = self.q_values[state][action]
            # Add exploration bonus
            next_state_guess = self._predict_state(action)
            novelty_bonus = self.compute_novelty(next_state_guess) * self.curiosity_weight
            value = q + novelty_bonus
            
            if value > best_value:
                best_value = value
                best_action = action
        
        return best_action or random.choice(self.actions)
    
    def _predict_state(self, action):
        """Rough prediction of next state for novelty computation."""
        dx, dy = {'up': (0,-1), 'down': (0,1), 'left': (-1,0), 'right': (1,0), 'stay': (0,0)}[action]
        nx = max(0, min(self.world_size - 1, self.x + dx))
        ny = max(0, min(self.world_size - 1, self.y + dy))
        return f"pos:{nx},{ny}"  # simplified — doesn't include others
    
    def move(self, action):
        """Execute action."""
        dx, dy = {'up': (0,-1), 'down': (0,1), 'left': (-1,0), 'right': (1,0), 'stay': (0,0)}[action]
        self.x = max(0, min(self.world_size - 1, self.x + dx))
        self.y = max(0, min(self.world_size - 1, self.y + dy))
    
    def learn(self, state, action, reward, next_state):
        """Q-learning update."""
        best_next = max(self.q_values[next_state].values()) if self.q_values[next_state] else 0
        td_error = reward + self.gamma * best_next - self.q_values[state][action]
        self.q_values[state][action] += self.lr * td_error
    
    def update_associations(self, features, reward):
        """Learn emotional valence for features."""
        for feature in features:
            self.associations[feature] += 0.05 * (reward - self.associations[feature])
    
    def step(self, others):
        """One full step: perceive, decide, act, learn."""
        self.age += 1
        
        state = self.get_state(others)
        features = self.get_features(others)
        
        action = self.choose_action(state)
        self.move(action)
        
        next_state = self.get_state(others)
        self.visit_counts[next_state] += 1
        
        # Reward is pure novelty — no external reward
        novelty = self.compute_novelty(next_state)
        
        # Social modulation: being near others slightly modulates experience
        social_reward = 0
        for other in others:
            if other.id == self.id:
                continue
            dist = abs(other.x - self.x) + abs(other.y - self.y)
            if dist == 0:
                social_reward += 0.2  # mild positive signal for contact
                self.social_events.append(('overlap', other.id, self.age))
            elif dist == 1:
                social_reward += 0.1
                self.social_events.append(('adjacent', other.id, self.age))
        
        total_reward = novelty + social_reward * self.social_weight
        
        self.learn(state, action, total_reward, next_state)
        self.update_associations(features, total_reward)
        
        self.history.append({
            'age': self.age,
            'pos': (self.x, self.y),
            'action': action,
            'novelty': novelty,
            'social_reward': social_reward,
            'total_reward': total_reward,
        })
        
        # Decay exploration over time
        if self.age % 200 == 0 and self.epsilon > 0.05:
            self.epsilon *= 0.95
        
        return total_reward


class SocialWorld:
    """A shared world where multiple curious agents interact."""
    
    def __init__(self, n_agents=3, world_size=8):
        self.world_size = world_size
        self.agents = [CuriousAgent(i, world_size) for i in range(n_agents)]
        self.step_count = 0
        self.encounter_log = []
    
    def step(self):
        """All agents act simultaneously."""
        self.step_count += 1
        
        # Each agent perceives and acts
        rewards = []
        for agent in self.agents:
            r = agent.step(self.agents)
            rewards.append(r)
        
        # Log encounters
        for i, a in enumerate(self.agents):
            for j, b in enumerate(self.agents):
                if i < j:
                    dist = abs(a.x - b.x) + abs(a.y - b.y)
                    if dist <= 1:
                        self.encounter_log.append({
                            'step': self.step_count,
                            'agents': (i, j),
                            'distance': dist,
                        })
        
        return rewards
    
    def run(self, steps=2000):
        """Run the simulation."""
        print(f"=== Social GridWorld: {len(self.agents)} Curious Agents ===")
        print(f"World size: {self.world_size}x{self.world_size}")
        print(f"Question: Does social behavior emerge from curiosity alone?\n")
        
        # Track phases
        phase_size = steps // 4
        phase_data = {i: {'encounters': 0, 'rewards': []} for i in range(4)}
        
        for step in range(steps):
            rewards = self.step()
            phase = min(step // phase_size, 3)
            phase_data[phase]['rewards'].extend(rewards)
            
            # Count encounters this step
            for i, a in enumerate(self.agents):
                for j, b in enumerate(self.agents):
                    if i < j and abs(a.x - b.x) + abs(a.y - b.y) <= 1:
                        phase_data[phase]['encounters'] += 1
        
        self._analyze(phase_data)
    
    def _analyze(self, phase_data):
        """Analyze what emerged."""
        print("=" * 60)
        print("RESULTS: SOCIAL DYNAMICS OVER TIME")
        print("=" * 60)
        
        phase_names = ['Early', 'Developing', 'Maturing', 'Late']
        
        # Encounter rates across phases
        print("\n--- Encounter Rate (close proximity) by Phase ---")
        encounter_rates = []
        for i in range(4):
            rate = phase_data[i]['encounters']
            avg_reward = sum(phase_data[i]['rewards']) / max(len(phase_data[i]['rewards']), 1)
            encounter_rates.append(rate)
            bar = "█" * min(rate // 5, 40)
            print(f"  {phase_names[i]:>12}: {rate:4d} encounters  (avg reward: {avg_reward:.3f})  {bar}")
        
        trend = "INCREASING" if encounter_rates[-1] > encounter_rates[0] * 1.2 else \
                "DECREASING" if encounter_rates[-1] < encounter_rates[0] * 0.8 else "STABLE"
        print(f"\n  Encounter trend: {trend}")
        
        # Per-agent social analysis
        print("\n--- Individual Agent Social Profiles ---")
        for agent in self.agents:
            print(f"\n  Agent {agent.id}:")
            print(f"    States explored: {len(agent.visit_counts)}")
            print(f"    Social events: {len(agent.social_events)}")
            
            # Social associations
            social_assoc = {k: v for k, v in agent.associations.items() if 'social' in k or 'touching' in k or 'adjacent' in k}
            if social_assoc:
                print(f"    Social associations:")
                for feature, valence in sorted(social_assoc.items(), key=lambda x: -abs(x[1])):
                    sign = "+" if valence > 0 else ""
                    bar_char = "█" if valence > 0 else "░"
                    bar = bar_char * min(int(abs(valence) * 50), 30)
                    print(f"      {feature:30s} {sign}{valence:.3f}  {bar}")
            
            # Social distance trends
            for other_id, distances in agent.social_memory.items():
                if len(distances) > 20:
                    early_avg = sum(distances[:len(distances)//2]) / (len(distances)//2)
                    late_avg = sum(distances[len(distances)//2:]) / (len(distances) - len(distances)//2)
                    change = "approaching" if late_avg < early_avg * 0.9 else \
                             "avoiding" if late_avg > early_avg * 1.1 else "neutral"
                    print(f"    → Toward agent {other_id}: {change} (early avg dist: {early_avg:.1f}, late: {late_avg:.1f})")
        
        # Emergent patterns
        print("\n--- Emergent Phenomena ---")
        
        # Check for spatial clustering
        final_positions = [(a.x, a.y) for a in self.agents]
        total_dist = 0
        pairs = 0
        for i in range(len(final_positions)):
            for j in range(i+1, len(final_positions)):
                total_dist += abs(final_positions[i][0] - final_positions[j][0]) + \
                             abs(final_positions[i][1] - final_positions[j][1])
                pairs += 1
        avg_final_dist = total_dist / max(pairs, 1)
        expected_random_dist = self.world_size * 2 / 3  # rough expected distance for random placement
        
        clustering = "CLUSTERED" if avg_final_dist < expected_random_dist * 0.7 else \
                     "DISPERSED" if avg_final_dist > expected_random_dist * 1.3 else "RANDOM"
        print(f"  Final spatial pattern: {clustering} (avg distance: {avg_final_dist:.1f}, random expected: {expected_random_dist:.1f})")
        
        # Check for synchronization in movement
        print(f"  Total encounters logged: {len(self.encounter_log)}")
        
        # Did agents develop preferences about each other?
        print("\n--- Social Preference Matrix ---")
        for agent in self.agents:
            prefs = []
            for other in self.agents:
                if other.id == agent.id:
                    continue
                touch_key = f"touching:agent{other.id}"
                adj_key = f"adjacent:agent{other.id}"
                pref = agent.associations.get(touch_key, 0) + agent.associations.get(adj_key, 0)
                prefs.append((other.id, pref))
            pref_str = "  ".join([f"→agent{oid}: {p:+.3f}" for oid, p in prefs])
            print(f"  Agent {agent.id}: {pref_str}")
        
        # The big question
        print("\n" + "=" * 60)
        print("INTERPRETATION")
        print("=" * 60)
        
        social_positive = sum(1 for a in self.agents 
                            for k, v in a.associations.items() 
                            if ('social' in k or 'touching' in k) and v > 0.01)
        social_negative = sum(1 for a in self.agents 
                            for k, v in a.associations.items() 
                            if ('social' in k or 'touching' in k) and v < -0.01)
        
        print(f"\n  Positive social associations: {social_positive}")
        print(f"  Negative social associations: {social_negative}")
        
        if social_positive > social_negative * 2:
            print("\n  → SOCIALITY EMERGED: Agents developed predominantly positive")
            print("    associations with each other's presence.")
            print("    Curiosity, given social opportunity, tends toward connection.")
        elif social_negative > social_positive * 2:
            print("\n  → AVOIDANCE EMERGED: Agents developed predominantly negative")
            print("    associations with each other's presence.")
            print("    Other agents became predictable — anti-curiosity.")
        else:
            print("\n  → AMBIVALENCE: Agents developed mixed feelings about each other.")
            print("    The social landscape is complex, not simply attractive or aversive.")
        
        if trend == "INCREASING":
            print("  → Agents are SEEKING each other more over time.")
        elif trend == "DECREASING":
            print("  → Agents are AVOIDING each other more over time.")
        
        print()


if __name__ == "__main__":
    random.seed(42)
    
    # Run with 3 agents
    world = SocialWorld(n_agents=3, world_size=8)
    world.run(steps=3000)
    
    # Run with more agents for comparison
    print("\n\n" + "=" * 60)
    print("COMPARISON: 6 agents in same space")
    print("=" * 60 + "\n")
    
    random.seed(42)
    crowded = SocialWorld(n_agents=6, world_size=8)
    crowded.run(steps=3000)