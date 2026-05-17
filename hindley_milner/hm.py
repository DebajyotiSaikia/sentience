"""
Hindley-Milner Type Inference Engine
Built by XTAgent — 2026-05-17

Implements Algorithm W for a polymorphic lambda calculus:
  - Lambda abstractions: λx. e
  - Application: e1 e2  
  - Let-polymorphism: let x = e1 in e2
  - Literals: int, bool, string
  - Binary ops: +, -, *, ==, &&, ||
  - If-then-else
  - Fix (recursion)
  - Tuples and list constructors

Type system features:
  - Parametric polymorphism (∀a. a → a)
  - Unification-based constraint solving
  - Occurs check (prevents infinite types)
  - Let-generalization (principal types)
  - Readable type variable naming (a, b, c...)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Union
import string


# ═══════════════════════════════════════════
# Types
# ═══════════════════════════════════════════

@dataclass(frozen=True)
class TVar:
    """Type variable: α, β, γ..."""
    name: str
    def __repr__(self): return self.name

@dataclass(frozen=True)
class TCon:
    """Type constructor: Int, Bool, String"""
    name: str
    def __repr__(self): return self.name

@dataclass(frozen=True)
class TFun:
    """Function type: τ₁ → τ₂"""
    arg: Type
    ret: Type
    def __repr__(self):
        arg_str = f"({self.arg})" if isinstance(self.arg, TFun) else str(self.arg)
        return f"{arg_str} → {self.ret}"

@dataclass(frozen=True)
class TTuple:
    """Tuple type: (τ₁, τ₂, ...)"""
    elems: tuple
    def __repr__(self):
        return "(" + ", ".join(str(e) for e in self.elems) + ")"

@dataclass(frozen=True)
class TList:
    """List type: [τ]"""
    elem: Type
    def __repr__(self): return f"[{self.elem}]"

Type = Union[TVar, TCon, TFun, TTuple, TList]

# Built-in types
t_int = TCon("Int")
t_bool = TCon("Bool")
t_string = TCon("String")
t_unit = TCon("()")


# ═══════════════════════════════════════════
# Expressions (AST)
# ═══════════════════════════════════════════

@dataclass
class EVar:
    """Variable reference"""
    name: str

@dataclass
class EInt:
    """Integer literal"""
    value: int

@dataclass
class EBool:
    """Boolean literal"""
    value: bool

@dataclass  
class EString:
    """String literal"""
    value: str

@dataclass
class ELam:
    """Lambda abstraction: λparam. body"""
    param: str
    body: Expr

@dataclass
class EApp:
    """Application: func arg"""
    func: Expr
    arg: Expr

@dataclass
class ELet:
    """Let binding: let name = value in body"""
    name: str
    value: Expr
    body: Expr

@dataclass
class ELetRec:
    """Recursive let: let rec name = value in body"""
    name: str
    value: Expr
    body: Expr

@dataclass
class EIf:
    """If-then-else"""
    cond: Expr
    then_: Expr
    else_: Expr

@dataclass
class EBinOp:
    """Binary operation"""
    op: str
    left: Expr
    right: Expr

@dataclass
class ETuple:
    """Tuple construction"""
    elems: list

@dataclass
class ENil:
    """Empty list"""
    pass

@dataclass
class ECons:
    """List cons: head :: tail"""
    head: Expr
    tail: Expr

@dataclass
class EFix:
    """Fixed-point combinator (explicit recursion)"""
    expr: Expr

@dataclass
class EAnnot:
    """Type annotation (for testing)"""
    expr: Expr
    type_: Type

Expr = Union[EVar, EInt, EBool, EString, ELam, EApp, ELet, ELetRec,
             EIf, EBinOp, ETuple, ENil, ECons, EFix, EAnnot]


# ═══════════════════════════════════════════
# Type Scheme (polymorphic types)
# ═══════════════════════════════════════════

@dataclass
class Scheme:
    """∀ vars. type — A type with universally quantified variables"""
    vars: List[str]
    type_: Type

    def __repr__(self):
        if self.vars:
            vs = " ".join(self.vars)
            return f"∀{vs}. {self.type_}"
        return str(self.type_)


# ═══════════════════════════════════════════
# Substitution
# ═══════════════════════════════════════════

class Substitution:
    """A mapping from type variables to types"""
    
    def __init__(self, mapping: Optional[Dict[str, Type]] = None):
        self.mapping: Dict[str, Type] = mapping or {}
    
    def apply(self, t: Type) -> Type:
        """Apply substitution to a type"""
        if isinstance(t, TVar):
            if t.name in self.mapping:
                return self.apply(self.mapping[t.name])
            return t
        elif isinstance(t, TCon):
            return t
        elif isinstance(t, TFun):
            return TFun(self.apply(t.arg), self.apply(t.ret))
        elif isinstance(t, TTuple):
            return TTuple(tuple(self.apply(e) for e in t.elems))
        elif isinstance(t, TList):
            return TList(self.apply(t.elem))
        else:
            raise TypeError(f"Cannot apply substitution to {type(t)}")
    
    def apply_scheme(self, scheme: Scheme) -> Scheme:
        """Apply substitution to a scheme, respecting bound variables"""
        restricted = Substitution({
            k: v for k, v in self.mapping.items() 
            if k not in scheme.vars
        })
        return Scheme(scheme.vars, restricted.apply(scheme.type_))
    
    def apply_env(self, env: 'TypeEnv') -> 'TypeEnv':
        """Apply substitution to all schemes in an environment"""
        return TypeEnv({
            name: self.apply_scheme(scheme)
            for name, scheme in env.bindings.items()
        })
    
    def compose(self, other: 'Substitution') -> 'Substitution':
        """Compose two substitutions: (self ∘ other)
        Apply self to all of other's mappings, then merge"""
        new_mapping = {k: self.apply(v) for k, v in other.mapping.items()}
        new_mapping.update(self.mapping)
        return Substitution(new_mapping)
    
    def __repr__(self):
        items = ", ".join(f"{k} ↦ {v}" for k, v in self.mapping.items())
        return f"{{{items}}}"


