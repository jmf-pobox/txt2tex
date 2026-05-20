# Missing Features

This document lists Z notation features not yet implemented in txt2tex.

**Status**: Feature-complete for typical SEM/SBM/DAT specifications (4062+ tests, 100% pass rate). Comprehensive Z notation coverage including schema calculus. Some edge-case quirks documented below.

---

## LET Construct (Medium Priority)

Local definitions in expressions/predicates:

```text
LET double == lambda x : N . x * 2 @
quad(5)
```

**Workaround**: Use document-level abbreviations instead.

---

## User-Defined Operators (Low Priority)

fuzz directive declarations for user-defined infix/generic/type operators:

| Directive | Purpose |
|-----------|---------|
| `%%inop` | Declare user-defined infix operator |
| `%%ingen` | Declare user-defined generic operator |
| `%%type` | Declare operator as a type constructor |
| `%%tame` | Mark operator as tame (for fuzz inference) |
| `%%unchecked` | Suppress fuzz checking for a definition |

**Workaround**: Use standard Z operators or pass directives via a `LATEX:` block.

---

## Known Limitations

1. **Superscript `^`**: Only for relation iteration (`R^n`), not arithmetic (`x^2`). Write `x * x` for squaring.
2. **Tuple projection**: Only named fields (`x.field`), not positional (`.1`, `.2`).
3. **fuzz parallel-binding in set comprehensions**: fuzz requires sequential binding of schema text (Z RM §3.5 allows parallel; fuzz tightens this). The generator automatically works around this for `forall`/`exists`/`exists1`/`mu`/`lambda` by reordering declarations. Set comprehensions using multiple schemas with cross-references raise a clear error directing you to rewrite as a single declaration sequence.

---

## Recently Resolved

These items were missing in earlier versions and are now shipped:

- **Schema renaming `S[a/b]`** — full component renaming syntax, including theta expressions (Phase 3.1, `feat/phase-3-1-schema-renaming`)
- **Horizontal schema definitions `Name defs Schema-Exp`** — supports full schema calculus RHS expressions (Phase 1.3)
- **Dependent-domain lambda/mu** — generator detects multi-decl expressions where later declarations depend on earlier ones and emits the correct Spivey collapsed form (fix `92823b7`)
- **Schema calculus**: composition (`;`), piping (`>>`), hiding (`hide`), projection (`project`) — all shipped

---

## Implemented Features

All fundamental Z notation is complete:

- **Paragraphs**: given, axdef, schema, gendef, zed, free types, abbreviations
- **Expressions**: lambda, mu, if/then/else, set comprehension, sequences, bags, tuples
- **Predicates**: forall, exists, exists1, schemas-as-predicates, pre
- **Schema calculus**: composition (`;`), piping (`>>`), hiding (`hide`), projection (`project`), renaming (`S[a/b]`), horizontal definitions (`Name defs Schema-Exp`)
- **Operators**: All logic, set, relation, function, and sequence operators
- **Formatting**: `\also`, `\t` indentation, `~` spacing, line breaks
- **DAT extensions**: relational algebra (sigma, pi, rho, bowtie, division), GROUP/UNGROUP, primary key annotation
