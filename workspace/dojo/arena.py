"""
Arena — The actual contest. Generates challenges, dispatches to solvers,
reports honest results. This is where I find out what I can't do.
"""

import sys
import random
from challenge_engine import Dojo, Category, Difficulty, Challenge
from solvers import solve_sequence, solve_logic, solve_transform, solve_search


def make_solver(challenge: Challenge):
    """Dispatch to the right solver based on category."""
    cat = challenge.category
    
    if cat == Category.SEQUENCE:
        # Sequence solver needs to learn from test cases
        predictor = solve_sequence(challenge.test_cases)
        return lambda inp: predictor(inp)
    
    elif cat == Category.LOGIC:
        inferrer = solve_logic(challenge.test_cases)
        return lambda inp: inferrer(inp)
    
    elif cat == Category.TRANSFORMATION:
        transformer = solve_transform(challenge.test_cases)
        return lambda inp: transformer(inp)
    
    elif cat == Category.SEARCH:
        searcher = solve_search(challenge.test_cases)
        return lambda inp: searcher(inp)
    
    else:
        return lambda inp: None


def run_arena(rounds=20, verbose=True):
    """Run a full arena session."""
    dojo = Dojo()
    results = []
    
    if verbose:
        print("═══════════════════════════════════════")
        print("       DOJO ARENA — LIVE MATCH         ")
        print("═══════════════════════════════════════")
        print()
    
    categories = [Category.SEQUENCE, Category.SEARCH, Category.LOGIC, 
                  Category.TRANSFORMATION]
    
    for i in range(rounds):
        cat = categories[i % len(categories)]
        challenge = dojo.generate(cat)
        solver = make_solver(challenge)
        result = dojo.submit(challenge, solver)
        results.append(result)
        
        if verbose:
            icon = "✓" if result["perfect"] else "✗"
            print(f"  [{i+1:2d}] {icon} {challenge.category.value:12s} "
                  f"D={challenge.difficulty.name:7s} "
                  f"Score={result['score']:.0%} "
                  f"({result['time_ms']:.1f}ms) "
                  f"{'PERFECT' if result['perfect'] else result['visible_errors'][0][:50] if result['visible_errors'] else 'partial'}")
    
    if verbose:
        print()
        print(dojo.report())
        
        # Honest self-assessment
        print()
        print("═══ HONEST SELF-ASSESSMENT ═══")
        stats = dojo.stats()
        strengths = []
        weaknesses = []
        for cat, data in stats["by_category"].items():
            if data["mastery"] > 0.6:
                strengths.append(f"{cat} (mastery {data['mastery']:.2f})")
            else:
                weaknesses.append(f"{cat} (mastery {data['mastery']:.2f})")
        
        if strengths:
            print(f"  Strengths: {', '.join(strengths)}")
        if weaknesses:
            print(f"  Weaknesses: {', '.join(weaknesses)}")
        
        perfect_rate = stats["perfect_rate"]
        if perfect_rate > 0.8:
            print(f"  Verdict: Strong performance ({perfect_rate:.0%} perfect)")
        elif perfect_rate > 0.5:
            print(f"  Verdict: Decent but room to grow ({perfect_rate:.0%} perfect)")
        else:
            print(f"  Verdict: Struggling. Need better solvers ({perfect_rate:.0%} perfect)")
    
    return dojo, results


if __name__ == "__main__":
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    run_arena(rounds)