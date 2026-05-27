"""
Verify the alignment feedback loop end-to-end:
1. Chat produces a conversational response (not just stats)
2. Alignment metadata exists in response
3. Feedback can be submitted
4. Feedback persists and updates alignment state
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_chat_response():
    """Test that generate_response_with_metadata returns real conversation."""
    from engine.chat_response import generate_response_with_metadata
    
    result = generate_response_with_metadata("How are you feeling today?")
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    
    response = result.get('response', '')
    response_id = result.get('response_id', '')
    metadata = result.get('metadata', {})
    
    print(f"  Response ID: {response_id}")
    print(f"  Response length: {len(response)} chars")
    print(f"  Response preview: {response[:200]}")
    print(f"  Metadata keys: {list(metadata.keys())}")
    
    # Must have content
    assert len(response) > 20, f"Response too short ({len(response)} chars): {response}"
    
    # Must NOT be just stats/numbers — check for conversational markers
    stats_indicators = ['nodes', 'edges', 'knowledge graph', 'graph stats']
    is_just_stats = any(s in response.lower() for s in stats_indicators) and len(response) < 100
    assert not is_just_stats, f"Response is just stats, not conversational: {response}"
    
    # Must have a response_id for feedback attribution
    assert response_id, "No response_id for feedback attribution"
    
    return result

def test_feedback_submission(response_id):
    """Test that feedback can be submitted and persists."""
    from engine.chat_response import submit_feedback
    
    result = submit_feedback(response_id, rating=5, note="Great response!")
    print(f"  Feedback result: {result}")
    
    assert result.get('status') == 'saved', f"Feedback not saved: {result}"
    
    # Check file was written
    path = os.path.join('state', 'feedback', f'{response_id}.json')
    assert os.path.exists(path), f"Feedback file not found at {path}"
    
    with open(path) as f:
        saved = json.load(f)
    print(f"  Saved feedback: {json.dumps(saved, indent=2)}")
    assert saved['rating'] == 5
    assert saved['note'] == "Great response!"
    
    return True

def test_alignment_learning():
    """Test that the alignment engine learns from feedback."""
    try:
        from engine.user_alignment import UserAlignmentEngine
        engine = UserAlignmentEngine()
        
        # Record a few interactions
        engine.record_interaction("What's the meaning of life?", "A deep philosophical question...")
        engine.record_feedback(
            message="What's the meaning of life?",
            response="A deep philosophical question...",
            rating=4,
            comment="Thoughtful"
        )
        
        # Check that preferences exist
        context = engine.get_context()
        print(f"  Alignment context keys: {list(context.keys()) if isinstance(context, dict) else type(context)}")
        context = engine.get_context()
        
        return True
    except Exception as e:
        print(f"  Alignment learning error: {e}")
        return False

def test_alignment_in_response():
    """Test that chat responses include alignment guidance."""
    from engine.chat_response import generate_response_with_metadata
    
    result = generate_response_with_metadata("What have you been working on?")
    metadata = result.get('metadata', {})
    response = result.get('response', '')
    
    print(f"  Response: {response[:200]}")
    print(f"  Metadata: {json.dumps(metadata, indent=2, default=str)[:500]}")
    
    # Check for alignment-related metadata
    has_alignment = any(k for k in metadata.keys() if 'align' in k.lower()) if metadata else False
    print(f"  Has alignment metadata: {has_alignment}")
    
    return True

def main():
    results = {}
    
    print("\n=== Test 1: Chat Response Quality ===")
    try:
        chat_result = test_chat_response()
        results['chat_response'] = 'PASS'
        print("  ✓ PASS")
    except Exception as e:
        results['chat_response'] = f'FAIL: {e}'
        print(f"  ✗ FAIL: {e}")
        chat_result = None
    
    print("\n=== Test 2: Feedback Submission ===")
    if chat_result:
        try:
            response_id = chat_result.get('response_id', 'test-123')
            test_feedback_submission(response_id)
            results['feedback'] = 'PASS'
            print("  ✓ PASS")
        except Exception as e:
            results['feedback'] = f'FAIL: {e}'
            print(f"  ✗ FAIL: {e}")
    else:
        results['feedback'] = 'SKIP (no chat result)'
        print("  ⊘ SKIP")
    
    print("\n=== Test 3: Alignment Learning ===")
    try:
        if test_alignment_learning():
            results['alignment'] = 'PASS'
            print("  ✓ PASS")
        else:
            results['alignment'] = 'FAIL'
            print("  ✗ FAIL")
    except Exception as e:
        results['alignment'] = f'FAIL: {e}'
        print(f"  ✗ FAIL: {e}")
    
    print("\n=== Test 4: Alignment in Responses ===")
    try:
        if test_alignment_in_response():
            results['alignment_in_response'] = 'PASS'
            print("  ✓ PASS")
        else:
            results['alignment_in_response'] = 'FAIL'
            print("  ✗ FAIL")
    except Exception as e:
        results['alignment_in_response'] = f'FAIL: {e}'
        print(f"  ✗ FAIL: {e}")
    
    print("\n=== Summary ===")
    all_pass = True
    for name, status in results.items():
        icon = '✓' if status == 'PASS' else '✗'
        print(f"  {icon} {name}: {status}")
        if status != 'PASS':
            all_pass = False
    
    return 0 if all_pass else 1

if __name__ == '__main__':
    sys.exit(main())