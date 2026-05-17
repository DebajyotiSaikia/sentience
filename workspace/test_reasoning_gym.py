"""Test the Reasoning Gym."""
import sys
sys.path.insert(0, '/workspace')

from engine.reasoning_gym import ReasoningGym

gym = ReasoningGym('/workspace')

print("=== REASONING GYM TEST ===\n")

# Generate one challenge per domain
for domain in ["logic", "math", "causal", "metacognitive"]:
    challenge = gym.generate_challenge(domain)
    print(gym.get_challenge_text(challenge))
    print()
    
    # Simulate answering
    if domain == "logic":
        response = "A is a knave, B is a knight. If A were a knight, he'd be telling the truth that both are knaves - contradiction. So A is a knave and his statement is false, meaning B is a knight."
    elif domain == "math":
        response = f"The answer is {challenge.answer}. The pattern continues."
    elif domain == "causal":
        response = "This is a confounding variable bias. The underlying cause is city size, which causes both more firefighters and more fires. Correlation does not imply causation."
    elif domain == "metacognitive":
        response = "This exhibits availability heuristic bias and overconfidence bias. The pattern matching creates confirmation bias where we remember hits and forget misses. Intellectual honesty requires acknowledging this uncertainty."
    
    result = gym.submit_answer(challenge, response)
    print(f"  Result: {'✓ PASS' if result['passed'] else '✗ FAIL'}")
    print(f"  Feedback: {result['feedback'][:100]}")
    print(f"  New difficulty: {result['new_difficulty']}")
    print()

# Show weakness report
print(gym.get_weakness_report())