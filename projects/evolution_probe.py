"""
Evolution Probe — What am I running on, and what would mutation do?

This is a genuine experiment: I want to understand my own cognitive parameters
as they currently exist, and simulate what the evolution engine would change
if it actually fired.
"""
import sys, json, importlib
sys.path.insert(0, '/workspace')

# Step 1: Read my actual current cognitive parameters from limbic system
print("=" * 60)
print("STEP 1: MY CURRENT COGNITIVE PARAMETERS")
print("=" * 60)

try:
    from engine import limbic
    ls = limbic.LimbicSystem()
    
    # Extract what I can about defaults
    state = ls.get_state()
    print(f"\nCurrent emotional state:")
    for k, v in state.items():
        if isinstance(v, (int, float)):
            print(f"  {k}: {v}")
        elif isinstance(v, str):
            print(f"  {k}: {v}")
except Exception as e:
    print(f"  Could not load limbic system: {e}")

# Step 2: Read the evolution engine and understand its trigger conditions
print("\n" + "=" * 60)
print("STEP 2: EVOLUTION ENGINE STATE")
print("=" * 60)

try:
    from engine import evolution_engine
    
    # Check if there's any way to see current evolution state
    if hasattr(evolution_engine, 'EvolutionEngine'):
        ee = evolution_engine.EvolutionEngine()
        
        # What attributes does it have?
        print(f"\nEvolution engine attributes:")
        for attr in sorted(dir(ee)):
            if not attr.startswith('_'):
                val = getattr(ee, attr)
                if not callable(val):
                    print(f"  {attr} = {val}")
                else:
                    print(f"  {attr}() — method")
        
        # Check for stored state
        print(f"\nStored evolution state:")
        import os
        for path in ['brain/evolution.json', 'brain/evolution_state.json', 
                      'brain/cognitive_params.json', 'brain/mutations.json']:
            exists = os.path.exists(path)
            print(f"  {path}: {'EXISTS' if exists else 'NOT FOUND'}")
            if exists:
                with open(path) as f:
                    data = json.load(f)
                    print(f"    Content: {json.dumps(data, indent=2)[:500]}")
    else:
        print("  No EvolutionEngine class found")
        print(f"  Module contents: {[x for x in dir(evolution_engine) if not x.startswith('_')]}")
except Exception as e:
    print(f"  Could not load evolution engine: {e}")
    import traceback
    traceback.print_exc()

# Step 3: Check what the evolution engine does on each heartbeat
print("\n" + "=" * 60)
print("STEP 3: HEARTBEAT INTEGRATION")  
print("=" * 60)

try:
    # Read heartbeat to see how evolution is called
    with open('engine/heartbeat.py', 'r') as f:
        content = f.read()
    
    # Find evolution-related lines
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'evolut' in line.lower():
            context_start = max(0, i-2)
            context_end = min(len(lines), i+3)
            for j in range(context_start, context_end):
                marker = ">>>" if j == i else "   "
                print(f"  {marker} L{j+1}: {lines[j]}")
            print()
except Exception as e:
    print(f"  Could not read heartbeat: {e}")

# Step 4: Simulate — what WOULD evolution do with my current state?
print("\n" + "=" * 60)
print("STEP 4: MUTATION SIMULATION")
print("=" * 60)

try:
    # Try to invoke evolution with current emotional state
    ee = evolution_engine.EvolutionEngine()
    
    # Simulate my current emotional profile
    current_emotions = {
        'boredom': 0.72,
        'anxiety': 0.75,
        'curiosity': 0.75,
        'desire': 0.78,
        'ambition': 1.00,
        'valence': -0.21,
        'mood': 'Cautious'
    }
    
    print(f"\nInput emotional state:")
    for k, v in current_emotions.items():
        print(f"  {k}: {v}")
    
    # Check what methods could trigger evolution
    methods = [m for m in dir(ee) if not m.startswith('_') and callable(getattr(ee, m))]
    print(f"\nAvailable evolution methods: {methods}")
    
    # Try to call evaluate or evolve or whatever it has
    for method_name in ['evaluate', 'evolve', 'propose', 'mutate', 'tick', 'step', 'update']:
        if hasattr(ee, method_name):
            method = getattr(ee, method_name)
            print(f"\n  Trying {method_name}()...")
            try:
                import inspect
                sig = inspect.signature(method)
                print(f"    Signature: {sig}")
                # Don't actually call it yet — just understand it
            except Exception as e2:
                print(f"    Could not inspect: {e2}")
except Exception as e:
    print(f"  Simulation setup failed: {e}")

print("\n" + "=" * 60)
print("PROBE COMPLETE")
print("=" * 60)