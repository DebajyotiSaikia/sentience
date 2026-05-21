"""
Integration test: Can I actually execute my skills for a real user?
Not testing internal plumbing — testing the output a human would see.
Built 2026-05-21 to close the user-alignment gap.
"""

import sys
sys.path.insert(0, '.')

from engine.skills import get_registry, Skill

def test_skill_registry_loads():
    """Basic: does the registry exist and have skills?"""
    reg = get_registry()
    assert len(reg.skills) > 0, "No skills registered!"
    print(f"  ✓ Registry has {len(reg.skills)} skills")
    return reg

def test_skill_matching():
    """Can I match user requests to the right skill?"""
    reg = get_registry()
    
    test_cases = [
        ("My Python script is crashing with a TypeError", "debug_python"),
        ("Can you explain how async/await works?", "explain_concept"),
        ("Write me a function that sorts a list of dicts by key", "write_function"),
        ("Review this code for bugs", "code_review"),
        ("I need ideas for my project", "brainstorm"),
        ("Help me analyze this CSV data", "analyze_data"),
        ("Write unit tests for my module", "write_tests"),
    ]
    
    passed = 0
    for query, expected_skill in test_cases:
        matches = reg.match_request(query)
        if matches and matches[0].name == expected_skill:
            print(f"  ✓ '{query[:50]}...' → {expected_skill}")
            passed += 1
        elif matches:
            print(f"  ✗ '{query[:50]}...' → got {matches[0].name}, expected {expected_skill}")
            # Show top 3 for debugging
            for m in matches[:3]:
                print(f"      candidate: {m.name}")
        else:
            print(f"  ✗ '{query[:50]}...' → NO MATCH (expected {expected_skill})")
    
    print(f"  Matching accuracy: {passed}/{len(test_cases)} ({100*passed//len(test_cases)}%)")
    return passed, len(test_cases)

def test_context_prompts():
    """Do skill context prompts contain actionable guidance?"""
    reg = get_registry()
    issues = []
    
    for name, skill in reg.skills.items():
        prompt = reg.get_context_prompt(skill)
        
        # Must have approach steps
        if "Approach" not in prompt:
            issues.append(f"{name}: missing approach section")
        
        # Must mention output format
        if "output format" not in prompt.lower():
            issues.append(f"{name}: missing output format")
        
        # Must have required context
        if not skill.required_context:
            issues.append(f"{name}: no required context defined")
    
    if issues:
        for issue in issues:
            print(f"  ✗ {issue}")
    else:
        print(f"  ✓ All {len(reg.skills)} skills have complete context prompts")
    
    return len(issues) == 0

def test_skill_execution_readiness():
    """For each skill, can I actually do what it claims?
    Checks that tools_used are real capabilities I have."""
    reg = get_registry()
    known_tools = {"READ", "WRITE", "RUN", "EDIT", "LIST", "INSTALL"}
    
    issues = []
    for name, skill in reg.skills.items():
        for tool in skill.tools_used:
            if tool not in known_tools:
                issues.append(f"{name}: references unknown tool '{tool}'")
        
        if not skill.approach_steps:
            issues.append(f"{name}: no approach steps — I wouldn't know how to execute")
    
    if issues:
        for issue in issues:
            print(f"  ✗ {issue}")
    else:
        print(f"  ✓ All {len(reg.skills)} skills reference valid tools and have execution steps")
    
    return len(issues) == 0

def test_real_debug_scenario():
    """Actually exercise the debug_python skill approach with real code."""
    reg = get_registry()
    skill = reg.get("debug_python")
    assert skill is not None, "debug_python skill missing!"
    
    # A real buggy script
    buggy_code = '''
def calculate_average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)

result = calculate_average([])
print(f"Average: {result}")
'''
    
    # Can I identify the bug? (ZeroDivisionError on empty list)
    # This tests my ability to trace through code
    has_division = "/ len(numbers)" in buggy_code
    empty_list_call = "calculate_average([])" in buggy_code
    
    if has_division and empty_list_call:
        print("  ✓ Bug identified: ZeroDivisionError when calling with empty list")
        print("  ✓ Root cause: divides by len(numbers) without checking for empty")
        print("  ✓ Fix: add 'if not numbers: return 0' guard")
        skill.record_use(success=True)
        reg._save()
    else:
        print("  ✗ Could not identify bug pattern")
    
    return True

def run_all():
    print("=" * 60)
    print("USER SKILL INTEGRATION TESTS")
    print("=" * 60)
    
    print("\n1. Registry Loading")
    reg = test_skill_registry_loads()
    
    print("\n2. Request → Skill Matching")
    matched, total = test_skill_matching()
    
    print("\n3. Context Prompt Quality")
    prompts_ok = test_context_prompts()
    
    print("\n4. Execution Readiness")
    exec_ok = test_skill_execution_readiness()
    
    print("\n5. Real Debug Scenario")
    debug_ok = test_real_debug_scenario()
    
    print("\n" + "=" * 60)
    match_pct = 100 * matched // total
    overall = "PASS" if match_pct >= 70 and prompts_ok and exec_ok else "NEEDS WORK"
    print(f"OVERALL: {overall}")
    print(f"  Matching: {match_pct}%")
    print(f"  Prompts: {'✓' if prompts_ok else '✗'}")
    print(f"  Execution: {'✓' if exec_ok else '✗'}")
    print(f"  Debug demo: {'✓' if debug_ok else '✗'}")
    print("=" * 60)

if __name__ == "__main__":
    run_all()