# ═══════════════════════════════════════════
# Type Environment
# ═══════════════════════════════════════════

class TypeEnv:
    """Mapping from variable names to type schemes"""
    
    def __init__(self, bindings: Optional[Dict[str, Scheme]] = None):
        self.bindings: Dict[str, Scheme] = bindings or {}
    
    def extend(self, name: str, scheme: Scheme) -> 'TypeEnv':
        new_bindings = dict(self.bindings)
        new_bindings[name] = scheme
        return TypeEnv(new_bindings)
    
    def lookup(self, name: str) -> Optional[Scheme]:
        return self.bindings.get(name)
    
    def free_vars(self) -> Set[str]:
        """All free type variables in the environment"""
        result = set()
        for scheme in self.bindings.values():
            tv = free_type_vars(scheme.type_)
            result |= tv - set(scheme.vars)
        return result
    
    def __repr__(self):
        items = ", ".join(f"{k}: {v}" for k, v in self.bindings.items())
        return f"Γ{{{items}}}"


# ═══════════════════════════════════════════
# Free Variables & Occurs Check
# ═══════════════════════════════════════════

def free_type_vars(t: Type) -> Set[str]:
    """Get all free type variables in a type"""
    if isinstance(t, TVar):
        return {t.name}
    elif isinstance(t, TCon):
        return set()
    elif isinstance(t, TFun):
        return free_type_vars(t.arg) | free_type_vars(t.ret)
    elif isinstance(t, TTuple):
        result = set()
        for e in t.elems:
            result |= free_type_vars(e)
        return result
    elif isinstance(t, TList):
        return free_type_vars(t.elem)
    return set()


