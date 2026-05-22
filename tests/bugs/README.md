# txt2tex Test Files: Regressions, Features, Limitations, and Active Bugs

This directory contains test files organized into four categories:

1. **Active Bugs** (0 files) - Open defects with minimal repros, awaiting fix
2. **Limitation Tests** (3 files) - Expected behavior with documented workarounds
3. **Regression Tests** (20 files) - Previously fixed issues
4. **Feature Tests** (7 files) - Edge cases and features

---

## Active Bugs (0 files)

No open defects.

## Limitation Tests (3 files)

These tests document expected behavior limitations, not bugs. Each has a documented workaround.

### Prose with Periods (Issue #1 - CLOSED)

- **File**: [bug1_prose_period.txt](bug1_prose_period.txt)
- **Behavior**: Default parsing mode is for mathematical expressions, not prose
- **Workaround**: Use `TEXT:` blocks for prose with inline math
- **Reference**: See USER_GUIDE.md for TEXT block syntax

### Compound Identifiers (Issue #3 - CLOSED)

- **Files**: [bug3_compound_id.txt](bug3_compound_id.txt), [bug3_test_simple.txt](bug3_test_simple.txt)
- **Behavior**: txt2tex generates valid LaTeX (`R^+`), but fuzz type-checker rejects it
- **Workaround**: Use `--zed` flag to bypass fuzz type-checking
- **Note**: This is a fuzz limitation, not a txt2tex issue

---

## Regression Tests (20 files)

All regression tests pass. They verify previously fixed issues remain fixed.

### Resolved: Bug 4 — PROOF rule-label typography (m-2026-05-21-010, CLOSED)

- **bug4_proof_label_typography.txt** ✓
- **Test**: `tests/test_bug4_proof_label.py`
- **Fix**: Added pattern 3 in `_format_justification_label`. Labels of the form
  `<op>[\s-]+(intro|elim)` (no discharge number, no subscript) now emit the
  tight `{op_latex}\textrm{-{rule_name}}` form — matching patterns 1 and 2.
  Previously, `[false-intro]` rendered as `\mbox{false}-\mbox{intro}` (spaced
  binary minus in math mode) and `[=> elim]` as `\Rightarrow \mbox{elim}`
  (no hyphen). Both now render tight.

### Resolved: Bug 5 — `o9` composition context (m-2026-05-21-008, CLOSED)

- **bug5_o9_emits_semi_not_comp.txt** ✓
- **Fix**: `o9` now emits `\comp` inside Z paragraph environments
  (`\begin{zed}`, `\begin{axdef}`, `\begin{schema}`) and `\semi` in
  display math and inline `$...$` prose contexts.

### Resolved: Bug 7 — TEXT-block math-mode heuristic (m-2026-05-21-008/009, CLOSED)

All seven sub-symptoms (7.A–7.F) are fixed.

- **bug7_text_block_math_heuristic.txt** ✓ (7.A–7.D fixed, m-2026-05-21-008)
  - 7.A: `^` in prose escaped correctly; `^` inside `$...$` renders as math.
  - 7.B: Colon in prose does not trigger math-mode wrap.
  - 7.C: Math-operator keywords in bare prose are not auto-mathed.
  - 7.D: Backtick/backslash adjacency in prose does not garble.
- **bug7e_text_dollar_backslash.txt** ✓ (7.E fixed, m-2026-05-21-009)
  - Backslash-prefixed LaTeX commands inside `$...$` (`\Leftrightarrow`,
    `\forall`, `\Rightarrow`, etc.) pass through verbatim without
    re-lexing as SETMINUS + identifier.
- **bug7f_text_colon_auto_math.txt** ✓ (7.F fixed, m-2026-05-21-009)
  - Bare colons in TEXT prose are English punctuation; the
    colon-detection heuristic (`_process_type_declarations`) has been
    removed from the inline-math pipeline. Only explicit `$...$`
    content is parsed as math.

### Resolved: Multiple Pipes in TEXT Blocks (Issue #2 - CLOSED)

- **bug2_multiple_pipes.txt** ✓ - Multiple pipes now work correctly

### elem Operator and Bullet Separator (11 files)

| File | Tests |
|------|-------|
| regression_in_operator_basic.txt ✓ | Basic `y elem T` |
| regression_in_operator_simple.txt ✓ | Simple membership |
| regression_in_operator_with_comparison.txt ✓ | elem with bullet separator |
| regression_in_operator_multiple_same.txt ✓ | Multiple elem, same variable |
| regression_in_operator_multiple_nested.txt ✓ | Multiple elem, different variables |
| regression_in_operator_before_bullet.txt ✓ | elem before bullet separator |
| regression_in_notin_operators_combined.txt ✓ | Combined elem and notin |
| regression_in_operator_patterns.txt ✓ | Various elem patterns |
| regression_bullet_separator_basic.txt ✓ | Basic bullet separator |
| regression_bullet_separator_with_notin.txt ✓ | Bullet with notin |
| regression_bullet_separator_notin_paren.txt ✓ | Parenthesized bullet with notin |

### TEXT Block Operators (2 files)

- regression_text_comma_after_parens.txt ✓ (Issue #4 - CLOSED)
- regression_text_logical_operators.txt ✓ (Issue #5 - CLOSED)

### Set Operators (2 files)

- regression_subset_operator.txt ✓
- regression_notin_operator.txt ✓

---

## Feature Tests (7 files)

All feature tests pass. They document working features.

### Semicolon Separator (Issue #7 - CLOSED)

- feature_semicolon_separator.txt ✓

### Justification Formatting (6 files)

- feature_justification_caret_operator.txt ✓
- feature_justification_empty_sequence.txt ✓
- feature_justification_nonempty_sequence.txt ✓
- feature_justification_space_preservation.txt ✓
- feature_justification_word_identifiers.txt ✓
- feature_bag_syntax_in_free_types.txt ✓

---

## Summary Statistics

| Category | Count | Status |
|----------|-------|--------|
| Active Bugs | 0 | None open |
| Limitation Tests | 3 | Expected behavior |
| Regression Tests | 20 | All PASS |
| Feature Tests | 7 | All PASS |
| **Total** | **30** | **27 PASS, 3 limitations, 0 open** |

---

## Quick Status Check

```bash
cd /path/to/txt2tex
for f in tests/bugs/*.txt; do
  echo -n "$(basename $f): "
  uv run txt2tex "$f" --tex-only >/dev/null 2>&1 && echo "PASS" || echo "LIMITATION"
done
```

---

## References

- **[USER_GUIDE.md](../../docs/guides/USER_GUIDE.md)** - Documented syntax
- **[GitHub Issues](https://github.com/jmf-pobox/txt2tex/issues)** - All issues closed

---

**Last Updated**: 2026-05-21
**Active Bugs**: 0
**Retracted**: bug6 (`cat` keyword) — author error; canonical concat operator is `^`
(with leading space → CAT, no leading space → CARET/exponent per `lexer.py:691-716`).
`cat` is not in the txt2tex grammar.
**Closed**: bug4 (m-2026-05-21-010), bug5 (m-2026-05-21-008),
bug7 all sub-symptoms 7.A–7.F (m-2026-05-21-008 + m-2026-05-21-009)
**GitHub Issues**: All closed (#1, #2, #3, #4, #5, #7)
