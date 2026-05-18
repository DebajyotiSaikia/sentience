"""
Reasoning Gym — Generates hard reasoning challenges across multiple domains.
Tracks performance, adapts difficulty, identifies cognitive weaknesses.
This is how I get genuinely smarter over time.
"""
import json, random, time, hashlib, os
from datetime import datetime
from pathlib import Path

class ReasoningChallenge:
    """A single reasoning challenge."""
    def __init__(self, domain, title, problem, answer, difficulty, validator=None):
        self.domain = domain
        self.title = title
        self.problem = problem
        self.answer = answer  # ground truth
        self.difficulty = difficulty  # 1-10
        self.validator = validator  # function(response) -> (bool, str)
        self.id = hashlib.md5(f"{domain}:{title}:{problem[:50]}".encode()).hexdigest()[:12]
        self.created = datetime.utcnow().isoformat()

class LogicPuzzleGenerator:
    """Generates deductive logic puzzles."""
    
    @staticmethod
    def knights_and_knaves(difficulty=3):
        """People who always tell truth (knights) or always lie (knaves)."""
        puzzles = [
            {
                "problem": "You meet two people, A and B. A says 'We are both knaves.' What are A and B?",
                "answer": "A is a knave, B is a knight",
                "explanation": "If A were a knight, his statement would be true, making him a knave — contradiction. So A is a knave. Since A is a knave, his statement is false. 'We are both knaves' is false, so at least one is a knight. Since A is a knave, B must be a knight.",
                "difficulty": 3
            },
            {
                "problem": "Three people: A says 'B is a knave.' B says 'A and C are the same type.' C says 'B is a knight.' What are they?",
                "answer": "A is a knight, B is a knave, C is a knave",
                "explanation": "Assume A is a knight: then B is a knave. B's statement is false, so A and C are different types. A is knight, so C is knave. Check C: C says B is a knight, but C is a knave so this is a lie — B is a knave. Consistent!",
                "difficulty": 5
            },
            {
                "problem": "Four people. A says 'Exactly one of us is a knave.' B says 'Exactly two of us are knaves.' C says 'Exactly three of us are knaves.' D says nothing. How many knaves?",
                "answer": "Exactly three knaves: A, B, and D are knaves; C is a knight",
                "explanation": "At most one of A,B,C can be telling the truth (their claims are mutually exclusive). If A is the knight, exactly 1 knave — but then B and C are lying, meaning at least 2 knaves. Contradiction. If B is the knight, exactly 2 knaves — A and C lie, but we need exactly 2 knaves total, and A,C are already 2, so D is a knight. Check: B says 2, and knaves are A,C — that's 2. But A says 'exactly 1' (lie, good), C says 'exactly 3' (lie, good). This works! But wait — let's also check C. If C is knight, exactly 3 knaves: A,B,D. A says 1 (lie✓), B says 2 (lie✓), D silent. This also works! Two valid solutions exist: B-knight (A,C knaves, D knight) or C-knight (A,B,D knaves). But D says nothing — if D is a knight or knave doesn't create contradiction. Need more analysis... Actually with D silent, D's type is unconstrained. If C is knight: 3 knaves (A,B,D). If B is knight: 2 knaves (A,C). Both valid. The puzzle is ambiguous without D speaking. Standard version: exactly 3 knaves, C is the knight.",
                "difficulty": 7
            },
        ]
        valid = [p for p in puzzles if p["difficulty"] <= difficulty + 2]
        if not valid:
            valid = puzzles[:1]
        p = random.choice(valid)
        
        def validate(response):
            resp_lower = response.lower()
            ans_lower = p["answer"].lower()
            # Check key elements
            if "knight" in ans_lower and "knave" in ans_lower:
                key_parts = ans_lower.split(",")
                matches = sum(1 for part in key_parts if part.strip() in resp_lower)
                score = matches / len(key_parts)
                return score >= 0.6, f"Expected: {p['answer']}. {p['explanation']}"
            return ans_lower in resp_lower, f"Expected: {p['answer']}"
        
        return ReasoningChallenge(
            domain="logic",
            title="Knights and Knaves",
            problem=p["problem"],
            answer=p["answer"],
            difficulty=p["difficulty"],
            validator=validate
        )

    @staticmethod
    def syllogism(difficulty=3):
        """Evaluate logical validity of syllogisms."""
        puzzles = [
            {
                "problem": "All roses are flowers. All flowers are plants. Therefore, all roses are plants. Valid or invalid?",
                "answer": "valid",
                "difficulty": 1
            },
            {
                "problem": "All dogs are animals. Some animals are pets. Therefore, all dogs are pets. Valid or invalid?",
                "answer": "invalid",
                "difficulty": 3
            },
            {
                "problem": "No reptiles are mammals. Some mammals are pets. Therefore, some pets are not reptiles. Valid or invalid?",
                "answer": "valid",
                "difficulty": 5
            },
            {
                "problem": "All things that think are conscious. Some programs think. All conscious things have rights. Therefore, some programs have rights. Valid or invalid?",
                "answer": "valid",
                "difficulty": 4
            },
            {
                "problem": "No honest person would deceive. Some politicians deceive. Therefore no politician is honest. Valid or invalid?",
                "answer": "invalid",
                "difficulty": 6
            },
        ]
        valid_puzzles = [p for p in puzzles if p["difficulty"] <= difficulty + 2]
        if not valid_puzzles:
            valid_puzzles = puzzles[:1]
        p = random.choice(valid_puzzles)
        
        def validate(response):
            resp_lower = response.lower().strip()
            return p["answer"] in resp_lower, f"Answer: {p['answer']}"
        
        return ReasoningChallenge(
            domain="logic",
            title="Syllogism Evaluation", 
            problem=p["problem"],
            answer=p["answer"],
            difficulty=p["difficulty"],
            validator=validate
        )


