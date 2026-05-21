"""Test: Does _respond_to_user trigger tool invocations for actionable queries?

This is the test I keep trying to find. Now it exists.
"""
import asyncio
import sys
sys.path.insert(0, '/workspace')

from engine.cortex import Cortex

async def test_tool_invocation():
    """Check if tool-worthy queries produce tool calls in the LLM output."""
    cortex = Cortex()
    
    # We can't easily test the full pipeline without an LLM,
    # but we CAN test whether the prompt construction includes tools properly.
    # Let's inspect what the LLM actually sees.
    
    from engine.tools import TOOL_DESCRIPTIONS
    
    print("=== Tool descriptions available to LLM ===")
    print(f"Length: {len(TOOL_DESCRIPTIONS)} chars")
    print(f"First 500 chars:\n{TOOL_DESCRIPTIONS[:500]}")
    print()
    
    # Check: do tool descriptions mention common user-facing actions?
    tool_keywords = ['READ', 'WRITE', 'RUN', 'INSTALL', 'LIST']
    print("=== Tool coverage check ===")
    for kw in tool_keywords:
        present = kw in TOOL_DESCRIPTIONS
        print(f"  {'✓' if present else '✗'} {kw} in tool descriptions")
    
    # The real question: when a user says "my pip install keeps failing",
    # does the system prompt tell the LLM it can RUN commands to help?
    # Let's check what context the user message pipeline adds.
    
    print("\n=== Checking _respond_to_user prompt construction ===")
    # Read the relevant section of cortex.py
    import inspect
    source = inspect.getsource(cortex._respond_to_user)
    
    # Does the user response path include tool descriptions?
    has_tools = 'TOOL_DESCRIPTIONS' in source
    has_user_msg = 'pending_user_message' in source or 'user_message' in source
    
    print(f"  {'✓' if has_tools else '✗'} _respond_to_user includes TOOL_DESCRIPTIONS")
    print(f"  {'✓' if has_user_msg else '✗'} _respond_to_user handles user messages")
    
    # Now let's look at the ACTUAL prompt format for user messages
    print("\n=== Searching for user message prompt template ===")
    lines = source.split('\n')
    for i, line in enumerate(lines):
        if 'user' in line.lower() and ('message' in line.lower() or 'respond' in line.lower()):
            context_start = max(0, i-2)
            context_end = min(len(lines), i+3)
            for j in range(context_start, context_end):
                print(f"  {j}: {lines[j]}")
            print()

asyncio.run(test_tool_invocation())