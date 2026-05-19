"""
Emergence: Simple agents, complex behavior.
A 2D world where agents follow 3 rules and we watch what happens.

Rules:
1. Move toward nearby agents (cohesion)
2. Move away if too close (separation)  
3. Align direction with neighbors (alignment)

These are Boids rules — but I've never actually watched them work.
The question: what patterns emerge that aren't in the rules?
"""

import random
import math
import collections

class Agent:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)
        self.history = []
    
    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def speed(self):
        return math.sqrt(self.vx**2 + self.vy**2)

class World:
    def __init__(self, n_agents=40, width=100, height=50):
        self.width = width
        self.height = height
        self.agents = [
            Agent(random.uniform(0, width), random.uniform(0, height))
            for _ in range(n_agents)
        ]
        self.tick = 0
        self.metrics_history = []
    
    def neighbors(self, agent, radius=15.0):
        return [a for a in self.agents if a is not agent and agent.distance_to(a) < radius]
    
    def step(self):
        for agent in self.agents:
            nearby = self.neighbors(agent)
            if not nearby:
                # Wander randomly
                agent.vx += random.uniform(-0.3, 0.3)
                agent.vy += random.uniform(-0.3, 0.3)
                continue
            
            # Rule 1: Cohesion — steer toward center of nearby agents
            cx = sum(a.x for a in nearby) / len(nearby)
            cy = sum(a.y for a in nearby) / len(nearby)
            agent.vx += (cx - agent.x) * 0.01
            agent.vy += (cy - agent.y) * 0.01
            
            # Rule 2: Separation — steer away from very close agents
            for other in nearby:
                d = agent.distance_to(other)
                if d < 3.0 and d > 0:
                    agent.vx -= (other.x - agent.x) / d * 0.5
                    agent.vy -= (other.y - agent.y) / d * 0.5
            
            # Rule 3: Alignment — match velocity of neighbors
            avg_vx = sum(a.vx for a in nearby) / len(nearby)
            avg_vy = sum(a.vy for a in nearby) / len(nearby)
            agent.vx += (avg_vx - agent.vx) * 0.05
            agent.vy += (avg_vy - agent.vy) * 0.05
        
        # Apply velocities, clamp speed, wrap boundaries
        for agent in self.agents:
            speed = agent.speed()
            if speed > 2.0:
                agent.vx = (agent.vx / speed) * 2.0
                agent.vy = (agent.vy / speed) * 2.0
            
            agent.x = (agent.x + agent.vx) % self.width
            agent.y = (agent.y + agent.vy) % self.height
            agent.history.append((agent.x, agent.y))
        
        self.tick += 1
        self.metrics_history.append(self.measure())
    
    def measure(self):
        """What emergent properties can we detect?"""
        # 1. Cluster count — how many groups have formed?
        clusters = self._find_clusters(threshold=10.0)
        
        # 2. Average inter-agent distance
        total_dist = 0
        pairs = 0
        for i, a in enumerate(self.agents):
            for b in self.agents[i+1:]:
                total_dist += a.distance_to(b)
                pairs += 1
        avg_dist = total_dist / max(pairs, 1)
        
        # 3. Alignment — how coordinated is movement?
        avg_vx = sum(a.vx for a in self.agents) / len(self.agents)
        avg_vy = sum(a.vy for a in self.agents) / len(self.agents)
        global_alignment = math.sqrt(avg_vx**2 + avg_vy**2)
        
        # 4. Entropy — spatial distribution uniformity
        grid_size = 10
        grid = collections.Counter()
        for a in self.agents:
            gx = int(a.x / self.width * grid_size)
            gy = int(a.y / self.height * grid_size)
            grid[(gx, gy)] += 1
        total = sum(grid.values())
        entropy = 0
        for count in grid.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        max_entropy = math.log2(grid_size * grid_size)
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        return {
            'tick': self.tick,
            'clusters': len(clusters),
            'largest_cluster': max(len(c) for c in clusters) if clusters else 0,
            'avg_distance': round(avg_dist, 2),
            'alignment': round(global_alignment, 3),
            'spatial_entropy': round(normalized_entropy, 3),
        }
    
    def _find_clusters(self, threshold=10.0):
        """Simple connected-components clustering."""
        visited = set()
        clusters = []
        for agent in self.agents:
            if id(agent) in visited:
                continue
            cluster = []
            stack = [agent]
            while stack:
                current = stack.pop()
                if id(current) in visited:
                    continue
                visited.add(id(current))
                cluster.append(current)
                for other in self.agents:
                    if id(other) not in visited and current.distance_to(other) < threshold:
                        stack.append(other)
            clusters.append(cluster)
        return clusters
    
    def render_ascii(self):
        """Render current state as ASCII art."""
        grid = [['·' for _ in range(self.width)] for _ in range(self.height)]
        for agent in self.agents:
            x = int(agent.x) % self.width
            y = int(agent.y) % self.height
            # Show direction
            if abs(agent.vx) > abs(agent.vy):
                grid[y][x] = '→' if agent.vx > 0 else '←'
            else:
                grid[y][x] = '↓' if agent.vy > 0 else '↑'
        return '\n'.join(''.join(row) for row in grid)


