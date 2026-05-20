# Phase 3 — Idiomatic Refactor (v3)

Produces `sem/solutions-corrected-v3.txt`, rewriting workarounds in the
original source to use the more idiomatic forms enabled by the work that
landed on `feat/phase-3-2-schema-calculus`.

## Refactor categories

### A. Multi-decl Spivey form in source (cosmetic)

The original source nested same-quantifier `forall`s explicitly. The dev
generator already collapses nested chains into Spivey form, so the
output of v2 and v3 is identical at these sites. v3 lifts the
nesting into the source where it belongs: a Z RM §3.6 schema text with
`;`-separated declarations.

| Before | After |
|---|---|
| `forall a : X \| forall b : Y \| P` | `forall a : X; b : Y \| P` |
| `forall a : A \| forall b : B \| forall c : C \| P` | `forall a : A; b : B; c : C \| P` |
| `forall s : ShowId \| forall e : EpisodeId \| ...` | `forall s : ShowId; e : EpisodeId \| ...` |
| `forall e : ListElement \| forall l : List \| ...` | `forall e : ListElement; l : List \| ...` |

Eleven source sites converted (gendef fst/snd, axdef podcast predicates,
axdef my_shows predicates, the three triple-projection gendefs, the
list induction step, and the part-(b)–(d) restatements in Question 9
and 8(e)). No LaTeX output delta at any of these sites.

### B. Set-equality replacement for the dependent-domain workaround

Original (and v2 with the chain-breaking `land` conjunct):

```text
forall s : dom podcast_episodes | forall e : podcast_episodes s |
  e elem podcast_episodes(s) <=> (s, e) elem dom episode_info
```

The user comment at part-8(c) said the biconditional was deliberate.
But the LHS `e elem podcast_episodes(s)` is trivially true under the
inner quantification, so the predicate reduces to "for all such (s, e),
(s, e) in dom episode_info" — a set-containment, not a true
biconditional.

The idiomatic Z form is a set equality with a tuple-typed binding,
which sidesteps the dependent-domain problem entirely because the
binding's domain `ShowId cross EpisodeId` is a static type:

```text
dom episode_info = { p : ShowId cross EpisodeId |
  fst p elem dom podcast_episodes land
  snd p elem podcast_episodes(fst p) }
```

Applied at both source sites (axdef predicate, part-8(c) restatement).
Updated explanatory `TEXT:` for part-8(c) to match.

Note: an even-cleaner Spivey form
`{ s : dom podcast_episodes; e : podcast_episodes s @ (s, e) }` is what
the Z RM literally permits, but fuzz's parallel-binding semantics
rejects the dependent-domain in a set comprehension's schema text
exactly as it does in a forall's. The tuple-binding form is fuzz-safe
and equivalent.

### C. Inline-vs-array layout improvement (corollary)

A bonus from category A: when a multi-decl Spivey schema text shortens
the formula enough to fit on one line, the generator no longer wraps
it in `\begin{array}{l}…\end{array}`. Visible at part-9(d):

```latex
\noindent\hspace*{\parindent}(d) $\forall s : ShowId; e : EpisodeId @ ...$
```

Replaces the longer multi-line version v2 produced from the nested
source. Subtle but improves part-label rendering.

## Diff summary (v3.tex vs v2.tex)

42 lines diff. Hunks:

| Hunk | Site | Change | Verdict |
|---|---|---|---|
| 1 | dev-line 609 | axdef predicate → set equality | category B |
| 2 | dev-line 646 | part-8(c) explanation form simplified | category B |
| 3 | dev-line 664 | updated TEXT for the set equality | category B |
| 4 | dev-line 879 | part-9(d) wraps inline instead of array | category C |

All other source changes (category A) are output-equivalent.

## Verification

```
uv run txt2tex sem/solutions-corrected-v3.txt
→ Generated: solutions-corrected-v3.tex
→ Type checking: passed
→ Compiling: solutions-corrected-v3.pdf
→ Generated: solutions-corrected-v3.pdf
```

Fuzz-clean. PDF compiled.

## What v3 demonstrates about this branch's features

- **Multi-decl Spivey form** (forall/exists/exists1/mu): every nested-
  same-quantifier chain in the source can be flattened to one schema
  text. Reader/writer see the same canonical form.
- **Bullet vs projection disambiguation**: the set comprehension
  `{ p : ShowId cross EpisodeId | … }` uses `fst p` and `snd p` as field
  projections within a body context; the parser correctly treats these
  as projections (not bullet separators) because the declared-variable
  set check is per-quantifier.
- **Q2(d) parser fix**: indirectly — the multi-decl Spivey form in
  source is the same parser path that previously failed for multi-typed
  comprehensions with conjunction predicates. v3 confirms the path is
  robust.

## What's NOT exercised by this file

- Algebra WYSIWYG line breaks — SEM has no relational algebra.
- pk / GROUP / UNGROUP / Z bindings — DAT-specific.
- Lambda paren wrap — the only lambdas in this file are inside
  expression contexts that already triggered wrapping in prod.

## Artifacts

- `sem/solutions-corrected-v3.txt` — refactored source.
- `sem/solutions-corrected-v3.tex` — fuzz-clean LaTeX.
- `sem/solutions-corrected-v3.pdf` — compiled PDF.

## Closing notes

- Eleven multi-decl source rewrites for category A; one set-equality
  rewrite for category B (applied at two sites).
- One generator improvement remains documented as a follow-up
  (`_collect_quantifier_chain` should detect domain dependency and skip
  the Spivey collapse in those cases — this would let the user write
  the natural nested form without needing the v2 noop conjunct).
