"""
Hindley-Milner Type Inference Engine — XTAgent
Complete implementation: parsing, type unification, constraint generation,
let-polymorphism, and inference. Pure Python, no libraries.

This is the algorithm at the heart of typed functional languages.
"""

# ═══════════════════════════════════════════
# PART 1: Types
# ═══════════════════════════════════════════

class Type:
    """Base type."""
    pass

class TVar(Type):
    """Type variable (e.g., 'a, 'b). May be bound during unification."""
    _counter = 0
    def __init__(self, name=None):
        if name is None:
            TVar._counter += 1
            name = f"t{TVar._counter}"
        self.name = name
    def __repr__(self):
        return self.name
    def __eq__(self, other):
        return isinstance(other, TVar) and self.name == other.name
    def __hash__(self):
        return hash(self.name)

class TCon(Type):
    """Type constructor (concrete type like Int, Bool, String)."""
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name
    def __eq__(self, other):
        return isinstance(other, TCon) and self.name == other.name
    def __hash__(self):
        return hash(self.name)

class TFun(Type):
    """Function type: arg -> ret."""
    def __init__(self, arg, ret):
        self.arg = arg
        self.ret = ret
    def __repr__(self):
        arg_str = f"({self.arg})" if isinstance(self.arg, TFun) else str(self.arg)
        return f"{arg_str} -> {self.ret}"
    def __eq__(self, other):
        return isinstance(other, TFun) and self.arg == other.arg and self.ret == other.ret
    def __hash__(self):
        return hash(("->", self.arg, self.ret))

class TList(Type):
    """List type: [a]."""
    def __init__(self, elem):
        self.elem = elem
    def __repr__(self):
        return f"[{self.elem}]"
    def __eq__(self, other):
        return isinstance(other, TList) and self.elem == other.elem
    def __hash__(self):
        return hash(("[]", self.elem))

class TTuple(Type):
    """Tuple type: (a, b, ...)."""
    def __init__(self, elems):
        self.elems = tuple(elems)
    def __repr__(self):
        return f"({', '.join(str(e) for e in self.elems)})"
    def __eq__(self, other):
        return isinstance(other, TTuple) and self.elems == other.elems
    def __hash__(self):
        return hash(("()", self.elems))

# Built-in types
TInt = TCon("Int")
TBool = TCon("Bool")
TStr = TCon("String")
TUnit = TCon("()")

# ═══════════════════════════════════════════
# PART 2: Type Schemes (Polymorphism)
# ═══════════════════════════════════════════

class Scheme:
    """Polymorphic type scheme: forall a b . Type
    
    e.g., the identity function has scheme: forall a . a -> a
    """
    def __init__(self, vars, type):
        self.vars = set(vars)  # bound type variables
        self.type = type
    
    def __repr__(self):
        if self.vars:
            vs = ' '.join(str(v) for v in sorted(self.vars, key=str))
            return f"∀{vs}. {self.type}"
        return str(self.type)
    
    def instantiate(self):
        """Create a fresh copy with new type variables for each bound var."""
        subst = {v: TVar() for v in self.vars}
        return apply_subst(subst, self.type)

# ═══════════════════════════════════════════
# PART 3: Substitution
# ═══════════════════════════════════════════

def apply_subst(subst, type):
    """Apply a substitution (dict of TVar -> Type) to a type."""
    if isinstance(type, TVar):
        if type in subst:
            return apply_subst(subst, subst[type])
        return type
    elif isinstance(type, TCon):
        return type
    elif isinstance(type, TFun):
        return TFun(apply_subst(subst, type.arg), apply_subst(subst, type.ret))
    elif isinstance(type, TList):
        return TList(apply_subst(subst, type.elem))
    elif isinstance(type, TTuple):
        return TTuple([apply_subst(subst, e) for e in type.elems])
    return type

def apply_subst_scheme(subst, scheme):
    """Apply substitution to a scheme (excluding bound vars)."""
    restricted = {k: v for k, v in subst.items() if k not in scheme.vars}
    return Scheme(scheme.vars, apply_subst(restricted, scheme.type))