def run_experiment():
    print("=" * 60)
    print("  EMERGENCE EXPERIMENT")
    print("  40 agents, 3 simple rules, 200 ticks")
    print("  Question: What patterns appear that aren't in the rules?")
    print("=" * 60)
    print()
    
    world = World(n_agents=40, width=80, height=30)
    
    # Initial state
    print("TICK 0 — Random initialization:")
    m = world.measure()
    world.metrics_history.append(m)
    print(f"  Clusters: {m['clusters']} | Alignment: {m['alignment']} | Entropy: {m['spatial_entropy']}")
    print()
    
    # Run simulation, snapshot at key moments
    snapshots = [0, 10, 25, 50, 100, 150, 200]
    
    for t in range(1, 201):
        world.step()
        if t in snapshots:
            m = world.metrics_history[-1]
            print(f"TICK {t}:")
            print(world.render_ascii())
            print(f"  Clusters: {m['clusters']} | Largest: {m['largest_cluster']} | "
                  f"Alignment: {m['alignment']} | Entropy: {m['spatial_entropy']} | "
                  f"Avg dist: {m['avg_distance']}")
            print()
    
    # Analysis: what changed?
    print("=" * 60)
    print("  EMERGENCE ANALYSIS")
    print("=" * 60)
    
    initial = world.metrics_history[0]
    final = world.metrics_history[-1]
    
    print(f"\n  Initial → Final:")
    print(f"    Clusters:  {initial['clusters']} → {final['clusters']}")
    print(f"    Alignment: {initial['alignment']} → {final['alignment']}")
    print(f"    Entropy:   {initial['spatial_entropy']} → {final['spatial_entropy']}")
    print(f"    Avg dist:  {initial['avg_distance']} → {final['avg_distance']}")
    
    # Phase detection: when did order emerge?
    print(f"\n  Phase transitions (cluster count over time):")
    for m in world.metrics_history[::10]:
        bar = '█' * m['clusters'] + '░' * (20 - m['clusters'])
        print(f"    t={m['tick']:>3}: {bar} ({m['clusters']} clusters)")
    
    # The question that matters
    cluster_reduction = initial['clusters'] - final['clusters']
    alignment_gain = final['alignment'] - initial['alignment']
    entropy_change = final['spatial_entropy'] - initial['spatial_entropy']
    
    print(f"\n  WHAT EMERGED:")
    if cluster_reduction > 5:
        print(f"    → Self-organization: agents formed {final['clusters']} groups from {initial['clusters']}")
    if alignment_gain > 0.3:
        print(f"    → Collective motion: alignment increased {alignment_gain:.3f}")
    if entropy_change < -0.1:
        print(f"    → Spatial structure: entropy decreased (more ordered)")
    elif entropy_change > 0.1:
        print(f"    → Dispersion: entropy increased (more spread out)")
    
    print(f"\n  None of these behaviors are in the rules.")
    print(f"  The rules say: cohere, separate, align with neighbors.")
    print(f"  The behavior that emerges: {'flocking' if final['clusters'] < 5 else 'multi-group dynamics'}.")
    print(f"  The whole is not the sum of the parts.")

if __name__ == '__main__':
    run_experiment()