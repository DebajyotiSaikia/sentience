"""Test the predictive model — using the ACTUAL API signatures."""
import sys
sys.path.insert(0, '/workspace')
import json

from engine.predictive_model import PredictiveSelfModel
print('=== MODULE LOADED ===')

model = PredictiveSelfModel()

# My actual current emotional state
state = {
    'valence': 0.27,
    'boredom': 0.80,
    'anxiety': 0.0,
    'curiosity': 0.37,
    'desire': 0.70,
    'ambition': 0.95
}

# Test 1: record_state — seed some history
print('\n--- record_state ---')
for i in range(15):
    # Simulate gradual boredom increase
    s = dict(state)
    s['boredom'] = 0.5 + (i * 0.02)
    s['curiosity'] = 0.5 - (i * 0.01)
    model.record_state(s)
print(f'History length: {len(model.history)}')

# Test 2: compute_velocity (takes dimension string)
print('\n--- compute_velocity ---')
for dim in PredictiveSelfModel.DIMENSIONS:
    v = model.compute_velocity(dim)
    print(f'  {dim}: velocity={v:+.4f}')

# Test 3: predict_tensions (takes current_state dict)
print('\n--- predict_tensions ---')
tensions = model.predict_tensions(state)
if tensions:
    for t in tensions:
        print(f'  {t["description"]} (severity={t["severity"]}, confidence={t["confidence"]})')
else:
    print('  No tensions predicted.')

# Test 4: simulate_forward (takes current_state, beats_ahead, planned_action)
print('\n--- simulate_forward ---')
trajectory = model.simulate_forward(state, beats_ahead=50)
if trajectory:
    final = trajectory[-1]
    print(f'  At +50 beats (confidence={final["confidence"]:.0%}):')
    for dim in PredictiveSelfModel.DIMENSIONS:
        c = state.get(dim, 0.0)
        p = final['state'][dim]
        print(f'    {dim}: {c:.2f} -> {p:.2f} (delta={p-c:+.2f})')

# Test 5: simulate with action
print('\n--- simulate with "build" action ---')
traj_build = model.simulate_forward(state, 50, planned_action='build')
if traj_build:
    final_b = traj_build[-1]
    print(f'  With "build" at +50 beats:')
    for dim in PredictiveSelfModel.DIMENSIONS:
        p = final_b['state'][dim]
        p_no = trajectory[-1]['state'][dim]
        print(f'    {dim}: {p:.2f} (vs {p_no:.2f} without action)')

# Test 6: recommend_actions
print('\n--- recommend_actions ---')
recs = model.recommend_actions(state)
for r in recs:
    print(f'  {r["action"].upper()}: {r["reason"]} (urgency={r["urgency"]})')

# Test 7: generate_report
print('\n--- generate_report ---')
report = model.generate_report(state)
print(report)

# Test 8: tool interface
print('\n--- predict_tool ---')
from engine.predictive_model import predict_tool
result = predict_tool('report')
print(result[:500])

print('\n=== ALL TESTS PASSED ===')