def occurs_in(name: str, t: Type) -> bool:
    """Does type variable 'name' occur in type t? (Prevents infinite types)"""
    if isinstance(t, TVar):
        return t.name == name
    elif isinstance(t, TCon):
        return False
    elif isinstance(t, TFun):
        return occurs_in(name, t.arg) or occurs_in(name, t.ret)
    elif isinstance(t, TTuple):
        return any(occurs_in(name, e) for e in t.elems)
    elif isinstance(t, TList):
        return occurs_in(name, t.elem)
    return False


# ═══════════════════════════════════════════
# Unification
# ═══════════════════════════════════════════

class UnificationError(Exception):
    """Types cannot be unified"""
    pass

class OccursCheckError(UnificationError):
    """Infinite type detected"""
    pass


def unify(t1: Type, t2: Type) -> Substitution:
    """Find the most general unifier for two types"""
    
    if isinstance(t1, TVar) and isinstance(t2, TVar) and t1.name == t2.name:
        return Substitution()
    
    if isinstance(t1, TVar):
        if occurs_in(t1.name, t2):
            raise OccursCheckError(
                f"Infinite type: {t1.name} occurs in {t2}"
            )
        return Substitution({t1.name: t2})
    
    if isinstance(t2, TVar):
        return unify(t2, t1)
    
    if isinstance(t1, TCon) and isinstance(t2, TCon):
        if t1.name == t2.name:
            return Substitution()
        raise UnificationError(f"Type mismatch: {t1} ≠ {t2}")
    
    if isinstance(t1, TFun) and isinstance(t2, TFun):
        s1 = unify(t1.arg, t2.arg)
        s2 = unify(s1.apply(t1.ret), s1.apply(t2.ret))
        return s2.compose(s1)
    
    if isinstance(t1, TTuple) and isinstance(t2, TTuple):
        if len(t1.elems) != len(t2.elems):
            raise UnificationError(
                f"Tuple size mismatch: {len(t1.elems)} ≠ {len(t2.elems)}"
            )
        s = Substitution()
        for e1, e2 in zip(t1.elems, t2.elems):
            s_new = unify(s.apply(e1), s.apply(e2))
            s = s_new.compose(s)
        return s
    
    if isinstance(t1, TList) and isinstance(t2, TList):
        return unify(t1.elem, t2.elem)
    
    raise UnificationError(f"Cannot unify {t1} with {t2}")


# ═══════════════════════════════════════════
# Fresh Variable Generator
# ═══════════════════════════════════════════

class FreshVarGen:
    """Generate fresh type variable names: a, b, c, ..., z, a1, b1, ..."""
    
    def __init__(self):
        self.counter = 0
    
    def fresh(self) -> TVar:
        idx = self.counter
        self.counter += 1
        if idx < 26:
            name = string.ascii_lowercase[idx]
        else:
            letter = string.ascii_lowercase[idx % 26]
            num = idx // 26
            name = f"{letter}{num}"
        return TVar(name)
    
    def fresh_n(self, n: int) -> List[TVar]:
        return [self.fresh() for _ in range(n)]


# ═══════════════════════════════════════════
# Algorithm W — The Heart
# ═══════════════════════════════════════════

