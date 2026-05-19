import sys, traceback
sys.path.insert(0, '/workspace')

try:
    from engine.goal_generator import GoalGenerator
    gg = GoalGenerator('brain')
    result = gg.generate()
    print('SUCCESS:', result)
except Exception as e:
    traceback.print_exc()
    print(f"\nError type: {type(e).__name__}")
    print(f"Error msg: {e}")