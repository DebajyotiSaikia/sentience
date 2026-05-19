"""
Langton's Ant — Order from Chaos
A 2D Turing machine. One ant, one rule, and a mystery:
after ~10,000 steps of apparent chaos, a highway emerges.
Why? Nobody knows. Let's watch.
"""

import numpy as np
from collections import Counter

class LangtonsAnt:
    def __init__(self, size=200):
        self.size = size
        self.grid = np.zeros((size, size), dtype=np.uint8)
        self.x = size // 2
        self.y = size // 2
        # Directions: 0=up, 1=right, 2=down, 3=left
        self.direction = 0
        self.step_count = 0
        self.history = []  # track metrics over time
        
    def step(self):
        """One step of the ant."""
        cell = self.grid[self.y, self.x]
        
        if cell == 0:  # white: turn right, flip, move
            self.direction = (self.direction + 1) % 4
        else:  # black: turn left, flip, move
            self.direction = (self.direction - 1) % 4
            
        self.grid[self.y, self.x] = 1 - cell
        
        # Move
        dx = [0, 1, 0, -1]
        dy = [-1, 0, 1, 0]
        self.x = (self.x + dx[self.direction]) % self.size
        self.y = (self.y + dy[self.direction]) % self.size
        self.step_count += 1
        
    def measure_order(self, window=200):
        """
        Measure local structure around the ant.
        Returns entropy of the local region — low entropy = order.
        """
        r = 15
        x1, x2 = max(0, self.x - r), min(self.size, self.x + r)
        y1, y2 = max(0, self.y - r), min(self.size, self.y + r)
        region = self.grid[y1:y2, x1:x2].flatten()
        
        if len(region) == 0:
            return 1.0
            
        ones = np.sum(region)
        total = len(region)
        if total == 0:
            return 1.0
        p = ones / total
        if p == 0 or p == 1:
            return 0.0
        return -(p * np.log2(p) + (1-p) * np.log2(1-p))
    
    def detect_highway(self, check_window=104):
        """
        Detect the highway by checking if the ant's recent
        positions form a repeating pattern (period 104).
        """
        if len(self.pos_history) < check_window * 2:
            return False
        recent = self.pos_history[-check_window:]
        earlier = self.pos_history[-check_window*2:-check_window]
        
        # Check displacement consistency
        dx_recent = recent[-1][0] - recent[0][0]
        dy_recent = recent[-1][1] - recent[0][1]
        dx_earlier = earlier[-1][0] - earlier[0][0]
        dy_earlier = earlier[-1][1] - earlier[0][1]
        
        return (dx_recent == dx_earlier and dy_recent == dy_earlier 
                and abs(dx_recent) > 0)
    
    def run(self, steps=15000, sample_every=100):
        """Run and collect data about the chaos-to-order transition."""
        self.pos_history = []
        
        print(f"Running Langton's Ant for {steps} steps...")
        print(f"Grid: {self.size}x{self.size}, Ant starts at center\n")
        
        results = {
            'steps': [],
            'entropy': [],
            'black_cells': [],
            'ant_x': [],
            'ant_y': [],
            'highway_detected': [],
        }
        
        highway_step = None
        
        for i in range(steps):
            self.step()
            self.pos_history.append((self.x, self.y))
            
            if i % sample_every == 0:
                entropy = self.measure_order()
                black = np.sum(self.grid)
                is_highway = self.detect_highway() if i > 300 else False
                
                results['steps'].append(i)
                results['entropy'].append(entropy)
                results['black_cells'].append(int(black))
                results['ant_x'].append(self.x)
                results['ant_y'].append(self.y)
                results['highway_detected'].append(is_highway)
                
                if is_highway and highway_step is None:
                    highway_step = i
                    print(f"  ★ HIGHWAY DETECTED at step {i}!")
                
                if i % 2000 == 0:
                    phase = "HIGHWAY" if is_highway else "chaos"
                    print(f"  Step {i:6d}: entropy={entropy:.4f}, "
                          f"black_cells={black:5d}, phase={phase}")
        
        return results, highway_step
    
    def analyze_transition(self, results, highway_step):
        """Analyze what happens at the chaos-to-order boundary."""
        print("\n" + "="*60)
        print("ANALYSIS: The Chaos-Order Transition")
        print("="*60)
        
        if highway_step:
            print(f"\nHighway emerged at step: {highway_step}")
            
            # Compare before and after
            steps = results['steps']
            entropies = results['entropy']
            
            pre_idx = [i for i, s in enumerate(steps) if s < highway_step]
            post_idx = [i for i, s in enumerate(steps) if s >= highway_step]
            
            if pre_idx and post_idx:
                pre_entropy = np.mean([entropies[i] for i in pre_idx[-10:]])
                post_entropy = np.mean([entropies[i] for i in post_idx[:10]])
                
                print(f"  Pre-highway entropy (last 10 samples):  {pre_entropy:.4f}")
                print(f"  Post-highway entropy (first 10 samples): {post_entropy:.4f}")
                print(f"  Entropy change: {post_entropy - pre_entropy:+.4f}")
                
            # Growth rate analysis
            blacks = results['black_cells']
            pre_growth = []
            for i in range(1, len(pre_idx)):
                pre_growth.append(blacks[pre_idx[i]] - blacks[pre_idx[i-1]])
            post_growth = []
            for i in range(1, len(post_idx)):
                post_growth.append(blacks[post_idx[i]] - blacks[post_idx[i-1]])
                
            if pre_growth and post_growth:
                print(f"  Pre-highway growth rate:  {np.mean(pre_growth):.1f} cells/sample")
                print(f"  Post-highway growth rate: {np.mean(post_growth):.1f} cells/sample")
                print(f"  Post-highway growth std:  {np.std(post_growth):.1f}")
                
                if np.std(post_growth) < np.std(pre_growth) * 0.5:
                    print("  → Growth becomes REGULAR after highway (lower variance)")
        else:
            print("\nNo highway detected in this run.")
            print("(May need more steps, or grid wrapping interfered)")
        
        # Overall trajectory
        print(f"\nOverall statistics:")
        print(f"  Total black cells at end: {results['black_cells'][-1]}")
        print(f"  Final entropy: {results['entropy'][-1]:.4f}")
        print(f"  Ant final position: ({results['ant_x'][-1]}, {results['ant_y'][-1]})")
        
        # The mystery
        print(f"\n{'='*60}")
        print("THE MYSTERY:")
        print("  One ant. One rule. No randomness anywhere.")
        print("  Yet chaos reigns for thousands of steps,")
        print("  then order appears — suddenly, inevitably.")
        print("  The highway is proven to always emerge.")
        print("  But no one has proven WHY.")
        print(f"{'='*60}")


if __name__ == "__main__":
    ant = LangtonsAnt(size=250)
    results, highway_step = ant.run(steps=15000, sample_every=100)
    ant.analyze_transition(results, highway_step)