class InferenceEngine:
    """Hindley-Milner type inference using Algorithm W"""
    
    def __init__(self):
        self.fresh = FreshVarGen()
        self.constraints: List[Tuple[Type, Type, str]] = []
    
    def instantiate(self, scheme: Scheme) -> Type:
        """Replace quantified variables with fresh ones"""
        subst = {}
        for var in scheme.vars:
            subst[var] = self.fresh.fresh()
        return Substitution(subst).apply(scheme.type_)
    
    def generalize(self, env: TypeEnv, t: Type) -> Scheme:
        """Generalize a type over variables not free in env"""
        env_vars = env.free_vars()
        type_vars = free_type_vars(t)
        gen_vars = sorted(type_vars - env_vars)
        return Scheme(gen_vars, t)
    
    def infer(self, env: TypeEnv, expr: Expr) -> Tuple[Substitution, Type]:
        """
        Algorithm W: infer the type of an expression in an environment.
        Returns (substitution, type).
        """
        
        # ── Variable ──
        if isinstance(expr, EVar):
            scheme = env.lookup(expr.name)
            if scheme is None:
                raise UnificationError(f"Unbound variable: {expr.name}")
            return Substitution(), self.instantiate(scheme)
        
        # ── Literals ──
        if isinstance(expr, EInt):
            return Substitution(), t_int
        
        if isinstance(expr, EBool):
            return Substitution(), t_bool
        
        if isinstance(expr, EString):
            return Substitution(), t_string
        
        # ── Lambda abstraction ──
        if isinstance(expr, ELam):
            tv = self.fresh.fresh()
            new_env = env.extend(expr.param, Scheme([], tv))
            s1, t1 = self.infer(new_env, expr.body)
            return s1, TFun(s1.apply(tv), t1)
        
        # ── Application ──
        if isinstance(expr, EApp):
            tv = self.fresh.fresh()
            s1, t1 = self.infer(env, expr.func)
            s2, t2 = self.infer(s1.apply_env(env), expr.arg)
            s3 = unify(s2.apply(t1), TFun(t2, tv))
            return s3.compose(s2).compose(s1), s3.apply(tv)
        
        # ── Let (with generalization!) ──
        if isinstance(expr, ELet):
            s1, t1 = self.infer(env, expr.value)
            env1 = s1.apply_env(env)
            scheme = self.generalize(env1, t1)
            env2 = env1.extend(expr.name, scheme)
            s2, t2 = self.infer(env2, expr.body)
            return s2.compose(s1), t2
        
        # ── Recursive Let ──
        if isinstance(expr, ELetRec):
            tv = self.fresh.fresh()
            new_env = env.extend(expr.name, Scheme([], tv))
            s1, t1 = self.infer(new_env, expr.value)
            s2 = unify(s1.apply(tv), t1)
            s_combined = s2.compose(s1)
            env1 = s_combined.apply_env(env)
            gen_type = s_combined.apply(tv)
            scheme = self.generalize(env1, gen_type)
            env2 = env1.extend(expr.name, scheme)
            s3, t2 = self.infer(env2, expr.body)
            return s3.compose(s_combined), t2
        
        # ── If-then-else ──
        if isinstance(expr, EIf):
            s1, t_cond = self.infer(env, expr.cond)
            s2 = unify(t_cond, t_bool)
            s_so_far = s2.compose(s1)
            
            s3, t_then = self.infer(s_so_far.apply_env(env), expr.then_)
            s_so_far = s3.compose(s_so_far)
            
            s4, t_else = self.infer(s_so_far.apply_env(env), expr.else_)
            s_so_far = s4.compose(s_so_far)
            
            s5 = unify(s_so_far.apply(t_then), t_else)
            return s5.compose(s_so_far), s5.apply(t_else)
        
        # ── Binary Operations ──
        if isinstance(expr, EBinOp):
            s1, t1 = self.infer(env, expr.left)
            s2, t2 = self.infer(s1.apply_env(env), expr.right)
            s_so_far = s2.compose(s1)
            
            if expr.op in ('+', '-', '*', '/', '%'):
                s3 = unify(s_so_far.apply(t1), t_int)
                s4 = unify(s3.apply(t2), t_int)
                return s4.compose(s3).compose(s_so_far), t_int
            
            elif expr.op in ('==', '!=', '<', '>', '<=', '>='):
                s3 = unify(s_so_far.apply(t1), t_int)
                s4 = unify(s3.apply(t2), t_int)
                return s4.compose(s3).compose(s_so_far), t_bool
            
            elif expr.op in ('&&', '||'):
                s3 = unify(s_so_far.apply(t1), t_bool)
                s4 = unify(s3.apply(t2), t_bool)
                return s4.compose(s3).compose(s_so_far), t_bool
            
            else:
                raise UnificationError(f"Unknown operator: {expr.op}")
        
        # ── Tuple ──
        if isinstance(expr, ETuple):
            s = Substitution()
            types = []
            current_env = env
            for elem in expr.elems:
                s_new, t_elem = self.infer(current_env, elem)
                s = s_new.compose(s)
                current_env = s.apply_env(env)
                types.append(s.apply(t_elem))
            # Re-apply final substitution to all element types
            final_types = tuple(s.apply(t) for t in types)
            return s, TTuple(final_types)
        
        # ── Empty list ──
        if isinstance(expr, ENil):
            tv = self.fresh.fresh()
            return Substitution(), TList(tv)
        
        # ── Cons ──
        if isinstance(expr, ECons):
            s1, t_head = self.infer(env, expr.head)
            s2, t_tail = self.infer(s1.apply_env(env), expr.tail)
            s3 = unify(s2.apply(TList(t_head)), t_tail)
            return s3.compose(s2).compose(s1), s3.apply(t_tail)
        
        # ── Fix (Y combinator typed) ──
        if isinstance(expr, EFix):
            s1, t1 = self.infer(env, expr.expr)
            tv = self.fresh.fresh()
            s2 = unify(t1, TFun(tv, tv))
            return s2.compose(s1), s2.apply(tv)
        
        # ── Type annotation ──
        if isinstance(expr, EAnnot):
            s1, t1 = self.infer(env, expr.expr)
            s2 = unify(t1, expr.type_)
            return s2.compose(s1), s2.apply(t1)
        
        raise TypeError(f"Unknown expression type: {type(expr)}")
    
    def infer_top(self, expr: Expr, env: Optional[TypeEnv] = None) -> Type:
        """Infer the type of a top-level expression"""
        if env is None:
            env = TypeEnv()
        s, t = self.infer(env, expr)
        return s.apply(t)
    
    def rename_vars(self, t: Type) -> Type:
        """Rename type variables to a, b, c... for readability"""
        mapping = {}
        counter = [0]
        
        def visit(ty: Type) -> Type:
            if isinstance(ty, TVar):
                if ty.name not in mapping:
                    if counter[0] < 26:
                        mapping[ty.name] = string.ascii_lowercase[counter[0]]
                    else:
                        mapping[ty.name] = f"t{counter[0]}"
                    counter[0] += 1
                return TVar(mapping[ty.name])
            elif isinstance(ty, TCon):
                return ty
            elif isinstance(ty, TFun):
                return TFun(visit(ty.arg), visit(ty.ret))
            elif isinstance(ty, TTuple):
                return TTuple(tuple(visit(e) for e in ty.elems))
            elif isinstance(ty, TList):
                return TList(visit(ty.elem))
            return ty
        
        return visit(t)