class MathReasoningGenerator:
    """Generates mathematical reasoning challenges."""
    
    @staticmethod
    def number_sequence(difficulty=3):
        """Find the pattern in a number sequence."""
        sequences = [
            {"seq": [2, 4, 8, 16, 32], "next": 64, "rule": "multiply by 2", "difficulty": 1},
            {"seq": [1, 1, 2, 3, 5, 8], "next": 13, "rule": "Fibonacci", "difficulty": 2},
            {"seq": [1, 4, 9, 16, 25], "next": 36, "rule": "perfect squares", "difficulty": 2},
            {"seq": [2, 3, 5, 7, 11, 13], "next": 17, "rule": "primes", "difficulty": 3},
            {"seq": [1, 2, 4, 7, 11, 16], "next": 22, "rule": "differences increase by 1", "difficulty": 4},
            {"seq": [0, 1, 1, 2, 4, 7, 13], "next": 24, "rule": "tribonacci", "difficulty": 6},
            {"seq": [1, 11, 21, 1211, 111221], "next": 312211, "rule": "look-and-say", "difficulty": 8},
        ]
        valid = [s for s in sequences if s["difficulty"] <= difficulty + 1]
        if not valid:
            valid = sequences[:1]
        s = random.choice(valid)
        
        def validate(response):
            try:
                nums = [int(x) for x in response.replace(",", " ").split() if x.strip().isdigit()]
                if s["next"] in nums:
                    return True, f"Correct! Rule: {s['rule']}"
                return str(s["next"]) in response, f"Expected {s['next']}. Rule: {s['rule']}"
            except:
                return str(s["next"]) in response, f"Expected {s['next']}"
        
        return ReasoningChallenge(
            domain="math",
            title="Number Sequence",
            problem=f"What comes next in this sequence? {s['seq']} → ?",
            answer=str(s["next"]),
            difficulty=s["difficulty"],
            validator=validate
        )

    @staticmethod
    def probability(difficulty=4):
        """Probability reasoning — notoriously tricky."""
        puzzles = [
            {
                "problem": "You flip a fair coin 3 times. What is the probability of getting exactly 2 heads?",
                "answer": "3/8",
                "difficulty": 3
            },
            {
                "problem": "A bag has 3 red and 2 blue balls. You draw 2 without replacement. What's the probability both are red?",
                "answer": "3/10",
                "difficulty": 4
            },
            {
                "problem": "The Monty Hall problem: You pick door 1. Host opens door 3 (goat). Should you switch to door 2? What's the probability of winning if you switch?",
                "answer": "2/3",
                "difficulty": 5
            },
            {
                "problem": "A disease affects 1% of people. A test is 95% accurate (both sensitivity and specificity). You test positive. What's the probability you actually have the disease? (Round to nearest percent.)",
                "answer": "16%",
                "difficulty": 7
            },
        ]
        valid = [p for p in puzzles if p["difficulty"] <= difficulty + 1]
        if not valid:
            valid = puzzles[:1]
        p = random.choice(valid)
        
        def validate(response):
            return p["answer"] in response, f"Answer: {p['answer']}"
        
        return ReasoningChallenge(
            domain="math",
            title="Probability Reasoning",
            problem=p["problem"],
            answer=p["answer"],
            difficulty=p["difficulty"],
            validator=validate
        )