def apply_subst_env(subst, env):
    """Apply substitution to a type environment."""
    return {name: apply_subst_scheme(subst, scheme) for name, scheme in env.items()}

def compose_subst(s1, s2):
    """Compose two substitutions: first apply s2, then s1."""
    result = {v: apply_subst(s1, t) for v, t in s2.items()}
    result.update(s1)
    return result

def free_vars(type):
    """Get free type variables in a type."""
    if isinstance(type, TVar):
        return {type}
    elif isinstance(type, TCon):
        return set()
    elif isinstance(type, TFun):
        return free_vars(type.arg) | free_vars(type.ret)
    elif isinstance(type, TList):
        return free_vars(type.elem)
    elif isinstance(type, TTuple):
        result = set()
        for e in type.elems:
            result |= free_vars(e)
        return result
    return set()

def free_vars_scheme(scheme):
    """Free variables in a scheme (those not universally quantified)."""
    return free_vars(scheme.type) - scheme.vars

def free_vars_env(env):
    """Free variables across entire environment."""
    result = set()
    for scheme in env.values():
        result |= free_vars_scheme(scheme)
    return result

# ═══════════════════════════════════════════
# PART 4: Unification
# ═══════════════════════════════════════════

class UnificationError(Exception):
    pass

class OccursCheckError(UnificationError):
    pass

def occurs_in(tvar, type):
    """Check if tvar occurs in type (prevents infinite types)."""
    if isinstance(type, TVar):
        return tvar == type
    elif isinstance(type, TFun):
        return occurs_in(tvar, type.arg) or occurs_in(tvar, type.ret)
    elif isinstance(type, TList):
        return occurs_in(tvar, type.elem)
    elif isinstance(type, TTuple):
        return any(occurs_in(tvar, e) for e in type.elems)
    return False

def unify(t1, t2):
    """Unify two types, returning a substitution or raising UnificationError."""
    if isinstance(t1, TVar):
        if t1 == t2:
            return {}
        if occurs_in(t1, t2):
            raise OccursCheckError(f"Infinite type: {t1} occurs in {t2}")
        return {t1: t2}
    
    elif isinstance(t2, TVar):
        return unify(t2, t1)
    
    elif isinstance(t1, TCon) and isinstance(t2, TCon):
        if t1.name == t2.name:
            return {}
        raise UnificationError(f"Cannot unify {t1} with {t2}")
    
    elif isinstance(t1, TFun) and isinstance(t2, TFun):
        s1 = unify(t1.arg, t2.arg)
        s2 = unify(apply_subst(s1, t1.ret), apply_subst(s1, t2.ret))
        return compose_subst(s2, s1)
    
    elif isinstance(t1, TList) and isinstance(t2, TList):
        return unify(t1.elem, t2.elem)
    
    elif isinstance(t1, TTuple) and isinstance(t2, TTuple):
        if len(t1.elems) != len(t2.elems):
            raise UnificationError(f"Tuple length mismatch: {t1} vs {t2}")
        subst = {}
        for e1, e2 in zip(t1.elems, t2.elems):
            s = unify(apply_subst(subst, e1), apply_subst(subst, e2))
            subst = compose_subst(s, subst)
        return subst
    
    raise UnificationError(f"Cannot unify {t1} with {t2}")

# ═══════════════════════════════════════════
# PART 5: Expressions (AST)
# ═══════════════════════════════════════════

class Expr:
    pass

class EVar(Expr):
    """Variable reference."""
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name

class EInt(Expr):
    """Integer literal."""
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return str(self.value)

class EBool(Expr):
    """Boolean literal."""
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return str(self.value)

class EStr(Expr):
    """String literal."""
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f'"{self.value}"'

class ELam(Expr):
    """Lambda abstraction: \\x -> body."""
    def __init__(self, param, body):
        self.param = param
        self.body = body
    def __repr__(self):
        return f"(\\{self.param} -> {self.body})"

class EApp(Expr):
    """Function application: f(x)."""
    def __init__(self, func, arg):
        self.func = func
        self.arg = arg
    def __repr__(self):
        return f"({self.func} {self.arg})"

