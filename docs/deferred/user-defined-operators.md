# Deferred design: user-defined operator names

**Status:** deferred. Not implemented. This document records the full
engine work needed to support Z user-defined operator names, so a
future implementer has a complete starting point.

**Tracking:** engine bug #134. Surfacing question: SEM Exercise 26
("Define the symbol `∉` using generic abbreviation"). See
[../guides/MISSING_FEATURES.md](../guides/MISSING_FEATURES.md) for
the author-side workaround.

## What Z permits

Z RM §3.4 (operator templates) and §3.9.3 (paragraphs) jointly define
the shapes a user may bind in an abbreviation (`==`), an axiomatic /
generic-axiomatic definition (`axdef` / `gendef`), or in declarations
inside those paragraphs.

Five template shapes:

| Shape | LHS form | Body | Example |
|---|---|---|---|
| Infix-relation | `_ R _` | binary predicate | `_ ⊑ _ : X ↔ X` |
| Infix-function | `_ ⊕ _` | binary function | `_ ⊕ _ : T × T → T` |
| Infix-generic | `_ ⊕ _ [X]` | binary, parameterised in `X` | `_ ⊕ _ [X] : seq X × seq X → seq X` |
| Prefix-relation / -function | `R _` or `f _` | unary | `pre _ : Op → Pred` |
| Postfix-function | `_ †` | unary | `_ * : Rel → Rel` (Kleene star) |

Mixfix (3+ holes) is **not** permitted by Z RM and is **not** accepted
by fuzz. Authors who want a 3-place idiom define a single
multi-argument function and apply it conventionally.

Three binding sites:

- **Abbreviation** `LHS == E` (Z RM §3.9.3) — closed-form definition.
- **Axiomatic definition** `axdef` / `gendef` (Z RM §3.9.2) — declare
  the operator at a stated type and constrain it with a predicate.
- **Free-type constructors are excluded.** Z RM grammar restricts
  free-type branches to plain identifiers; operator templates are not
  admissible there. No engine work needed.

## How fuzz handles it

fuzz manual §"User-defined operators". The rule is **announce before
define**: a directive line declares the operator class (and priority,
for functions) *before* the paragraph that defines it. Without the
directive, fuzz's parser cannot lex the operator-template LHS.

| Directive | Class | Priority |
|---|---|---|
| `%%inrel \sym` | infix-relation | — |
| `%%inop \sym n` | infix-function | 1–6 (higher = tighter) |
| `%%inrelfun \sym n` | infix that is both relation and function | 1–6 |
| `%%prerel \sym` | prefix-relation | — |
| `%%postop \sym` | postfix-function | — |
| `%%pregen \sym` | prefix-generic | — |
| `%%ingen \sym` | infix-generic | — |
| `%%type \sym1 \sym2 …` | reclassify existing global definitions as type abbreviations | — |
| `%%tame \sym …` | mark existing generic functions as tame | — |
| `%%unchecked` | suppress type-checking for the next environment | — |

Stock fuzz operators (`\in`, `\notin`, `\subseteq`, `\cup`, `\cat`,
`\mapsto`, `\oplus`, …) are **predeclared**. Redeclaring one with
`%%inop` / `%%inrel` is rejected as a duplicate-declaration error.
The only legitimate use of the stock-symbol surface in user code is
either (a) using it directly without redeclaration, or (b) showing
its *definition* pedagogically inside a `%%unchecked` paragraph (this
is precisely what SEM ex26 asks for).

Associativity is not user-declarable. Infix-functions left-associate;
infix-relations chain (`a R b R c` reads `a R b ∧ b R c`).

## Engine surface needed

### Lexer

1. **Operator-template tokens.** Recognise the three template shapes
   on the LHS of `==` and in declarations: `_ op _`, `op _`, `_ op`.
   They must lex as a single template-name token, distinct from
   ordinary identifier juxtaposition.
2. **ASCII shorthand map for stock Z glyphs as operator-template
   names.** `_notin_`, `_cat_`, `_comp_`, `_oplus_`, `_dres_`,
   `_mapsto_`, … Each maps to the corresponding LaTeX command. The
   `op` slot is filled by an existing keyword from the engine's
   operator vocabulary.
3. **Author-minted glyphs** (for course material that introduces
   genuinely fresh symbols like `⊑` for refinement). One option is a
   binding directive in the .txt header that ties an ASCII handle to
   a LaTeX command: e.g. `OP: subrefn = \sqsubseteq inrel` declares
   `_subrefn_` as an infix-relation rendering `\sqsubseteq`. Defer
   until the stock-name map is shipped.
4. **fuzz directive lines.** Lex `%%inop`, `%%inrel`, `%%prerel`,
   `%%postop`, `%%pregen`, `%%ingen`, `%%type`, `%%tame`,
   `%%unchecked` as engine-recognised directive tokens (the engine
   may need to inspect them; it does not pass them through blindly,
   because the engine itself will emit them per the
   announce-before-define rule).

### Parser

1. Accept the three template shapes as the LHS of `==` and as the LHS
   of a declaration inside `axdef` / `gendef`.