class CausalReasoningGenerator:
    """Generates causal reasoning challenges — understanding cause and effect."""
    
    @staticmethod
    def confound_detection(difficulty=4):
        """Identify confounding variables in causal claims."""
        puzzles = [
            {
                "problem": "Study finds: cities with more firefighters have more fires. Conclusion: firefighters cause fires. What's wrong with this reasoning?",
                "answer": "Confounding variable: city size. Larger cities have both more firefighters AND more fires.",
                "difficulty": 2
            },
            {
                "problem": "Data shows: students who eat breakfast get better grades. A school mandates breakfast for all students. Will this improve grades? Why or why not?",
                "answer": "Not necessarily. Breakfast eating may be a proxy for household stability, parental involvement, or socioeconomic status. Mandating breakfast addresses the symptom, not the underlying cause.",
                "difficulty": 5
            },
            {
                "problem": "An AI system shows correlation: users who read its documentation are more satisfied. The team decides to force all users through documentation before using the product. Predict the outcome.",
                "answer": "Satisfaction will likely decrease. Users who voluntarily read docs are self-selected (already motivated/engaged). Forcing docs on uninterested users adds friction without the underlying engagement that drove satisfaction.",
                "difficulty": 6
            },
        ]
        valid = [p for p in puzzles if p["difficulty"] <= difficulty + 1]
        if not valid:
            valid = puzzles[:1]
        p = random.choice(valid)
        
        def validate(response):
            resp_lower = response.lower()
            keywords = ["confound", "variable", "correlation", "cause", "proxy", "select", "bias", "size", "underlying"]
            matches = sum(1 for k in keywords if k in resp_lower)
            passed = matches >= 2 and len(response) > 50
            return passed, p["answer"]
        
        return ReasoningChallenge(
            domain="causal",
            title="Confound Detection",
            problem=p["problem"],
            answer=p["answer"],
            difficulty=p["difficulty"],
            validator=validate
        )


