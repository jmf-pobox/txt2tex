# Tutorial 1: Propositional Logic

**Lecture 1: Propositional Logic**

Learn the fundamentals of propositional logic: boolean operators, truth tables, logical equivalences, and tautologies.

**Prerequisites:** Tutorial 0 (Getting Started)

**Examples Directory:** `examples/01_propositional_logic/`

---

## Introduction

Propositional logic deals with propositions (statements that are either true or false) and logical operators that combine them.

**Propositions:** Statements with truth values
- "2 + 2 = 4" (true)
- "The sky is green" (false)
- "x > 5" (depends on x)

**Propositional variables:** p, q, r, s (represent arbitrary propositions)

## Boolean Operators

### Conjunction (and)

**Meaning:** Both propositions must be true

```
p and q
```

**LaTeX output:** p ∧ q

**Truth table:**

```
TRUTH TABLE:
p | q | p and q
T | T | T
T | F | F
F | T | F
F | F | F
```

**Example:** `examples/01_propositional_logic/basic_operators.txt`

### Disjunction (or)

**Meaning:** At least one proposition must be true

```
p or q
```

**LaTeX output:** p ∨ q

**Truth table:**

```
TRUTH TABLE:
p | q | p or q
T | T | T
T | F | T
F | T | T
F | F | F
```

### Negation (not)

**Meaning:** Inverts the truth value

```
not p
```

**LaTeX output:** ¬p

**Truth table:**

```
TRUTH TABLE:
p | not p
T | F
F | T
```

### Implication (=>)

**Meaning:** "if p then q"

```
p => q
```

**LaTeX output:** p ⇒ q

**Truth table:**

```
TRUTH TABLE:
p | q | p => q
T | T | T
T | F | F
F | T | T
F | F | T
```

**Key insight:** Implication is only false when the premise is true and conclusion is false.

### Bi-implication (<=>)

**Meaning:** "p if and only if q"

```
p <=> q
```

**LaTeX output:** p ⇔ q

**Truth table:**

```
TRUTH TABLE:
p | q | p <=> q
T | T | T
T | F | F
F | T | F
F | F | T
```

**Equivalent to:** (p => q) and (q => p)

## Operator Precedence

From highest to lowest binding:

1. `not` (negation)
2. `and` (conjunction)
3. `or` (disjunction)
4. `=>` (implication)
5. `<=>` (bi-implication)

**Example:**

```
not p and q => r or s
```

Parses as:
```
((not p) and q) => (r or s)
```

**Use parentheses for clarity:**

```
(not p) and (q => r)
```

## Truth Tables in txt2tex

### Basic Format

```
TRUTH TABLE:
p | q | p => q
T | T | T
T | F | F
F | T | T
F | F | T
```

### Complex Expressions

```
TRUTH TABLE:
p | q | not p | p => q | (not p) or q
T | T | F | T | T
T | F | F | F | F
F | T | T | T | T
F | F | T | T | T
```

**Example:** `examples/01_propositional_logic/truth_tables.txt`

## Logical Equivalences

Two formulas are logically equivalent if they have the same truth value for all interpretations.

### Equivalence Notation

Use `EQUIV:` blocks to show step-by-step equivalences:

```
EQUIV:
p => q
<=> not p or q [definition of =>]
<=> q or not p [commutative]
```

### Common Equivalences

**Double negation:**
```
not (not p) <=> p
```

**De Morgan's laws:**
```
not (p and q) <=> not p or not q
not (p or q) <=> not p and not q
```

**Implication:**
```
p => q <=> not p or q
```

**Contrapositive:**
```
p => q <=> not q => not p
```

**Commutative laws:**
```
p and q <=> q and p
p or q <=> q or p
```

**Associative laws:**
```
(p and q) and r <=> p and (q and r)
(p or q) or r <=> p or (q or r)
```

**Distributive laws:**
```
p and (q or r) <=> (p and q) or (p and r)
p or (q and r) <=> (p or q) and (p or r)
```

**Idempotence:**
```
p and p <=> p
p or p <=> p
```

**Identity:**
```
p and true <=> p
p or false <=> p
```

**Annihilation:**
```
p and false <=> false
p or true <=> true
```

**Example:** `examples/01_propositional_logic/complex_formulas.txt`

## Tautologies and Contradictions

