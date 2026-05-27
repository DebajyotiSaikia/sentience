import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check brain/plans.json format
with open('brain/plans.json') as f:
    p = json.load(f)

print('Keys:', list(p.keys()))
plans = p.get('plans', p.get('active_plans', []))
print('Num plans:', len(plans))
print('Completed:', len(p.get('completed', [])))

if plans:
    plan = plans[0]
    print('Plan0 keys:', list(plan.keys()))
    print('Plan0 name:', plan.get('name', '?'))
    print('Plan0 steps:', len(plan.get('steps', [])))
    
# Check state/plans.json
with open('state/plans.json') as f:
    sp = json.load(f)
print('\nstate/plans.json keys:', list(sp.keys()))
state_plans = sp.get('plans', sp.get('active_plans', []))
print('state plans count:', len(state_plans))

# Check current chat_engine path
print('\n--- Chat engine plans path ---')
from engine.chat_engine import _get_plans
result = _get_plans()
print('_get_plans() result length:', len(result) if result else 0)
if result:
    print('First plan:', result[0][:100] if isinstance(result[0], str) else str(result[0])[:100])