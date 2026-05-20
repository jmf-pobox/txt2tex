# Phase 1 — Baseline Regression Diff

Comparison of LaTeX output for `sem/solutions-corrected.txt` between the
production txt2tex (installed in `sem/.venv/`, equivalent to the v1.2.0
release branch) and the current dev build on
`feat/phase-3-2-schema-calculus`.

## Method

```text
sem/.venv/bin/txt2tex --tex-only baseline-prod.txt     → baseline-prod.tex
uv run --project … txt2tex --tex-only baseline-dev.txt → baseline-dev.tex
diff baseline-prod.tex baseline-dev.tex               → full.diff
```

Both invocations use the same input source. Only the txt2tex binary
differs.

- Total diff lines: 140
- Changed segments: ~25 hunks
- All changes are isolated to multi-decl quantifier emission and a few
  related indentation shifts.

## Pattern groups

Every diff falls into one of four groups, each tied to the Spivey-form
multi-decl quantifier work that landed on this branch
(`_collect_quantifier_chain` + `_generate_logical_quantifier`).

### Group A — Multi-decl `\forall` / `\exists` with independent domains

The dominant diff pattern. Prod emits nested:

```latex
\forall a : X @ \forall b : Y @ fst(a, b) = a
```

Dev emits Spivey-canonical:

```latex
\forall a : X; b : Y @ fst(a, b) = a
```

Variables in the schema text have independent domain expressions — neither
domain references a sibling variable. Both forms are well-formed Z and
both type-check in fuzz.

**Verdict: MORE CORRECT.** Spivey-canonical form is what Oxford SE
students see in lectures and matches Z RM §3.10 / §3.6. The nested form
was a generator workaround and produced semantically equivalent but
non-canonical output.

Affected lines (dev): 505, 592, 598, 611–613, 651, 688–689, 712–713,
808–812, 834–835, 858–859, 882, 913, 922–923, 932–933, 966–967, 1077,
1100, 1106, 1112, 1123, 1134–1137, 1148–1151.

Count: ≈ 22 diff hunks.

### Group B — Multi-decl `\forall` with DEPENDENT domains (fuzz-breaking)

A single hunk in the file triggers a fuzz REGRESSION. Source
(`solutions-corrected.txt:315–316`):

```text
forall s : dom podcast_episodes | forall e : podcast_episodes s |
  e elem podcast_episodes(s) <=> (s, e) elem dom episode_info
```

Prod emits two nested `\forall` tokens, so `s` is bound before `e`'s
domain `podcast_episodes(s)` is evaluated:

```latex
\forall s : \dom podcast_episodes @ \forall e : podcast_episodes(s) @
  e \in podcast_episodes(s) \iff (s, e) \in \dom episode_info
```

Dev emits the Spivey form with both variables in one schema text:

```latex
\forall s : \dom podcast_episodes; e : podcast_episodes(s) @
  e \in podcast_episodes(s) \iff (s, e) \in \dom episode_info
```

Fuzz rejects the dev output:

```text
"baseline-dev.tex", line 609: Identifier s is not declared
```

Z RM §3.6 says the scope of `s` extends rightward through the schema
text, but fuzz appears to evaluate the second declaration's domain in
the outer scope (parallel-binding semantics). Whether fuzz's behaviour
matches the Z RM is a separate question; the operative fact is that the
dev output is rejected by the type-checker that the project standardises
on.

**Verdict: REGRESSION.** The chain-collapse logic in
`_collect_quantifier_chain` does not check whether subsequent
declarations' domains reference earlier variables. It blindly merges any
same-quantifier nest into one Spivey-form output, even when that loses
the sequential binding semantics fuzz requires.

The fuzz error stops type-checking at this line, so the rest of the
file is not validated. (Other Group-A changes are fuzz-clean, verified
by manual inspection of the surrounding `\nat`-typed expressions.)

Affected lines (dev): 609 (one hunk).

Count: 1 diff hunk.

### Group C — Indent-level shifts

Where the Spivey collapse reduces nesting depth, the body of the
quantifier sits at one fewer indent level. Prod typically used `\t2`
(matching the two nested `\forall` tokens); dev uses `\t1`. Visible at
lines 689, 713, 812, 835, 859, 923, 933, 967, 1135, 1149.

**Verdict: MORE CORRECT (corollary).** The reduced indent matches the
reduced syntactic nesting and reads naturally.

### Group D — Three-decl chain collapse

For three independent declarations the diff is identical in spirit to
Group A:

```latex
\forall a : A @ \forall b : B @ \forall c : C @ fstOfTriple(a, b, c) = a
↓
\forall a : A; b : B; c : C @ fstOfTriple(a, b, c) = a
```

**Verdict: MORE CORRECT.** Same justification as Group A. fuzz-clean.

Affected lines (dev): 1100, 1106, 1112.

Count: 3 hunks.

## Summary

| Group | Hunks | Verdict | Action |
|---|---|---|---|
| A — independent multi-decl | ≈ 22 | MORE CORRECT | none |
| B — dependent multi-decl | 1 | REGRESSION (fuzz) | Phase 2 input modification |
| C — indent shifts | (within A/D) | MORE CORRECT | none |
| D — three-decl chain | 3 | MORE CORRECT | none |

**Headline:** the Spivey conversion is an unambiguous improvement on
every quantifier site EXCEPT one — the dependent-domain case at
`solutions-corrected.txt:315–316`, which produces fuzz-rejected output.

## Phase 2 input modification target

Phase 2 will produce `solutions-corrected-v2.txt` with the dependent
quantifier rewritten so the Spivey collapse cannot bridge the
dependency. The simplest mechanical change is to parenthesise the inner
quantifier so the parser treats it as a self-contained sub-expression
rather than a same-quantifier nest:

```text
forall s : dom podcast_episodes |
  (forall e : podcast_episodes s |
   e elem podcast_episodes(s) <=> (s, e) elem dom episode_info)
```

This preserves nested-form emission, sidesteps the chain collapse, and
keeps fuzz happy. The source change is one paragraph; everything else
in the file is unchanged.

## Other observations

- No diffs in algebra/proof-tree/set-comprehension territory. The
  recently-shipped algebra WYSIWYG breaks, paren-wrap fix, and
  bullet-vs-projection disambiguation either don't apply to this input
  or apply silently (no visible delta).
- The Spivey conversion strictly reduces token count (`@ \forall`
  removed per nested level) and improves readability in the rendered
  PDF.
- No regression on indentation, schema layout, axdef structure, or any
  proof tree.

## Artifacts

- `sem/baseline-prod.tex` — prod output, fuzz-clean.
- `sem/baseline-dev.tex` — dev output, fuzz rejects at line 609.
- `sem/full.diff` — `diff prod dev` raw output.

## Next step

Phase 2: produce `sem/solutions-corrected-v2.txt` with the one source
change above; verify fuzz-clean output; produce `.tex` and `.pdf`;
write `report-phase2.md`.
