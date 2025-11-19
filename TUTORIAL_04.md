# Tutorial 4: Proof Trees

**Lecture 4: Deductive Proofs**

Learn natural deduction, proof tree syntax, and how to write formal proofs.

**Prerequisites:** Tutorials 1-3  
**Examples:** `examples/04_proof_trees/`  
**Reference:** `docs/PROOF_SYNTAX.md`

---

## Introduction to Proof Trees

**Proof tree:** Structured argument showing how conclusions follow from premises using inference rules.

**txt2tex syntax:**
```
PROOF:
  premise [justification]
  conclusion [rule applied]
```

## Basic Proof Structure

```
PROOF:
  p [premise]
  p => q [premise]
  q [=> elim]
```

This proves q from premises p and p => q using modus ponens (=> elim).

## Inference Rules

### Conjunction (and)

**And Introduction:**
```
P    Q
──────── [and intro]
P and Q
```

**And Elimination:**
```
P and Q              P and Q
─────── [and elim left]    ───────  [and elim right]
   P                    Q
```

### Disjunction (or)

**Or Introduction:**
```
  P                    Q
───────── [or intro left]    ───────── [or intro right]
P or Q                P or Q
```

**Or Elimination (case analysis):**
```
P or Q    P => R    Q => R
──────────────────────────── [or elim]
           R
```

### Implication (=>)

**Implication Introduction:**
```
  [P]
   ⋮
   Q
─────── [=> intro]
P => Q
```

**Implication Elimination (modus ponens):**
```
P    P => Q
─────────── [=> elim]
     Q
```

### Negation (not)

**Not Introduction:**
```
  [P]
   ⋮
 false
───────  [not intro]
 not P
```

**Not Elimination:**
```
P    not P
────────── [contradiction]
  false
```

## Example Proofs

### Example 1: Modus Ponens

```
PROOF:
  p [premise]
  p => q [premise]
  q [=> elim]
```

### Example 2: And Elimination

```
PROOF:
  p and q [premise]
  p [and elim left]
  q [and elim right]
```

### Example 3: Implication Introduction

```
PROOF:
  p [assumption 1]
  p => p [=> intro from 1]
```

### Example 4: Nested Proof

```
PROOF:
  p [assumption 1]
    q [assumption 2]
    p [from 1]
    q => p [=> intro from 2]
  p => (q => p) [=> intro from 1]
```

**See:** `examples/04_proof_trees/nested_proofs.txt`

## Indentation Rules

- Top-level premises: no indentation
- Nested assumption: indent 2 spaces
- Conclusions within assumption: same indentation
- Discharge: outdent to parent level

**Example:**
```
PROOF:
  p [assumption 1]
    q [assumption 2]
    r [from q]
  q => r [=> intro from 2]
  p => (q => r) [=> intro from 1]
```

**See:** `docs/PROOF_SYNTAX.md`

## Complete Example

```
=== Proof Tree Examples ===

** Example 1: Simple Implication **

TEXT: Prove (p and q) => p

PROOF:
  p and q [premise]
  p [and elim left]

** Example 2: Transitivity of Implication **

TEXT: Prove (p => q) and (q => r) => (p => r)

PROOF:
  p => q [premise]
  q => r [premise]
  p [assumption 1]
  q [=> elim with p => q]
  r [=> elim with q => r]
  p => r [=> intro from 1]

** Example 3: Proof by Contradiction **

TEXT: Prove (p and not p) => q

PROOF:
  p and not p [premise]
  p [and elim left]
  not p [and elim right]
  false [contradiction]
  q [false elim]
```

**See:** `examples/04_proof_trees/simple_proofs.txt`, `examples/04_proof_trees/contradiction.txt`

## Summary

You've learned:
- ✅ Proof tree structure (PROOF: blocks)
- ✅ Introduction and elimination rules
- ✅ Nested proofs and assumptions
- ✅ Proper indentation
- ✅ Proof by contradiction

**Next Tutorial:** [Tutorial 5: Z Notation Definitions](TUTORIAL_05.md)

---

**Practice:** Work through `examples/04_proof_trees/`