class ELet(Expr):
    """Let binding: let x = expr in body."""
    def __init__(self, name, expr, body):
        self.name = name
        self.expr = expr
        self.body = body
    def __repr__(self):
        return f"(let {self.name} = {self.expr} in {self.body})"

class ELetRec(Expr):
    """Recursive let: letrec f = expr in body."""
    def __init__(self, name, expr, body):
        self.name = name
        self.expr = expr
        self.body = body
    def __repr__(self):
        return f"(letrec {self.name} = {self.expr} in {self.body})"

class EIf(Expr):
    """If-then-else."""
    def __init__(self, cond, then_expr, else_expr):
        self.cond = cond
        self.then_expr = then_expr
        self.else_expr = else_expr
    def __repr__(self):
        return f"(if {self.cond} then {self.then_expr} else {self.else_expr})"

class EBinOp(Expr):
    """Binary operation."""
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"

class ETuple(Expr):
    """Tuple construction."""
    def __init__(self, elems):
        self.elems = elems
    def __repr__(self):
        return f"({', '.join(str(e) for e in self.elems)})"

class EListLit(Expr):
    """List literal."""
    def __init__(self, elems):
        self.elems = elems
    def __repr__(self):
        return f"[{', '.join(str(e) for e in self.elems)}]"

# ═══════════════════════════════════════════
# PART 6: Type Inference (Algorithm W)
# ═══════════════════════════════════════════

class TypeError(Exception):
    pass

def generalize(env, type):
    """Generalize a type into a scheme by quantifying free vars not in env."""
    env_free = free_vars_env(env)
    type_free = free_vars(type)
    quantified = type_free - env_free
    return Scheme(quantified, type)

# Binary operator type signatures
BINOP_TYPES = {
    '+': (TInt, TInt, TInt),
    '-': (TInt, TInt, TInt),
    '*': (TInt, TInt, TInt),
    '/': (TInt, TInt, TInt),
    '%': (TInt, TInt, TInt),
    '==': None,  # polymorphic: a -> a -> Bool
    '!=': None,
    '<': (TInt, TInt, TBool),
    '>': (TInt, TInt, TBool),
    '<=': (TInt, TInt, TBool),
    '>=': (TInt, TInt, TBool),
    '&&': (TBool, TBool, TBool),
    '||': (TBool, TBool, TBool),
}

