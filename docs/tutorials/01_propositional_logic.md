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

### Conjunction (land)

**Meaning:** Both propositions must be true

```
p land q
```

**LaTeX output:** p ∧ q

**Truth table:**

```
TRUTH TABLE:
p | q | p land q
T | T | T
T | F | F
F | T | F
F | F | F
```

**Example:** `examples/01_propositional_logic/basic_operators.txt`

### Disjunction (lor)

**Meaning:** At least one proposition must be true

```
p lor q
```

**LaTeX output:** p ∨ q

**Truth table:**

```
TRUTH TABLE:
p | q | p lor q
T | T | T
T | F | T
F | T | T
F | F | F
```

### Negation (lnot)

**Meaning:** Inverts the truth value

```
lnot p
```

**LaTeX output:** ¬p

**Truth table:**

```
TRUTH TABLE:
p | lnot p
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

**Key insight:** Implication is only false when the premise is true land conclusion is false.

### Bi-implication (<=>)

**Meaning:** "p if land only if q"

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

**Equivalent to:** (p => q) land (q => p)

## Operator Precedence

From highest to lowest binding:

1. `lnot` (negation)
2. `land` (conjunction)
3. `lor` (disjunction)
4. `=>` (implication)
5. `<=>` (bi-implication)

**Example:**

```
lnot p land q => r lor s
```

Parses as:
```
((lnot p) land q) => (r lor s)
```

**Use parentheses for clarity:**

```
(lnot p) land (q => r)
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
p | q | lnot p | p => q | (lnot p) lor q
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
<=> lnot p lor q [definition of =>]
<=> q lor lnot p [commutative]
```

### Common Equivalences

**Double negation:**
```
lnot (lnot p) <=> p
```

**De Morgan's laws:**
```
lnot (p land q) <=> lnot p lor lnot q
lnot (p lor q) <=> lnot p land lnot q
```

**Implication:**
```
p => q <=> lnot p lor q
```

**Contrapositive:**
```
p => q <=> lnot q => lnot p
```

**Commutative laws:**
```
p land q <=> q land p
p lor q <=> q lor p
```

**Associative laws:**
```
(p land q) land r <=> p land (q land r)
(p lor q) lor r <=> p lor (q lor r)
```

**Distributive laws:**
```
p land (q lor r) <=> (p land q) lor (p land r)
p lor (q land r) <=> (p lor q) land (p lor r)
```

**Idempotence:**
```
p land p <=> p
p lor p <=> p
```

**Identity:**
```
p land true <=> p
p lor false <=> p
```

**Annihilation:**
```
p land false <=> false
p lor true <=> true
```

**Example:** `examples/01_propositional_logic/complex_formulas.txt`

## Tautologies and Contradictions

**Tautology:** Always true (regardless of variable values)

```
p lor lnot p                    [law of excluded middle]
lnot (p land lnot p)             [law of non-contradiction]
p => p                        [reflexivity]
(p land (p => q)) => q         [modus ponens]
```

**Contradiction:** Always false

```
p land lnot p
false
```

**Contingency:** Sometimes true, sometimes false (depends on variables)

```
p land q
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
<=> lnot (p => q) lor r [=> definition]
<=> lnot (lnot p lor q) lor r [=> definition]
<=> (p land lnot q) lor r [De Morgan]
```

## Practice Exercises

### Exercise 1: Truth Tables

Create truth tables for:
1. `(p => q) land (q => r)`
2. `p <=> (q land r)`
3. `lnot (p lor q) => (lnot p land lnot q)`

### Exercise 2: Equivalences

Prove these equivalences:

1. `p => (q => r) <=> (p land q) => r`
2. `(p => q) land (p => lnot q) <=> lnot p`
3. `p => lnot p <=> lnot p`

### Exercise 3: Tautologies

Determine which are tautologies:

1. `p => (q => p)`
2. `(p => q) => (lnot q => lnot p)`
3. `p lor q => q lor p`

## Common Mistakes

### Mistake 1: Confusing land/lor

```
❌ Wrong interpretation: "p land q" means both, not one lor the other
✅ Correct: "p land q" requires BOTH p land q to be true
```

### Mistake 2: Implication confusion

```
❌ Wrong: p => q means "p implies q" means "q implies p"
✅ Correct: p => q is NOT the same as q => p
✅ Converse: q => p
✅ Contrapositive: lnot q => lnot p (equivalent to p => q)
```

### Mistake 3: Forgetting parentheses

```
❌ Ambiguous: lnot p land q
✅ Clear: (lnot p) land q
✅ Clear: lnot (p land q)
```

## Complete Example

Here's a complete document demonstrating propositional logic:

```
=== Propositional Logic Examples ===

TEXT: This document proves several logical equivalences.

** Example 1: Implication to Disjunction **

TEXT: We prove that p => q is equivalent to lnot p lor q.

EQUIV:
p => q
<=> lnot p lor q [definition of =>]

TEXT: Truth table verification:

TRUTH TABLE:
p | q | p => q | lnot p | lnot p lor q
T | T | T | F | T
T | F | F | F | F
F | T | T | T | T
F | F | T | T | T

TEXT: The columns for "p => q" land "lnot p lor q" are identical.

** Example 2: De Morgan's Law **

EQUIV:
lnot (p land q)
<=> lnot p lor lnot q [De Morgan's law]

TEXT: Proof by truth table:

TRUTH TABLE:
p | q | p land q | lnot (p land q) | lnot p | lnot q | lnot p lor lnot q
T | T | T | F | F | F | F
T | F | F | T | F | T | T
F | T | F | T | T | F | T
F | F | F | T | T | T | T
```

Save as `my_logic.txt` and compile:

```bash
txt2tex my_logic.txt
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
- ✅ Boolean operators (land, lor, lnot, =>, <=>)
- ✅ Truth tables and how to write them
- ✅ Logical equivalences and common laws
- ✅ Tautologies and contradictions
- ✅ EQUIV blocks for proving equivalences

**Next Tutorial:** [Tutorial 2: Predicate Logic](docs/tutorials/02_predicate_logic.md)

Learn about quantifiers, predicates, and reasoning about sets of objects.

---

**Practice:** Work through the examples in `examples/01_propositional_logic/` and try the exercises above.
