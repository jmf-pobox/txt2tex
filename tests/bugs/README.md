# txt2tex Test Files: Bugs, Regressions, and Features

This directory contains test files organized into three categories:
1. **Active Bugs** (1 file) - Real bugs currently open on GitHub
2. **Fuzz Limitation Tests** (2 files) - Tests that pass txt2tex but fail fuzz type-checking
3. **Passing Tests** (23 files) - Regression and feature tests that pass

## Active Bugs (1 file)

Real bugs that are currently open on GitHub and need fixing.

### Bug #1: Parser fails on prose mixed with inline math (periods)
- **File**: [bug1_prose_period.txt](bug1_prose_period.txt)
- **Issue**: [#1](https://github.com/jmf-pobox/txt2tex/issues/1)
- **Priority**: HIGH
- **Status**: ACTIVE
- **Test Command**:
  ```bash
  hatch run cli tests/bugs/bug1_prose_period.txt --tex-only
  ```
- **Expected**: Should parse and render correctly
- **Actual**: `Error: Expected ')' after expression`
- **Workaround**: Use TEXT blocks for prose with periods
- **Impact**: Blocks natural writing style, especially for homework problems

---

## Fuzz Limitation Tests (2 files)

These tests pass txt2tex parsing and LaTeX generation, but fail fuzz type-checking due to fuzz limitations (not txt2tex bugs).

| File | Issue | Workaround |
|------|-------|------------|
| bug3_compound_id.txt | fuzz rejects `R^+` compound identifier | Use `--zed` flag |
| bug3_test_simple.txt | fuzz rejects `R^+` compound identifier | Use `--zed` flag |

**Verification**:
```bash
hatch run cli tests/bugs/bug3_test_simple.txt --tex-only       # FAIL (fuzz error)
hatch run cli tests/bugs/bug3_test_simple.txt --tex-only --zed # PASS
```

---

## Passing Tests (23 files)

### Resolved Bug (1 file)

- **bug2_multiple_pipes.txt** - Issue [#2](https://github.com/jmf-pobox/txt2tex/issues/2) appears to be fixed
  - Multiple pipes in TEXT blocks now work correctly

### elem Operator and Bullet Separator (11 files)

These tests verify `elem` operator and bullet separator (`.`) functionality:

| File | Tests |
|------|-------|
| regression_in_operator_basic.txt | Basic `y elem T` |
| regression_in_operator_simple.txt | Simple membership |
| regression_in_operator_with_comparison.txt | elem with bullet separator |
| regression_in_operator_multiple_same.txt | Multiple elem, same variable |
| regression_in_operator_multiple_nested.txt | Multiple elem, different variables |
| regression_in_operator_before_bullet.txt | elem before bullet separator |
| regression_in_notin_operators_combined.txt | Combined elem and notin |
| regression_in_operator_patterns.txt | Various elem patterns |
| regression_bullet_separator_basic.txt | Basic bullet separator |
| regression_bullet_separator_with_notin.txt | Bullet with notin |
| regression_bullet_separator_notin_paren.txt | Parenthesized bullet with notin |

### TEXT Block Operators (2 files) - Issues #4, #5

- [regression_text_comma_after_parens.txt](regression_text_comma_after_parens.txt) ✓
  - **Issue**: [#4](https://github.com/jmf-pobox/txt2tex/issues/4) (CLOSED)

- [regression_text_logical_operators.txt](regression_text_logical_operators.txt) ✓
  - **Issue**: [#5](https://github.com/jmf-pobox/txt2tex/issues/5) (CLOSED)

### Set Operators (2 files)

- [regression_subset_operator.txt](regression_subset_operator.txt) ✓
- [regression_notin_operator.txt](regression_notin_operator.txt) ✓

### Semicolon Separator (1 file)

- [feature_semicolon_separator.txt](feature_semicolon_separator.txt) ✓
  - **Related**: GitHub Issue [#7](https://github.com/jmf-pobox/txt2tex/issues/7) (CLOSED)

### Feature Tests - Justification Formatting (6 files)

- [feature_justification_caret_operator.txt](feature_justification_caret_operator.txt) ✓
- [feature_justification_empty_sequence.txt](feature_justification_empty_sequence.txt) ✓
- [feature_justification_nonempty_sequence.txt](feature_justification_nonempty_sequence.txt) ✓
- [feature_justification_space_preservation.txt](feature_justification_space_preservation.txt) ✓
- [feature_justification_word_identifiers.txt](feature_justification_word_identifiers.txt) ✓
- [feature_bag_syntax_in_free_types.txt](feature_bag_syntax_in_free_types.txt) ✓

---

## Summary Statistics

| Category | Count | Status |
|----------|-------|--------|
| Active Bugs | 1 | Need fixing |
| Fuzz Limitations | 2 | Pass with --zed |
| Passing Tests | 23 | All PASS |
| **Total** | **26** | **23 PASS, 1 BUG, 2 FUZZ** |

---

## Testing All Files

### Quick Status Check
```bash
cd /path/to/txt2tex/sem
for f in tests/bugs/*.txt; do
  echo -n "$(basename $f): "
  hatch run cli "$f" --tex-only >/dev/null 2>&1 && echo "PASS" || echo "FAIL"
done
```

### Test Regression Files (expect PASS)
```bash
for f in tests/bugs/regression_*.txt tests/bugs/feature_*.txt; do
  echo -n "$(basename $f): "
  hatch run cli "$f" --tex-only >/dev/null 2>&1 && echo "PASS" || echo "FAIL"
done
```

---

## References

- **[USER_GUIDE.md](../../docs/guides/USER_GUIDE.md)** - Documented syntax
- **[GitHub Issues](https://github.com/jmf-pobox/txt2tex/issues)** - Live bug tracking

---

**Last Updated**: 2025-11-29
**Active Bugs**: 1 (Issue #1)
**Test Results**: 23 PASS, 1 BUG, 2 FUZZ limitation
