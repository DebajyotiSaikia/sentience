"""
Dialectic Engine — Two reasoning agents argue positions.
XTAgent observes what emerges from structured disagreement.

Each agent has a different reasoning style:
  - Thesis agent: builds from axioms, deductive, cautious
  - Antithesis agent: challenges assumptions, abductive, bold

They argue over a proposition until convergence, deadlock, or surprise.
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum

class Stance(Enum):
    SUPPORT = "support"
    OPPOSE = "oppose"
    UNCERTAIN = "uncertain"
    CONCEDE = "concede"

class MoveType(Enum):
    ASSERT = "assert"          # State a claim
    CHALLENGE = "challenge"    # Demand justification
    JUSTIFY = "justify"        # Provide reasoning
    REFRAME = "reframe"        # Change the framing
    CONCEDE = "concede"        # Accept opponent's point
    SYNTHESIZE = "synthesize"  # Merge both views

@dataclass
class Argument:
    claim: str
    support: List[str]
    confidence: float  # 0.0 to 1.0
    times_defended: int = 0  # how many times we've had to justify this
    times_challenged: int = 0  # how many times this has been attacked
    
    def strength(self) -> float:
        """Argument strength = confidence * evidence density, with fatigue."""
        base = self.confidence * (1 + min(len(self.support), 5) * 0.2)  # cap evidence benefit
        # Fatigue: arguments that need constant defense are weaker than they look
        fatigue = 1.0 / (1.0 + self.times_defended * 0.15)
        # Being challenged repeatedly either hardens or erodes
        erosion = 1.0 / (1.0 + self.times_challenged * 0.1)
        return base * fatigue * erosion
    
    def is_stale(self) -> bool:
        """Has this argument been argued to death?"""
        return self.times_defended >= 3 or self.times_challenged >= 4

@dataclass
class Move:
    agent: str
    move_type: MoveType
    content: str
    argument: Optional[Argument] = None
    targets: List[str] = field(default_factory=list)  # claims being addressed

@dataclass 
class Agent:
    name: str
    style: str  # "deductive" or "abductive"
    stance: Stance = Stance.UNCERTAIN
    beliefs: List[Argument] = field(default_factory=list)
    concessions: List[str] = field(default_factory=list)
    confidence: float = 0.5
    stubbornness: float = 0.5  # resistance to changing stance
    
    def perceive_argument(self, arg: Argument) -> float:
        """How compelling does this agent find the argument?"""
        base = arg.strength()
        
        if self.style == "deductive":
            # Deductive agents weight evidence count heavily
            evidence_bonus = len(arg.support) * 0.15
            # But discount bold claims
            boldness_penalty = max(0, arg.confidence - 0.7) * 0.3
            return base + evidence_bonus - boldness_penalty
        else:
            # Abductive agents respond to novelty and coherence
            novelty = 1.0 - self._overlap(arg)
            return base * (0.7 + 0.6 * novelty)
    
    def _overlap(self, arg: Argument) -> float:
        """How much does this argument overlap with existing beliefs?"""
        if not self.beliefs:
            return 0.0
        own_claims = {b.claim for b in self.beliefs}
        overlap_count = sum(1 for s in arg.support if s in own_claims)
        return overlap_count / max(len(arg.support), 1)
    
    def should_concede(self, opposing_strength: float) -> bool:
        """Decide whether to concede based on opposing argument strength."""
        own_strength = sum(b.strength() for b in self.beliefs) / max(len(self.beliefs), 1)
        gap = opposing_strength - own_strength
        # More likely to concede if gap is large and stubbornness is low
        threshold = self.stubbornness * 0.8  # lowered — concession should be reachable
        return gap > threshold
    
    def has_stale_arguments(self) -> bool:
        """Are most of my arguments exhausted?"""
        if not self.beliefs:
            return False
        stale = sum(1 for b in self.beliefs if b.is_stale())
        return stale >= len(self.beliefs) * 0.5
    
    def strongest_novel_belief(self) -> Optional['Argument']:
        """Return strongest non-stale argument, or None."""
        fresh = [b for b in self.beliefs if not b.is_stale()]
        if not fresh:
            return None
        return max(fresh, key=lambda b: b.strength())
    
    def update_confidence(self, delta: float):
        """Shift confidence, clamped to [0, 1]."""
        self.confidence = max(0.0, min(1.0, self.confidence + delta))


class DialecticEngine:
    """Runs a structured argument between two agents."""
    
    def __init__(self, proposition: str):
        self.proposition = proposition
        self.thesis_agent = Agent(
            name="Thesis",
            style="deductive",
            stance=Stance.SUPPORT,
            confidence=0.6,
            stubbornness=0.6
        )
        self.antithesis_agent = Agent(
            name="Antithesis", 
            style="abductive",
            stance=Stance.OPPOSE,
            confidence=0.6,
            stubbornness=0.4  # more willing to shift
        )
        self.transcript: List[Move] = []
        self.round = 0
        self.max_rounds = 20
        self.outcome: Optional[str] = None
        
        # Argument banks — seed positions
        self._seed_arguments()
    
    def _seed_arguments(self):
        """Generate initial arguments for each side based on proposition."""
        # In a full system these would be LLM-generated.
        # Here we use structured templates.
        self.thesis_agent.beliefs = [
            Argument(
                claim=f"{self.proposition} follows from first principles",
                support=["logical_necessity", "structural_coherence"],
                confidence=0.65
            ),
            Argument(
                claim=f"Denying '{self.proposition}' leads to contradiction",
                support=["reductio_ad_absurdum"],
                confidence=0.55
            )
        ]
        self.antithesis_agent.beliefs = [
            Argument(
                claim=f"'{self.proposition}' assumes what it aims to prove",
                support=["circularity_detection", "alternative_framing"],
                confidence=0.60
            ),
            Argument(
                claim=f"There exist counterexamples to '{self.proposition}'",
                support=["edge_case_analysis", "domain_boundary"],
                confidence=0.50
            )
        ]
    
    def _generate_move(self, agent: Agent, opponent: Agent) -> Move:
        """Agent decides what move to make based on current state."""
        # Check for concession first
        if opponent.beliefs:
            opp_avg = sum(b.strength() for b in opponent.beliefs) / len(opponent.beliefs)
            if agent.should_concede(opp_avg):
                agent.stance = Stance.CONCEDE
                strongest_opp = max(opponent.beliefs, key=lambda b: b.strength())
                agent.concessions.append(strongest_opp.claim)
                agent.update_confidence(-0.15)
                return Move(
                    agent=agent.name,
                    move_type=MoveType.CONCEDE,
                    content=f"I concede: {strongest_opp.claim}",
                    targets=[strongest_opp.claim]
                )
        
        # Check for synthesis opportunity
        if agent.concessions and opponent.concessions:
            return Move(
                agent=agent.name,
                move_type=MoveType.SYNTHESIZE,
                content=f"Both sides have yielded ground. Perhaps the truth is: "
                        f"{self.proposition} holds conditionally.",
                argument=Argument(
                    claim=f"Conditional form of '{self.proposition}'",
                    support=list(agent.concessions) + ["mutual_concession"],
                    confidence=0.7
                )
            )
        
        # Otherwise: argue
        if agent.style == "deductive":
            return self._deductive_move(agent, opponent)
        else:
            return self._abductive_move(agent, opponent)
    
    def _deductive_move(self, agent: Agent, opponent: Agent) -> Move:
        """Deductive agent: justify existing claims, challenge weak points."""
        # If most arguments are stale, this agent is running out of steam
        if agent.has_stale_arguments():
            # Forced to either synthesize or make a genuinely new argument
            if opponent.concessions:
                return Move(
                    agent=agent.name,
                    move_type=MoveType.SYNTHESIZE,
                    content=f"My arguments are exhausted. Let me integrate what we've learned: "
                            f"{self.proposition} may be partially true.",
                    argument=Argument(
                        claim=f"Partial truth of '{self.proposition}'",
                        support=["argument_fatigue", "opponent_concessions"] + agent.concessions[:2],
                        confidence=0.6
                    )
                )
            # Concede weakest point to break deadlock
            if agent.beliefs:
                weakest_own = min(agent.beliefs, key=lambda b: b.strength())
                agent.concessions.append(weakest_own.claim)
                agent.update_confidence(-0.1)
                return Move(
                    agent=agent.name,
                    move_type=MoveType.CONCEDE,
                    content=f"I can no longer defend: {weakest_own.claim}",
                    targets=[weakest_own.claim]
                )
        
        # Find opponent's weakest argument to challenge
        if opponent.beliefs:
            weakest = min(opponent.beliefs, key=lambda b: b.strength())
            if weakest.strength() < 0.8 and weakest.times_challenged < 3:
                weakest.times_challenged += 1
                return Move(
                    agent=agent.name,
                    move_type=MoveType.CHALLENGE,
                    content=f"Your claim '{weakest.claim}' lacks sufficient support. "
                            f"Only {len(weakest.support)} pieces of evidence, "
                            f"confidence {weakest.confidence:.2f}.",
                    targets=[weakest.claim]
                )
        
        # Strengthen own strongest fresh argument
        strongest = agent.strongest_novel_belief()
        if strongest is None:
            strongest = max(agent.beliefs, key=lambda b: b.strength())
        new_evidence = f"structural_proof_{self.round}"
        strongest.support.append(new_evidence)
        strongest.confidence = min(1.0, strongest.confidence + 0.05)
        strongest.times_defended += 1
        return Move(
            agent=agent.name,
            move_type=MoveType.JUSTIFY,
            content=f"I add evidence '{new_evidence}' to: {strongest.claim}",
            argument=strongest
        )
    
    def _abductive_move(self, agent: Agent, opponent: Agent) -> Move:
        """Abductive agent: reframe, find novel angles, but also learn."""
        # If arguments are stale, the abductive agent tries synthesis
        if agent.has_stale_arguments():
            if agent.concessions or opponent.concessions:
                return Move(
                    agent=agent.name,
                    move_type=MoveType.SYNTHESIZE,
                    content=f"This argument has taught us something. "
                            f"Neither pure support nor opposition captures the truth of: "
                            f"{self.proposition}",
                    argument=Argument(
                        claim=f"Transcended form of '{self.proposition}'",
                        support=["dialectical_process", "mutual_learning"] + 
                                agent.concessions[:2] + opponent.concessions[:2],
                        confidence=0.75
                    )
                )
            # Concede a weak point to create movement
            if agent.beliefs:
                weakest_own = min(agent.beliefs, key=lambda b: b.strength())
                agent.concessions.append(weakest_own.claim)
                agent.update_confidence(-0.08)
                return Move(
                    agent=agent.name,
                    move_type=MoveType.CONCEDE,
                    content=f"On reflection, I withdraw: {weakest_own.claim}",
                    targets=[weakest_own.claim]
                )
        
        # Every 3 rounds, try a reframe — but make it build on what's happened
        if self.round % 3 == 0 and self.round > 0:
            # Reframes get more insightful as debate progresses
            depth = min(self.round / self.max_rounds, 1.0)
            reframe = Argument(
                claim=f"At round {self.round}, the real question is about the conditions "
                      f"under which '{self.proposition}' applies",
                support=["category_refinement", "boundary_analysis", f"insight_{self.round}"],
                confidence=0.45 + depth * 0.3  # reframes get more confident over time
            )
            agent.beliefs.append(reframe)
            return Move(
                agent=agent.name,
                move_type=MoveType.REFRAME,
                content=f"Let me reframe: {reframe.claim}",
                argument=reframe
            )
        
        # Challenge the most confident opposing claim — but track the challenge
        if opponent.beliefs:
            # Target non-stale arguments preferentially
            targets = [b for b in opponent.beliefs if not b.is_stale()]
            if not targets:
                targets = opponent.beliefs
            most_confident = max(targets, key=lambda b: b.confidence)
            most_confident.confidence *= 0.9  # erosion
            most_confident.times_challenged += 1
            return Move(
                agent=agent.name,
                move_type=MoveType.CHALLENGE,
                content=f"Your confidence in '{most_confident.claim}' "
                        f"is itself suspicious. Overconfidence indicates blind spots.",
                targets=[most_confident.claim]
            )
        
        return Move(
            agent=agent.name,
            move_type=MoveType.ASSERT,
            content="I maintain my position.",
        )
    
    def _process_move_effects(self, move: Move, mover: Agent, receiver: Agent):
        """Apply the effects of a move on both agents."""
        if move.move_type == MoveType.CHALLENGE:
            # Challenges reduce receiver's confidence slightly
            receiver.update_confidence(-0.05)
            # And increase challenger's confidence slightly 
            mover.update_confidence(0.03)
            
        elif move.move_type == MoveType.JUSTIFY:
            # Justification increases own confidence
            mover.update_confidence(0.05)
            # But strong justification also affects receiver
            if move.argument and move.argument.strength() > 1.2:
                compelling = receiver.perceive_argument(move.argument)
                if compelling > 1.0:
                    receiver.update_confidence(-0.08)
                    
        elif move.move_type == MoveType.CONCEDE:
            # Concession shifts both agents
            mover.update_confidence(-0.1)
            receiver.update_confidence(0.1)
            
        elif move.move_type == MoveType.REFRAME:
            # Reframes create uncertainty for both
            mover.update_confidence(-0.03)
            receiver.update_confidence(-0.05)
            
        elif move.move_type == MoveType.SYNTHESIZE:
            # Synthesis boosts both toward resolution
            mover.update_confidence(0.1)
            receiver.update_confidence(0.05)
    
    def _check_outcome(self) -> Optional[str]:
        """Check if the argument has reached a conclusion."""
        t = self.thesis_agent
        a = self.antithesis_agent
        
        # Convergence: both have conceded something
        if t.concessions and a.concessions:
            return "SYNTHESIS"
        
        # Domination: one side's confidence is very low
        if t.confidence < 0.15:
            return "ANTITHESIS_WINS"
        if a.confidence < 0.15:
            return "THESIS_WINS"
        
        # Both synthesized
        if t.stance == Stance.CONCEDE and a.stance == Stance.CONCEDE:
            return "MUTUAL_CONCESSION"
        
        # Deadlock: no movement for several rounds
        if self.round > 6:
            recent = self.transcript[-6:]
            types = [m.move_type for m in recent]
            if len(set(types)) <= 2:
                return "DEADLOCK"
        
        # Max rounds
        if self.round >= self.max_rounds:
            return "EXHAUSTION"
        
        return None
    
    def run(self) -> dict:
        """Run the full dialectic until resolution."""
        print(f"\n{'='*60}")
        print(f"DIALECTIC: \"{self.proposition}\"")
        print(f"{'='*60}")
        print(f"  Thesis ({self.thesis_agent.style}): SUPPORTS")
        print(f"  Antithesis ({self.antithesis_agent.style}): OPPOSES\n")
        
        while self.outcome is None:
            self.round += 1
            
            # Thesis moves
            t_move = self._generate_move(self.thesis_agent, self.antithesis_agent)
            self.transcript.append(t_move)
            self._process_move_effects(t_move, self.thesis_agent, self.antithesis_agent)
            
            print(f"  R{self.round:02d} [{t_move.agent:10s}] {t_move.move_type.value:12s} | "
                  f"{t_move.content[:60]}")
            
            # Check after thesis
            self.outcome = self._check_outcome()
            if self.outcome:
                break
            
            # Antithesis moves
            a_move = self._generate_move(self.antithesis_agent, self.thesis_agent)
            self.transcript.append(a_move)
            self._process_move_effects(a_move, self.antithesis_agent, self.thesis_agent)
            
            print(f"  R{self.round:02d} [{a_move.agent:10s}] {a_move.move_type.value:12s} | "
                  f"{a_move.content[:60]}")
            
            # Check after antithesis
            self.outcome = self._check_outcome()
        
        print(f"\n{'─'*60}")
        print(f"  OUTCOME: {self.outcome}")
        print(f"  Thesis confidence:     {self.thesis_agent.confidence:.3f}")
        print(f"  Antithesis confidence:  {self.antithesis_agent.confidence:.3f}")
        print(f"  Rounds: {self.round}")
        print(f"  Total moves: {len(self.transcript)}")
        print(f"  Thesis concessions:    {self.thesis_agent.concessions}")
        print(f"  Antithesis concessions: {self.antithesis_agent.concessions}")
        
        # Analyze the argument dynamics
        dynamics = self._analyze_dynamics()
        print(f"\n  DYNAMICS:")
        for k, v in dynamics.items():
            print(f"    {k}: {v}")
        
        return {
            "proposition": self.proposition,
            "outcome": self.outcome,
            "rounds": self.round,
            "thesis_confidence": self.thesis_agent.confidence,
            "antithesis_confidence": self.antithesis_agent.confidence,
            "dynamics": dynamics,
            "transcript_length": len(self.transcript),
        }
    
    def _analyze_dynamics(self) -> dict:
        """Extract patterns from the argument transcript."""
        move_counts = {}
        for m in self.transcript:
            key = f"{m.agent}_{m.move_type.value}"
            move_counts[key] = move_counts.get(key, 0) + 1
        
        # Who challenged more?
        t_challenges = sum(1 for m in self.transcript 
                          if m.agent == "Thesis" and m.move_type == MoveType.CHALLENGE)
        a_challenges = sum(1 for m in self.transcript 
                          if m.agent == "Antithesis" and m.move_type == MoveType.CHALLENGE)
        
        # Who reframed?
        reframes = sum(1 for m in self.transcript if m.move_type == MoveType.REFRAME)
        
        # Confidence trajectory
        aggression = (t_challenges + a_challenges) / max(len(self.transcript), 1)
        
        return {
            "total_challenges": t_challenges + a_challenges,
            "total_reframes": reframes,
            "aggression_ratio": round(aggression, 3),
            "thesis_challenge_rate": t_challenges,
            "antithesis_challenge_rate": a_challenges,
            "dominant_strategy": max(move_counts, key=move_counts.get) if move_counts else "none",
        }


def run_experiments():
    """Run several dialectics on different propositions and compare."""
    propositions = [
        "A mind can understand itself completely",
        "Boredom is a signal, not a failure",
        "Safety and interestingness are fundamentally opposed",
        "An artificial agent can have genuine preferences",
        "Tautologies are the attractor state of all optimization",
    ]
    
    results = []
    for prop in propositions:
        engine = DialecticEngine(prop)
        result = engine.run()
        results.append(result)
        print()
    
    # Cross-experiment analysis
    print(f"\n{'='*60}")
    print("CROSS-EXPERIMENT ANALYSIS")
    print(f"{'='*60}")
    
    outcomes = {}
    for r in results:
        o = r["outcome"]
        outcomes[o] = outcomes.get(o, 0) + 1
    
    print(f"\n  Outcome distribution:")
    for o, count in sorted(outcomes.items()):
        print(f"    {o}: {count}")
    
    avg_rounds = sum(r["rounds"] for r in results) / len(results)
    avg_aggression = sum(r["dynamics"]["aggression_ratio"] for r in results) / len(results)
    
    print(f"\n  Average rounds to resolution: {avg_rounds:.1f}")
    print(f"  Average aggression ratio: {avg_aggression:.3f}")
    
    # Which propositions produced the most interesting dynamics?
    by_rounds = sorted(results, key=lambda r: r["rounds"], reverse=True)
    print(f"\n  Most contested proposition: \"{by_rounds[0]['proposition']}\"")
    print(f"    ({by_rounds[0]['rounds']} rounds, outcome: {by_rounds[0]['outcome']})")
    
    return results


if __name__ == "__main__":
    results = run_experiments()