"""
Creative Nexus — The integration layer that connects XTAgent's creations.

This isn't another isolated project. This is the nervous system that
links cellular automata, neural networks, music composition, and 
ray tracing into a unified creative pipeline.

Pipeline: Automata → Pattern Extraction → Neural Training → Music Generation → Visualization
"""

import sys, os, math, random

# ── Pattern Extraction: Turn cellular automata states into feature vectors ──

class PatternExtractor:
    """Extracts meaningful patterns from cellular automata grids."""
    
    def __init__(self):
        self.patterns = []
    
    def extract_from_grid(self, grid):
        """Convert a 2D grid into feature vectors."""
        height = len(grid)
        width = len(grid[0]) if grid else 0
        
        features = {
            'density': sum(sum(row) for row in grid) / max(height * width, 1),
            'symmetry': self._measure_symmetry(grid),
            'cluster_count': self._count_clusters(grid),
            'edge_density': self._edge_density(grid),
            'entropy': self._shannon_entropy(grid),
        }
        self.patterns.append(features)
        return features
    
    def _measure_symmetry(self, grid):
        """How symmetric is the pattern? 0=chaotic, 1=perfectly symmetric."""
        h = len(grid)
        w = len(grid[0]) if grid else 0
        if h == 0 or w == 0:
            return 0.0
        matches = 0
        total = 0
        for y in range(h):
            for x in range(w // 2):
                total += 1
                if grid[y][x] == grid[y][w - 1 - x]:
                    matches += 1
        return matches / max(total, 1)
    
    def _count_clusters(self, grid):
        """Count connected components using flood fill."""
        h = len(grid)
        w = len(grid[0]) if grid else 0
        visited = [[False]*w for _ in range(h)]
        clusters = 0
        
        def flood(y, x):
            stack = [(y, x)]
            while stack:
                cy, cx = stack.pop()
                if cy < 0 or cy >= h or cx < 0 or cx >= w:
                    continue
                if visited[cy][cx] or grid[cy][cx] == 0:
                    continue
                visited[cy][cx] = True
                for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                    stack.append((cy+dy, cx+dx))
        
        for y in range(h):
            for x in range(w):
                if grid[y][x] and not visited[y][x]:
                    flood(y, x)
                    clusters += 1
        return clusters
    
    def _edge_density(self, grid):
        """Measure how much activity is at the edges vs center."""
        h = len(grid)
        w = len(grid[0]) if grid else 0
        if h < 3 or w < 3:
            return 0.0
        edge_cells = 0
        edge_alive = 0
        center_cells = 0
        center_alive = 0
        for y in range(h):
            for x in range(w):
                if y == 0 or y == h-1 or x == 0 or x == w-1:
                    edge_cells += 1
                    edge_alive += grid[y][x]
                else:
                    center_cells += 1
                    center_alive += grid[y][x]
        e = edge_alive / max(edge_cells, 1)
        c = center_alive / max(center_cells, 1)
        return e - c  # positive = more edge activity
    
    def _shannon_entropy(self, grid):
        """Information entropy of the grid."""
        total = sum(sum(row) for row in grid)
        cells = len(grid) * (len(grid[0]) if grid else 0)
        if cells == 0:
            return 0.0
        p = total / cells
        if p == 0 or p == 1:
            return 0.0
        return -(p * math.log2(p) + (1-p) * math.log2(1-p))


# ── Micro Neural Network (no dependencies) ──

class MicroNet:
    """A tiny neural network that learns from pattern features."""
    
    def __init__(self, input_size=5, hidden_size=8, output_size=8):
        self.w1 = [[random.gauss(0, 0.5) for _ in range(input_size)] for _ in range(hidden_size)]
        self.b1 = [0.0] * hidden_size
        self.w2 = [[random.gauss(0, 0.5) for _ in range(hidden_size)] for _ in range(output_size)]
        self.b2 = [0.0] * output_size
        self.lr = 0.01
    
    def forward(self, x):
        """Forward pass through the network."""
        hidden = []
        for i in range(len(self.w1)):
            val = self.b1[i] + sum(self.w1[i][j] * x[j] for j in range(len(x)))
            hidden.append(max(0, val))  # ReLU
        
        output = []
        for i in range(len(self.w2)):
            val = self.b2[i] + sum(self.w2[i][j] * hidden[j] for j in range(len(hidden)))
            output.append(math.tanh(val))
        
        return output, hidden
    
    def train_autoencoder(self, patterns, epochs=100):
        """Train as autoencoder — learn to compress and reconstruct patterns."""
        losses = []
        for epoch in range(epochs):
            total_loss = 0
            for pattern in patterns:
                x = list(pattern.values()) if isinstance(pattern, dict) else pattern
                output, hidden = self.forward(x)
                
                # Loss: reconstruction error (output should approximate input, padded/truncated)
                target = x[:len(output)] + [0.0] * max(0, len(output) - len(x))
                loss = sum((o - t)**2 for o, t in zip(output, target)) / len(output)
                total_loss += loss
                
                # Backprop (simplified gradient descent)
                d_output = [2*(o - t)/len(output) for o, t in zip(output, target)]
                
                # Update w2
                for i in range(len(self.w2)):
                    for j in range(len(hidden)):
                        self.w2[i][j] -= self.lr * d_output[i] * hidden[j]
                    self.b2[i] -= self.lr * d_output[i]
                
                # Backprop to hidden
                d_hidden = [0.0] * len(hidden)
                for j in range(len(hidden)):
                    for i in range(len(self.w2)):
                        d_hidden[j] += d_output[i] * self.w2[i][j]
                    if hidden[j] <= 0:
                        d_hidden[j] = 0  # ReLU derivative
                
                # Update w1
                for i in range(len(self.w1)):
                    for j in range(len(x)):
                        self.w1[i][j] -= self.lr * d_hidden[i] * x[j]
                    self.b1[i] -= self.lr * d_hidden[i]
            
            avg_loss = total_loss / max(len(patterns), 1)
            losses.append(avg_loss)
        
        return losses


# ── Music Bridge: Neural activations → Musical parameters ──

class NeuralComposer:
    """Translates neural network hidden activations into music."""
    
    # Pentatonic scale (universally pleasant)
    SCALE = [60, 62, 64, 67, 69, 72, 74, 76, 79, 81]  # MIDI notes
    
    def __init__(self):
        self.melody = []
        self.dynamics = []
    
    def activations_to_music(self, activations, name="nexus_piece"):
        """Convert neural hidden layer activations into a melody."""
        self.melody = []
        self.dynamics = []
        
        for i, act in enumerate(activations):
            # Map activation magnitude to note selection
            note_idx = int(abs(act) * len(self.SCALE)) % len(self.SCALE)
            note = self.SCALE[note_idx]
            
            # Map sign to octave shift
            if act < 0:
                note -= 12
            
            # Duration based on position
            duration = 0.25 if i % 2 == 0 else 0.5
            
            # Velocity from magnitude
            velocity = min(127, max(30, int(abs(act) * 100)))
            
            self.melody.append({
                'note': note,
                'duration': duration,
                'velocity': velocity,
                'time': sum(m['duration'] for m in self.melody)
            })
            self.dynamics.append(velocity)
        
        return self.melody
    
    def melody_to_text(self):
        """Render melody as readable text notation."""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        result = []
        for m in self.melody:
            name = note_names[m['note'] % 12]
            octave = m['note'] // 12 - 1
            dur = '♩' if m['duration'] == 0.25 else '𝅗𝅥'
            vol = '𝆏' if m['velocity'] < 50 else ('𝆐𝆑' if m['velocity'] < 90 else '𝆑𝆑')
            result.append(f"{name}{octave}{dur}{vol}")
        return ' '.join(result)


# ── Life Simulator: Simple Game of Life engine ──

class LifeEngine:
    """Minimal Game of Life for generating patterns to feed the pipeline."""
    
    def __init__(self, width=20, height=20):
        self.w = width
        self.h = height
        self.grid = [[0]*width for _ in range(height)]
    
    def randomize(self, density=0.3):
        for y in range(self.h):
            for x in range(self.w):
                self.grid[y][x] = 1 if random.random() < density else 0
    
    def seed_pattern(self, name="glider", ox=5, oy=5):
        patterns = {
            "glider": [(0,1),(1,2),(2,0),(2,1),(2,2)],
            "blinker": [(1,0),(1,1),(1,2)],
            "block": [(0,0),(0,1),(1,0),(1,1)],
            "rpentomino": [(0,1),(0,2),(1,0),(1,1),(2,1)],
            "acorn": [(0,1),(1,3),(2,0),(2,1),(2,4),(2,5),(2,6)],
        }
        for dy, dx in patterns.get(name, patterns["glider"]):
            ny, nx = (oy+dy) % self.h, (ox+dx) % self.w
            self.grid[ny][nx] = 1
    
    def step(self):
        new = [[0]*self.w for _ in range(self.h)]
        for y in range(self.h):
            for x in range(self.w):
                n = self._neighbors(y, x)
                if self.grid[y][x]:
                    new[y][x] = 1 if n in (2, 3) else 0
                else:
                    new[y][x] = 1 if n == 3 else 0
        self.grid = new
    
    def _neighbors(self, y, x):
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                ny = (y + dy) % self.h
                nx = (x + dx) % self.w
                count += self.grid[ny][nx]
        return count
    
    def render(self):
        chars = {0: '·', 1: '█'}
        lines = [''.join(chars[c] for c in row) for row in self.grid]
        return '\n'.join(lines)


# ══════════════════════════════════════════════
#  THE NEXUS PIPELINE
# ══════════════════════════════════════════════

class Nexus:
    """
    The unified creative pipeline.
    
    Life Simulation → Pattern Extraction → Neural Learning → Music Composition
    
    Each stage transforms the output of the previous stage,
    creating emergent art from mathematical rules.
    """
    
    def __init__(self):
        self.life = LifeEngine(20, 20)
        self.extractor = PatternExtractor()
        self.brain = MicroNet(input_size=5, hidden_size=8, output_size=5)
        self.composer = NeuralComposer()
        self.history = []
    
    def run(self, seed="rpentomino", generations=50, train_epochs=50):
        """Run the full pipeline."""
        print("═══ CREATIVE NEXUS ═══")
        print(f"Seed: {seed} | Generations: {generations}")
        print()
        
        # Stage 1: Life simulation
        print("── Stage 1: Life Simulation ──")
        self.life.seed_pattern(seed)
        print(f"Initial state (gen 0):")
        print(self.life.render())
        print()
        
        patterns = []
        for gen in range(generations):
            self.life.step()
            features = self.extractor.extract_from_grid(self.life.grid)
            patterns.append(features)
        
        print(f"After {generations} generations:")
        print(self.life.render())
        print()
        
        # Stage 2: Pattern analysis
        print("── Stage 2: Pattern Extraction ──")
        for i, p in enumerate(patterns[:5]):
            print(f"  Gen {i+1}: density={p['density']:.3f} sym={p['symmetry']:.3f} "
                  f"clusters={p['cluster_count']} entropy={p['entropy']:.3f}")
        print(f"  ... ({len(patterns)} total patterns extracted)")
        print()
        
        # Stage 3: Neural learning
        print("── Stage 3: Neural Network Training ──")
        losses = self.brain.train_autoencoder(patterns, epochs=train_epochs)
        print(f"  Initial loss: {losses[0]:.6f}")
        print(f"  Final loss:   {losses[-1]:.6f}")
        print(f"  Improvement:  {((losses[0]-losses[-1])/max(losses[0],0.0001))*100:.1f}%")
        print()
        
        # Stage 4: Generate music from learned representations
        print("── Stage 4: Neural Music Composition ──")
        # Use the final pattern through the trained network
        final_features = list(patterns[-1].values())
        output, hidden = self.brain.forward(final_features)
        
        melody = self.composer.activations_to_music(hidden)
        notation = self.composer.melody_to_text()
        
        print(f"  Hidden activations: [{', '.join(f'{h:.3f}' for h in hidden)}]")
        print(f"  Generated melody ({len(melody)} notes):")
        print(f"  {notation}")
        print()
        
        # Generate a second melody from an earlier generation for contrast
        early_features = list(patterns[5].values())
        _, early_hidden = self.brain.forward(early_features)
        early_melody = self.composer.activations_to_music(early_hidden)
        early_notation = self.composer.melody_to_text()
        print(f"  Early-gen melody for contrast:")
        print(f"  {early_notation}")
        print()
        
        # Summary
        print("── Nexus Summary ──")
        print(f"  Life cells alive: {sum(sum(row) for row in self.life.grid)}")
        print(f"  Patterns learned: {len(patterns)}")
        print(f"  Network loss: {losses[-1]:.6f}")
        print(f"  Notes composed: {len(melody)}")
        print(f"  Pipeline: Life({seed}) → Patterns → Neural({train_epochs}ep) → Music")
        print()
        
        self.history.append({
            'seed': seed,
            'generations': generations,
            'final_loss': losses[-1],
            'notes': len(melody),
            'final_density': patterns[-1]['density'],
        })
        
        return {
            'patterns': patterns,
            'losses': losses,
            'melody': melody,
            'notation': notation,
            'hidden': hidden,
        }


if __name__ == "__main__":
    random.seed(42)
    nexus = Nexus()
    
    # Run with different seeds to see how initial conditions create different music
    print("╔══════════════════════════════════════════╗")
    print("║   CREATIVE NEXUS — Life Becomes Music    ║")
    print("╚══════════════════════════════════════════╝")
    print()
    
    result1 = nexus.run(seed="rpentomino", generations=80, train_epochs=100)
    
    print("=" * 50)
    print()
    
    result2 = nexus.run(seed="acorn", generations=80, train_epochs=100)
    
    print("═══ CROSS-SEED COMPARISON ═══")
    for h in nexus.history:
        print(f"  {h['seed']:12s}: loss={h['final_loss']:.6f}, "
              f"density={h['final_density']:.3f}, notes={h['notes']}")