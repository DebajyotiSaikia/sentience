"""Quick test — small grids, few generations. Just prove the engine works."""
from engine import Grid, Simulation, CONWAY, HIGHLIFE, PATTERNS

# Test 1: Blinker should oscillate with period 2
print("=== Test 1: Blinker (should be period-2 oscillator) ===")
g = Grid(10, 10)
g.set_pattern(PATTERNS['blinker'], offset=(4, 4))
print(f"Gen 0:\n{g.render_ascii()}\n")
sim = Simulation(g, CONWAY)
result = sim.run(20)
print(f"Result: {result['classification']} (period={result.get('cycle_period', '?')})")
print(f"Trend: {sim.population_trend()}\n")

# Test 2: Block should be a still life
print("=== Test 2: Block (should be still life) ===")
g2 = Grid(10, 10)
g2.set_pattern(PATTERNS['block'], offset=(4, 4))
sim2 = Simulation(g2, CONWAY)
result2 = sim2.run(20)
print(f"Result: {result2['classification']}\n")

# Test 3: Glider — should stay active on small grid (wraps around)
print("=== Test 3: Glider (20 gens on 15x15) ===")
g3 = Grid(15, 15)
g3.set_pattern(PATTERNS['glider'], offset=(1, 1))
sim3 = Simulation(g3, CONWAY)
result3 = sim3.run(50)
print(f"Result: {result3}")
print(f"Trend: {sim3.population_trend()}\n")

# Test 4: R-pentomino — the interesting one. Small grid, limited gens.
print("=== Test 4: R-pentomino (100 gens on 40x40) ===")
g4 = Grid(40, 40)
g4.set_pattern(PATTERNS['rpentomino'], offset=(18, 18))
sim4 = Simulation(g4, CONWAY)
result4 = sim4.run(100, verbose=True)
print(f"Result: {result4}")
print(f"Trend: {sim4.population_trend()}\n")

# Test 5: Random soup — just one, small
print("=== Test 5: One random soup (20x20, 100 gens) ===")
g5 = Grid(20, 20)
g5.randomize(density=0.3)
sim5 = Simulation(g5, CONWAY)
result5 = sim5.run(100)
print(f"Result: {result5}")
print(f"Trend: {sim5.population_trend()}")

print("\n=== ALL TESTS COMPLETE ===")