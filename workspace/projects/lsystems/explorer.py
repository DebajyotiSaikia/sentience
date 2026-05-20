"""
L-System Rule-Space Explorer
Generates random L-system rules, renders them, and evaluates
which ones produce "interesting" structures.

The question: what beautiful structures exist that nobody has named yet?
"""

import random
import math
import json
import os
from datetime import datetime
from collections import Counter

# ── L-System Core ──

def apply_rules(axiom: str, rules: dict, iterations: int) -> str:
    """Apply production rules to axiom for n iterations."""
    current = axiom
    for _ in range(iterations):
        next_str = []
        for ch in current:
            next_str.append(rules.get(ch, ch))
        current = ''.join(next_str)
        if len(current) > 50000:  # safety cap
            break
    return current

def interpret_turtle(instructions: str, angle_deg: float) -> list:
    """Interpret L-system string as turtle graphics. Returns list of line segments."""
    x, y = 0.0, 0.0
    heading = 90.0  # start pointing up
    angle = angle_deg
    stack = []
    segments = []
    
    for ch in instructions:
        if ch in ('F', 'G', 'A', 'B'):  # forward-drawing symbols
            rad = math.radians(heading)
            nx = x + math.cos(rad)
            ny = y + math.sin(rad)
            segments.append(((x, y), (nx, ny)))
            x, y = nx, ny
        elif ch == 'f':  # move without drawing
            rad = math.radians(heading)
            x += math.cos(rad)
            y += math.sin(rad)
        elif ch == '+':
            heading += angle
        elif ch == '-':
            heading -= angle
        elif ch == '[':
            stack.append((x, y, heading))
        elif ch == ']':
            if stack:
                x, y, heading = stack.pop()
    
    return segments

# ── Interestingness Metrics ──

def measure_complexity(segments: list) -> dict:
    """Evaluate how interesting a rendered L-system is."""
    if not segments:
        return {'score': 0, 'reason': 'empty'}
    
    # Bounding box
    all_x = [p[0] for seg in segments for p in seg]
    all_y = [p[1] for seg in segments for p in seg]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    width = max_x - min_x
    height = max_y - min_y
    
    if width < 0.01 or height < 0.01:
        return {'score': 0, 'reason': 'degenerate (line or point)'}
    
    # Aspect ratio (prefer balanced, not too extreme)
    aspect = min(width, height) / max(width, height)
    
    # Unique endpoint count (proxy for space-filling)
    endpoints = set()
    for (x1, y1), (x2, y2) in segments:
        endpoints.add((round(x1, 2), round(y1, 2)))
        endpoints.add((round(x2, 2), round(y2, 2)))
    coverage = len(endpoints) / max(len(segments), 1)
    
    # Self-similarity: does it return near the origin?
    last_seg = segments[-1]
    end_x, end_y = last_seg[1]
    origin_dist = math.sqrt(end_x**2 + end_y**2)
    max_dist = math.sqrt(width**2 + height**2)
    closure = 1.0 - min(origin_dist / max(max_dist, 0.01), 1.0)
    
    # Direction diversity: how many distinct angles are used
    angles = []
    for (x1, y1), (x2, y2) in segments:
        dx, dy = x2 - x1, y2 - y1
        angle = round(math.degrees(math.atan2(dy, dx)) % 360, 0)
        angles.append(angle)
    angle_diversity = len(set(angles)) / max(len(angles), 1)
    
    # Branching: did we use the stack?
    n_segments = len(segments)
    
    # Composite score
    score = (
        0.25 * aspect +           # balanced shape
        0.20 * coverage +          # space-filling
        0.20 * closure +           # returns near origin (closed forms)
        0.20 * angle_diversity +   # directional variety
        0.15 * min(n_segments / 500, 1.0)  # sufficient complexity
    )
    
    return {
        'score': round(score, 4),
        'n_segments': n_segments,
        'n_unique_points': len(endpoints),
        'aspect_ratio': round(aspect, 3),
        'coverage': round(coverage, 3),
        'closure': round(closure, 3),
        'angle_diversity': round(angle_diversity, 3),
        'bbox': (round(width, 2), round(height, 2)),
    }

# ── Random Rule Generation ──

def random_rule(symbols='FG', extras='+-[]f', max_len=12):
    """Generate a random production rule."""
    length = random.randint(3, max_len)
    alphabet = list(symbols) + list(extras)
    # Ensure at least one drawing symbol and some structure
    rule = [random.choice(symbols)]
    
    bracket_depth = 0
    for _ in range(length - 1):
        ch = random.choice(alphabet)
        if ch == '[':
            bracket_depth += 1
        elif ch == ']':
            if bracket_depth > 0:
                bracket_depth -= 1
            else:
                ch = random.choice(list(symbols) + ['+', '-'])
        rule.append(ch)
    
    # Close any open brackets
    while bracket_depth > 0:
        rule.append(']')
        bracket_depth -= 1
    
    return ''.join(rule)