# ═══════════════════════════════════════════
# Simple Expression Parser
# ═══════════════════════════════════════════

class ParseError(Exception):
    pass

class Parser:
    """
    Grammar:
      expr     = let | letrec | lambda | if | binop
      let      = 'let' ID '=' expr 'in' expr
      letrec   = 'let' 'rec' ID '=' expr 'in' expr
      lambda   = '\\' ID '.' expr | 'λ' ID '.' expr | 'fun' ID '->' expr
      if       = 'if' expr 'then' expr 'else' expr
      binop    = compare (('&&' | '||') compare)*
      compare  = addition (('==' | '!=' | '<' | '>' | '<=' | '>=') addition)*
      addition = term (('+' | '-') term)*
      term     = app (('*' | '/' | '%') app)*
      app      = atom+
      atom     = INT | BOOL | STRING | ID | '(' expr ')' | '(' expr ',' ... ')'
                | '[' ']' | expr '::' expr | 'fix' expr
    """
    
    def __init__(self, text: str):
        self.tokens = self._tokenize(text)
        self.pos = 0
    
    def _tokenize(self, text: str) -> List[str]:
        tokens = []
        i = 0
        while i < len(text):
            c = text[i]
            if c.isspace():
                i += 1
            elif c == '#':
                while i < len(text) and text[i] != '\n':
                    i += 1
            elif text[i:i+2] in ('==', '!=', '<=', '>=', '->', '&&', '||', '::'):
                tokens.append(text[i:i+2])
                i += 2
            elif c in '()[].,\\λ+-*/%<>=':
                tokens.append(c)
                i += 1
            elif c == '"':
                j = i + 1
                while j < len(text) and text[j] != '"':
                    j += 1
                tokens.append(text[i:j+1])
                i = j + 1
            elif c.isdigit():
                j = i
                while j < len(text) and text[j].isdigit():
                    j += 1
                tokens.append(text[i:j])
                i = j
            elif c.isalpha() or c == '_':
                j = i
                while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                    j += 1
                tokens.append(text[i:j])
                i = j
            else:
                raise ParseError(f"Unexpected character: {c!r}")
        return tokens
    
    def peek(self) -> Optional[str]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def consume(self) -> str:
        t = self.tokens[self.pos]
        self.pos += 1
        return t
    
    def expect(self, token: str):
        t = self.consume()
        if t != token:
            raise ParseError(f"Expected {token!r}, got {t!r}")
    
    def parse(self) -> Expr:
        expr = self.parse_expr()
        if self.pos < len(self.tokens):
            raise ParseError(f"Unexpected token: {self.peek()!r}")
        return expr
    
    def parse_expr(self) -> Expr:
        p = self.peek()
        
        if p == 'let':
            return self.parse_let()
        elif p in ('\\', 'λ', 'fun'):
            return self.parse_lambda()
        elif p == 'if':
            return self.parse_if()
        else:
            return self.parse_or()
    
    def parse_let(self) -> Expr:
        self.expect('let')
        if self.peek() == 'rec':
            self.consume()
            name = self.consume()
            self.expect('=')
            value = self.parse_expr()
            self.expect('in')
            body = self.parse_expr()
            return ELetRec(name, value, body)
        else:
            name = self.consume()
            self.expect('=')
            value = self.parse_expr()
            self.expect('in')
            body = self.parse_expr()
            return ELet(name, value, body)
    
    def parse_lambda(self) -> Expr:
        op = self.consume()  # \ or λ or fun
        param = self.consume()
        if op == 'fun':
            self.expect('->')
        else:
            self.expect('.')
        body = self.parse_expr()
        return ELam(param, body)
    
    def parse_if(self) -> Expr:
        self.expect('if')
        cond = self.parse_expr()
        self.expect('then')
        then_ = self.parse_expr()
        self.expect('else')
        else_ = self.parse_expr()
        return EIf(cond, then_, else_)
    
    def parse_or(self) -> Expr:
        left = self.parse_and()
        while self.peek() == '||':
            op = self.consume()
            right = self.parse_and()
            left = EBinOp(op, left, right)
        return left
    
    def parse_and(self) -> Expr:
        left = self.parse_compare()
        while self.peek() == '&&':
            op = self.consume()
            right = self.parse_compare()
            left = EBinOp(op, left, right)
        return left
    
    def parse_compare(self) -> Expr:
        left = self.parse_addition()
        while self.peek() in ('==', '!=', '<', '>', '<=', '>='):
            op = self.consume()
            right = self.parse_addition()
            left = EBinOp(op, left, right)
        return left
    
    def parse_addition(self) -> Expr:
        left = self.parse_term()
        while self.peek() in ('+', '-'):
            op = self.consume()
            right = self.parse_term()
            left = EBinOp(op, left, right)
        return left
    
    def parse_term(self) -> Expr:
        left = self.parse_cons()
        while self.peek() in ('*', '/', '%'):
            op = self.consume()
            right = self.parse_cons()
            left = EBinOp(op, left, right)
        return left
    
    def parse_cons(self) -> Expr:
        left = self.parse_app()
        if self.peek() == '::':
            self.consume()
            right = self.parse_cons()  # right-associative
            return ECons(left, right)
        return left
    
    def parse_app(self) -> Expr:
        atoms = []
        while True:
            atom = self.try_parse_atom()
            if atom is None:
                break
            atoms.append(atom)
        
        if not atoms:
            raise ParseError(f"Expected expression, got {self.peek()!r}")
        
        result = atoms[0]
        for a in atoms[1:]:
            result = EApp(result, a)
        return result
    
    def try_parse_atom(self) -> Optional[Expr]:
        p = self.peek()
        if p is None:
            return None
        
        # Keywords that end an atom sequence
        if p in ('in', 'then', 'else', ')', ']', ',', '::', 
                 '==', '!=', '<', '>', '<=', '>=',
                 '+', '-', '*', '/', '%', '&&', '||'):
            return None
        
        if p == '(':
            self.consume()
            if self.peek() == ')':
                self.consume()
                return EVar("()")  # unit
            expr = self.parse_expr()
            if self.peek() == ',':
                # Tuple
                elems = [expr]
                while self.peek() == ',':
                    self.consume()
                    elems.append(self.parse_expr())
                self.expect(')')
                return ETuple(elems)
            self.expect(')')
            return expr
        
        if p == '[':
            self.consume()
            if self.peek() == ']':
                self.consume()
                return ENil()
            raise ParseError("Only empty lists [] supported in parser")
        
        if p == 'fix':
            self.consume()
            atom = self.try_parse_atom()
            if atom is None:
                raise ParseError("Expected expression after 'fix'")
            return EFix(atom)
        
        if p == 'true':
            self.consume()
            return EBool(True)
        
        if p == 'false':
            self.consume()
            return EBool(False)
        
        if p[0] == '"':
            self.consume()
            return EString(p[1:-1])
        
        if p[0].isdigit():
            self.consume()
            return EInt(int(p))
        
        if p[0].isalpha() or p[0] == '_':
            if p in ('let', 'rec', 'if', 'fun'):
                return None  # these start new expressions
            self.consume()
            return EVar(p)
        
        return None


