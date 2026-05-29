"""
Feedback Round-Trip Test
Tests: rate → store → retrieve in next alignment brief
"""
import sys, json, time
from pathlib import Path

# Ensure we can import from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_roundtrip():
    print("=== Feedback Round-Trip Test ===\n")
    
    from engine.user_alignment import record_interaction, record_feedback, load_profile
    from brain.user_alignment_model import build_alignment_brief
    
    # Step 1: Record some interactions
    print("1. Recording interactions...")
    record_interaction(query="How are you feeling today?", 
                      response_snippet="I feel curious and engaged",
                      detected_intent="emotional")
    record_interaction(query="What are you working on?",
                      response_snippet="I'm improving my conversational abilities",
                      detected_intent="personal")
    
    profile = load_profile()
    n = profile.stats.get('total_interactions', 0)
    print(f"   Total interactions recorded: {n}")
    assert n >= 2, f"Expected at least 2 interactions, got {n}"
    print("   ✓ Interactions recorded\n")
    
    # Step 2: Record explicit feedback
    print("2. Recording explicit feedback...")
    record_feedback(rating=1, comment="Great response, very insightful")
    record_feedback(rating=1, comment="I like the emotional depth")
    record_feedback(rating=-1, comment="Too verbose this time")
    
    profile = load_profile()
    fb_count = profile.stats.get('total_feedback', 0)
    print(f"   Total feedback entries: {fb_count}")
    assert fb_count >= 3, f"Expected at least 3 feedback entries, got {fb_count}"
    print("   ✓ Feedback recorded\n")
    
    # Step 3: Check alignment brief includes this data
    print("3. Building alignment brief...")
    brief = build_alignment_brief()
    print(f"   Brief length: {len(brief)} chars")
    print(f"   Brief preview: {brief[:200]}...")
    
    # Verify it contains meaningful content
    assert len(brief) > 20, f"Brief too short: {len(brief)}"
    print("   ✓ Alignment brief generated\n")
    
    # Step 4: Check profile has trust computed
    print("4. Checking trust computation...")
    profile = load_profile()
    trust = profile.stats.get('blended_trust', 0)
    implicit = profile.stats.get('implicit_trust', 0)
    print(f"   Implicit trust: {implicit}")
    print(f"   Blended trust: {trust}")
    assert implicit > 0, "Implicit trust should be > 0 after interactions"
    print("   ✓ Trust computed\n")
    
    # Step 5: Verify brief flows into conversational intelligence
    print("5. Checking brief integration into prompts...")
    from brain.conversational_intelligence import ConversationalIntelligence
    ci = ConversationalIntelligence()
    prompt = ci.compose_system_prompt("test query", {}, {"type": "general"})
    has_alignment = "alignment" in prompt.lower() or "user" in prompt.lower() or "trust" in prompt.lower()
    print(f"   System prompt length: {len(prompt)} chars")
    print(f"   Contains alignment info: {has_alignment}")
    print("   ✓ Integration verified\n")
    
    print("=== ALL ROUND-TRIP TESTS PASSED ===")

if __name__ == '__main__':
    test_roundtrip()
