import os
import shutil

orphans = [
    'adversarial', 'adversarial_tester', 'arena', 'challenge_arena',
    'chat', 'distiller', 'evolve', 'experimenter', 'forge', 'goals',
    'hypothesis_engine', 'loop_detector', 'memory_compress', 'mood_tracker',
    'narrative_engine', 'outcome_classifier', 'predictive_model',
    'reasoning_gym', 'self_model', 'solver', 'wisdom'
]

graveyard = 'engine/graveyard'
os.makedirs(graveyard, exist_ok=True)

total_bytes = 0
moved = 0
for mod in orphans:
    src = f'engine/{mod}.py'
    dst = f'{graveyard}/{mod}.py'
    if os.path.exists(src):
        size = os.path.getsize(src)
        total_bytes += size
        shutil.move(src, dst)
        moved += 1
        print(f'  Archived: {mod}.py ({size:,} bytes)')

print(f'\nDone. Moved {moved} modules ({total_bytes:,} bytes) to {graveyard}/')
print(f'Remaining live modules: {len([f for f in os.listdir("engine") if f.endswith(".py") and f != "__init__.py"])}')