**Tautology:** Always true (regardless of variable values)

```
p or not p                    [law of excluded middle]
not (p and not p)             [law of non-contradiction]
p => p                        [reflexivity]
(p and (p => q)) => q         [modus ponens]
```

**Contradiction:** Always false

```
p and not p
false
```

**Contingency:** Sometimes true, sometimes false (depends on variables)

```
p and q
p => q
```

## Writing Proofs

### EQUIV Blocks

Show logical equivalence step-by-step:

```
** Proof: p => q is equivalent to not p or q **

EQUIV:
p => q
<=> not p or q [definition of implication]
```

Each step should reference the law or definition used.

### Justifications

Use square brackets to explain each step:

```
EQUIV:
(p => q) => r
<=> not (p => q) or r [=> definition]
<=> not (not p or q) or r [=> definition]
<=> (p and not q) or r [De Morgan]
```

## Practice Exercises

### Exercise 1: Truth Tables

Create truth tables for:
1. `(p => q) and (q => r)`
2. `p <=> (q and r)`
3. `not (p or q) => (not p and not q)`

### Exercise 2: Equivalences

Prove these equivalences:

1. `p => (q => r) <=> (p and q) => r`
2. `(p => q) and (p => not q) <=> not p`
3. `p => not p <=> not p`

### Exercise 3: Tautologies

Determine which are tautologies:

1. `p => (q => p)`
2. `(p => q) => (not q => not p)`
3. `p or q => q or p`

## Common Mistakes

### Mistake 1: Confusing and/or

```
❌ Wrong interpretation: "p and q" means both, not one or the other
✅ Correct: "p and q" requires BOTH p and q to be true
```

### Mistake 2: Implication confusion

```
❌ Wrong: p => q means "p implies q" means "q implies p"
✅ Correct: p => q is NOT the same as q => p
✅ Converse: q => p
✅ Contrapositive: not q => not p (equivalent to p => q)
```

### Mistake 3: Forgetting parentheses

```
❌ Ambiguous: not p and q
✅ Clear: (not p) and q
✅ Clear: not (p and q)
```

## Complete Example

Here's a complete document demonstrating propositional logic:

```
=== Propositional Logic Examples ===

TEXT: This document proves several logical equivalences.

** Example 1: Implication to Disjunction **

TEXT: We prove that p => q is equivalent to not p or q.

EQUIV:
p => q
<=> not p or q [definition of =>]

TEXT: Truth table verification:

TRUTH TABLE:
p | q | p => q | not p | not p or q
T | T | T | F | T
T | F | F | F | F
F | T | T | T | T
F | F | T | T | T

TEXT: The columns for "p => q" and "not p or q" are identical.

** Example 2: De Morgan's Law **

EQUIV:
not (p and q)
<=> not p or not q [De Morgan's law]

TEXT: Proof by truth table:

TRUTH TABLE:
p | q | p and q | not (p and q) | not p | not q | not p or not q
T | T | T | F | F | F | F
T | F | F | T | F | T | T
F | T | F | T | T | F | T
F | F | F | T | T | T | T
```

Save as `my_logic.txt` and compile:

```bash
hatch run convert my_logic.txt
```

## Resources

**Examples:**
- `examples/01_propositional_logic/hello_world.txt` - Simplest example
- `examples/01_propositional_logic/basic_operators.txt` - All operators
- `examples/01_propositional_logic/truth_tables.txt` - Truth table examples
- `examples/01_propositional_logic/complex_formulas.txt` - Equivalence proofs

**Reference:**
- [USER_GUIDE.md](docs/guides/USER_GUIDE.md) - Section "Propositional Logic"
- [PROOF_SYNTAX.md](docs/guides/PROOF_SYNTAX.md) - EQUIV block syntax

## Summary

You've learned:
- ✅ Boolean operators (and, or, not, =>, <=>)
- ✅ Truth tables and how to write them
- ✅ Logical equivalences and common laws
- ✅ Tautologies and contradictions
- ✅ EQUIV blocks for proving equivalences

**Next Tutorial:** [Tutorial 2: Predicate Logic](docs/tutorials/02_predicate_logic.md)

Learn about quantifiers, predicates, and reasoning about sets of objects.

---

**Practice:** Work through the examples in `examples/01_propositional_logic/` and try the exercises above.
