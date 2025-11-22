# Lecture 2: Predicate Logic

This directory contains examples for Lecture 2, covering predicate logic and quantifiers.

## Topics Covered

- Universal quantification (`forall`)
- Existential quantification (`exists`)
- Unique existential quantification (`exists1`)
- Multi-variable quantifiers
- Nested quantifiers
- Bullet separator (`.`) for constraint/body separation
- Variable declarations and binding

## Key Quantifiers

```
forall x : N | x > 0              →  ∀x : ℕ • x > 0
exists y : Z | y < 0              →  ∃y : ℤ • y < 0
exists1 x : N | x * x = 4         →  ∃₁x : ℕ • x × x = 4
forall x : N | x > 0 . x < 10     →  ∀x : ℕ ∣ x > 0 • x < 10
```

## Important Notes

- Nested quantifiers in `and`/`or` expressions must be parenthesized
- The bullet separator (`.`) can separate constraints from body
- Comma-separated variables share the same domain

## Examples in This Directory

Browse the `.txt` files to see:
- Basic quantifier usage
- Multi-variable declarations
- Nested quantification patterns
- Bullet separator demonstrations

## See Also

- **docs/guides/USER_GUIDE.md** - Section "Predicate Logic"
- **docs/tutorials/02_predicate_logic.md** - Detailed tutorial for Lecture 2
- **Previous**: 01_propositional_logic/
- **Next**: 03_equality/
