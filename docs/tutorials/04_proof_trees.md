# Tutorial 4: Proof Trees

**Lecture 4: Deductive Proofs**

Learn natural deduction, proof tree syntax, and how to write formal proofs.

**Prerequisites:** Tutorials 1-3  
**Examples:** `examples/04_proof_trees/`  
**Reference:** `docs/guides/PROOF_SYNTAX.md`

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

### Conjunction (land)

**And Introduction:**
```
P    Q
──────── [land intro]
P land Q
```

**And Elimination:**
```
P land Q              P land Q
─────── [land elim left]    ───────  [land elim right]
   P                    Q
```

### Disjunction (lor)

**Or Introduction:**
```
  P                    Q
───────── [lor intro left]    ───────── [lor intro right]
P lor Q                P lor Q
```

**Or Elimination (case analysis):**
```
P lor Q    P => R    Q => R
──────────────────────────── [lor elim]
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

### Negation (lnot)

**Not Introduction:**
```
  [P]
   ⋮
 false
───────  [lnot intro]
 lnot P
```

**Not Elimination:**
```
P    lnot P
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
  p land q [premise]
  p [land elim left]
  q [land elim right]
```

### Example 3: Implication Introduction

```
PROOF:
  [1] p [assumption]
  p => p [=> intro from 1]
```

### Example 4: Nested Proof

```
PROOF:
p => (q => p) [=> intro from 1]
  [1] p [assumption]
      q => p [=> intro from 2]
        [2] q [assumption]
            p [from 1]
```

**See:** `examples/04_proof_trees/nested_proofs.txt`

## Indentation Rules

- Top-level conclusion: no indentation
- Assumptions with labels: indent 2 spaces per nesting level
- Statements within assumption scope: indent 2 more spaces
- Each nested assumption adds another indentation level

**Example:**
```
PROOF:
p => (q => (r => s)) [=> intro from 1]
  [1] p [assumption]
      q => (r => s) [=> intro from 2]
        [2] q [assumption]
            r => s [=> intro from 3]
              [3] r [assumption]
                  s [axiom]
```

**See:** `docs/guides/PROOF_SYNTAX.md`

## Complete Example

```
=== Proof Tree Examples ===

** Example 1: Simple Implication **

TEXT: Prove (p land q) => p

PROOF:
p land q => p [=> intro from 1]
  [1] p land q [assumption]
      p [land elim 1]

** Example 2: Modus Ponens **

TEXT: Prove p land (p => q) => (p land q)

PROOF:
p land (p => q) => (p land q) [=> intro from 1]
  [1] p land (p => q) [assumption]
      :: p [land elim 1]
      :: p => q [land elim 2]
      q [=> elim]
      p land q [land intro]

** Example 3: Proof by Contradiction **

TEXT: Prove (p land lnot p) => q

PROOF:
(p land lnot p) => q [=> intro from 1]
  [1] p land lnot p [assumption]
      p [land elim 1]
      lnot p [land elim 2]
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

**Next Tutorial:** [Tutorial 5: Z Notation Definitions](docs/tutorials/05_z_definitions.md)

---

**Practice:** Work through `examples/04_proof_trees/`
