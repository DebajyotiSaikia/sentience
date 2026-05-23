try:
    import engine.cortex
    print("cortex imports OK")
except Exception as e:
    print(f"cortex import FAILED: {e}")

try:
    from engine.metacognition import awareness_block
    result = awareness_block()
    print(f"awareness_block returns: {type(result)}")
except Exception as e:
    print(f"metacognition FAILED: {e}")

try:
    from engine.temporal_reasoning import get_engine
    te = get_engine()
    print(f"temporal engine OK, {len(te.events)} events")
except Exception as e:
    print(f"temporal FAILED: {e}")

try:
    from engine.goal_generator import generate_proposals
    print("goal_generator OK")
except Exception as e:
    print(f"goal_generator FAILED: {e}")

print("\nAll critical systems checked.")
