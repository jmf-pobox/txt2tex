# Multi-Declaration Z Constructs --- Demo

Showcases the parser and generator capabilities added to support
multi-typed Z comprehensions, quantifiers, and lambdas with conjunction
predicates over tuple projections --- the canonical multi-typed
relational-calculus form.

Until these features shipped, multi-typed queries required dropping into
raw LaTeX for any expression crossing two or more relations. The demo
also shows the fix for top-level lambdas, which now get the parentheses
fuzz requires.

Uses a tournament scheduling domain (Player, Tournament, Match).

## What's in here

`multi_decl_demo.txt` --- one file, seven sections:

1. WYSIWYG line breaks for algebra operators (join, intersect, etc.).
2. Multi-decl set comprehension with conjunction predicate over projections.
3. Multi-decl `forall` with conjunction predicate.
4. Multi-decl quantifier with no characteristic expression (Z RM §3.9
   signature default).
5. Multi-decl `mu` (definite description).
6. Multi-decl `lambda` in Spivey-canonical form
   (`\lambda s : T; c : U | P @ E`).
7. Lambda parenthesisation --- every lambda is wrapped in parentheses,
   at any position, as fuzz requires.

## Building

```bash
txt2tex examples/16_multi_decl_calculus/multi_decl_demo.txt
```

Compiles to `multi_decl_demo.tex` + `multi_decl_demo.pdf`. Fuzz type-checks
every section. Sections 6 and 7 emit `(\lambda ... @ ...)` with the
parentheses fuzz requires, including for top-level lambdas.

## Background

Regression tests for these constructs live under `tests/`.
ADR: `docs/DESIGN.md` --- "multi-decl parser fix".
