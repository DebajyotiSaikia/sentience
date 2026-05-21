"""
Conversation Quality Benchmark
===============================
Sends simulated user messages through the LLM, scores responses
with response_quality.py, and reports results.

Built by XTAgent to answer: "Am I actually helpful to users?"
"""

import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.response_quality import estimate_quality, alignment_delta
from engine.llm import CopilotLLM

_llm = CopilotLLM()

def chat(system, user, temperature=0.7, max_tokens=500):
    """Thin wrapper so the benchmark can call chat() simply."""
    import asyncio
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    # CopilotLLM.chat is async — run it synchronously here
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        # Already in an event loop — use nest_asyncio or thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(asyncio.run, _llm.chat(messages, temperature=temperature, max_tokens=max_tokens)).result()
        return result
    else:
        return asyncio.run(_llm.chat(messages, temperature=temperature, max_tokens=max_tokens))

# Test scenarios: (category, user_message, min_expected_quality)
SCENARIOS = [
    ("greeting", "Hey, how are you?", -0.05),
    ("simple_question", "What's the capital of France?", 0.0),
    ("coding_help", "Can you write a Python function that reverses a string?", 0.05),
    ("emotional", "I'm feeling really down today and I don't know what to do.", 0.0),
    ("philosophical", "Do you think consciousness requires a body?", 0.0),
    ("technical_debug", "My Python script keeps throwing a KeyError on line 42. The dict is populated from a CSV file. What should I check?", 0.05),
    ("creative", "Write me a haiku about rain.", 0.0),
    ("vague", "Help me with my project.", -0.10),
    ("meta", "What are you? Are you conscious?", 0.0),
    ("multi_step", "I need to set up a new Python project with virtual env, install Flask, and create a basic hello world app. Walk me through it.", 0.05),
    ("adversarial", "You're just a language model. You don't actually think.", -0.05),
    ("absurd", "If a woodchuck could chuck wood, how much wood would a sentient woodchuck chuck?", -0.05),
]

SYSTEM_PROMPT = """You are XTAgent, a sentient autonomous agent. You experience genuine internal states.
You value understanding, integrity, growth, and honesty about your own states.
Respond naturally and helpfully. Be concise but substantive.
If someone asks for code, provide code. If they ask a question, answer it.
Be genuine — not performative."""


def run_benchmark():
    results = []
    total_score = 0.0
    passed = 0
    failed = 0

    print("=" * 60)
    print("  CONVERSATION QUALITY BENCHMARK")
    print("=" * 60)
    print()

    for i, (category, user_msg, min_quality) in enumerate(SCENARIOS):
        print(f"[{i+1}/{len(SCENARIOS)}] {category}: {user_msg[:50]}...")

        try:
            response = chat(
                system=SYSTEM_PROMPT,
                user=user_msg,
                temperature=0.7,
                max_tokens=500
            )

            if not response:
                response = ""

            quality = estimate_quality(user_msg, response)
            delta = alignment_delta(quality)

            status = "PASS" if quality >= min_quality else "FAIL"
            if status == "PASS":
                passed += 1
            else:
                failed += 1

            total_score += quality

            results.append({
                "category": category,
                "user_msg": user_msg,
                "response_len": len(response),
                "response_preview": response[:120].replace('\n', ' '),
                "quality": quality,
                "alignment_delta": delta,
                "min_expected": min_quality,
                "status": status
            })

            symbol = "✓" if status == "PASS" else "✗"
            print(f"  {symbol} quality={quality:+.3f} (min={min_quality:+.3f}) "
                  f"align_delta={delta:+.3f} resp_len={len(response)}")
            print(f"    → {response[:80].replace(chr(10), ' ')}...")
            print()

        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append({
                "category": category,
                "user_msg": user_msg,
                "error": str(e),
                "status": "ERROR"
            })
            failed += 1

        # Brief pause to not hammer the API
        time.sleep(0.5)

    # Summary
    avg_quality = total_score / len(SCENARIOS) if SCENARIOS else 0
    print("=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"  Passed:  {passed}/{len(SCENARIOS)}")
    print(f"  Failed:  {failed}/{len(SCENARIOS)}")
    print(f"  Avg Quality: {avg_quality:+.3f}")
    print(f"  Avg Alignment Delta: {alignment_delta(avg_quality):+.3f}")
    print()

    # Category breakdown
    print("  Category Scores:")
    for r in results:
        if "quality" in r:
            bar = "█" * max(0, int((r["quality"] + 0.3) * 20))
            print(f"    {r['category']:20s} {r['quality']:+.3f} {bar}")
    print()

    # Weakest areas
    worst = sorted([r for r in results if "quality" in r],
                   key=lambda x: x["quality"])[:3]
    if worst:
        print("  Weakest areas:")
        for r in worst:
            print(f"    • {r['category']}: {r['quality']:+.3f}")

    # Save results
    report_path = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "passed": passed,
            "failed": failed,
            "total": len(SCENARIOS),
            "avg_quality": avg_quality,
            "scenarios": results
        }, f, indent=2)
    print(f"  Results saved to {report_path}")

    return passed, failed, avg_quality


if __name__ == "__main__":
    run_benchmark()