# Tutorial 2: Predicate Logic

**Lecture 2: Predicate Logic**

Extend propositional logic with quantifiers and predicates to reason about collections of objects.

**Prerequisites:** Tutorial 1 (Propositional Logic)  
**Examples:** `examples/02_predicate_logic/`, `examples/03_equality/`

---

## Introduction

Predicate logic adds:
- **Predicates:** Properties of objects (P(x), Q(x, y))
- **Quantifiers:** forall (∀) and exists (∃)
- **Domains:** Sets that variables range over

## Declarations

Variables must be declared with their types:

```
x : N          (x is a natural number)
p : Person     (p is a Person)
s : P N        (s is a set of natural numbers)
```

## Universal Quantifier (forall)

**Meaning:** Property holds for all values in the domain

**Syntax:**
```
forall x : N | x >= 0
```

**Reads as:** "For all x in N, x is greater than or equal to 0"

**LaTeX output:** ∀x : ℕ • x ≥ 0

### Multiple Variables

```
forall x, y : N | x + y = y + x
```

"For all natural numbers x and y, x + y equals y + x"

### With Constraints

```
forall x : N | x > 5 => x > 0
```

"For all x in N, if x > 5 then x > 0"

## Existential Quantifier (exists)

**Meaning:** Property holds for at least one value

**Syntax:**
```
exists x : N | x > 100
```

**Reads as:** "There exists an x in N such that x > 100"

**LaTeX output:** ∃x : ℕ • x > 100

### Unique Existence (exists1)

```
exists1 x : N | x * x = 16
```

"There exists exactly one x in N such that x² = 16"

## The Mu Operator

**Syntax:**
```
mu x : T | constraint
```

**Meaning:** The unique x in T satisfying the constraint

**Example:**
```
mu x : N | x * x = 25
```

Evaluates to 5 (the unique natural number whose square is 25).

**With expression:**
```
mu x : N | x > 5 land x < 7 . x + 1
```

Finds x = 6, then evaluates x + 1 = 7.

**See:** `examples/03_equality/mu_operator.txt`, `examples/03_equality/mu_with_expression.txt`

## One-Point Rule

Simplify quantifiers when the variable is constrained to a single value.

**Rule:**
```
forall x : T | x = a => P(x)  ≡  P(a)
exists x : T | x = a land P(x)  ≡  P(a)
```

**Example:**
```
forall x : N | x = 5 => x > 0
≡ 5 > 0
≡ true
```

**See:** `examples/03_equality/one_point_rule.txt`

## Nested Quantifiers

Quantifiers can be nested:

```
forall x : N | exists y : N | x + y = 10
```

"For every natural number x, there exists a y such that x + y = 10"

**Order matters:**
```
forall x | exists y | P(x, y)    (different from)
exists y | forall x | P(x, y)
```

## Quantifier Laws

**Distribution:**
```
forall x | P(x) land Q(x)  ≡  (forall x | P(x)) land (forall x | Q(x))
exists x | P(x) lor Q(x)   ≡  (exists x | P(x)) lor (exists x | Q(x))
```

**Negation:**
```
lnot (forall x | P(x))  ≡  exists x | lnot P(x)
lnot (exists x | P(x))  ≡  forall x | lnot P(x)
```

**Vacuous quantification:**
```
forall x : {} | P(x)  ≡  true
exists x : {} | P(x)  ≡  false
```

## Complete Example

```
=== Predicate Logic Examples ===

** Example 1: Universal Quantifier **

TEXT: All natural numbers are non-negative.

forall n : N | n >= 0

** Example 2: Existential Quantifier **

TEXT: There exists a natural number greater than 1000.

exists n : N | n > 1000

** Example 3: Nested Quantifiers **

TEXT: For every natural number, there is a larger natural number.

forall x : N | exists y : N | y > x

** Example 4: Mu Operator **

TEXT: Find the unique natural number between 5 land 7.

mu x : N | x > 5 land x < 7

TEXT: This evaluates to 6.
```

## Summary

You've learned:
- ✅ Variable declarations and types
- ✅ Universal quantifier (forall)
- ✅ Existential quantifier (exists, exists1)
- ✅ Mu operator for unique values
- ✅ One-point rule
- ✅ Nested quantifiers and quantifier laws

**Next Tutorial:** [Tutorial 3: Sets and Types](docs/tutorials/03_sets_and_types.md)

---

**Practice:** Explore `examples/02_predicate_logic/` and `examples/03_equality/`
