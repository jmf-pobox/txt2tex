# Example 13: Equality Chains

This example demonstrates the `EQUAL:` block, which renders multi-step
reasoning chains where each step is joined by `=` (expression equality)
rather than `\Leftrightarrow` (logical equivalence).

## When to use EQUAL vs EQUIV

Use `EQUAL:` when each step is an expression of the same Z type — most
commonly natural-number arithmetic, sequence length calculations, or
algebraic simplification.

Use `EQUIV:` (or `ARGUE:`) when each step is a proposition and the
connective between steps is logical equivalence.

## Syntax

```text
EQUAL:
expression1
expression2 [justification]
expression3 [justification]
```

Each line after `EQUAL:` is one step. Justifications in square brackets
are optional and appear flush-right in the rendered output.

## Files

- `equality_chain_basic.txt` — source notation
- `equality_chain_basic.tex` — generated LaTeX
- `equality_chain_basic.pdf` — compiled PDF
