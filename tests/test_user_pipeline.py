"""
Test the user-facing pipeline components end-to-end.
Does my skill matching work? Does the enrichment add value?
Let me find out by actually running them.
"""

import sys
sys.path.insert(0, '.')

from engine.skills import get_registry

def test_skill_matching():
    """Do user requests actually find relevant skills?"""
    registry = get_registry()
    
    test_cases = [
        ("Can you help me debug this Python error?", ["debug_python"]),
        ("Write me a function that sorts a list", ["write_function"]),
        ("Review my code please", ["code_review"]),
        ("I need ideas for a new project", ["brainstorm"]),
        ("Explain how async/await works", ["explain_concept"]),
        ("My pip install keeps failing", ["troubleshoot_environment"]),
        ("Can you analyze this CSV data?", ["analyze_data"]),
        ("Help me design a REST API", ["design_system"]),
        ("Write tests for my module", ["write_tests"]),
        ("Refactor this messy function", ["refactor_code"]),
    ]
    
    passed = 0
    failed = 0
    
    print("=" * 60)
    print("SKILL MATCHING TEST")
    print("=" * 60)
    
    for user_input, expected_skills in test_cases:
        matches = registry.match_request(user_input)
        match_names = [m.name for m in matches]
        
        # Check if expected skill is in top 3 results
        top3 = match_names[:3]
        found = any(exp in top3 for exp in expected_skills)
        
        status = "✓" if found else "✗"
        if found:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status} Input: \"{user_input}\"")
        print(f"  Expected: {expected_skills}")
        print(f"  Got top 3: {top3}")
        if not found:
            print(f"  ALL matches: {match_names}")
    
    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{passed + failed} passed")
    print(f"{'=' * 60}")
    return failed == 0


def test_skill_context_prompts():
    """Do skill context prompts look useful?"""
    registry = get_registry()
    
    print("\n\n" + "=" * 60)
    print("SKILL CONTEXT PROMPT EXAMPLES")
    print("=" * 60)
    
    # Show what the LLM would see when executing a skill
    for skill_name in ["debug_python", "write_function", "brainstorm"]:
        skill = registry.get(skill_name)
        if skill:
            prompt = registry.get_context_prompt(skill)
            print(f"\n--- {skill_name} ---")
            print(prompt)


def test_skill_usage_tracking():
    """Does usage tracking work?"""
    registry = get_registry()
    
    print("\n\n" + "=" * 60)
    print("USAGE TRACKING TEST")
    print("=" * 60)
    
    skill = registry.get("debug_python")
    before = skill.times_used
    
    registry.record_use("debug_python", success=True)
    registry.record_use("debug_python", success=True)
    registry.record_use("debug_python", success=False)
    
    after = skill.times_used
    print(f"  Before: {before} uses, After: {after} uses")
    print(f"  Success rate: {skill.success_rate:.2f}")
    print(f"  Last used: {skill.last_used}")
    
    expected_uses = before + 3
    if after == expected_uses and 0.5 < skill.success_rate < 1.0:
        print("  ✓ Usage tracking works correctly")
        return True
    else:
        print("  ✗ Usage tracking broken")
        return False


def test_category_listing():
    """Does the registry produce useful output?"""
    registry = get_registry()
    
    print("\n\n" + "=" * 60)
    print("FULL SKILL LISTING")
    print("=" * 60)
    print(registry.list_all())


if __name__ == "__main__":
    all_pass = True
    all_pass &= test_skill_matching()
    test_skill_context_prompts()
    all_pass &= test_skill_usage_tracking()
    test_category_listing()
    
    print("\n" + "=" * 60)
    if all_pass:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
    print("=" * 60)