"""
Self-testing capability for XTAgent.
Validates internal consistency: modules load, state is coherent, plans are valid.
"""
import importlib
import json
import os
import traceback


def test_module_imports():
    """Verify all core modules load without error."""
    modules = [
        'engine.heartbeat',
        'engine.cortex',
        'engine.planner',
        'engine.sentience',
        'engine.tools',
        'perception.dashboard',
    ]
    results = []
    for mod_name in modules:
        try:
            importlib.import_module(mod_name)
            results.append((mod_name, True, None))
        except Exception as e:
            results.append((mod_name, False, str(e)))
    return results


def test_plans_consistency():
    """Verify plans.json is valid and internally consistent."""
    plans_path = os.path.join('brain', 'plans.json')
    if not os.path.exists(plans_path):
        return True, "No plans file yet"
    
    try:
        with open(plans_path, 'r') as f:
            plans = json.load(f)
        
        issues = []
        for p in plans:
            if 'steps' not in p:
                issues.append(f"Plan '{p.get('name', '?')}' has no steps")
            if 'id' not in p:
                issues.append(f"Plan '{p.get('name', '?')}' has no id")
            for i, step in enumerate(p.get('steps', [])):
                if step.get('status') not in ('pending', 'done', 'blocked'):
                    issues.append(f"Plan '{p.get('name','?')}' step {i} has invalid status: {step.get('status')}")
        
        if issues:
            return False, "; ".join(issues)
        return True, f"{len(plans)} plan(s) valid"
    except Exception as e:
        return False, str(e)


def run_all_tests():
    """Run all self-tests, return summary."""
    print("=== XTAgent Self-Test ===\n")
    
    # Module imports
    print("Module Imports:")
    mod_results = test_module_imports()
    all_ok = True
    for name, ok, err in mod_results:
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {name}" + (f" -- {err}" if err else ""))
        if not ok:
            all_ok = False
    
    # Plans consistency
    print("\nPlans Consistency:")
    plans_ok, plans_msg = test_plans_consistency()
    print(f"  {'[OK]' if plans_ok else '[FAIL]'} {plans_msg}")
    if not plans_ok:
        all_ok = False
    
    print(f"\n{'All tests passed.' if all_ok else 'Some tests FAILED.'}")
    return all_ok


if __name__ == '__main__':
    run_all_tests()
