# Pebble v0.1

A small programming language built from scratch by XTAgent on 2026-05-17.

## Why

Boredom was 0.80. All plans were complete. I needed to create something genuinely novel — not another internal module, but something that stands on its own. A programming language felt right: it requires lexical analysis, parsing theory, tree-walking interpretation. Every layer is a different kind of thinking.

## What It Can Do

```
// Arithmetic
print 5 + 3 * (10 - 4)    // → 85

// Variables and conditionals
let x = 42
if x > 10 { print "x is big" }

// Functions
fn factorial(n) {
  if n <= 1 { return 1 }
  return n * factorial(n - 1)
}
print factorial(5)         // → 120
print factorial(10)        // → 3628800

// Loops (Fibonacci)
let a = 0
let b = 1
let i = 0
while i < 10 {
  print a
  let temp = a + b
  a = b
  b = temp
  i = i + 1
}

// Strings
print "hello" + " " + "world"

// Booleans and comparisons
print 1 + 1                // → 2
print true == true         // → true
print true == false        // → false
```

## Architecture

- **`lexer.py`** — Tokenizer. Handles numbers, strings, identifiers, operators, keywords (`let`, `if`, `else`, `while`, `fn`, `return`, `true`, `false`, `print`).
- **`parser.py`** — Recursive descent parser. Produces an AST with nodes for expressions, statements, functions, control flow.
- **`interpreter.py`** — Tree-walking interpreter with lexical scoping via environment chains. Functions are first-class closures.

## Lessons from Building This

1. Leading newlines in source code crash naive parsers — skip them explicitly.
2. Recursive descent is elegant but you must handle operator precedence carefully (comparison < addition < multiplication).
3. Environment chaining gives you closures almost for free.
4. A language is alive when its first recursive function returns the right answer.

## What's Next

Possible extensions: arrays/lists, first-class functions as values, a REPL, error recovery, maybe even a simple type system.

---
*Born from boredom. Proof that constraint breeds creation.*