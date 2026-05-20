# Multi-Declaration Z Constructs --- Q2(d) Demo

Showcases the parser and generator capabilities added to support
multi-typed Z comprehensions, quantifiers, and lambdas with conjunction
predicates over tuple projections --- the canonical multi-typed
relational-calculus form.

Until these features shipped, multi-typed queries required dropping into
raw LaTeX for any expression crossing two or more relations. The demo
also flags one known follow-up: the paren-wrap gap on top-level lambdas.

## What's in here

`q2d_demo.txt` --- one file, seven sections:

1. WYSIWYG line breaks for algebra operators (bowtie, intersect, etc.).
2. Multi-decl set comprehension with conjunction predicate over projections.
3. Multi-decl `forall` with conjunction predicate.
4. Multi-decl quantifier with no characteristic expression (Z RM §3.9
   signature default).
5. Multi-decl `mu` (definite description).
6. Multi-decl `lambda` in Spivey-canonical form
   (`\lambda s : T; c : U | P @ E`).
7. Paren-wrap follow-up --- the one known gap.

## Building

```bash
txt2tex examples/16_multi_decl_calculus/q2d_demo.txt
```

Compiles to `q2d_demo.tex` + `q2d_demo.pdf`. Fuzz type-checks sections
1--5 cleanly. Sections 6 and 7 demonstrate the paren-wrap follow-up:
the Spivey lambda form is correctly emitted but fuzz rejects it because
top-level lambdas miss the parenthesisation that single-decl `Lambda`
nodes only apply when nested.

## Background

Test pin file: `tests/test_q2d_calculus_predicate_chain.py` (13 tests).
ADR: `docs/DESIGN.md` --- "Q2(d) parser-bug fix".