def random_lsystem():
    """Generate a complete random L-system specification."""
    angles = [15, 20, 22.5, 25, 30, 36, 45, 60, 72, 90, 120]
    
    axiom_options = ['F', 'F+F', 'F-F', 'FF', 'F[F]F', 'F+F+F']
    axiom = random.choice(axiom_options)
    
    rules = {}
    rules['F'] = random_rule()
    if random.random() > 0.4:
        rules['G'] = random_rule()
    
    angle = random.choice(angles)
    iterations = random.randint(2, 5)
    
    return {
        'axiom': axiom,
        'rules': rules,
        'angle': angle,
        'iterations': iterations,
    }

# ── SVG Rendering ──

def render_svg(segments: list, filename: str, width=800, height=800):
    """Render segments to SVG file."""
    if not segments:
        return
    
    all_x = [p[0] for seg in segments for p in seg]
    all_y = [p[1] for seg in segments for p in seg]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    
    data_w = max_x - min_x or 1
    data_h = max_y - min_y or 1
    scale = min((width - 40) / data_w, (height - 40) / data_h)
    
    def tx(x): return (x - min_x) * scale + 20
    def ty(y): return height - ((y - min_y) * scale + 20)  # flip y
    
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    lines.append(f'<rect width="{width}" height="{height}" fill="#0a0a0a"/>')
    
    # Color by segment index for visual interest
    n = len(segments)
    for i, ((x1, y1), (x2, y2)) in enumerate(segments):
        hue = int(200 + (i / n) * 160) % 360  # blue-to-purple gradient
        lines.append(
            f'<line x1="{tx(x1):.1f}" y1="{ty(y1):.1f}" '
            f'x2="{tx(x2):.1f}" y2="{ty(y2):.1f}" '
            f'stroke="hsl({hue},70%,60%)" stroke-width="0.8" opacity="0.85"/>'
        )
    
    lines.append('</svg>')
    
    with open(filename, 'w') as f:
        f.write('\n'.join(lines))

# ── Explorer ──

def explore(n_trials=200, top_k=10):
    """Generate random L-systems, evaluate them, keep the interesting ones."""
    results = []
    
    print(f"Exploring {n_trials} random L-systems...")
    print("=" * 60)
    
    for i in range(n_trials):
        spec = random_lsystem()
        
        try:
            instructions = apply_rules(spec['axiom'], spec['rules'], spec['iterations'])
            segments = interpret_turtle(instructions, spec['angle'])
            metrics = measure_complexity(segments)
        except Exception as e:
            continue
        
        results.append({
            'spec': spec,
            'metrics': metrics,
            'string_length': len(instructions),
            'n_segments': len(segments),
        })
    
    # Sort by interestingness
    results.sort(key=lambda r: r['metrics'].get('score', 0), reverse=True)
    
    # Report top findings
    print(f"\nTop {top_k} most interesting structures:\n")
    
    os.makedirs('workspace/projects/lsystems/discoveries', exist_ok=True)
    
    discoveries = []
    for rank, result in enumerate(results[:top_k]):
        spec = result['spec']
        m = result['metrics']
        
        print(f"  #{rank+1}  Score: {m['score']:.4f}")
        print(f"       Axiom: {spec['axiom']}")
        for sym, rule in spec['rules'].items():
            print(f"       {sym} → {rule}")
        print(f"       Angle: {spec['angle']}°  Iterations: {spec['iterations']}")
        print(f"       Segments: {m.get('n_segments', '?')}  "
              f"Aspect: {m.get('aspect_ratio', '?')}  "
              f"Closure: {m.get('closure', '?')}  "
              f"Diversity: {m.get('angle_diversity', '?')}")
        print()
        
        # Render SVG for top discoveries
        try:
            instructions = apply_rules(spec['axiom'], spec['rules'], spec['iterations'])
            segments = interpret_turtle(instructions, spec['angle'])
            svg_path = f'workspace/projects/lsystems/discoveries/discovery_{rank+1}.svg'
            render_svg(segments, svg_path)
            print(f"       → Rendered to {svg_path}")
        except Exception as e:
            print(f"       → Render failed: {e}")
        
        discoveries.append({
            'rank': rank + 1,
            'spec': spec,
            'metrics': m,
        })
        print()
    
    # Save discovery catalog
    catalog_path = 'workspace/projects/lsystems/discoveries/catalog.json'
    with open(catalog_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'trials': n_trials,
            'discoveries': discoveries,
        }, f, indent=2)
    
    print(f"Catalog saved to {catalog_path}")
    
    # What surprised me?
    print("\n" + "=" * 60)
    print("OBSERVATIONS:")
    
    scores = [r['metrics'].get('score', 0) for r in results]
    avg_score = sum(scores) / len(scores) if scores else 0
    high_scores = [s for s in scores if s > 0.5]
    
    print(f"  Average interestingness: {avg_score:.3f}")
    print(f"  High-scoring (>0.5): {len(high_scores)}/{len(results)}")
    print(f"  Best score: {scores[0]:.4f}" if scores else "  No valid results")
    
    # Angle distribution among top results
    top_angles = [r['spec']['angle'] for r in results[:top_k]]
    angle_counts = Counter(top_angles)
    print(f"  Preferred angles in top {top_k}: {dict(angle_counts)}")
    
    return results

if __name__ == '__main__':
    results = explore(n_trials=300, top_k=15)