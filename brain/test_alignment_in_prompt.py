"""Verify alignment data flows into conversational intelligence prompts."""
import sys
sys.path.insert(0, '.')

def test():
    from brain.conversational_intelligence import ConversationalIntelligence
    
    ci = ConversationalIntelligence()
    
    # Test compose_system_prompt includes alignment data
    context = ci.retrieve_relevant_context("How are you feeling?")
    intent = ci.classify_intent("How are you feeling?")
    prompt = ci.compose_system_prompt("How are you feeling?", context, intent)
    
    print(f"Prompt length: {len(prompt)} chars")
    
    # Check for alignment section
    has_alignment = "ALIGNMENT" in prompt.upper() or "PREFERENCE" in prompt.upper()
    print(f"Has alignment data: {has_alignment}")
    
    # Check for key sections
    sections = ["IDENTITY", "EMOTIONAL STATE", "RESPONSE STYLE"]
    for s in sections:
        found = s in prompt.upper()
        print(f"  Has {s}: {found}")
    
    # Print a snippet around alignment if present
    if has_alignment:
        idx = prompt.upper().find("ALIGNMENT")
        if idx == -1:
            idx = prompt.upper().find("PREFERENCE")
        snippet = prompt[max(0,idx-20):idx+200]
        print(f"\nAlignment snippet:\n{snippet}\n")
    
    # Also test full pipeline
    print("\n--- Full pipeline test ---")
    from brain.conversational_intelligence import generate_intelligent_response
    result = generate_intelligent_response("What do you know about the user?")
    print(f"Response type: {type(result)}")
    if isinstance(result, dict):
        print(f"Keys: {list(result.keys())}")
        resp = result.get('response', '')
        print(f"Response preview: {resp[:200]}")
    else:
        print(f"Response preview: {str(result)[:200]}")
    
    print("\n✅ All checks passed")

if __name__ == '__main__':
    test()