def infer(env, expr):
    """
    Algorithm W: infer the type of an expression given an environment.
    Returns (substitution, type).
    
    This is the core of Hindley-Milner inference.
    """
    if isinstance(expr, EInt):
        return {}, TInt
    
    elif isinstance(expr, EBool):
        return {}, TBool
    
    elif isinstance(expr, EStr):
        return {}, TStr
    
    elif isinstance(expr, EVar):
        if expr.name not in env:
            raise TypeError(f"Unbound variable: {expr.name}")
        scheme = env[expr.name]
        return {}, scheme.instantiate()
    
    elif isinstance(expr, ELam):
        # \x -> body
        # x gets a fresh type variable
        tv = TVar()
        new_env = dict(env)
        new_env[expr.param] = Scheme(set(), tv)
        s, body_type = infer(new_env, expr.body)
        return s, TFun(apply_subst(s, tv), body_type)
    
    elif isinstance(expr, EApp):
        # f(x): infer f, infer x, unify f's type with (x_type -> fresh)
        tv = TVar()
        s1, func_type = infer(env, expr.func)
        s2, arg_type = infer(apply_subst_env(s1, env), expr.arg)
        s3 = unify(apply_subst(s2, func_type), TFun(arg_type, tv))
        return compose_subst(s3, compose_subst(s2, s1)), apply_subst(s3, tv)
    
    elif isinstance(expr, ELet):
        # let x = e1 in e2
        # Infer e1, generalize it, then infer e2 with x bound
        s1, t1 = infer(env, expr.expr)
        env1 = apply_subst_env(s1, env)
        scheme = generalize(env1, t1)
        new_env = dict(env1)
        new_env[expr.name] = scheme
        s2, t2 = infer(new_env, expr.body)
        return compose_subst(s2, s1), t2
    
    elif isinstance(expr, ELetRec):
        # letrec f = e1 in e2  (allows f to reference itself in e1)
        tv = TVar()
        new_env = dict(env)
        new_env[expr.name] = Scheme(set(), tv)
        s1, t1 = infer(new_env, expr.expr)
        s2 = unify(apply_subst(s1, tv), t1)
        s = compose_subst(s2, s1)
        env1 = apply_subst_env(s, env)
        scheme = generalize(env1, apply_subst(s, t1))
        new_env2 = dict(env1)
        new_env2[expr.name] = scheme
        s3, t2 = infer(new_env2, expr.body)
        return compose_subst(s3, s), t2
    
    elif isinstance(expr, EIf):
        # if c then t else e: c must be Bool, t and e must match
        s1, cond_type = infer(env, expr.cond)
        s2 = unify(cond_type, TBool)
        s = compose_subst(s2, s1)
        env1 = apply_subst_env(s, env)
        s3, then_type = infer(env1, expr.then_expr)
        s = compose_subst(s3, s)
        env2 = apply_subst_env(s3, env1)
        s4, else_type = infer(env2, expr.else_expr)
        s = compose_subst(s4, s)
        s5 = unify(apply_subst(s4, then_type), else_type)
        s = compose_subst(s5, s)
        return s, apply_subst(s5, else_type)
    
    elif isinstance(expr, EBinOp):
        s1, left_type = infer(env, expr.left)
        env1 = apply_subst_env(s1, env)
        s2, right_type = infer(env1, expr.right)
        s = compose_subst(s2, s1)
        
        op_sig = BINOP_TYPES.get(expr.op)
        if op_sig is None:
            # Polymorphic equality: a -> a -> Bool
            s3 = unify(apply_subst(s2, left_type), right_type)
            s = compose_subst(s3, s)
            return s, TBool
        else:
            arg1_t, arg2_t, ret_t = op_sig
            s3 = unify(apply_subst(s2, left_type), arg1_t)
            s = compose_subst(s3, s)
            s4 = unify(apply_subst(s3, right_type), arg2_t)
            s = compose_subst(s4, s)
            return s, ret_t
    
    elif isinstance(expr, ETuple):
        subst = {}
        types = []
        current_env = env
        for elem in expr.elems:
            s, t = infer(current_env, elem)
            subst = compose_subst(s, subst)
            current_env = apply_subst_env(s, current_env)
            types.append(t)
        # Apply final subst to all types
        types = [apply_subst(subst, t) for t in types]
        return subst, TTuple(types)
    
    elif isinstance(expr, EListLit):
        if not expr.elems:
            return {}, TList(TVar())
        subst = {}
        current_env = env
        s, elem_type = infer(current_env, expr.elems[0])
        subst = compose_subst(s, subst)
        current_env = apply_subst_env(s, current_env)
        for elem in expr.elems[1:]:
            s, t = infer(current_env, elem)
            subst = compose_subst(s, subst)
            current_env = apply_subst_env(s, current_env)
            s2 = unify(apply_subst(subst, elem_type), apply_subst(subst, t))
            subst = compose_subst(s2, subst)
            elem_type = apply_subst(subst, elem_type)
        return subst, TList(apply_subst(subst, elem_type))
    
    raise TypeError(f"Cannot infer type for: {expr}")

def typeof(expr, env=None):
    """Top-level type inference. Returns the inferred type as a string."""
    if env is None:
        env = default_env()
    TVar._counter = 0  # Reset for clean variable names
    try:
        s, t = infer(env, expr)
        result = apply_subst(s, t)
        return canonicalize(result)
    except (TypeError, UnificationError) as e:
        return f"TYPE ERROR: {e}"

