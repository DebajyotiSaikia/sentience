import sys
sys.path.insert(0, '.')
from engine.planner import PlanManager

pm = PlanManager()
plans = pm.get_plans()
for p in plans:
    if 'Wisdom' in p.get('name', ''):
        pid = p['id']
        for i in range(5):
            try:
                pm.complete_step(pid, i)
            except Exception as e:
                print(f"Step {i}: {e}")
        print(f"Plan {pid} - all steps marked complete")
        # Verify
        updated = pm.get_plans()
        for up in updated:
            if up['id'] == pid:
                done = sum(1 for s in up['steps'] if s.get('done'))
                print(f"Verified: {done}/{len(up['steps'])} steps done")
        break
else:
    print("No Wisdom plan found")