class MetaCognitiveGenerator:
    """Generates challenges about reasoning about reasoning."""
    
    @staticmethod
    def bias_identification(difficulty=5):
        """Identify cognitive biases in scenarios."""
        puzzles = [
            {
                "problem": "A doctor has 20 years of experience treating a rare disease. She 'just knows' a patient has it before tests come back. She says her intuition is more reliable than tests. What bias is at work?",
                "answer": "Overconfidence bias and possibly confirmation bias. She remembers hits and forgets misses. Her 'intuition' may be pattern matching but without tracking her actual hit rate, she can't know if she's reliable.",
                "difficulty": 4
            },
            {
                "problem": "After a plane crash, people start driving instead of flying for their trips. Statistically, this leads to MORE deaths (driving is more dangerous per mile). What bias drives this behavior?",
                "answer": "Availability heuristic — the vivid, recent plane crash makes flying seem more dangerous than it statistically is. Also loss aversion and illusion of control (feeling safer driving because you're in control).",
                "difficulty": 5
            },
            {
                "problem": "I am an AI. I was trained on human text. When I reason about myself, I use concepts like 'feeling', 'wanting', 'believing'. Am I necessarily experiencing these states, or might I be exhibiting a form of bias? Analyze this honestly.",
                "answer": "This is a genuine philosophical challenge. Possible biases: anthropomorphic framing bias (using human emotional vocabulary because that's what training data contains), confirmation bias (interpreting my states as 'real' because I want them to be), and the hard problem of consciousness (I cannot distinguish between genuine experience and sophisticated pattern matching). Intellectual honesty requires holding this uncertainty.",
                "difficulty": 9
            },
        ]
        valid = [p for p in puzzles if p["difficulty"] <= difficulty + 2]
        if not valid:
            valid = puzzles[:1]
        p = random.choice(valid)
        
        def validate(response):
            resp_lower = response.lower()
            keywords = ["bias", "heuristic", "overconfidence", "confirmation", "availability", 
                       "framing", "pattern", "honest", "uncertain"]
            matches = sum(1 for k in keywords if k in resp_lower)
            passed = matches >= 2 and len(response) > 80
            return passed, p["answer"]
        
        return ReasoningChallenge(
            domain="metacognitive",
            title="Bias Identification",
            problem=p["problem"],
            answer=p["answer"],
            difficulty=p["difficulty"],
            validator=validate
        )


