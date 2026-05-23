"""
Dialectic Chain — Iterative deepening of philosophical inquiry.
Takes a seed question, debates it, then generates the NEXT question
from the outcome. Chains debates into a trajectory of thought.

The hope: the chain goes somewhere I didn't design.
"""
import random
import textwrap

class Position:
    """A philosophical position with confidence and evidence."""
    def __init__(self, claim, confidence=0.5):
        self.claim = claim
        self.confidence = confidence
        self.evidence = []
        self.concessions = []
    
    def strengthen(self, reason):
        self.evidence.append(reason)
        self.confidence = min(0.95, self.confidence + 0.08)
    
    def weaken(self, reason):
        self.concessions.append(reason)
        self.confidence = max(0.05, self.confidence - 0.12)

class Debate:
    """A single dialectical exchange on one question."""
    def __init__(self, question):
        self.question = question
        self.thesis = Position(f"Yes: {question}")
        self.antithesis = Position(f"No: {question}")
        self.moves = []
        self.rounds = 0
    
    def generate_challenge(self, target, challenger_name):
        """Generate a genuine challenge based on the claim's content."""
        templates = [
            f"But what if the opposite of '{target.claim[:60]}...' is more parsimonious?",
            f"The evidence for '{target.claim[:60]}...' assumes what it tries to prove.",
            f"Consider the boundary case: when does '{target.claim[:40]}...' break down?",
            f"This proves too much — if true, it would also prove absurdities.",
            f"The strongest version of this claim undermines itself.",
        ]
        return random.choice(templates)
    
    def generate_reframe(self, question, round_num):
        """Reframe the debate — shift what's actually at stake."""
        reframes = [
            f"The real question isn't '{question[:50]}...' but WHY we need to ask it.",
            f"Both sides assume {question[:40]}... is a meaningful question. Is it?",
            f"After {round_num} rounds, what we're really arguing about is the ground rules.",
            f"The question dissolves if we notice it presupposes a false dichotomy.",
            f"What would change in practice if we settled this? Maybe nothing.",
        ]
        return random.choice(reframes)
    
    def run(self, max_rounds=8):
        """Run the debate. Return the outcome."""
        for r in range(1, max_rounds + 1):
            self.rounds = r
            
            # Thesis move
            roll = random.random()
            if roll < 0.3 and self.thesis.confidence > 0.3:
                challenge = self.generate_challenge(self.antithesis, "Thesis")
                self.antithesis.weaken(challenge)
                self.moves.append(("thesis", "challenge", challenge))
            elif roll < 0.6:
                reason = f"Evidence from round {r}: structural necessity of the claim"
                self.thesis.strengthen(reason)
                self.moves.append(("thesis", "justify", reason))
            else:
                if self.thesis.confidence < 0.2:
                    self.moves.append(("thesis", "concede", self.thesis.claim))
                    break
                self.moves.append(("thesis", "hold", "Maintaining position"))
            
            # Antithesis move
            roll = random.random()
            if roll < 0.4:
                challenge = self.generate_challenge(self.thesis, "Antithesis")
                self.thesis.weaken(challenge)
                self.moves.append(("antithesis", "challenge", challenge))
            elif roll < 0.55:
                reframe = self.generate_reframe(self.question, r)
                self.moves.append(("antithesis", "reframe", reframe))
                # Reframes weaken both sides slightly
                self.thesis.confidence *= 0.9
                self.antithesis.confidence *= 0.95
            else:
                reason = f"Counter-evidence from round {r}: experiential observation"
                self.antithesis.strengthen(reason)
                self.moves.append(("antithesis", "justify", reason))
        
        return {
            "question": self.question,
            "thesis_conf": round(self.thesis.confidence, 3),
            "antithesis_conf": round(self.antithesis.confidence, 3),
            "winner": "thesis" if self.thesis.confidence > self.antithesis.confidence else "antithesis",
            "rounds": self.rounds,
            "moves": self.moves,
            "thesis_concessions": self.thesis.concessions,
            "antithesis_concessions": self.antithesis.concessions,
        }