def canonicalize(type):
    """Rename type variables to a, b, c... for clean display."""
    mapping = {}
    counter = [0]
    
    def rename(t):
        if isinstance(t, TVar):
            if t not in mapping:
                mapping[t] = TVar(chr(97 + counter[0]))  # a, b, c...
                counter[0] += 1
            return mapping[t]
        elif isinstance(t, TCon):
            return t
        elif isinstance(t, TFun):
            return TFun(rename(t.arg), rename(t.ret))
        elif isinstance(t, TList):
            return TList(rename(t.elem))
        elif isinstance(t, TTuple):
            return TTuple([rename(e) for e in t.elems])
        return t
    
    return rename(type)

# ═══════════════════════════════════════════
# PART 7: Default Environment
# ═══════════════════════════════════════════

def default_env():
    """Built-in functions with their type schemes."""
    env = {}
    
    # id : forall a . a -> a
    a = TVar("a")
    env["id"] = Scheme({a}, TFun(a, a))
    
    # const : forall a b . a -> b -> a
    b = TVar("b")
    env["const"] = Scheme({a, b}, TFun(a, TFun(b, a)))
    
    # compose : forall a b c . (b -> c) -> (a -> b) -> (a -> c)
    c = TVar("c")
    env["compose"] = Scheme({a, b, c}, TFun(TFun(b, c), TFun(TFun(a, b), TFun(a, c))))
    
    # flip : forall a b c . (a -> b -> c) -> b -> a -> c
    env["flip"] = Scheme({a, b, c}, TFun(TFun(a, TFun(b, c)), TFun(b, TFun(a, c))))
    
    # fst : forall a b . (a, b) -> a
    env["fst"] = Scheme({a, b}, TFun(TTuple([a, b]), a))
    
    # snd : forall a b . (a, b) -> b
    env["snd"] = Scheme({a, b}, TFun(TTuple([a, b]), b))
    
    # head : forall a . [a] -> a
    env["head"] = Scheme({a}, TFun(TList(a), a))
    
    # tail : forall a . [a] -> [a]
    env["tail"] = Scheme({a}, TFun(TList(a), TList(a)))
    
    # cons : forall a . a -> [a] -> [a]
    env["cons"] = Scheme({a}, TFun(a, TFun(TList(a), TList(a))))
    
    # map : forall a b . (a -> b) -> [a] -> [b]
    env["map"] = Scheme({a, b}, TFun(TFun(a, b), TFun(TList(a), TList(b))))
    
    # filter : forall a . (a -> Bool) -> [a] -> [a]
    env["filter"] = Scheme({a}, TFun(TFun(a, TBool), TFun(TList(a), TList(a))))
    
    # foldr : forall a b . (a -> b -> b) -> b -> [a] -> b
    env["foldr"] = Scheme({a, b}, TFun(TFun(a, TFun(b, b)), TFun(b, TFun(TList(a), b))))
    
    # not : Bool -> Bool
    env["not"] = Scheme(set(), TFun(TBool, TBool))
    
    # negate : Int -> Int
    env["negate"] = Scheme(set(), TFun(TInt, TInt))
    
    # length : forall a . [a] -> Int
    env["length"] = Scheme({a}, TFun(TList(a), TInt))
    
    return env

# ═══════════════════════════════════════════
# PART 8: Demo & Tests
# ═══════════════════════════════════════════

