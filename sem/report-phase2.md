# Phase 2 — Input Modifications (v2)

Produces `sem/solutions-corrected-v2.txt` with the minimum source change
that makes the dev build's output fuzz-clean on the same input.

## Input change

One pattern, applied at two source sites:

- `sem/solutions-corrected.txt:315-316` — inside the main `axdef` where
  clause.
- `sem/solutions-corrected.txt:332-333` — the part-8(c) restatement of
  the same predicate for documentation.

Original (both sites):

```text
forall s : dom podcast_episodes | forall e : podcast_episodes s |
  e elem podcast_episodes(s) <=> (s, e) elem dom episode_info
```

v2 (both sites):

```text
forall s : dom podcast_episodes | s elem podcasts land
  (forall e : podcast_episodes s |
   e elem podcast_episodes(s) <=> (s, e) elem dom episode_info)
```

## Why this works

The dev build's `_collect_quantifier_chain` collapses a chain of
same-quantifier `Quantifier` AST nodes (parent's `body` is itself a
`Quantifier` with the same `quantifier` attribute) into one
Spivey-canonical schema text. The chain-collapse logic walks `body`
unconditionally and does not check whether subsequent declarations'
domains reference earlier-declared variables.

The v2 modification interposes a `BinaryOp(land, ...)` between the outer
and inner `forall`. The outer's `body` is now a conjunction, not a
`Quantifier`, so the chain-collapse never fires. The generator emits the
explicit nested form, which fuzz accepts because the outer `s` is bound
before the inner declaration's domain `podcast_episodes(s)` is evaluated.

The left conjunct `s elem podcasts` is vacuously true given the outer
binding `s : dom podcast_episodes` and the axdef invariant
`podcasts = dom (podcast_episodes)` declared one predicate earlier. It
adds no semantic content; its only job is to break the AST chain.

## Output diff (v2 vs original-on-dev)

Two hunks affected. Both replace the broken Spivey collapse with a
nested form plus the noop conjunct:

```latex
< \forall s : \dom podcast_episodes; e : podcast_episodes(s) @
<   e \in podcast_episodes(s) \iff (s, e) \in \dom episode_info
---
> \forall s : \dom podcast_episodes @ s \in podcasts \land
>   (\forall e : podcast_episodes(s) @
>    e \in podcast_episodes(s) \iff (s, e) \in \dom episode_info)
```

## Verification

```text
uv run txt2tex sem/solutions-corrected-v2.txt
→ Generated: solutions-corrected-v2.tex
→ Type checking: passed
→ Compiling: solutions-corrected-v2.pdf
→ Generated: solutions-corrected-v2.pdf
```

Fuzz now passes for the entire document. Where prod and the original
dev output had ≈ 25 hunks of difference, v2's output preserves all the
"more correct" Spivey-form changes from Phase 1 (Groups A and D) AND
adds the explicit nested form for the one dependent-domain case
(Phase 1 Group B).

Overflow warning emitted (long line at the new conjunction site) but
non-blocking.

## What stays as-is from Phase 1

All MORE CORRECT changes from Phase 1 (Groups A, C, D) remain in v2
because v2 reuses the dev build. The reader gets:

- Multi-decl `\forall a : X; b : Y @ …` Spivey form everywhere the
  domains are independent.
- Three-decl `\forall a : A; b : B; c : C @ …` similarly.
- One isolated nested `\forall s : … @ \forall e : … @` only at the
  podcast-episodes site, with the noop conjunct preceding it.

## Limitation noted

The `s elem podcasts` conjunct is cosmetic noise. The semantically
clean fix would be a small generator change in
`_collect_quantifier_chain` to detect when the next declaration's
domain references an earlier-bound variable and refuse to collapse in
that case. That work is out of scope for Phase 2 but worth a follow-up
ticket. Phase 3 will address the same predicate by rewriting it in a
more idiomatic Z form that sidesteps the dependent-domain entirely.

## Artifacts

- `sem/solutions-corrected-v2.txt` — modified source.
- `sem/solutions-corrected-v2.tex` — fuzz-clean LaTeX.
- `sem/solutions-corrected-v2.pdf` — compiled PDF.

## Next step

Phase 3: produce `sem/solutions-corrected-v3.txt` that rewrites the
predicate using a set-containment form (idiomatic Z) and also takes
advantage of other features shipped in this branch (algebra WYSIWYG
breaks, multi-decl comprehension with conjunction predicates, etc.)
wherever applicable.