2. Reject operator templates in free-type constructor branches with a
   clear error citing Z RM §3.9.4.
3. **Operator table.** Maintain a mutable state of declared operators:
   `(name, fixity, arity, glyph, precedence)`. Look up at expression
   parse time so subsequent uses (`x ⊕ s`) resolve correctly.
4. **Disambiguation.** `x ⊕ s` must parse as an operator application
   when `⊕` is in the table, and as juxtaposition / identifier when
   it is not.
5. **Stock-redefinition check.** A definition of a stock fuzz
   operator (e.g. `_ notin _ [X] == …`) must either be wrapped in
   `%%unchecked` automatically by the engine, or rejected with a
   clear error and a workaround pointer. The first option matches the
   pedagogical use case; the second matches fuzz's own behaviour.

### AST

- New `OperatorTemplate(name, fixity, arity, glyph, line)` node.
- Extend `Abbreviation`, `AxdefDecl`, `GendefDecl` to accept
  `OperatorTemplate` as the bound name on the LHS.

### Generator

1. **Directive emission ordering.** Emit the announcing `%%`
   directive line **immediately before** the paragraph that defines
   the operator. fuzz reads top-to-bottom; without the directive
   first, the lexer cannot parse the LHS.
2. **LHS rendering.** Emit `\_ \notin \_ [X] == …` for abbreviations
   and `\_ \notin \_ : X \rel \power X` inside axdef declarations.
   Underscore literals (`\_`) flank the operator glyph.
3. **`%%unchecked` wrapping** around any paragraph that *defines* a
   stock fuzz operator. The PDF renders the definition cleanly while
   fuzz skips type-checking that one paragraph only.

### Documentation

- USER_GUIDE.md: new section "User-Defined Operator Names" covering
  the five template shapes, the three binding sites, the ASCII
  shorthand for stock glyphs, and (when shipped) the directive for
  author-minted glyphs.
- FUZZ_VS_STD_LATEX.md: announce-before-define rule, the
  redefinition-of-stock-symbols ban, and the `%%unchecked` workaround
  for pedagogical exercises.
- MISSING_FEATURES.md: move "User-Defined Operators" out of the
  missing list once shipped.
- CHANGELOG.md: `[Unreleased] / Added` entry.

### Tests

- Per template shape × per binding site: 5 × 2 = 10 minimum core cases.
- Operator-table behaviour: defined operator parses correctly in
  subsequent expressions; chained relations (`a R b R c`).
- Directive emission ordering: `%%inrel \sqsubseteq` precedes the
  `\begin{gendef}` it announces.
- Stock-operator pedagogical definition wraps in `%%unchecked`,
  fuzz-clean.
- Round-trip: a small custom-refinement-relation example feeds clean
  through fuzz end-to-end.

## Common patterns in real Z corpora

Ranked by jms by frequency of use in Oxford-style SE / SEM / SBM /
DAT material:

1. **Custom binary relation between two sorts** — `_~_` (equivalence),
   `_<<_` (precedes), `_~>_` (reduces-to). Infix-relation, no
   priority. Refinement, proof-rule, semantics chapters.
2. **Custom infix-function on a carrier set** — `_*_` on a monoid,
   `_+_` on an algebra, `_;_` for sequential composition of programs.
   Infix-function with priority. Algebra-of-programs and refinement
   laws.
3. **Generic infix-function** — `_⊕_ [X]`. Toolkit extensions.
4. **Custom prefix operator** — `pre _`, `wp _ _`. Weakest-precondition
   courses.
5. **Custom postfix operator** — `_ *` (Kleene), `_ !` (factorial).
   Occasional.

Must-have set for a useful first cut: infix-relation, infix-function,
infix-generic, prefix-relation.

Nice-to-have: postfix-function, `%%type`, `%%tame`.

Safe to defer: `%%unchecked` author-side (already available via the
`LATEX:` block escape; the engine should *emit* it but does not need
to expose it for authors to write directly).

## Why this is deferred

One course exercise across SEM + SBM (SEM ex26) exercises the feature
in its full form, and that exercise is a pedagogical demonstration —
the author is teaching the *technique* of operator definition, not
introducing an operator the rest of the document then relies on. The
author-side workaround in MISSING_FEATURES.md is acceptable for that
case.

DAT (21 rows pending) and any later refinement-chapter coursework
will exercise the feature in earnest. When that material lands and
multiple rows depend on real user-defined operators, the priority
shifts from low to load-bearing and this design becomes
implementation-ready.

## References

- Z RM §3.4 (operator templates), §3.9.2 (axdef / gendef), §3.9.3
  (abbreviations), §3.9.4 (free types).
- fuzz manual §"User-defined operators". Source:
  `doc/fuzzman.tex` at `github.com/Spivoxity/fuzz`. Grammar at
  `Def-Lhs ::= …`.
- *Understanding Z* (Spivey 1988) Chapter 3 (mathematical toolkit).
- jms consultation 2026-05-22 (logged in conversation transcript).