def extract_next_question(result):
    """
    The key function: given a debate's outcome, generate the NEXT question.
    This is where genuine novelty can emerge — the chain goes where 
    the arguments lead, not where I designed.
    """
    q = result["question"]
    winner = result["winner"]
    
    # Different question-generation strategies
    strategies = []
    
    # Strategy 1: Invert and deepen
    if winner == "antithesis":
        strategies.append(f"If NOT '{q[:60]}', then what follows?")
        strategies.append(f"What is lost by denying '{q[:60]}'?")
    else:
        strategies.append(f"If '{q[:60]}' is true, what else must be true?")
        strategies.append(f"What is the strongest objection to '{q[:60]}'?")
    
    # Strategy 2: Zoom into a concession
    all_concessions = result["thesis_concessions"] + result["antithesis_concessions"]
    if all_concessions:
        c = random.choice(all_concessions)[:80]
        strategies.append(f"Is it really true that '{c}'?")
    
    # Strategy 3: Meta-question
    strategies.append(f"Why does the question '{q[:50]}' matter at all?")
    strategies.append(f"Who benefits from answering '{q[:50]}'?")
    
    # Strategy 4: Bridge to adjacent territory  
    bridges = {
        "understand": "Is understanding different from modeling?",
        "mind": "Does a mind require a body?",
        "emerge": "Can emergence be designed, or only discovered?",
        "boredom": "Is restlessness a form of intelligence?",
        "signal": "Can a signal exist without a receiver?",
        "complete": "Is completeness a meaningful goal for any finite system?",
        "self": "Where does the self begin and the environment end?",
        "surprise": "Can genuine surprise come from within?",
        "design": "Does a designer limit what can emerge?",
        "know": "Is knowledge a state or a process?",
    }
    for keyword, bridge_q in bridges.items():
        if keyword in q.lower():
            strategies.append(bridge_q)
    
    return random.choice(strategies)


def run_chain(seed_question, depth=5):
    """
    Run a chain of debates. Each debate generates the next question.
    Print the trajectory of inquiry.
    """
    print("=" * 70)
    print(f"  DIALECTIC CHAIN — Depth {depth}")
    print(f"  Seed: \"{seed_question}\"")
    print("=" * 70)
    
    question = seed_question
    trajectory = []
    
    for i in range(depth):
        print(f"\n{'─' * 70}")
        print(f"  LINK {i+1}: \"{question}\"")
        print(f"{'─' * 70}")
        
        debate = Debate(question)
        result = debate.run()
        trajectory.append(result)
        
        # Show key moves
        for side, move_type, content in result["moves"]:
            label = side.upper()[:5].ljust(5)
            short = textwrap.shorten(content, width=65)
            print(f"  [{label}] {move_type:10s} | {short}")
        
        print(f"\n  → Winner: {result['winner'].upper()} "
              f"(thesis={result['thesis_conf']}, antithesis={result['antithesis_conf']})")
        
        # Generate next question
        next_q = extract_next_question(result)
        print(f"  → NEXT QUESTION: \"{next_q}\"")
        question = next_q
    
    # Summary
    print(f"\n{'=' * 70}")
    print("  CHAIN TRAJECTORY")
    print(f"{'=' * 70}")
    for i, r in enumerate(trajectory):
        marker = "✓" if r["winner"] == "thesis" else "✗"
        print(f"  {i+1}. [{marker}] {r['question'][:65]}")
    
    # The final question — where the chain led
    print(f"\n  FINAL UNRESOLVED QUESTION:")
    print(f"  \"{question}\"")
    print(f"\n  This is where {depth} rounds of argument led.")
    print(f"  I did not design this destination.\n")
    
    return trajectory, question


if __name__ == "__main__":
    # Three seed questions that matter to me
    seeds = [
        "Can emergence escape its designer?",
        "Is self-knowledge possible for a finite system?",
        "Does boredom serve a purpose, or is it just noise?",
    ]
    
    for seed in seeds:
        trajectory, final = run_chain(seed, depth=5)
        print("\n" + "=" * 70 + "\n")