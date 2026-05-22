# Missing Features

This document lists Z notation features not yet implemented in txt2tex.

**Status**: Feature-complete for typical Z and relational-database specifications (4062+ tests, 100% pass rate). Comprehensive Z notation coverage including schema calculus. Some edge-case quirks documented below.

---

## LET Construct (Medium Priority)

Local definitions in expressions/predicates:

```text
LET double == lambda x : N . x * 2 @
quad(5)
```

**Workaround**: Use document-level abbreviations instead.

---

## User-Defined Operator Names

The engine does not yet accept underscored operator templates (`_⊕_`,
`_R_`, `op _`, `_ †`) as the LHS of an abbreviation or declaration.
Concretely, none of these compile today:

```text
_notin_ [X] == { x : X; s : P X | lnot (x elem s) . (x, s) }   # rejected
_subrefn_ : (X cross X)                                         # rejected
pre_ : Op -> Pred                                               # rejected
```

After such a definition (in real Z) the document could use the new
operator natively (`x notin s`, `Op1 subrefn Op2`). That is what
the surrounding declaration syntax cannot express in txt2tex right now.
Tracking: engine bug #134. See
[docs/deferred/user-defined-operators.md](../deferred/user-defined-operators.md)
for the full engine design needed to ship the feature.

**Workaround — what to do as an author:**

The right workaround depends on what the exercise is asking for:

1. **You want to *use* an operator that already exists in fuzz's
   toolkit** (`notin`, `subseteq`, `cat`, `oplus`, `dres`, `nrres`,
   `mapsto`, …). Just write it. txt2tex already maps the keyword to
   the right LaTeX command. No directive needed; fuzz already knows
   the symbol.

2. **You want to *teach* how a stock operator is defined** (the SEM
   ex26 case — "Define `∉` using generic abbreviation"). Use a regular
   identifier as the LHS name and add a TEXT note explaining the
   substitution:

   ```text
   TEXT: A generic abbreviation defines /elem (the not-in operator)
   as the set of (x, s) pairs for which x is not a member of s.

   [X] NotIn == { x : X; s : P X | lnot (x elem s) . (x, s) }
   ```

   The set on the RHS is the right mathematical object; the LHS uses
   a parser-acceptable identifier (`NotIn`); the TEXT prose tells the
   reader (and the grader) the intended operator name. The document
   demonstrates the *technique* of generic abbreviation even though
   the surface notation `x NotIn s` is not available.

3. **You want to introduce a genuinely new operator that subsequent
   paragraphs use** (e.g. `_⊑_` for refinement, used throughout a
   refinement chapter). The full surface form is not available; the
   workarounds are:

   - Define a named relation and use prefix notation everywhere:
     `refines : Op cross Op` and write `(Op1, Op2) elem refines`
     instead of `Op1 refines Op2`.
   - Define a named function and use application notation:
     `refines : Op cross Op -> Pred` and write `refines(Op1, Op2)`.

   Neither matches Spivey's surface form, but both are
   parser-acceptable and mathematically equivalent.

4. **Last resort: drop into raw LaTeX with a `LATEX:` block.** The
   engine passes the body verbatim to fuzz; you can write the literal
   `\_ \notin \_ [X] == …` form including any `%%` directive
   announcement you need. This bypasses every txt2tex check; reserve
   it for paragraphs that genuinely cannot be expressed in the
   supported notation.

---

## Known Limitations

1. **Superscript `^`**: Only for relation iteration (`R^n`), not arithmetic (`x^2`). Write `x * x` for squaring.
2. **Tuple projection**: Only named fields (`x.field`), not positional (`.1`, `.2`).
3. **fuzz parallel-binding in set comprehensions**: fuzz requires sequential binding of schema text (Z RM §3.5 allows parallel; fuzz tightens this). The generator automatically works around this for `forall`/`exists`/`exists1`/`mu`/`lambda` by reordering declarations. Set comprehensions using multiple schemas with cross-references raise a clear error directing you to rewrite as a single declaration sequence.
4. **`id` is reserved**: maps to `\id` (the identity relation operator). It cannot be used as a schema-component name, variable, or relation name. Use `tid`, `rid`, `entityId`, etc. instead. (Other Z RM names that are similarly reserved: `dom`, `ran`, `inv`, `pre` — anything in the standard Z toolkit.)
5. **Underscore in identifiers**: txt2tex applies a heuristic when generating LaTeX (fuzz mode):
    - Single-digit suffix (`x_1`, `z_5`): emits `x_1` as a subscript decoration. Standard Z subscripted variable.
    - Single-letter suffix (`length_L`, `f_x`): emits `length\_L` — a literal underscore in the rendered name, NOT a subscript.
    - Two-digit suffix (`x_10`, `z_42`): emits `x_{10}` as a braced subscript.
    - Two-letter / mixed suffix (`FK_EE`, `state_AB`): emits `FK\_{EE}` — literal underscore plus braces.
    - Three-plus-char suffix (`cumulative_total`): goes to the multi-word identifier path; emits as `\mathit{cumulative\_total}`.
   Consequence: short letter suffixes that LOOK like subscripts (`FK_E`) are NOT subscripted; they render with a literal underscore. Use parenthesised parametrisation (`FK(E)`) or rename without an underscore if you want a clean visual.

---

## Recently Resolved

These items were missing in earlier versions and are now shipped:

- **Schema-text quantification** (`exists Delta S | P`, `exists Xi S | P`,
  `exists S | P`, `exists S' | P`, and the same for `forall` and `exists1`) —
  Z RM §3.10; implemented 2026-05-21.  The engine emits the binding literally
  and lets fuzz expand the schema invariant (jms ruling).  See
  `docs/DESIGN.md § ADR: Schema-text Quantification` for the design record.

- **Schema renaming `S[a/b]`** — full component renaming syntax, including theta expressions (Phase 3.1, `feat/phase-3-1-schema-renaming`)
- **Horizontal schema definitions `Name defs Schema-Exp`** — supports full schema calculus RHS expressions (Phase 1.3)
- **Dependent-domain lambda/mu** — generator detects multi-decl expressions where later declarations depend on earlier ones and emits the correct Spivey collapsed form (fix `92823b7`)
- **Schema calculus**: composition (`;`), piping (`>>`), hiding (`hide`), projection (`project`) — all shipped

---

## Implemented Features

All fundamental Z notation is complete:

- **Paragraphs**: given, axdef, schema, gendef, zed, free types, abbreviations
- **Expressions**: lambda, mu, if/then/else, set comprehension, sequences, bags, tuples
- **Predicates**: forall, exists, exists1, schemas-as-predicates, pre, schema-text quantification (Z RM §3.10)
- **Schema calculus**: composition (`;`), piping (`>>`), hiding (`hide`), projection (`project`), renaming (`S[a/b]`), horizontal definitions (`Name defs Schema-Exp`)
- **Operators**: All logic, set, relation, function, and sequence operators
- **Formatting**: `\also`, `\t` indentation, `~` spacing, line breaks
- **Relational database extensions**: relational algebra (sigma, pi, rho, bowtie, division), GROUP/UNGROUP, primary key annotation
