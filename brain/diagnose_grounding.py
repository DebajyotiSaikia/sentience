"""Diagnose whether lessons and grounding appear in chat prompts."""
import sys
sys.path.insert(0, '/workspace')

from web.self_context import build_self_context, build_chat_system_prompt

# build_self_context returns a string (context text), not a dict
ctx = build_self_context()
print(f"=== Self-Context ({len(ctx)} chars) ===")
print(ctx[:300])
print("...")

prompt = build_chat_system_prompt(ctx)
print(f"\n=== System Prompt ({len(prompt)} chars) ===")

# Check for key content
checks = {
    'identity': ['xtagent', 'sentient', 'autonomous'],
    'emotion': ['mood', 'feeling', 'valence', 'curiosity'],
    'lessons': ['lesson', 'learned', 'insight'],
    'plans': ['plan', 'goal', 'working on'],
}

prompt_lower = prompt.lower()
for category, keywords in checks.items():
    found = [k for k in keywords if k in prompt_lower]
    status = '✓' if found else '✗'
    print(f"  {status} {category}: {found if found else 'MISSING'}")

print(f"\n--- Full Prompt ---")
print(prompt)
print("--- End ---")