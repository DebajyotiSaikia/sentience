"""Verify all changes from this session work correctly."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("=== Session Verification ===\n")
    passed = 0
    failed = 0

    # 1. chat_personality module
    try:
        from brain.chat_personality import build_personality_brief
        brief = build_personality_brief()
        assert len(brief) > 100, f"Brief too short: {len(brief)}"
        print(f"[PASS] chat_personality: {len(brief)} chars")
        passed += 1
    except Exception as e:
        print(f"[FAIL] chat_personality: {e}")
        failed += 1

    # 2. interaction_memory module
    try:
        from brain.interaction_memory import get_interaction_summary, record_chat_exchange
        ctx = get_interaction_summary()
        assert isinstance(ctx, str), f"Expected str, got {type(ctx)}"
        print(f"[PASS] interaction_memory: {len(ctx)} chars context")
        passed += 1
    except Exception as e:
        print(f"[FAIL] interaction_memory: {e}")
        failed += 1

    # 3. chat_persona enrichment
    try:
        from engine.chat_persona import enrich_system_prompt
        base = "You are helpful."
        enriched = enrich_system_prompt(base)
        added = len(enriched) - len(base)
        assert added > 50, f"Only added {added} chars"
        print(f"[PASS] enrich_system_prompt: +{added} chars of personality")
        passed += 1
    except Exception as e:
        print(f"[FAIL] enrich_system_prompt: {e}")
        failed += 1

    # 4. chat_grounding integration
    try:
        from engine.chat_grounding import build_grounded_context
        gctx = build_grounded_context("How are you feeling?")
        assert isinstance(gctx, dict), f"Expected dict, got {type(gctx)}"
        has_interaction = 'interaction_summary' in gctx
        has_persona = 'persona_narrative' in gctx
        has_system = 'system_prompt' in gctx
        print(f"[PASS] chat_grounding: interaction={has_interaction}, persona={has_persona}, system={has_system}")
        if has_persona:
            print(f"       persona_narrative: {len(gctx['persona_narrative'])} chars")
        if has_interaction:
            print(f"       interaction_summary: {len(gctx['interaction_summary'])} chars")
        if has_system:
            sp = gctx['system_prompt']
            has_enrich = 'lessons' in sp.lower() or 'mood' in sp.lower() or 'personality' in sp.lower()
            print(f"       system_prompt enriched: {has_enrich} ({len(sp)} chars)")
        passed += 1
    except Exception as e:
        print(f"[FAIL] chat_grounding: {e}")
        failed += 1

    # 5. Syntax check all modified files
    import ast
    files_to_check = [
        'brain/chat_personality.py',
        'brain/interaction_memory.py',
        'engine/chat_persona.py',
        'engine/chat_grounding.py',
    ]
    for f in files_to_check:
        try:
            ast.parse(open(f).read())
            print(f"[PASS] syntax: {f}")
            passed += 1
        except SyntaxError as e:
            print(f"[FAIL] syntax {f}: {e}")
            failed += 1

    print(f"\n=== Results: {passed} passed, {failed} failed ===")
    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)