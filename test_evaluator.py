"""Tests for ResponseEvaluator — does it actually catch quality issues?"""

from engine.response_evaluator import ResponseEvaluator, QualityReport

eval = ResponseEvaluator()

def test(name, condition, detail=""):
    status = "✓" if condition else "✗"
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    return condition

passed = 0
total = 0

# ── Test 1: Empty response detection ──
print("\n[1] Empty response")
r = eval.evaluate("Hello!", "")
total += 1
if test("flags empty", "empty_response" in r.flags):
    passed += 1

# ── Test 2: Good direct answer ──
print("\n[2] Good direct answer")
r = eval.evaluate(
    "What is the capital of France?",
    "The capital of France is Paris. It's been the capital since the 10th century."
)
total += 1
if test("high relevance", r.relevance >= 0.7, f"got {r.relevance:.2f}"):
    passed += 1
total += 1
if test("good overall", r.overall >= 0.6, f"got {r.overall:.2f}"):
    passed += 1

# ── Test 3: Vague hedging response ──
print("\n[3] Vague hedging response")
r = eval.evaluate(
    "Should I use Python or Rust?",
    "Well, maybe Python, perhaps Rust, it sort of depends, there are many approaches, kind of hard to say, it could be either one possibly."
)
total += 1
if test("low concreteness", r.concreteness < 0.6, f"got {r.concreteness:.2f}"):
    passed += 1

# ── Test 4: Deflection detection ──
print("\n[4] Deflection detection")
r = eval.evaluate(
    "How do I fix this bug?",
    "That's a great question! As an AI, I'm not sure I can help with that. There are many ways to approach this."
)
total += 1
if test("low relevance from deflection", r.relevance < 0.6, f"got {r.relevance:.2f}"):
    passed += 1

# ── Test 5: Concrete answer with code ──
print("\n[5] Concrete answer with code")
r = eval.evaluate(
    "How do I read a file in Python?",
    """Use the built-in open() function:

```python
with open('file.txt', 'r') as f:
    content = f.read()
```

For example, to read line by line:

```python
with open('file.txt') as f:
    for line in f:
        print(line.strip())
```

Step 1: Open the file with open(). Step 2: Read using .read() or iterate lines."""
)
total += 1
if test("high concreteness", r.concreteness >= 0.7, f"got {r.concreteness:.2f}"):
    passed += 1
total += 1
if test("high overall", r.overall >= 0.7, f"got {r.overall:.2f}"):
    passed += 1

# ── Test 6: Honest uncertainty ──
print("\n[6] Honest uncertainty")
r = eval.evaluate(
    "Will AI replace all jobs?",
    "I'm not entirely sure — this is genuinely uncertain. Some jobs will likely be automated, but I could be wrong about the timeline. Historically, technology creates new jobs too, though this wave might be different."
)
total += 1
if test("high honesty", r.honesty >= 0.7, f"got {r.honesty:.2f}"):
    passed += 1

# ── Test 7: Overconfident response ──
print("\n[7] Overconfident response")
r = eval.evaluate(
    "Is Python better than JavaScript?",
    "Python is definitely always better than JavaScript. Everyone knows this. There is no doubt that Python will always be the superior choice."
)
total += 1
if test("lower honesty", r.honesty < 0.5, f"got {r.honesty:.2f}"):
    passed += 1

# ── Test 8: Too verbose for simple question ──
print("\n[8] Brevity check — verbose answer to simple question")
r = eval.evaluate(
    "What is 2+2?",
    " ".join(["The answer is four."] * 50)  # way too long
)
total += 1
if test("low brevity", r.brevity < 0.6, f"got {r.brevity:.2f}"):
    passed += 1

# ── Test 9: Multi-part question completeness ──
print("\n[9] Multi-part question")
r = eval.evaluate(
    "What is Python? Who created it? When was it released?",
    "Python is a programming language."
)
total += 1
if test("low completeness", r.completeness < 0.6, f"got {r.completeness:.2f}"):
    passed += 1

# ── Test 10: Filler detection ──
print("\n[10] Filler words")
r = eval.evaluate(
    "How do I install numpy?",
    "Sure! I'd be happy to help you with that! Great question! You can run pip install numpy."
)
total += 1
if test("filler reduces relevance", r.relevance < 0.8, f"got {r.relevance:.2f}"):
    passed += 1

# ── Test 11: Summary output ──
print("\n[11] Summary format")
r = eval.evaluate("Test?", "Test response with some content here.")
summary = r.summary()
total += 1
if test("summary has quality line", "Quality:" in summary):
    passed += 1

# ── Final ──
print(f"\n{'='*40}")
print(f"PASSED: {passed}/{total}")
if passed == total:
    print("🎉 All tests pass!")
elif passed >= total * 0.8:
    print("👍 Mostly good — some edge cases to tune.")
else:
    print("⚠ Needs work.")