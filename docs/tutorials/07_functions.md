# Tutorial 7: Functions

**Lecture 7: Functions**

Learn function types, function application, lambda expressions, and function composition.

**Prerequisites:** Tutorial 6  
**Examples:** `examples/08_functions/`

---

## Function Types

Functions are special relations where each input maps to at most one output.

### Total Functions (->)

**f : X -> Y** - Defined for all x in X

```
square : N -> N
forall n : N | square(n) = n * n
```

### Partial Functions (+->)

**f : X +-> Y** - May not be defined for all x

```
predecessor : N +-> N
forall n : N | n > 0 . predecessor(n) = n - 1
```

### Other Function Types

- **X ⇸ Y** (77->) - Finite partial function
- **X ↣ Y** (>->) - Injection (one-to-one)
- **X ↠ Y** (->>) - Surjection (onto)
- **X ⤖ Y** (>->>) - Bijection (one-to-one and onto)

**See:** `examples/08_functions/finite_functions.txt`

## Function Application

Apply functions using parentheses:

```
square(5) = 25
add(2, 3) = 5
```

**Multi-argument functions:**
```
add : N cross N -> N
forall a, b : N | add(a, b) = a + b
```

**See:** `examples/07_relations/restrictions.txt` (function application section)

## Lambda Expressions

Anonymous function definitions:

```
lambda x : N . x * x        (square function)
lambda x, y : N . x + y     (add function)
```

**Nested lambdas:**
```
lambda x : N . lambda y : N . x + y
```

**See:** `examples/08_functions/lambda_expressions.txt`

## Function Composition

### Forward Composition (o9)

Apply f then g:

```
f o9 g = lambda x . g(f(x))
```

**Example:**
```
addOne : N -> N
double : N -> N
combined = addOne o9 double

combined(5) = double(addOne(5)) = double(6) = 12
```

### Backward Composition (o)

Traditional math notation (apply second function first):

```
f o g = lambda x . f(g(x))
```

**See:** `examples/08_functions/function_composition.txt`

## Higher-Order Functions

Functions that take or return functions:

```
gendef [X, Y]
  map : (X -> Y) cross seq X -> seq Y
where
  map(f, ⟨⟩) = ⟨⟩
  forall f : X -> Y; x : X; s : seq X |
    map(f, ⟨x⟩ ⌢ s) = ⟨f(x)⟩ ⌢ map(f, s)
end
```

**See:** `examples/08_functions/higher_order_functions.txt`

## Complete Example

```
=== Function Examples ===

given Person, Age

** Example 1: Total Function **

axdef
  getAge : Person -> Age
where
  forall p : Person | getAge(p) >= 0
end

** Example 2: Partial Function **

axdef
  manager : Person +-> Person
where
  forall p : Person | p elem dom manager => manager(p) /= p
end

** Example 3: Function Composition **

axdef
  successor : N -> N
  double : N -> N
  pipeline : N -> N
where
  forall n : N | successor(n) = n + 1
  forall n : N | double(n) = 2 * n
  pipeline = successor o9 double
end

TEXT: pipeline(5) = double(successor(5)) = double(6) = 12
```

## Summary

You've learned:
- ✅ Function types (total, partial, injection, surjection, bijection)
- ✅ Function application syntax
- ✅ Lambda expressions
- ✅ Function composition
- ✅ Higher-order functions

**Next Tutorial:** [Tutorial 8: Sequences](docs/tutorials/08_sequences.md)

---

**Practice:** Explore `examples/08_functions/`
