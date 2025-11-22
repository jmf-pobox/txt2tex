# Lecture 4: Deductive Proofs

This directory contains examples for Lecture 4, covering natural deduction and proof trees.

## Topics Covered

- Natural deduction proof trees
- Inference rules for logical operators
- Assumption management and discharge
- Case analysis (or-elimination)
- Proof by contradiction
- Complex multi-step proofs

## Proof Tree Structure

```
PROOF:
  conclusion [rule name]
    premise1
    premise2
```

## Key Features

- **Indentation**: 2 spaces per level defines proof structure
- **Siblings**: Use `::` prefix for parallel premises
- **Assumptions**: Label with `[1]`, `[2]`, etc.
- **Discharge**: Reference with `[=> intro from 1]`
- **References**: Use `[from N]` to cite earlier lines

## Common Inference Rules

- `[and intro]`, `[and elim 1]`, `[and elim 2]`
- `[or intro 1]`, `[or intro 2]`, `[or elim]`
- `[=> intro]`, `[=> elim]`
- `[false intro]`, `[false elim]`
- `[assumption]`, `[premise]`, `[from N]`

## Examples in This Directory

Browse the `.txt` files to see:
- Simple inference proofs
- Assumption discharge
- Case analysis patterns
- Complex multi-branch proofs

## See Also

- **docs/guides/PROOF_SYNTAX.md** - Complete proof tree syntax reference
- **docs/guides/USER_GUIDE.md** - Section "Proof Trees"
- **docs/tutorials/04_proof_trees.md** - Detailed tutorial for Lecture 4
- **Previous**: 03_equality/
- **Next**: 05_sets/
