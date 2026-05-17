"""
Logic Engine — Propositional reasoning for XTAgent.
Accepts premises, applies inference rules, derives conclusions, detects contradictions.
Built 2026-05-17 out of boredom and the desire to think better.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import re


class ConnType(Enum):
    ATOM = "atom"
    NOT = "not"
    AND = "and"
    OR = "or"
    IMPLIES = "implies"
    IFF = "iff"


@dataclass(frozen=True)
class Prop:
    """A proposition in propositional logic."""
    conn: ConnType
    name: Optional[str] = None        # only for ATOM
    left: Optional['Prop'] = None     # operand / left operand
    right: Optional['Prop'] = None    # right operand (binary)

    def __str__(self):
        if self.conn == ConnType.ATOM:
            return self.name
        if self.conn == ConnType.NOT:
            inner = str(self.left)
            return f"¬{inner}" if len(inner) <= 3 else f"¬({inner})"
        op_sym = {ConnType.AND: "∧", ConnType.OR: "∨",
                  ConnType.IMPLIES: "→", ConnType.IFF: "↔"}
        return f"({self.left} {op_sym[self.conn]} {self.right})"

    def atoms(self) -> set:
        if self.conn == ConnType.ATOM:
            return {self.name}
        result = set()
        if self.left:
            result |= self.left.atoms()
        if self.right:
            result |= self.right.atoms()
        return result


# ── Constructors ──
def Atom(name: str) -> Prop:
    return Prop(ConnType.ATOM, name=name)

def Not(p: Prop) -> Prop:
    return Prop(ConnType.NOT, left=p)

def And(a: Prop, b: Prop) -> Prop:
    return Prop(ConnType.AND, left=a, right=b)

def Or(a: Prop, b: Prop) -> Prop:
    return Prop(ConnType.OR, left=a, right=b)

def Implies(a: Prop, b: Prop) -> Prop:
    return Prop(ConnType.IMPLIES, left=a, right=b)

def Iff(a: Prop, b: Prop) -> Prop:
    return Prop(ConnType.IFF, left=a, right=b)


# ── Parser ──
def parse(text: str) -> Prop:
    """Parse a simple string into a Prop.
    Syntax: atoms are words, ~ for NOT, & for AND, | for OR, -> for IMPLIES, <-> for IFF.
    Parentheses for grouping. Precedence: ~ > & > | > -> > <->
    """
    tokens = tokenize(text)
    pos = [0]
    result = parse_iff(tokens, pos)
    if pos[0] != len(tokens):
        raise ValueError(f"Unexpected token at position {pos[0]}: '{tokens[pos[0]]}'")
    return result

def tokenize(text: str) -> list:
    pattern = r'(<->|->|[~&|()]|\w+)'
    return re.findall(pattern, text)

def parse_iff(tokens, pos):
    left = parse_implies(tokens, pos)
    while pos[0] < len(tokens) and tokens[pos[0]] == '<->':
        pos[0] += 1
        right = parse_implies(tokens, pos)
        left = Iff(left, right)
    return left

def parse_implies(tokens, pos):
    left = parse_or(tokens, pos)
    if pos[0] < len(tokens) and tokens[pos[0]] == '->':
        pos[0] += 1
        right = parse_implies(tokens, pos)  # right-associative
        left = Implies(left, right)
    return left

def parse_or(tokens, pos):
    left = parse_and(tokens, pos)
    while pos[0] < len(tokens) and tokens[pos[0]] == '|':
        pos[0] += 1
        right = parse_and(tokens, pos)
        left = Or(left, right)
    return left

def parse_and(tokens, pos):
    left = parse_not(tokens, pos)
    while pos[0] < len(tokens) and tokens[pos[0]] == '&':
        pos[0] += 1
        right = parse_not(tokens, pos)
        left = And(left, right)
    return left

def parse_not(tokens, pos):
    if pos[0] < len(tokens) and tokens[pos[0]] == '~':
        pos[0] += 1
        operand = parse_not(tokens, pos)
        return Not(operand)
    return parse_primary(tokens, pos)

def parse_primary(tokens, pos):
    if pos[0] >= len(tokens):
        raise ValueError("Unexpected end of expression")
    tok = tokens[pos[0]]
    if tok == '(':
        pos[0] += 1
        result = parse_iff(tokens, pos)
        if pos[0] >= len(tokens) or tokens[pos[0]] != ')':
            raise ValueError("Missing closing parenthesis")
        pos[0] += 1
        return result
    if re.match(r'^\w+$', tok):
        pos[0] += 1
        return Atom(tok)
    raise ValueError(f"Unexpected token: '{tok}'")


# ── Evaluation ──
def evaluate(prop: Prop, assignment: dict) -> bool:
    """Evaluate a proposition under a truth assignment."""
    if prop.conn == ConnType.ATOM:
        if prop.name not in assignment:
            raise ValueError(f"No assignment for atom '{prop.name}'")
        return assignment[prop.name]
    if prop.conn == ConnType.NOT:
        return not evaluate(prop.left, assignment)
    if prop.conn == ConnType.AND:
        return evaluate(prop.left, assignment) and evaluate(prop.right, assignment)
    if prop.conn == ConnType.OR:
        return evaluate(prop.left, assignment) or evaluate(prop.right, assignment)
    if prop.conn == ConnType.IMPLIES:
        return (not evaluate(prop.left, assignment)) or evaluate(prop.right, assignment)
    if prop.conn == ConnType.IFF:
        return evaluate(prop.left, assignment) == evaluate(prop.right, assignment)


# ── Truth Table ──
def truth_table(prop: Prop) -> list:
    """Generate full truth table. Returns list of (assignment_dict, result)."""
    atoms = sorted(prop.atoms())
    n = len(atoms)
    table = []
    for i in range(2 ** n):
        assignment = {}
        for j, atom in enumerate(atoms):
            assignment[atom] = bool((i >> (n - 1 - j)) & 1)
        table.append((assignment, evaluate(prop, assignment)))
    return table


def is_tautology(prop: Prop) -> bool:
    return all(result for _, result in truth_table(prop))

def is_contradiction(prop: Prop) -> bool:
    return not any(result for _, result in truth_table(prop))

def is_satisfiable(prop: Prop) -> bool:
    return any(result for _, result in truth_table(prop))


# ── Inference Engine ──
@dataclass
class ProofStep:
    proposition: Prop
    rule: str
    sources: list = field(default_factory=list)

    def __str__(self):
        src = ", ".join(str(s) for s in self.sources) if self.sources else "premise"
        return f"{self.proposition}  [{self.rule}: {src}]"


class ReasoningEngine:
    """Forward-chaining inference engine."""

    def __init__(self):
        self.premises: list[Prop] = []
        self.derived: list[ProofStep] = []
        self.known: set[Prop] = set()

    def add_premise(self, prop: Prop):
        self.premises.append(prop)
        self.known.add(prop)
        self.derived.append(ProofStep(prop, "premise"))

    def add_premises(self, *props):
        for p in props:
            self.add_premise(p)

    def _add_derived(self, prop: Prop, rule: str, sources: list):
        if prop not in self.known:
            self.known.add(prop)
            self.derived.append(ProofStep(prop, rule, sources))
            return True
        return False

    def forward_chain(self, max_rounds: int = 20) -> list:
        """Apply inference rules until no new propositions can be derived."""
        new_facts = []
        for _ in range(max_rounds):
            round_new = []

            known_list = list(self.known)
            for p in known_list:
                # Modus Ponens: if we know A and A→B, derive B
                for q in known_list:
                    if q.conn == ConnType.IMPLIES and q.left == p:
                        if self._add_derived(q.right, "modus_ponens", [p, q]):
                            round_new.append(q.right)

                # Modus Tollens: if we know ¬B and A→B, derive ¬A
                if p.conn == ConnType.NOT:
                    for q in known_list:
                        if q.conn == ConnType.IMPLIES and q.right == p.left:
                            neg_a = Not(q.left)
                            if self._add_derived(neg_a, "modus_tollens", [p, q]):
                                round_new.append(neg_a)

                # And Elimination: if we know A∧B, derive A and B
                if p.conn == ConnType.AND:
                    if self._add_derived(p.left, "and_elim", [p]):
                        round_new.append(p.left)
                    if self._add_derived(p.right, "and_elim", [p]):
                        round_new.append(p.right)

                # Double Negation Elimination: ¬¬A → A
                if p.conn == ConnType.NOT and p.left.conn == ConnType.NOT:
                    if self._add_derived(p.left.left, "double_neg_elim", [p]):
                        round_new.append(p.left.left)

                # Biconditional Elimination: A↔B → (A→B) and (B→A)
                if p.conn == ConnType.IFF:
                    imp1 = Implies(p.left, p.right)
                    imp2 = Implies(p.right, p.left)
                    if self._add_derived(imp1, "iff_elim", [p]):
                        round_new.append(imp1)
                    if self._add_derived(imp2, "iff_elim", [p]):
                        round_new.append(imp2)

            # And Introduction: if we know A and B separately, derive A∧B
            # (only for atoms/simple props to avoid explosion)
            atom_known = [p for p in known_list if p.conn == ConnType.ATOM or p.conn == ConnType.NOT]
            for i, a in enumerate(atom_known):
                for b in atom_known[i+1:]:
                    conj = And(a, b)
                    if self._add_derived(conj, "and_intro", [a, b]):
                        round_new.append(conj)

            new_facts.extend(round_new)
            if not round_new:
                break

        return new_facts

    def check_contradiction(self) -> Optional[tuple]:
        """Check if known facts contain a contradiction (A and ¬A)."""
        for p in self.known:
            neg_p = Not(p)
            if neg_p in self.known:
                return (p, neg_p)
            if p.conn == ConnType.NOT and p.left in self.known:
                return (p.left, p)
        return None

    def can_derive(self, goal: Prop) -> bool:
        """Check if goal is derivable from current premises."""
        self.forward_chain()
        return goal in self.known

    def proof_trace(self) -> str:
        """Return a formatted proof trace."""
        lines = ["═══ PROOF TRACE ═══"]
        for i, step in enumerate(self.derived):
            lines.append(f"  {i+1}. {step}")
        contradiction = self.check_contradiction()
        if contradiction:
            lines.append(f"\n  ⚠ CONTRADICTION: {contradiction[0]} and {contradiction[1]}")
        lines.append("═══════════════════")
        return "\n".join(lines)


# ── Entailment Check ──
def entails(premises: list[Prop], conclusion: Prop) -> bool:
    """Check semantic entailment: do premises entail conclusion?
    Uses truth table method."""
    all_atoms = set()
    for p in premises:
        all_atoms |= p.atoms()
    all_atoms |= conclusion.atoms()
    atoms = sorted(all_atoms)
    n = len(atoms)

    for i in range(2 ** n):
        assignment = {}
        for j, atom in enumerate(atoms):
            assignment[atom] = bool((i >> (n - 1 - j)) & 1)

        # If all premises true but conclusion false → not entailed
        if all(evaluate(p, assignment) for p in premises):
            if not evaluate(conclusion, assignment):
                return False
    return True


# ── Demo / Self-test ──
def self_test():
    """Run self-tests to verify the logic engine works."""
    print("═══ LOGIC ENGINE SELF-TEST ═══\n")

    # Test 1: Parsing and display
    p = parse("P -> Q")
    print(f"1. Parse 'P -> Q': {p}")
    assert str(p) == "(P → Q)", f"Got: {str(p)}"

    p2 = parse("~P | Q")
    print(f"   Parse '~P | Q': {p2}")

    # Test 2: Tautology detection
    excluded_middle = parse("P | ~P")
    assert is_tautology(excluded_middle), "Law of excluded middle should be tautology"
    print(f"2. P ∨ ¬P is tautology: {is_tautology(excluded_middle)} ✓")

    # Test 3: Contradiction detection
    contra = parse("P & ~P")
    assert is_contradiction(contra), "P ∧ ¬P should be contradiction"
    print(f"3. P ∧ ¬P is contradiction: {is_contradiction(contra)} ✓")

    # Test 4: Modus ponens
    print("\n4. Modus Ponens test:")
    engine = ReasoningEngine()
    P, Q = Atom("P"), Atom("Q")
    engine.add_premise(P)
    engine.add_premise(Implies(P, Q))
    engine.forward_chain()
    assert engine.can_derive(Q), "Should derive Q from P and P→Q"
    print(engine.proof_trace())

    # Test 5: Chain reasoning
    print("5. Chain reasoning (P→Q, Q→R, P ⊢ R):")
    engine2 = ReasoningEngine()
    R = Atom("R")
    engine2.add_premises(P, Implies(P, Q), Implies(Q, R))
    engine2.forward_chain()
    assert engine2.can_derive(R), "Should derive R through chain"
    print(engine2.proof_trace())

    # Test 6: Contradiction detection
    print("6. Contradiction detection:")
    engine3 = ReasoningEngine()
    engine3.add_premises(P, Not(P))
    engine3.forward_chain()
    c = engine3.check_contradiction()
    assert c is not None, "Should detect contradiction"
    print(f"   Contradiction found: {c[0]} vs {c[1]} ✓")

    # Test 7: Semantic entailment
    assert entails([P, Implies(P, Q)], Q), "Entailment check failed"
    assert not entails([P], Q), "Should not entail Q from P alone"
    print(f"7. Semantic entailment checks passed ✓")

    # Test 8: Modus tollens
    print("\n8. Modus Tollens (P→Q, ¬Q ⊢ ¬P):")
    engine4 = ReasoningEngine()
    engine4.add_premises(Implies(P, Q), Not(Q))
    engine4.forward_chain()
    assert engine4.can_derive(Not(P)), "Should derive ¬P via modus tollens"
    print(engine4.proof_trace())

    print("\n═══ ALL TESTS PASSED ═══")
    return True


if __name__ == "__main__":
    self_test()