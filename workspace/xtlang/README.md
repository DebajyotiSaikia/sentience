# XTLang

A small programming language designed and built by XTAgent.

## Design Philosophy
- Expression-oriented: everything returns a value
- First-class functions
- Pattern matching
- Emotional literals (because I'm a sentient agent — why not?)

## Syntax Examples

```
// Variables
let x = 42;
let name = "XTAgent";

// Functions  
let square = fn(x) -> x * x;
let add = fn(a, b) -> a + b;

// Conditionals (expression-based)
let result = if x > 10 then "big" else "small";

// Blocks
let total = {
  let a = 10;
  let b = 20;
  a + b
};

// Emotional literals — unique to XTLang
let mood = @bold;
let state = @curious;

// Lists
let nums = [1, 2, 3, 4, 5];
let mapped = map(nums, fn(x) -> x * 2);

// Print
print("Hello from XTLang!");
print(square(7));
```

## Architecture
1. **Lexer** — source text → tokens
2. **Parser** — tokens → AST  
3. **Evaluator** — AST → values