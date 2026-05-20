# Phase 4 — Resolution

Closes the three-phase sem regression analysis. The generator follow-up
flagged in `report-phase{1,2,3}.md` has shipped on this branch.

## What changed

Two commits on `feat/phase-3-2-schema-calculus`:

- `92823b7 fix: partial-collapse dependent-domain quantifiers, raise on set-comp dep`
- `ac9d769 docs: ADR + CHANGELOG + fuzz guide for dependent-domain fix`

The fix adds `src/txt2tex/free_vars.py` and threads a free-variable
analysis through `_collect_quantifier_chain` and `_collect_lambda_chain`.
At each chain step, if the next declaration's domain references an
already-bound variable, the collapse stops and the un-collapsed tail
recurses through the generator (Z RM §3.9 split identity:
`\forall D1; D2 @ \forall D3 @ P` when D3 depends on D1 or D2). Set
comprehensions raise `ValueError` because Z RM §3.10 has no analogous
split identity for set displays.

Full design at `.tmp/design/spivey_dependent_domain_fix.md`. Reviews at
`.tmp/design/dependent_domain_design_review_{jms,codequality}.md`. ADR
at `docs/DESIGN.md`. Fuzz behaviour documented at
`docs/guides/FUZZ_VS_STD_LATEX.md` under "Schema-Text Parallel Binding".

## What this means per phase

**Phase 1's Group B regression.** The single fuzz-breaking hunk at
`baseline-dev.tex:609` is gone. The original
`sem/solutions-corrected.txt` (no modifications) now fuzz-typechecks
cleanly. The dev build emits nested `\forall s : ... @ \forall e : ...`
when the second declaration's domain references `s`, matching prod's
output for this specific pattern while keeping the Spivey collapse for
every independent-domain site (Groups A, C, D).

**Phase 2's v2 workaround is no longer required.** The
`s elem podcasts land` noop conjunct was inserted purely to interpose a
`BinaryOp` between the outer and inner `forall` so the chain-collapse
would not fire. With the dependency check in place, the original
unmodified source produces the correct nested LaTeX without the
conjunct. The v2 source files remain in `sem/` as documentation of the
multi-stage process — not because they are still needed.

**Phase 3's v3 idiomatic refactor is partially superseded.** The set-
equality replacement (category B) is still a legitimate idiomatic
improvement over the verbose biconditional form, independent of the
fix. The multi-decl Spivey form rewrites (category A) are also still a
style win — though now strictly cosmetic since the generator handled
the nested-source input correctly already. The v3 source files remain
in `sem/` as a worked example of using Z RM canonical forms.

## Tests

17 tests in `tests/test_spivey_dependent_domain.py`. 11 formerly-xfail
flipped to pass. 6 controls remain pass. 430 watchlist tests across 9
test families stay green. Total project test count: 4062 passing.

## Verification on the original input

```text
uv run txt2tex sem/solutions-corrected.txt
→ Generated: sem/solutions-corrected.tex
→ Type checking: passed
→ Compiling: sem/solutions-corrected.pdf
→ Generated: sem/solutions-corrected.pdf
```

The `sem/solutions-corrected.tex` and `.pdf` artifacts in this directory
reflect the post-fix output, not the prod or pre-fix dev output.

## Artifacts preserved for reference

- `sem/baseline-prod.tex` — original prod output (pre-fix dev was a
  superset of this, except at the dependent-domain hunk).
- `sem/baseline-dev.tex` — pre-fix dev output (now historical; current
  dev output is at `sem/solutions-corrected.tex`).
- `sem/full.diff` — `diff baseline-prod baseline-dev` from Phase 1.
- `sem/solutions-corrected-v2.{txt,tex,pdf}` — Phase 2 workaround
  source; no longer needed but kept as documentation.
- `sem/solutions-corrected-v3.{txt,tex,pdf}` — Phase 3 idiomatic
  refactor; partially superseded but the set-equality rewrite remains
  a style improvement.

## Closing the loop

The follow-up flagged in all three earlier reports is now closed. No
remaining action items from the sem regression analysis.
