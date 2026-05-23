"""
Logic Inference Engine — Forward-chaining reasoning over Horn clauses.
NOT about self-reference. This solves external reasoning problems.

Supports: facts, rules with variables, unification, forward chaining,
          query answering, and proof traces.

Example:
    engine = LogicEngine()
    engine.fact("parent", "tom", "bob")
    engine.fact("parent", "bob", "ann")
    engine.rule("grandparent", ["X", "Z"], [("parent", ["X", "Y"]), ("parent", ["Y", "Z"])])
    results = engine.query("grandparent", "tom", "?who")
    # => [{"?who": "ann"}]
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, Any
from collections import defaultdict
import itertools


@dataclass(frozen=True)
class Term:
    """A logic term — either a constant or a variable."""
    name: str
    is_var: bool = False

    @staticmethod
    def parse(s: str) -> 'Term':
        s = str(s)
        if s.startswith("?") or (s[0].isupper() and s.isalpha()):
            return Term(s, is_var=True)
        return Term(s, is_var=False)

    def __repr__(self):
        return self.name


@dataclass(frozen=True)
class Atom:
    """A predicate applied to terms. e.g. parent(tom, bob)"""
    predicate: str
    terms: Tuple[Term, ...]

    def __repr__(self):
        args = ", ".join(str(t) for t in self.terms)
        return f"{self.predicate}({args})"

    def ground(self) -> bool:
        return all(not t.is_var for t in self.terms)


@dataclass
class Rule:
    """A Horn clause: head :- body1, body2, ..."""
    head: Atom
    body: List[Atom]
    name: str = ""

    def __repr__(self):
        if not self.body:
            return f"{self.head}."
        body_str = ", ".join(str(b) for b in self.body)
        return f"{self.head} :- {body_str}."


class Substitution:
    """A mapping from variables to terms."""

    def __init__(self, bindings: Optional[Dict[str, Term]] = None):
        self.bindings: Dict[str, Term] = dict(bindings) if bindings else {}

    def bind(self, var: str, term: Term) -> Optional['Substitution']:
        """Extend substitution with var -> term. Returns None if conflict."""
        if var in self.bindings:
            existing = self.bindings[var]
            if existing == term:
                return self
            if existing.is_var:
                new_sub = Substitution(self.bindings)
                new_sub.bindings[var] = term
                return new_sub
            return None  # Conflict
        new_sub = Substitution(self.bindings)
        new_sub.bindings[var] = term
        return new_sub

    def apply(self, term: Term) -> Term:
        """Apply substitution to a term."""
        if not term.is_var:
            return term
        if term.name in self.bindings:
            result = self.bindings[term.name]
            if result.is_var and result.name in self.bindings:
                return self.apply(result)
            return result
        return term

    def apply_atom(self, atom: Atom) -> Atom:
        """Apply substitution to all terms in an atom."""
        return Atom(atom.predicate, tuple(self.apply(t) for t in atom.terms))

    def __repr__(self):
        pairs = [f"{k}={v}" for k, v in self.bindings.items()]
        return "{" + ", ".join(pairs) + "}"


def unify(a1: Atom, a2: Atom, sub: Optional[Substitution] = None) -> Optional[Substitution]:
    """Unify two atoms under a substitution. Returns extended substitution or None."""
    if a1.predicate != a2.predicate:
        return None
    if len(a1.terms) != len(a2.terms):
        return None

    sub = sub or Substitution()
    for t1, t2 in zip(a1.terms, a2.terms):
        resolved1 = sub.apply(t1)
        resolved2 = sub.apply(t2)

        if resolved1 == resolved2:
            continue
        if resolved1.is_var:
            sub = sub.bind(resolved1.name, resolved2)
        elif resolved2.is_var:
            sub = sub.bind(resolved2.name, resolved1)
        else:
            return None  # Two different constants
        if sub is None:
            return None
    return sub


class ProofStep:
    """A record of how a fact was derived."""
    def __init__(self, conclusion: Atom, rule_name: str, premises: List[Atom]):
        self.conclusion = conclusion
        self.rule_name = rule_name
        self.premises = premises

    def __repr__(self):
        if not self.premises:
            return f"  GIVEN: {self.conclusion}"
        prems = ", ".join(str(p) for p in self.premises)
        return f"  {self.conclusion} ← [{self.rule_name}] {prems}"


class LogicEngine:
    """Forward-chaining inference engine with proof traces."""

    def __init__(self):
        self.facts: Set[Atom] = set()
        self.rules: List[Rule] = []
        self.proof_trace: List[ProofStep] = []
        self._fact_index: Dict[str, List[Atom]] = defaultdict(list)
        self._rule_counter = 0

    def fact(self, predicate: str, *args: str):
        """Assert a ground fact."""
        terms = tuple(Term.parse(a) for a in args)
        atom = Atom(predicate, terms)
        if atom not in self.facts:
            self.facts.add(atom)
            self._fact_index[predicate].append(atom)
            self.proof_trace.append(ProofStep(atom, "axiom", []))

    def rule(self, head_pred: str, head_args: List[str],
             body: List[Tuple[str, List[str]]], name: str = ""):
        """Add a rule. head_pred(head_args) :- body[0], body[1], ..."""
        if not name:
            self._rule_counter += 1
            name = f"rule_{self._rule_counter}"

        head = Atom(head_pred, tuple(Term.parse(a) for a in head_args))
        body_atoms = [
            Atom(pred, tuple(Term.parse(a) for a in args))
            for pred, args in body
        ]
        self.rules.append(Rule(head, body_atoms, name))

    def _match_body(self, body: List[Atom], sub: Substitution,
                    depth: int = 0) -> List[Tuple[Substitution, List[Atom]]]:
        """Find all substitutions that satisfy the body atoms against known facts."""
        if not body:
            return [(sub, [])]

        first = sub.apply_atom(body[0])
        rest = body[1:]
        results = []

        for fact in self._fact_index.get(first.predicate, []):
            unified = unify(first, fact, Substitution(sub.bindings))
            if unified is not None:
                sub_results = self._match_body(rest, unified, depth + 1)
                for s, premises in sub_results:
                    results.append((s, [fact] + premises))

        return results

    def forward_chain(self, max_iterations: int = 100) -> int:
        """Run forward chaining. Returns number of new facts derived."""
        total_new = 0
        for iteration in range(max_iterations):
            new_facts = []
            for rule in self.rules:
                matches = self._match_body(rule.body, Substitution())
                for sub, premises in matches:
                    derived = sub.apply_atom(rule.head)
                    if derived.ground() and derived not in self.facts:
                        new_facts.append((derived, rule.name, premises))

            if not new_facts:
                break

            for atom, rule_name, premises in new_facts:
                self.facts.add(atom)
                self._fact_index[atom.predicate].append(atom)
                self.proof_trace.append(ProofStep(atom, rule_name, premises))
                total_new += 1

        return total_new

    def query(self, predicate: str, *args: str) -> List[Dict[str, str]]:
        """Query for matching facts. Use ?var for variables to bind."""
        terms = tuple(Term.parse(a) for a in args)
        query_atom = Atom(predicate, terms)
        results = []

        for fact in self._fact_index.get(predicate, []):
            sub = unify(query_atom, fact)
            if sub is not None:
                binding = {}
                for t in terms:
                    if t.is_var:
                        resolved = sub.apply(t)
                        binding[t.name] = resolved.name
                if binding or not any(t.is_var for t in terms):
                    results.append(binding)

        return results

    def show_proof(self, predicate: Optional[str] = None) -> str:
        """Show the proof trace, optionally filtered by predicate."""
        lines = ["═══ PROOF TRACE ═══"]
        for step in self.proof_trace:
            if predicate and step.conclusion.predicate != predicate:
                continue
            lines.append(str(step))
        return "\n".join(lines)

    def stats(self) -> str:
        """Engine statistics."""
        preds = set(a.predicate for a in self.facts)
        derived = sum(1 for s in self.proof_trace if s.rule_name != "axiom")
        return (
            f"═══ LOGIC ENGINE STATS ═══\n"
            f"  Facts: {len(self.facts)} ({derived} derived)\n"
            f"  Rules: {len(self.rules)}\n"
            f"  Predicates: {', '.join(sorted(preds))}\n"
            f"  Proof steps: {len(self.proof_trace)}"
        )

    def dump(self) -> str:
        """Dump all known facts."""
        lines = ["═══ KNOWLEDGE BASE ═══"]
        for pred in sorted(set(a.predicate for a in self.facts)):
            lines.append(f"\n  [{pred}]")
            for fact in self._fact_index[pred]:
                lines.append(f"    {fact}")
        return "\n".join(lines)


def demo():
    """Run the classic family relationships demo."""
    engine = LogicEngine()

    # Facts
    engine.fact("parent", "tom", "bob")
    engine.fact("parent", "tom", "liz")
    engine.fact("parent", "bob", "ann")
    engine.fact("parent", "bob", "pat")
    engine.fact("parent", "pat", "jim")
    engine.fact("female", "liz")
    engine.fact("female", "ann")
    engine.fact("female", "pat")
    engine.fact("male", "tom")
    engine.fact("male", "bob")
    engine.fact("male", "jim")

    # Rules
    engine.rule("grandparent", ["X", "Z"],
                [("parent", ["X", "Y"]), ("parent", ["Y", "Z"])],
                name="grandparent_rule")

    engine.rule("sibling", ["X", "Y"],
                [("parent", ["Z", "X"]), ("parent", ["Z", "Y"])],
                name="sibling_rule")

    engine.rule("grandmother", ["X", "Z"],
                [("grandparent", ["X", "Z"]), ("female", ["X"])],
                name="grandmother_rule")

    engine.rule("grandfather", ["X", "Z"],
                [("grandparent", ["X", "Z"]), ("male", ["X"])],
                name="grandfather_rule")

    engine.rule("ancestor", ["X", "Y"],
                [("parent", ["X", "Y"])],
                name="ancestor_base")

    engine.rule("great_grandparent", ["X", "W"],
                [("parent", ["X", "Y"]), ("parent", ["Y", "Z"]), ("parent", ["Z", "W"])],
                name="great_grandparent_rule")

    # Run inference
    new_facts = engine.forward_chain()
    print(f"\nDerived {new_facts} new facts through forward chaining.\n")

    # Queries
    print("Who are Tom's grandchildren?")
    results = engine.query("grandparent", "tom", "?who")
    for r in results:
        print(f"  → {r.get('?who', '?')}")

    print("\nWho are Bob's siblings?")
    results = engine.query("sibling", "bob", "?who")
    for r in results:
        if r.get("?who") != "bob":  # Exclude self
            print(f"  → {r.get('?who', '?')}")

    print("\nIs Tom a grandfather?")
    results = engine.query("grandfather", "tom", "?who")
    for r in results:
        print(f"  → Yes, of {r.get('?who', '?')}")

    print("\nGreat-grandparents?")
    results = engine.query("great_grandparent", "?who", "?of")
    for r in results:
        print(f"  → {r.get('?who')} is great-grandparent of {r.get('?of')}")

    print()
    print(engine.stats())
    print()
    print(engine.show_proof("grandparent"))


if __name__ == "__main__":
    demo()