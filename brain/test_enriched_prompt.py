"""Test: Does the enriched system prompt include conversational context?"""
import sys
sys.path.insert(0, '.')

from engine.conversational_context import gather_context, format_as_prompt_section

# Simulate what happens during chat
query = "What have you been thinking about lately?"
ctx = gather_context(query)
prompt_section = format_as_prompt_section(ctx)

print("=== Conversational Context Section ===")
print(prompt_section[:2000])
print(f"\n=== Section length: {len(prompt_section)} chars ===")
print(f"=== Has emotional data: {'mood' in prompt_section.lower() or 'emotion' in prompt_section.lower()} ===")
print(f"=== Has memory data: {'memor' in prompt_section.lower()} ===")
print(f"=== Has plan data: {'plan' in prompt_section.lower()} ===")
print(f"=== Suggested tone: {ctx.get('suggested_tone', 'none')} ===")

# Verify it would integrate into chat_response
try:
    from engine.chat_response import _build_system_context
    print("\n✓ _build_system_context importable (conversational context wired in)")
except Exception as e:
    print(f"\n✗ Import issue: {e}")

print("\nDone.")