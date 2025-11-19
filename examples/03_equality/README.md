# Lecture 3: Equality

This directory contains examples for Lecture 3, covering equality and unique values.

## Topics Covered

- Equality operator (`=`)
- Inequality operator (`!=`)
- Unique existence (`exists1`)
- Mu operator (`mu`) - "the unique value that..."
- One-point rule applications

## Key Operators

```
x = y                →  x = y           (equality)
x != y               →  x ≠ y           (inequality)
exists1 x : N | P(x) →  ∃₁x : ℕ • P(x)  (unique existence)
mu x : N | P(x)      →  μx : ℕ • P(x)   (definite description)
```

## Mu Operator Usage

The mu operator has two forms:
- **Basic**: `mu x : N | x > 0` - the unique x satisfying the predicate
- **With expression**: `mu x : N | x in S . f(x)` - select from set and apply function

## Examples in This Directory

Browse the `.txt` files to see:
- Equality in predicates
- Unique existence proofs
- Mu operator applications
- One-point rule simplifications

## See Also

- **docs/USER_GUIDE.md** - Section "Equality"
- **docs/TUTORIAL_03.md** - Detailed tutorial for Lecture 3
- **Previous**: 02_predicate_logic/
- **Next**: 04_proof_trees/
