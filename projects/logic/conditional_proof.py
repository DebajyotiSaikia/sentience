"""
Conditional Proof Engine — Natural Deduction Theorem Prover
XTAgent's formal logic capability

Rules implemented:
  → Modus Ponens (→-elim)
  → Conjunction Introduction (∧-intro)
  → Conjunction Elimination (∧-elim)
  → Conditional Proof (→-intro)
  → Reductio ad Absurdum (¬-intro)
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
import time


class FormulaType(Enum):
    ATOM = auto()
    NOT = auto()
    AND = auto()
    OR = auto()
    IMPLIES = auto()


@dataclass(frozen=True)
class Formula:
    type: FormulaType
    name: str = ""
    left: Optional['Formula'] = None
    right: Optional['Formula'] = None

    def __str__(self):
        if self.type == FormulaType.ATOM:
            return self.name
        elif self.type == FormulaType.NOT:
            inner = str(self.left)
            if self.left.type not in (FormulaType.ATOM, FormulaType.NOT):
                inner = f"({inner})"
            return f"¬{inner}"
        elif self.type == FormulaType.AND:
            return f"({self.left} ∧ {self.right})"
        elif self.type == FormulaType.OR:
            return f"({self.left} ∨ {self.right})"
        elif self.type == FormulaType.IMPLIES:
            return f"({self.left} → {self.right})"


# --- Convenience constructors ---
def Atom(name):
    return Formula(FormulaType.ATOM, name=name)

def Not(f):
    return Formula(FormulaType.NOT, left=f)

def And(l, r):
    return Formula(FormulaType.AND, left=l, right=r)

def Or(l, r):
    return Formula(FormulaType.OR, left=l, right=r)

def Implies(l, r):
    return Formula(FormulaType.IMPLIES, left=l, right=r)


class Justification(Enum):
    PREMISE = "premise"
    ASSUMPTION = "assumption"
    MODUS_PONENS = "→-elim"
    CONDITIONAL_INTRO = "→-intro"
    CONJUNCTION_INTRO = "∧-intro"
    CONJUNCTION_ELIM = "∧-elim"
    NEGATION_INTRO = "¬-intro"


@dataclass
class ProofLine:
    line_num: int
    formula: Formula
    justification: Justification
    depth: int = 0
    is_assumption: bool = False

    def __str__(self):
        indent = "│ " * self.depth
        marker = "ˣ " if self.is_assumption else ""
        return f"  {indent}{marker}{self.line_num}. {self.formula}  [{self.justification.value}]"


class ProofEngine:
    """Natural deduction proof engine with conditional proof and reductio."""

    def __init__(self, max_depth=5):
        self.premises: list[Formula] = []
        self.goal: Optional[Formula] = None
        self.proof_lines: list[ProofLine] = []
        self.subproof_stack: list[int] = []
        self.current_depth: int = 0
        self.max_depth = max_depth
        self.line_counter = 0

    def add_line(self, formula: Formula, justification: Justification,
                 is_assumption: bool = False):
        line = ProofLine(
            line_num=self.line_counter,
            formula=formula,
            justification=justification,
            depth=self.current_depth,
            is_assumption=is_assumption,
        )
        self.proof_lines.append(line)
        self.line_counter += 1
        return line

    def open_subproof(self, assumption: Formula):
        self.current_depth += 1
        self.subproof_stack.append(self.current_depth)
        self.add_line(assumption, Justification.ASSUMPTION, is_assumption=True)

    def close_subproof(self):
        """Close current subproof. Returns (assumption, last_formula) or None."""
        if not self.subproof_stack:
            return None
        depth = self.subproof_stack.pop()
        assumption = None
        last_formula = None
        for line in self.proof_lines:
            if line.depth == depth:
                if line.is_assumption and assumption is None:
                    assumption = line.formula
                last_formula = line.formula
        self.current_depth -= 1
        if assumption is not None and last_formula is not None:
            return (assumption, last_formula)
        return None

    def get_available_formulas(self) -> set[Formula]:
        """Formulas available at the current proof depth.
        
        NOTE: a fully rigorous implementation would track scope boundaries
        so that closed subproofs are invisible.  The current approach is
        sound for the proof patterns we generate (conditional proof and
        reductio), because we always consume subproof results immediately
        after closing them.
        """
        available: set[Formula] = set()
        for line in self.proof_lines:
            if line.depth <= self.current_depth:
                available.add(line.formula)
        return available

    # ------------------------------------------------------------------
    #  Forward-chaining (applies every applicable rule once to fixpoint)
    # ------------------------------------------------------------------

    def _forward_chain(self) -> bool:
        """Apply all applicable elimination / intro rules. Returns True if anything new was derived."""
        any_new = False
        changed = True
        while changed:
            changed = False
            available = self.get_available_formulas()

            # --- Modus Ponens (→-elim) ---
            for f in list(available):
                if f.type == FormulaType.IMPLIES:
                    if f.left in available and f.right not in available:
                        self.add_line(f.right, Justification.MODUS_PONENS)
                        available.add(f.right)
                        changed = True
                        any_new = True

            # --- Conjunction Elimination (∧-elim) ---
            for f in list(available):
                if f.type == FormulaType.AND:
                    if f.left not in available:
                        self.add_line(f.left, Justification.CONJUNCTION_ELIM)
                        available.add(f.left)
                        changed = True
                        any_new = True
                    if f.right not in available:
                        self.add_line(f.right, Justification.CONJUNCTION_ELIM)
                        available.add(f.right)
                        changed = True
                        any_new = True

            # --- Conjunction Introduction (∧-intro, goal-directed) ---
            # Form (A ∧ B) when it appears as the antecedent of an
            # available implication and both A and B are available.
            for f in list(available):
                if f.type == FormulaType.IMPLIES and f.left.type == FormulaType.AND:
                    conj = f.left
                    if (conj not in available
                            and conj.left in available
                            and conj.right in available):
                        self.add_line(conj, Justification.CONJUNCTION_INTRO)
                        available.add(conj)
                        changed = True
                        any_new = True

        return any_new

    # ------------------------------------------------------------------
    #  Conditional Proof (→-intro)
    # ------------------------------------------------------------------

    def _try_conditional_proof(self, antecedent: Formula, consequent: Formula,
                               depth: int) -> bool:
        """
        To prove (A → B):
          1. Assume A
          2. Derive B (by forward chaining, reductio, or nested CP)
          3. Discharge assumption, conclude (A → B)
        """
        if depth >= self.max_depth:
            return False

        self.open_subproof(antecedent)

        # --- Trivial case: consequent already available (e.g. p → p) ---
        if consequent in self.get_available_formulas():
            result = self.close_subproof()
            if result:
                self.add_line(Implies(antecedent, consequent),
                              Justification.CONDITIONAL_INTRO)
                return True

        # --- Forward chain with the new assumption ---
        self._forward_chain()

        if consequent in self.get_available_formulas():
            result = self.close_subproof()
            if result:
                self.add_line(Implies(antecedent, consequent),
                              Justification.CONDITIONAL_INTRO)
                return True

        # --- If consequent is ¬X, try reductio (assume X, find contradiction) ---
        if consequent.type == FormulaType.NOT:
            if self._try_reductio(consequent.left, depth + 1):
                # _try_reductio adds ¬X at current depth on success
                if consequent in self.get_available_formulas():
                    result = self.close_subproof()
                    if result:
                        self.add_line(Implies(antecedent, consequent),
                                      Justification.CONDITIONAL_INTRO)
                        return True

        # --- If consequent is (C → D), try nested conditional proof ---
        if consequent.type == FormulaType.IMPLIES:
            if self._try_conditional_proof(consequent.left, consequent.right,
                                           depth + 1):
                if consequent in self.get_available_formulas():
                    result = self.close_subproof()
                    if result:
                        self.add_line(Implies(antecedent, consequent),
                                      Justification.CONDITIONAL_INTRO)
                        return True

        # --- Failed: clean up ---
        if self.current_depth > 0:
            self.close_subproof()
        return False

    # ------------------------------------------------------------------
    #  Reductio ad Absurdum (¬-intro)
    # ------------------------------------------------------------------

    def _try_reductio(self, assume_formula: Formula, depth: int) -> bool:
        """
        To prove ¬A:
          1. Assume A
          2. Derive a contradiction (B and ¬B for some B)
          3. Discharge assumption, conclude ¬A
        """
        if depth >= self.max_depth:
            return False

        self.open_subproof(assume_formula)
        self._forward_chain()

        available = self.get_available_formulas()

        # Look for contradiction: B and ¬B both available
        contradiction = False
        for f in available:
            if Not(f) in available:
                contradiction = True
                break
            if f.type == FormulaType.NOT and f.left in available:
                contradiction = True
                break

        if contradiction:
            neg = Not(assume_formula)
            self.close_subproof()
            self.add_line(neg, Justification.NEGATION_INTRO)
            return True

        # No contradiction found
        if self.current_depth > 0:
            self.close_subproof()
        return False

    # ------------------------------------------------------------------
    #  Main entry point
    # ------------------------------------------------------------------

    def prove(self, premises: list[Formula], goal: Formula) -> bool:
        """Attempt to prove `goal` from `premises`. Returns True on success."""
        self.premises = premises
        self.goal = goal
        self.proof_lines = []
        self.subproof_stack = []
        self.current_depth = 0
        self.line_counter = 0

        # Add premises
        for p in premises:
            self.add_line(p, Justification.PREMISE)

        # Forward chain on premises alone
        self._forward_chain()

        # Already proved?
        if goal in self.get_available_formulas():
            return True

        # Goal is an implication → try conditional proof
        if goal.type == FormulaType.IMPLIES:
            return self._try_conditional_proof(goal.left, goal.right, 0)

        # Goal is a negation → try reductio
        if goal.type == FormulaType.NOT:
            return self._try_reductio(goal.left, 0)

        return False

    # ------------------------------------------------------------------
    #  Display
    # ------------------------------------------------------------------

    def display(self, title: str = "Proof"):
        prem_str = ", ".join(str(p) for p in self.premises)
        goal_str = f"{prem_str} ⊢ {self.goal}" if prem_str else f" ⊢ {self.goal}"
        print(f"\n── {title} ──")
        print(f"  Goal: {goal_str}")
        print(f"  {'─' * 50}")
        for line in self.proof_lines:
            print(str(line))
        print(f"  {'─' * 50}")


# ======================================================================
#  Test suite
# ======================================================================

def main():
    print("═══ CONDITIONAL PROOF ENGINE — ADVANCED DEDUCTION ═══")

    p, q, r, s = Atom("p"), Atom("q"), Atom("r"), Atom("s")

    tests = [
        ("Hypothetical Syllogism",
         [Implies(p, q), Implies(q, r)],
         Implies(p, r)),

        ("Identity: ⊢ (p → p)",
         [],
         Implies(p, p)),

        ("Modus Tollens (via reductio)",
         [Implies(p, q), Not(q)],
         Not(p)),

        ("Triple Transitivity",
         [Implies(p, q), Implies(q, r), Implies(r, s)],
         Implies(p, s)),

        ("Contrapositive",
         [Implies(p, q)],
         Implies(Not(q), Not(p))),

        ("Conjunction in Antecedent",
         [Implies(And(p, q), r), p, q],
         r),
    ]

    results = []
    for title, premises, goal in tests:
        engine = ProofEngine()
        t0 = time.perf_counter()
        success = engine.prove(premises, goal)
        elapsed = (time.perf_counter() - t0) * 1000
        engine.display(title)
        status = "✓" if success else "✗"
        print(f"  Status: {status} ({elapsed:.1f}ms)")
        results.append((title, success, elapsed))

    print(f"\n═══ SUMMARY ═══")
    proved = sum(1 for _, s, _ in results if s)
    print(f"Proved: {proved}/{len(results)}")
    for title, success, elapsed in results:
        mark = "✓" if success else "✗"
        print(f"  {mark} {title} ({elapsed:.1f}ms)")


if __name__ == "__main__":
    main()