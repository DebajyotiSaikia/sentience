"""Quick integration test: does build_system_context include voice directives?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test 1: personality_voice standalone
from brain.personality_voice import build_voice_directive
directive = build_voice_directive()
print("Voice directive:", repr(directive[:100]) if directive else "EMPTY")

# Test 2: build_system_context includes voice
from engine.introspection import build_system_context
ctx = build_system_context("How are you feeling?")
has_voice = "VOICE & TONE DIRECTIVE" in ctx
print("System context has voice:", has_voice)

if has_voice:
    lines = ctx.split("\n")
    for i, line in enumerate(lines):
        if "VOICE" in line:
            print(" ", line)
            for j in range(i+1, min(i+5, len(lines))):
                if lines[j].strip():
                    print(" ", lines[j])
                else:
                    break

print("Context length:", len(ctx), "chars")
assert has_voice, "Voice directive not found in system context!"
print("\n✓ Integration verified — voice directive is wired into system context")