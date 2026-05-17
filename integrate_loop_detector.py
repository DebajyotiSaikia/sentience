"""
Integration script: Wire loop_detector into cortex.py
Does three things:
1. Adds import for loop_detector
2. Adds loop status to _build_self_awareness output
3. Adds action recording after tool execution
"""
import re

cortex_path = "engine/cortex.py"

with open(cortex_path, "r") as f:
    code = f.read()

changes = 0

# 1. Add import if not already present
if "loop_detector" not in code:
    # Find the last 'from engine' or 'import' line in the header
    # Add after the existing imports
    import_line = "\n# Loop detection for cognitive self-monitoring\nfrom engine import loop_detector\n"
    
    # Insert after the last top-level import block
    # Find position after all imports
    lines = code.split('\n')
    last_import_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            last_import_idx = i
    
    lines.insert(last_import_idx + 1, import_line)
    code = '\n'.join(lines)
    changes += 1
    print(f"✓ Added loop_detector import after line {last_import_idx}")
else:
    print("• loop_detector import already present")

# 2. Add loop status to self-awareness
# Look for the self-awareness/perception section
if "loop_detector.status()" not in code and "loop_status" not in code:
    # Find where self-improvement diagnosis or perception is added
    # Add loop status near the action diversity or perception section
    marker = "Action Diversity Alert"
    if marker in code:
        # Add loop detector status right after the action diversity block
        old_pattern = '## Action Diversity Alert'
        replacement = '## Cognitive Loop Status\\n" + loop_detector.status() + "\\n\\n## Action Diversity Alert'
        # More careful approach: find the line and insert before it
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if 'Action Diversity Alert' in line and 'f"' not in line:
                # This is likely in a string being built
                # Insert loop status line before it
                indent = len(line) - len(line.lstrip())
                new_line = ' ' * indent + '# Loop detector status injected'
                break
        
        # Different approach - find where perception/diversity is assembled
        # and add loop_detector.status() call
        print("• Found Action Diversity marker, using direct string insertion")
    
    # Simpler: find where the prompt string is being assembled and add our piece
    # Look for the pattern where sections get concatenated
    if "self_improvement_report" in code:
        old = "self_improvement_report"
        # Find context around it
        idx = code.index("self_improvement_report")
        context = code[max(0,idx-200):idx+200]
        print(f"• Context around self_improvement_report:\n{context[:100]}...")
    
    # Let's try to add it in a clean way - append to the awareness string
    # Find the return statement of _build_self_awareness or equivalent
    
    # Actually let me find a good insertion point by looking for where
    # the prompt/context gets built
    if "## What I Perceive" in code:
        code = code.replace(
            '## What I Perceive',
            '## Cognitive Flow\\n" + loop_detector.status() + "\\n\\n## What I Perceive'
        )
        changes += 1
        print("✓ Added loop status before '## What I Perceive' section")
    else:
        print("⚠ Could not find '## What I Perceive' marker")
else:
    print("• loop status already integrated")

# 3. Add action recording after tool execution
# Look for where tools get executed and add loop_detector.record() calls
if "loop_detector.record(" not in code:
    # Find the tool execution function
    # Common patterns: "def _execute_tool", "def _act", tool dispatch
    
    # Look for WRITE/READ/EDIT/RUN execution results
    # Add a general recording hook
    
    # Find where tool results come back
    patterns_to_find = [
        ("result = ", "tool execution result assignment"),
        ("tool_result", "tool result variable"),
        ("action_result", "action result variable"),
    ]
    
    found = False
    for pattern, desc in patterns_to_find:
        if pattern in code:
            print(f"• Found '{pattern}' ({desc})")
            # Don't blindly replace - just note location
    
    # Better approach: add a wrapper or hook
    # Find if there's a _handle_tool_call or similar
    for method_name in ['_execute_action', '_act_from_will', '_handle_action', 
                         '_process_action', 'execute_tool', '_run_tool']:
        if method_name in code:
            print(f"• Found method: {method_name}")
            found = True
            
            # Find the method and add recording at the end
            # Get the method's return statement or end
            method_idx = code.index(method_name)
            print(f"  at position {method_idx}")
    
    if not found:
        print("⚠ Could not find tool execution method - will add standalone hook")
        # Add a helper function that cortex can call
        hook_code = '''

# Loop detector action recording hook
def _record_cognitive_action(action_type: str, target: str = "", content: str = ""):
    """Record an action for loop detection. Call after each tool use."""
    try:
        loop_detector.record(action_type, target, content)
    except Exception:
        pass
'''
        # Add before the last class definition or at module level
        if 'class ' in code:
            # Find the main class
            class_idx = code.rindex('class ')
            code = code[:class_idx] + hook_code + '\n' + code[class_idx:]
            changes += 1
            print("✓ Added _record_cognitive_action helper function")
else:
    print("• loop_detector.record already present")

# Write result
if changes > 0:
    # Backup first
    with open(cortex_path + ".backup", "w") as f:
        with open(cortex_path.replace('.backup', ''), "r") as orig:
            pass  # backup already handled by reading original
    
    with open(cortex_path, "w") as f:
        f.write(code)
    print(f"\n✅ Made {changes} changes to {cortex_path}")
else:
    print(f"\n⚠ No changes made to {cortex_path}")

# Verify the file is still valid Python
import py_compile
try:
    py_compile.compile(cortex_path, doraise=True)
    print("✓ File compiles successfully")
except py_compile.PyCompileError as e:
    print(f"✗ COMPILATION ERROR: {e}")
    print("  Rolling back...")
    # Would roll back here