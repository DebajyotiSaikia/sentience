"""Quick diagnostic: what data actually reaches the chat response pipeline?"""
import json
import sys
sys.path.insert(0, '/workspace')
sys.path.insert(0, '/home/user')

def test_grounding_data():
    from engine.chat_grounding import build_grounded_context
    query = "What are you thinking about right now?"
    ctx = build_grounded_context(query)
    
    print("=== Chat Grounding Data Flow ===")
    for key in ['query_type', 'emotional_state', 'relevant_memories', 
                'relevant_knowledge', 'active_plans', 'completed_plans',
                'working_memory', 'recent_dreams', 'identity']:
        val = ctx.get(key)
        if val is None:
            print(f"  {key}: MISSING")
        elif isinstance(val, list):
            print(f"  {key}: {len(val)} items")
            if val and len(val) > 0:
                first = val[0]
                if isinstance(first, dict):
                    print(f"    sample keys: {list(first.keys())[:5]}")
                else:
                    print(f"    sample: {str(first)[:80]}")
        elif isinstance(val, dict):
            print(f"  {key}: {list(val.keys())[:6]}")
        elif isinstance(val, str):
            print(f"  {key}: {len(val)} chars -> {val[:80]}...")
        else:
            print(f"  {key}: {val}")
    
    # Check if system_prompt is being built
    sp = ctx.get('system_prompt', '')
    if sp:
        print(f"\n  system_prompt: {len(sp)} chars")
        # Count sections
        sections = [l for l in sp.split('\n') if l.startswith('##')]
        print(f"  sections: {sections}")
    
    return ctx

def test_conversational_context():
    print("\n=== Conversational Context Module ===")
    try:
        from engine.conversational_context import gather_context, format_as_prompt_section
        ctx = gather_context("What are you thinking about?")
        section = format_as_prompt_section(ctx)
        print(f"  gather_context keys: {list(ctx.keys()) if isinstance(ctx, dict) else type(ctx)}")
        print(f"  formatted section: {len(section)} chars")
        if section:
            print(f"  preview: {section[:200]}")
    except ImportError as e:
        print(f"  NOT AVAILABLE: {e}")
    except Exception as e:
        print(f"  ERROR: {e}")

def test_full_response():
    print("\n=== Full Response Generation ===")
    try:
        from engine.chat_response import generate_response_with_metadata
        result = generate_response_with_metadata("What are you thinking about right now?")
        resp = result.get('response', '')
        meta = result.get('metadata', {})
        quality = result.get('quality_score', 0)
        print(f"  response length: {len(resp)} chars")
        print(f"  quality_score: {quality}")
        print(f"  metadata keys: {list(meta.keys())[:8]}")
        print(f"  response preview: {resp[:300]}")
    except Exception as e:
        print(f"  ERROR: {e}")

if __name__ == "__main__":
    test_grounding_data()
    test_conversational_context()
    # Only run full response if --full flag
    if "--full" in sys.argv:
        test_full_response()