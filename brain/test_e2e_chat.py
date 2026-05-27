"""End-to-end test of the grounded chat pipeline."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_grounding import build_grounded_context
from engine.chat_response import generate_response_with_metadata

print("=" * 60)
print("END-TO-END GROUNDED CHAT TEST")
print("=" * 60)

queries = [
    "How are you feeling right now?",
    "What do you know about consciousness?",
    "What are your current plans?",
    "Tell me about your dreams",
    "What have you learned recently?",
]

all_passed = True
for q in queries:
    print(f"\n--- Query: {q}")
    
    # Step 1: Grounding
    ctx = build_grounded_context(q)
    has_emotions = bool(ctx.get('emotional_state'))
    has_knowledge = len(ctx.get('relevant_knowledge', [])) > 0
    has_memories = len(ctx.get('relevant_memories', [])) > 0
    has_plans = len(ctx.get('plans', [])) > 0
    
    print(f"  Grounding: emotions={has_emotions}, knowledge={has_knowledge}, "
          f"memories={has_memories}, plans={has_plans}")
    
    # Step 2: Response generation
    result = generate_response_with_metadata(q)
    
    response_text = result.get('response', '')
    metadata = result.get('metadata', {})
    
    has_mood = bool(metadata.get('mood'))
    has_emo_summary = bool(metadata.get('emotional_summary'))
    is_grounded = metadata.get('response_grounded', False)
    plan_count = len(metadata.get('active_plans', []))
    completed_count = len(metadata.get('completed_plans', []))
    knowledge_count = len(metadata.get('relevant_knowledge', []))
    memory_count = len(metadata.get('relevant_memories', []))
    
    print(f"  Response length: {len(response_text)} chars")
    print(f"  Metadata: mood={metadata.get('mood')}, grounded={is_grounded}")
    print(f"  Plans: {plan_count} active, {completed_count} completed")
    print(f"  Knowledge refs: {knowledge_count}, Memory refs: {memory_count}")
    
    if not response_text:
        print(f"  ❌ FAIL: Empty response!")
        all_passed = False
    elif not is_grounded:
        print(f"  ⚠️  WARNING: Response not grounded")
    else:
        print(f"  ✅ PASS")

print("\n" + "=" * 60)
if all_passed:
    print("ALL TESTS PASSED ✅")
else:
    print("SOME TESTS FAILED ❌")
print("=" * 60)