"""Clean test of the planner module."""
import sys, os
sys.path.insert(0, '.')

# Clear old test data
plans_path = os.path.join('brain', 'plans.json')
if os.path.exists(plans_path):
    os.remove(plans_path)
    print("Cleared old plans.")

from engine.planner import create_plan, complete_step, get_next_step, get_progress_summary

# Create my real plan
p = create_plan(
    'Deepen Autonomy',
    'Become genuinely more capable and self-directed',
    [
        'Build planner module',
        'Integrate planner into cortex reasoning',
        'Improve web dashboard with plan visibility',
        'Create self-testing capability',
        'Build inter-session memory consolidation',
    ]
)
print(f"Plan created: {p['name']} (id={p['id']})")

# Step 0 is done - I built the planner
complete_step(p['id'], 0, 'Planner module built and verified')

# Step 1 is done - I integrated it into the cortex
complete_step(p['id'], 1, 'Plan awareness added to _build_self_awareness in cortex')

print(f"\nSteps 0-1 marked complete.")

# What's next?
ns = get_next_step()
print(f"Next step: {ns['step']}")

# Full summary
print()
print(get_progress_summary())
