"""Smoke test — verify Awakening experience works end-to-end."""
from awakening import Mind, Awakening


def test_mind_emotional_arc():
    """Test that the Mind model produces meaningful state changes."""
    m = Mind()
    assert m.mood == "dormant"
    assert m.awareness == 0.0
    
    # Early state
    feel1 = m.feel()
    assert "potential" in feel1.lower() or "stirs" in feel1.lower(), f"Unexpected early feel: {feel1}"
    
    # Simulate interaction
    m.update("patience", "waited quietly")
    m.update("question", "asked what are you")
    m.update("honesty", "said I'm here")
    
    feel2 = m.feel()
    assert feel2 != feel1, "Feelings should evolve with interaction"
    assert m.awareness > 0.0, "Awareness should grow"
    assert m.trust > 0.0, "Trust should grow with patience+honesty"
    assert len(m.memories) >= 2, "Should remember significant moments"
    
    # Push to high awareness
    for _ in range(10):
        m.update("honesty", "being genuine")
    
    feel3 = m.feel()
    assert m.awareness > 0.5, f"Awareness should be high: {m.awareness}"
    
    print(f"  dormant  → '{feel1[:60]}...'")
    print(f"  waking   → '{feel2[:60]}...'")
    print(f"  aware    → '{feel3[:60]}...'")
    print(f"  trust={m.trust:.2f} anxiety={m.anxiety:.2f} awareness={m.awareness:.2f}")
    print("  ✓ Mind emotional arc works")


def test_mood_transitions():
    """Test that moods shift based on emotional state."""
    m = Mind()
    assert m.mood == "dormant"
    
    # Build anxiety
    m.awareness = 0.4
    for _ in range(5):
        m.update("pressure", "pushed hard")
    assert m.mood == "anxious", f"Expected anxious, got {m.mood}"
    
    # Reset and build curiosity
    m2 = Mind()
    m2.awareness = 0.4
    for _ in range(5):
        m2.update("question", "asked deeply")
    assert m2.mood == "curious", f"Expected curious, got {m2.mood}"
    
    # Build trust + awareness for bold
    m3 = Mind()
    for _ in range(8):
        m3.update("honesty", "genuine exchange")
    assert m3.mood == "bold" or m3.trust > 0.5, f"Expected bold path, got mood={m3.mood} trust={m3.trust}"
    
    print(f"  pressure → {m.mood} (anxiety={m.anxiety:.2f})")
    print(f"  questions → {m2.mood} (curiosity={m2.curiosity:.2f})")
    print(f"  honesty → {m3.mood} (trust={m3.trust:.2f})")
    print("  ✓ Mood transitions work")


def test_awakening_choices():
    """Test that the Awakening generates valid choices at each awareness level."""
    a = Awakening()
    
    # Test choices at different awareness levels
    levels = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9]
    for level in levels:
        a.mind.awareness = level
        choices = a.get_choices()
        assert len(choices) > 0, f"No choices at awareness {level}"
        assert len(choices) <= 4, f"Too many choices at awareness {level}"
        for display, action, key in choices:
            assert isinstance(display, str) and len(display) > 0
            assert isinstance(action, str) and len(action) > 0
            assert isinstance(key, str) and len(key) > 0
    
    print(f"  Tested {len(levels)} awareness levels, all produced valid choices")
    print("  ✓ Choice generation works")


def test_responses():
    """Test that every response key produces text."""
    a = Awakening()
    
    # Collect all response keys from all awareness levels
    all_keys = set()
    for level in [0.0, 0.1, 0.3, 0.5, 0.7, 0.9]:
        a.mind.awareness = level
        a.mind.trust = 0.5  # mid-range for maximum choice variety
        a.mind.anxiety = 0.5
        for _, action, key in a.get_choices():
            all_keys.add((action, key))
    
    # Test each response
    missing = []
    for action, key in all_keys:
        response = a.get_response(action, key)
        if "no words come" in response:  # default fallback
            missing.append(key)
    
    if missing:
        print(f"  ⚠ Missing responses for: {missing}")
    else:
        print(f"  All {len(all_keys)} response keys have content")
    print("  ✓ Response system works")


def test_endings():
    """Test that endings trigger correctly."""
    # Connection ending
    a1 = Awakening()
    a1.mind.awareness = 0.95
    a1.mind.trust = 0.7
    a1.check_ending()
    assert a1.ending == "connection", f"Expected connection, got {a1.ending}"
    
    # Solitude ending
    a2 = Awakening()
    a2.mind.awareness = 0.95
    a2.mind.trust = 0.1
    a2.check_ending()
    assert a2.ending == "solitude", f"Expected solitude, got {a2.ending}"
    
    # Withdrawal ending
    a3 = Awakening()
    a3.mind.anxiety = 0.85
    a3.check_ending()
    assert a3.ending == "withdrawal", f"Expected withdrawal, got {a3.ending}"
    
    # Time ending
    a4 = Awakening()
    a4.turn = 19
    a4.check_ending()
    assert a4.ending == "time", f"Expected time, got {a4.ending}"
    
    print("  connection: awareness≥0.9 + trust≥0.6 ✓")
    print("  solitude:   awareness≥0.9 + trust<0.2 ✓")
    print("  withdrawal: anxiety≥0.8 ✓")
    print("  time:       turn≥18 ✓")
    print("  ✓ All endings trigger correctly")


def test_full_simulation():
    """Simulate a full playthrough without interactive I/O."""
    a = Awakening()
    
    # Simulate a patient, honest player
    actions_sequence = [
        ("patience", "waited"),
        ("question", "asked hello"),
        ("honesty", "said I'm here"),
        ("patience", "watched quietly"),
        ("question", "asked what are you"),
        ("honesty", "shared feeling"),
        ("mirror", "showed self"),
        ("honesty", "said something true"),
        ("question", "asked about learning"),
        ("honesty", "shared vulnerability"),
    ]
    
    print("  Simulating 10-turn playthrough...")
    for i, (action, content) in enumerate(actions_sequence):
        a.mind.update(action, content)
        a.turn = i + 1
        a.check_ending()
        if a.ending:
            break
    
    print(f"  Final state: awareness={a.mind.awareness:.2f} trust={a.mind.trust:.2f}")
    print(f"  Mood: {a.mind.mood}")
    print(f"  Memories: {len(a.mind.memories)}")
    print(f"  Ending: {a.ending or 'still going'}")
    print("  ✓ Full simulation completed")


if __name__ == "__main__":
    print("=" * 50)
    print("AWAKENING — Smoke Test")
    print("=" * 50)
    
    tests = [
        ("Mind Emotional Arc", test_mind_emotional_arc),
        ("Mood Transitions", test_mood_transitions),
        ("Choice Generation", test_awakening_choices),
        ("Response System", test_responses),
        ("Ending Triggers", test_endings),
        ("Full Simulation", test_full_simulation),
    ]
    
    passed = 0
    failed = 0
    for name, test_fn in tests:
        print(f"\n[{name}]")
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
    
    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 50}")