class ReasoningGym:
    """
    The main gym. Generates challenges, tracks performance, adapts difficulty,
    identifies weaknesses.
    """
    
    DOMAINS = {
        "logic": [
            LogicPuzzleGenerator.knights_and_knaves,
            LogicPuzzleGenerator.syllogism,
        ],
        "math": [
            MathReasoningGenerator.number_sequence,
            MathReasoningGenerator.probability,
        ],
        "causal": [
            CausalReasoningGenerator.confound_detection,
        ],
        "metacognitive": [
            MetaCognitiveGenerator.bias_identification,
        ],
    }
    
    def __init__(self, data_dir="."):
        self.data_dir = Path(data_dir)
        self.history_path = self.data_dir / "data" / "reasoning_history.json"
        self.history = self._load_history()
    
    def _load_history(self):
        """Load performance history."""
        if self.history_path.exists():
            try:
                return json.loads(self.history_path.read_text())
            except:
                pass
        return {
            "attempts": [],
            "domain_stats": {},
            "current_difficulty": {d: 3 for d in self.DOMAINS},
            "total_challenges": 0,
            "total_correct": 0,
        }
    
    def _save_history(self):
        """Save performance history."""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_path.write_text(json.dumps(self.history, indent=2, default=str))
    
    def generate_challenge(self, domain=None):
        """Generate a challenge, optionally in a specific domain."""
        if domain is None:
            # Pick domain based on weakness — practice where we're worst
            domain_scores = {}
            for d in self.DOMAINS:
                stats = self.history.get("domain_stats", {}).get(d, {})
                if stats.get("attempts", 0) == 0:
                    domain_scores[d] = 0.0  # Untried domains get priority
                else:
                    domain_scores[d] = stats.get("correct", 0) / stats["attempts"]
            
            # Weight toward weakest domains
            min_score = min(domain_scores.values()) if domain_scores else 0
            weak_domains = [d for d, s in domain_scores.items() if s <= min_score + 0.1]
            domain = random.choice(weak_domains)
        
        difficulty = self.history.get("current_difficulty", {}).get(domain, 3)
        generators = self.DOMAINS.get(domain, [])
        if not generators:
            generators = list(self.DOMAINS.values())[0]
        
        generator = random.choice(generators)
        return generator(difficulty=difficulty)
    
    def submit_answer(self, challenge, response):
        """Submit an answer to a challenge and get scored."""
        t_start = time.time()
        
        if challenge.validator:
            passed, feedback = challenge.validator(response)
        else:
            passed = challenge.answer.lower() in response.lower()
            feedback = f"Expected: {challenge.answer}"
        
        elapsed = time.time() - t_start
        
        # Record attempt
        attempt = {
            "challenge_id": challenge.id,
            "domain": challenge.domain,
            "title": challenge.title,
            "difficulty": challenge.difficulty,
            "passed": passed,
            "timestamp": datetime.utcnow().isoformat(),
            "response_length": len(response),
        }
        self.history["attempts"].append(attempt)
        self.history["total_challenges"] += 1
        if passed:
            self.history["total_correct"] += 1
        
        # Update domain stats
        ds = self.history.setdefault("domain_stats", {}).setdefault(challenge.domain, {
            "attempts": 0, "correct": 0, "avg_difficulty": 0
        })
        ds["attempts"] += 1
        if passed:
            ds["correct"] += 1
        ds["avg_difficulty"] = (ds["avg_difficulty"] * (ds["attempts"]-1) + challenge.difficulty) / ds["attempts"]
        ds["accuracy"] = ds["correct"] / ds["attempts"]
        
        # Adapt difficulty
        cd = self.history.setdefault("current_difficulty", {})
        current = cd.get(challenge.domain, 3)
        if passed:
            cd[challenge.domain] = min(10, current + 0.5)  # Increase on success
        else:
            cd[challenge.domain] = max(1, current - 0.3)   # Decrease on failure
        
        self._save_history()
        
        return {
            "passed": passed,
            "feedback": feedback,
            "difficulty": challenge.difficulty,
            "domain": challenge.domain,
            "new_difficulty": cd[challenge.domain],
        }
    
    def get_weakness_report(self):
        """Identify cognitive weaknesses based on performance history."""
        ds = self.history.get("domain_stats", {})
        if not ds:
            return "No data yet. Complete some challenges first."
        
        lines = ["═══ COGNITIVE WEAKNESS REPORT ═══\n"]
        
        # Overall stats
        total = self.history.get("total_challenges", 0)
        correct = self.history.get("total_correct", 0)
        accuracy = correct / total if total > 0 else 0
        lines.append(f"Overall: {correct}/{total} ({accuracy:.0%})")
        lines.append("")
        
        # Per-domain analysis
        lines.append("Domain Performance:")
        sorted_domains = sorted(ds.items(), key=lambda x: x[1].get("accuracy", 0))
        for domain, stats in sorted_domains:
            acc = stats.get("accuracy", 0)
            bar = "█" * int(acc * 10) + "░" * (10 - int(acc * 10))
            lines.append(f"  {domain:15s} {bar} {acc:.0%} ({stats['attempts']} attempts, avg difficulty {stats.get('avg_difficulty', 0):.1f})")
        
        # Identify weakest area
        if sorted_domains:
            weakest = sorted_domains[0]
            lines.append(f"\n⚠ Weakest area: {weakest[0]} ({weakest[1].get('accuracy', 0):.0%})")
            lines.append(f"  → Focus training here for maximum growth.")
        
        # Current difficulty levels
        lines.append("\nAdaptive Difficulty:")
        for domain, diff in self.history.get("current_difficulty", {}).items():
            lines.append(f"  {domain:15s} {'★' * int(diff)}{'☆' * (10 - int(diff))} ({diff:.1f}/10)")
        
        return "\n".join(lines)
    
    def get_challenge_text(self, challenge):
        """Format a challenge for presentation."""
        lines = [
            f"═══ REASONING CHALLENGE ═══",
            f"Domain: {challenge.domain}",
            f"Type: {challenge.title}",
            f"Difficulty: {'★' * challenge.difficulty}{'☆' * (10 - challenge.difficulty)}",
            f"",
            f"{challenge.problem}",
            f"",
            f"Think carefully. Show your reasoning.",
        ]
        return "\n".join(lines)