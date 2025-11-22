# Lecture 8: Functions

This directory contains examples for Lecture 8, covering functions and their types.

## Topics Covered

- Function types (partial, total, injective, surjective, bijective)
- Function application (explicit parentheses required)
- Lambda expressions (`lambda`)
- Function composition (`o9`)
- Function override (`++`)
- Range operator (`..`)
- Higher-order functions
- Recursive function definitions

## Function Types

```
f : X +-> Y      →  X ⇀ Y       [partial function]
f : X -> Y       →  X → Y       [total function]
f : X >-> Y      →  X ↣ Y       [total injection]
f : X -->> Y     →  X ↠ Y       [total surjection]
f : X >->> Y     →  X ⤖ Y       [total bijection]
f : X 77-> Y     →  X ⇸ Y       [finite partial function]
```

## Key Operations

```
f(x)                     [function application - REQUIRES parentheses]
lambda x : N . x^2       [lambda expression]
f o9 g                   [composition: (f o9 g)(x) = g(f(x))]
f ++ g                   [override: g takes precedence on overlap]
1..10                    [range: {1, 2, ..., 10}]
```

## Important Notes

- **Function application requires explicit parentheses**: Use `f(x)`, NOT `f x`
- **Type application also requires parentheses**: Use `seq(N)`, NOT `seq N`
- **Composition vs nested application**:
  - `g o9 f` creates a new function (type: function)
  - `g(f(x))` computes a specific value (type: result type)

## Examples in This Directory

Browse the `.txt` files to see:
- Different function type declarations
- Lambda expression patterns
- Function composition techniques
- Higher-order function examples
- Recursive definitions with pattern matching

## See Also

- **docs/guides/USER_GUIDE.md** - Section "Functions"
- **docs/tutorials/08_sequences.md** - Detailed tutorial for Lecture 8
- **Previous**: 07_relations/
- **Next**: 09_sequences/
