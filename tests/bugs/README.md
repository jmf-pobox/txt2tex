# txt2tex Test Files: Regressions, Features, and Limitations

This directory contains test files organized into three categories:
1. **Limitation Tests** (3 files) - Expected behavior with documented workarounds
2. **Regression Tests** (16 files) - Previously fixed issues
3. **Feature Tests** (7 files) - Edge cases and features

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

## Regression Tests (16 files)

All regression tests pass. They verify previously fixed issues remain fixed.

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
| Limitation Tests | 3 | Expected behavior |
| Regression Tests | 16 | All PASS |
| Feature Tests | 7 | All PASS |
| **Total** | **26** | **23 PASS, 3 limitations** |

---

## Quick Status Check

```bash
cd /path/to/txt2tex/sem
for f in tests/bugs/*.txt; do
  echo -n "$(basename $f): "
  hatch run cli "$f" --tex-only >/dev/null 2>&1 && echo "PASS" || echo "LIMITATION"
done
```

---

## References

- **[USER_GUIDE.md](../../docs/guides/USER_GUIDE.md)** - Documented syntax
- **[GitHub Issues](https://github.com/jmf-pobox/txt2tex/issues)** - All issues closed

---

**Last Updated**: 2025-11-29
**Active Bugs**: 0
**GitHub Issues**: All closed (#1, #2, #3, #4, #5, #7)