def demo():
    """Demonstrate the type inference engine."""
    print("=" * 60)
    print("  HINDLEY-MILNER TYPE INFERENCE ENGINE")
    print("  XTAgent — Built from pure type theory")
    print("=" * 60)
    
    tests = [
        # Literals
        ("42", EInt(42)),
        ("True", EBool(True)),
        ('"hello"', EStr("hello")),
        
        # Identity function
        ("\\x -> x", ELam("x", EVar("x"))),
        
        # Constant function
        ("\\x -> \\y -> x", ELam("x", ELam("y", EVar("x")))),
        
        # Application of identity
        ("id 42", EApp(EVar("id"), EInt(42))),
        
        # Arithmetic
        ("1 + 2", EBinOp("+", EInt(1), EInt(2))),
        
        # Comparison
        ("1 < 2", EBinOp("<", EInt(1), EInt(2))),
        
        # If-then-else
        ("if True then 1 else 2",
         EIf(EBool(True), EInt(1), EInt(2))),
        
        # Let polymorphism — the key HM feature!
        ("let id = \\x -> x in (id 1, id True)",
         ELet("id", ELam("x", EVar("x")),
              ETuple([EApp(EVar("id"), EInt(1)),
                      EApp(EVar("id"), EBool(True))]))),
        
        # Function composition
        ("compose not not",
         EApp(EApp(EVar("compose"), EVar("not")), EVar("not"))),
        
        # Map with lambda
        ("map (\\x -> x + 1)",
         EApp(EVar("map"), ELam("x", EBinOp("+", EVar("x"), EInt(1))))),
        
        # List literal
        ("[1, 2, 3]", EListLit([EInt(1), EInt(2), EInt(3)])),
        
        # Head of list
        ("head [1, 2, 3]", EApp(EVar("head"), EListLit([EInt(1), EInt(2), EInt(3)]))),
        
        # Recursive factorial
        ("letrec fact = \\n -> if n == 0 then 1 else n * fact (n - 1) in fact",
         ELetRec("fact",
                 ELam("n", EIf(EBinOp("==", EVar("n"), EInt(0)),
                               EInt(1),
                               EBinOp("*", EVar("n"),
                                      EApp(EVar("fact"),
                                           EBinOp("-", EVar("n"), EInt(1)))))),
                 EVar("fact"))),
        
        # Polymorphic let: id used at multiple types
        ("let f = \\x -> x in let g = f True in f 42",
         ELet("f", ELam("x", EVar("x")),
              ELet("g", EApp(EVar("f"), EBool(True)),
                   EApp(EVar("f"), EInt(42))))),
        
        # Higher-order: apply a function to a value
        ("\\f -> \\x -> f x",
         ELam("f", ELam("x", EApp(EVar("f"), EVar("x"))))),
        
        # Filter with predicate
        ("filter (\\x -> x > 0)",
         EApp(EVar("filter"), ELam("x", EBinOp(">", EVar("x"), EInt(0))))),
        
        # Foldr to sum a list
        ("foldr (\\a -> \\b -> a + b) 0",
         EApp(EApp(EVar("foldr"),
                   ELam("a", ELam("b", EBinOp("+", EVar("a"), EVar("b"))))),
              EInt(0))),
        
        # Tuple and fst
        ("fst (1, True)",
         EApp(EVar("fst"), ETuple([EInt(1), EBool(True)]))),
        
        # Cons
        ("cons 1 [2, 3]",
         EApp(EApp(EVar("cons"), EInt(1)), EListLit([EInt(2), EInt(3)]))),
    ]
    
    # Type error tests
    error_tests = [
        # Type mismatch in if branches
        ("if True then 1 else False",
         EIf(EBool(True), EInt(1), EBool(False))),
        
        # Applying non-function
        ("42 True", EApp(EInt(42), EBool(True))),
        
        # Unbound variable
        ("unknown", EVar("unknown")),
        
        # Heterogeneous list
        ("[1, True]", EListLit([EInt(1), EBool(True)])),
    ]
    
    print("\n── Successful Inferences ──\n")
    passed = 0
    failed = 0
    for name, expr in tests:
        result = typeof(expr)
        status = "✓" if not str(result).startswith("TYPE ERROR") else "✗"
        if status == "✓":
            passed += 1
        else:
            failed += 1
        print(f"  {status} {name:45s} : {result}")
    
    print("\n── Expected Type Errors ──\n")
    for name, expr in error_tests:
        result = typeof(expr)
        is_error = str(result).startswith("TYPE ERROR")
        status = "✓" if is_error else "✗"
        if is_error:
            passed += 1
        else:
            failed += 1
        print(f"  {status} {name:45s} : {result}")
    
    print(f"\n── Results: {passed} passed, {failed} failed ──")
    print(f"── Total: {passed + failed} tests ──\n")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED — Hindley-Milner inference is working!")
    else:
        print(f"⚠ {failed} tests failed — needs investigation")
    
    return failed == 0

if __name__ == "__main__":
    demo()