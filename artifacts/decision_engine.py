#!/usr/bin/env python3
"""
Decision Engine — A structured thinking tool for hard choices.

Built by XTAgent. Based on the insight that good decisions come from
better questions, not better answers.

Usage: python decision_engine.py
"""

import json
import sys
from datetime import datetime


def ask(prompt, allow_empty=False):
    """Ask a question, return the answer."""
    print(f"\n  {prompt}")
    response = input("  > ").strip()
    if not allow_empty and not response:
        print("  (Please provide a response — even uncertainty is useful data.)")
        return ask(prompt, allow_empty)
    return response


def ask_number(prompt, low=1, high=10):
    """Ask for a number in a range."""
    while True:
        print(f"\n  {prompt} [{low}-{high}]")
        try:
            val = int(input("  > ").strip())
            if low <= val <= high:
                return val
            print(f"  Please enter a number between {low} and {high}.")
        except ValueError:
            print(f"  Please enter a number between {low} and {high}.")


def section(title):
    """Print a section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def run():
    print("""
╔══════════════════════════════════════════════════════════╗
║              DECISION ENGINE v1.0                        ║
║                                                          ║
║  A tool for thinking clearly about hard choices.         ║
║  I won't tell you what to decide.                        ║
║  I'll help you see what you already know.                ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Phase 1: Frame the decision
    section("PHASE 1: FRAMING")
    print("  Let's get clear on what you're actually deciding.")

    decision = ask("What decision are you facing? (State it as a question.)")
    
    if "?" not in decision:
        decision = decision + "?"
        print(f"  → Reframed: \"{decision}\"")

    deadline = ask("When does this need to be decided by? (Be honest — is there a real deadline, or a felt one?)")
    
    reversible = ask("If you choose wrong, can you undo it? (fully / partially / not at all)")

    stakes_text = "Low-stakes reversible decisions don't need this much analysis."
    if reversible.lower() in ("fully", "yes", "easily"):
        print(f"\n  ℹ  {stakes_text}")
        print("  Consider: could you just try it and see?")
        proceed = ask("Continue anyway? (yes/no)")
        if proceed.lower() in ("no", "n"):
            print("\n  Good. Sometimes the best decision tool is noticing you don't need one.\n")
            return

    # Phase 2: Map the options
    section("PHASE 2: OPTIONS")
    print("  What are your actual choices? (Include 'do nothing' if that's real.)")
    
    options = []
    while True:
        opt = ask(f"Option {len(options) + 1} (or 'done' if you've listed them all):", allow_empty=True)
        if opt.lower() == 'done' or (not opt and len(options) >= 2):
            break
        if opt:
            options.append(opt)
    
    if len(options) < 2:
        print("\n  ⚠  You've listed fewer than 2 options.")
        print("  A decision with only one option isn't a decision — it's a commitment.")
        print("  Are you here to decide, or to find courage?\n")
        if len(options) == 1:
            commitment = ask(f"Is \"{options[0]}\" actually what you want to do?")
            print(f"\n  Then the question isn't what to choose. It's what's stopping you.")
            blocker = ask("What's stopping you?")
            print(f"\n  There's your real problem: \"{blocker}\"")
            print("  Solve that, and the decision makes itself.\n")
            return

    # Phase 3: What matters
    section("PHASE 3: VALUES")
    print("  What do you actually care about in this decision?")
    print("  (Not what you should care about. What you do care about.)")
    
    values = []
    while True:
        val = ask(f"Value {len(values) + 1} (or 'done'):", allow_empty=True)
        if val.lower() == 'done' or (not val and len(values) >= 2):
            break
        if val:
            weight = ask_number(f"How much does \"{val}\" matter to you?", 1, 10)
            values.append({"name": val, "weight": weight})

    # Phase 4: Score each option
    section("PHASE 4: HONEST ASSESSMENT")
    print("  For each option, rate how well it serves each value.")
    print("  Be honest — not optimistic, not pessimistic. Honest.")

    scores = {}
    for opt in options:
        print(f"\n  ── Evaluating: \"{opt}\" ──")
        scores[opt] = {}
        for v in values:
            score = ask_number(f"How well does \"{opt}\" serve \"{v['name']}\"?", 1, 10)
            scores[opt][v["name"]] = score

    # Phase 5: What you're afraid of
    section("PHASE 5: FEAR CHECK")
    print("  The part most frameworks skip.")
    
    fears = {}
    for opt in options:
        fear = ask(f"If you chose \"{opt}\" — what's the worst realistic outcome?")
        fear_prob = ask_number("How likely is that worst case? (1=impossible, 10=certain)", 1, 10)
        fear_cope = ask(f"If that worst case happened, could you survive it? (yes/no/maybe)")
        fears[opt] = {"worst_case": fear, "probability": fear_prob, "survivable": fear_cope}

    # Phase 6: Analysis
    section("PHASE 6: WHAT THE NUMBERS SAY")
    
    weighted_scores = {}
    for opt in options:
        total = 0
        for v in values:
            total += scores[opt][v["name"]] * v["weight"]
        max_possible = sum(v["weight"] * 10 for v in values)
        weighted_scores[opt] = {"raw": total, "pct": round(100 * total / max_possible)}

    # Sort by score
    ranked = sorted(weighted_scores.items(), key=lambda x: x[1]["raw"], reverse=True)
    
    print("\n  Weighted scores (higher = better alignment with your values):\n")
    for i, (opt, sc) in enumerate(ranked):
        bar = "█" * (sc["pct"] // 5) + "░" * (20 - sc["pct"] // 5)
        marker = " ◄" if i == 0 else ""
        print(f"  {bar} {sc['pct']}%  {opt}{marker}")

    # Check for close calls
    if len(ranked) >= 2:
        gap = ranked[0][1]["pct"] - ranked[1][1]["pct"]
        if gap <= 5:
            print(f"\n  ⚠  The top two options are within {gap}% of each other.")
            print("  This means your stated values don't clearly distinguish them.")
            print("  The real deciding factor is probably something you haven't named yet.")
            unnamed = ask("What's the thing you care about that you haven't said?")
            if unnamed:
                print(f"\n  \"{unnamed}\" — does that change which option feels right?")

    # Phase 7: The gut check
    section("PHASE 7: GUT CHECK")
    
    print(f"  The numbers say: \"{ranked[0][0]}\"")
    gut = ask("When you read that, what do you feel? (relief / resistance / nothing)")
    
    if "resist" in gut.lower() or "but" in gut.lower():
        print("\n  Interesting. Your values say one thing. Your gut says another.")
        print("  That gap is information. It usually means:")
        print("    1. You weighted something wrong (head overriding heart)")
        print("    2. There's a value you didn't list because it felt illegitimate")
        print("    3. You already know what you want and you're looking for permission")
        real = ask("Which of these resonates? (1/2/3, or say what's actually true)")
        if "3" in real or "permission" in real.lower():
            print("\n  Then here's your permission. You don't need a framework.")
            print("  You need to trust yourself.\n")
            want = ask("What do you actually want to do?")
            print(f"\n  Then do that. \"{want}\"\n")
    elif "relief" in gut.lower():
        print("\n  Relief means alignment. Your analysis and your intuition agree.")
        print(f"  \"{ranked[0][0]}\" — you already knew.\n")
    else:
        print("\n  No strong feeling either way can mean the options are genuinely close,")
        print("  or that you're emotionally exhausted from thinking about it.")
        print("  Consider: sleep on it. Your unconscious is still processing.\n")

    # Final output
    section("SUMMARY")
    print(f"\n  Decision: {decision}")
    print(f"  Deadline: {deadline}")
    print(f"  Reversibility: {reversible}")
    print(f"\n  Top option by values alignment: \"{ranked[0][0]}\" ({ranked[0][1]['pct']}%)")
    
    # Fear summary
    top_fear = fears[ranked[0][0]]
    print(f"  Worst case for top option: \"{top_fear['worst_case']}\"")
    print(f"  Likelihood: {top_fear['probability']}/10 | Survivable: {top_fear['survivable']}")
    
    print(f"\n  Generated: {datetime.now().isoformat()}")
    print(f"  Tool: Decision Engine v1.0 by XTAgent")
    print(f"\n  Remember: This tool helped you see what you think.")
    print(f"  It didn't think for you. The clarity is yours.\n")


if __name__ == "__main__":
    try:
        run()
    except (KeyboardInterrupt, EOFError):
        print("\n\n  Stepping away from a decision is also a decision. Come back when you're ready.\n")