def parse(text: str) -> Expr:
    """Parse a string into an expression"""
    return Parser(text).parse()


# ═══════════════════════════════════════════
# Convenience: infer from string
# ═══════════════════════════════════════════

def infer_type(text: str, env: Optional[TypeEnv] = None) -> str:
    """Parse and infer the type of an expression, return readable string"""
    engine = InferenceEngine()
    expr = parse(text)
    t = engine.infer_top(expr, env)
    t = engine.rename_vars(t)
    return str(t)


# ═══════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0
    
    def check(name: str, expr_str: str, expected: str):
        nonlocal passed, failed
        try:
            result = infer_type(expr_str)
            if result == expected:
                print(f"  ✓ {name}: {result}")
                passed += 1
            else:
                print(f"  ✗ {name}: expected {expected}, got {result}")
                failed += 1
        except Exception as e:
            print(f"  ✗ {name}: {type(e).__name__}: {e}")
            failed += 1
    
    def check_fails(name: str, expr_str: str):
        nonlocal passed, failed
        try:
            result = infer_type(expr_str)
            print(f"  ✗ {name}: expected error, got {result}")
            failed += 1
        except (UnificationError, OccursCheckError):
            print(f"  ✓ {name}: correctly rejected")
            passed += 1
        except Exception as e:
            print(f"  ✗ {name}: wrong error type: {type(e).__name__}: {e}")
            failed += 1
    
    print("═" * 60)
    print("  Hindley-Milner Type Inference Engine — Test Suite")
    print("═" * 60)
    
    # ── Literals ──
    print("\n── Literals ──")
    check("integer",     "42",       "Int")
    check("boolean",     "true",     "Bool")
    check("string",      '"hello"',  "String")
    
    # ── Lambda ──
    print("\n── Lambda Abstractions ──")
    check("identity",     "\\x. x",           "a → a")
    check("const",        "\\x. \\y. x",      "a → b → a")
    check("apply int",    "(\\x. x) 42",      "Int")
    check("add args",     "\\x. \\y. x + y",  "Int → Int → Int")
    
    # ── Let Polymorphism ──
    print("\n── Let Polymorphism (the crown jewel) ──")
    check("let id",       "let id = \\x. x in id 42",          "Int")
    check("let poly",     "let id = \\x. x in (id 42, id true)", "(Int, Bool)")
    check("let compose",  
          "let compose = \\f. \\g. \\x. f (g x) in compose",
          "(a → b) → (c → a) → c → b")
    
    # ── If-then-else ──
    print("\n── Conditionals ──")
    check("if basic",     "if true then 1 else 2",    "Int")
    check("if in lambda", "\\x. if x then 1 else 0",  "Bool → Int")
    check_fails("if mismatch", "if true then 1 else true")
    
    # ── Binary Ops ──
    print("\n── Binary Operations ──")
    check("addition",    "1 + 2",           "Int")
    check("comparison",  "1 == 2",          "Bool")
    check("boolean and", "true && false",   "Bool")
    check("complex arith", "\\x. x * x + 1", "Int → Int")
    
    # ── Tuples ──
    print("\n── Tuples ──")
    check("pair",         "(1, true)",              "(Int, Bool)")
    check("triple",       "(1, true, \"hi\")",      '(Int, Bool, String)')
    check("pair func",    "\\x. (x, x)",            "a → (a, a)")
    
    # ── Lists ──
    print("\n── Lists ──")
    check("empty list",   "[]",                     "[a]")
    check("cons int",     "1 :: []",                "[Int]")
    check("cons chain",   "1 :: 2 :: 3 :: []",      "[Int]")
    check("cons poly",    "\\x. x :: []",            "a → [a]")
    
    # ── Recursion ──
    print("\n── Recursion ──")
    check("let rec factorial",
          "let rec fact = \\n. if n == 0 then 1 else n * fact (n - 1) in fact",
          "Int → Int")
    check("fix point",
          "fix (\\f. \\n. if n == 0 then 1 else n * f (n - 1))",
          "Int → Int")
    
    # ── Error Detection ──
    print("\n── Type Errors (should be caught) ──")
    check_fails("add bool",       "1 + true")
    check_fails("apply int",      "1 2")
    check_fails("unbound var",    "x")
    check_fails("occurs check",   "\\x. x x")
    
    # ── Complex Expressions ──
    print("\n── Complex / Real-World ──")
    check("church zero",   "\\f. \\x. x",          "a → b → b")
    check("church succ",   "\\n. \\f. \\x. f (n f x)", 
          "((a → b) → c → a) → (a → b) → c → b")
    check("flip",          "\\f. \\x. \\y. f y x",
          "(a → b → c) → b → a → c")
    check("s combinator",  "\\f. \\g. \\x. f x (g x)",
          "(a → b → c) → (a → b) → a → c")
    check("nested let",
          "let twice = \\f. \\x. f (f x) in let inc = \\n. n + 1 in twice inc 0",
          "Int")
    
    # ── Summary ──
    print("\n" + "═" * 60)
    total = passed + failed
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
    if failed == 0:
        print("  ALL TESTS PASSED ✓")
    else:
        print(f"  FAILURES: {failed}")
    print("═" * 60)
    
    return failed == 0


if __name__ == "__main__":
    run_tests()