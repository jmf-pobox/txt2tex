# txt2tex Test Files: Bugs, Regressions, and Features

This directory contains test files organized into three categories:
1. **Active Bugs** (1 file) - Real bugs currently open on GitHub
2. **Stale Tests** (13 files) - Tests using deprecated/incorrect syntax
3. **Passing Tests** (12 files) - Regression and feature tests that pass

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

## Stale Tests (13 files)

These tests fail because they use **deprecated or incorrect syntax**, NOT because of bugs in txt2tex.

### Tests Using Deprecated `in` Keyword (10 files)

**Problem**: Tests use `in` for set membership, but the correct keyword is `elem`.

Per USER_GUIDE.md: *"Use `elem` for set membership. The `in` keyword was deprecated in favor of `elem` to avoid ambiguity with English prose."*

| File | Issue | Fix |
|------|-------|-----|
| regression_in_operator_basic.txt | Uses `y in T` | Change to `y elem T` |
| regression_in_operator_with_comparison.txt | Uses `x in S` | Change to `x elem S` |
| regression_in_operator_multiple_same.txt | Uses `x in S` | Change to `x elem S` |
| regression_in_operator_multiple_nested.txt | Uses `x in S` | Change to `x elem S` |
| regression_in_operator_before_bullet.txt | Uses `x in S` | Change to `x elem S` |
| regression_in_notin_operators_combined.txt | Uses `x in S` | Change to `x elem S` |
| regression_in_operator_patterns.txt | Uses `x in S` | Change to `x elem S` |
| regression_bullet_separator_basic.txt | Uses `x in S` | Change to `x elem S` |
| regression_bullet_separator_with_notin.txt | Uses `x in S` | Change to `x elem S` |
| regression_bullet_separator_notin_paren.txt | Uses `x in S` | Change to `x elem S` |

**Verification**: The bullet separator syntax (`.`) works correctly with `elem`:
```bash
echo "(forall x : N | x elem S . y < 10)" > /tmp/test.txt
hatch run cli /tmp/test.txt --tex-only  # PASSES
```

### Tests Using Incorrect `and` Keyword (1 file)

**Problem**: Test uses `and` for logical conjunction, but the correct keyword is `land`.

Per USER_GUIDE.md: *"English-style `and`, `or`, `not` are NOT supported in Z notation expressions."*

| File | Issue | Fix |
|------|-------|-----|
| feature_semicolon_separator.txt | Uses `x > 0 and y > 0` | Change to `x > 0 land y > 0` |

**Verification**: Semicolon separator works correctly with `land`:
```bash
echo "forall x : N; y : M | x > 0 land y > 0" > /tmp/test.txt
hatch run cli /tmp/test.txt --tex-only  # PASSES
```

### Tests Hitting Fuzz Limitations (2 files)

**Problem**: txt2tex parsing and LaTeX generation work correctly, but fuzz type-checker cannot handle compound identifiers like `R+`.

| File | Issue | Workaround |
|------|-------|------------|
| bug3_compound_id.txt | fuzz rejects `R^+` | Use `--zed` flag to skip fuzz |
| bug3_test_simple.txt | fuzz rejects `R^+` | Use `--zed` flag to skip fuzz |

**Verification**: Parsing and generation work, only fuzz fails:
```bash
hatch run cli tests/bugs/bug3_test_simple.txt --tex-only       # FAIL (fuzz error)
hatch run cli tests/bugs/bug3_test_simple.txt --tex-only --zed # PASS
```

This is a **fuzz limitation**, not a txt2tex bug. The generated LaTeX is correct.

---

## Passing Tests (12 files)

### Resolved Bug (1 file)

- **bug2_multiple_pipes.txt** - Issue [#2](https://github.com/jmf-pobox/txt2tex/issues/2) appears to be fixed
  - Multiple pipes in TEXT blocks now work correctly

### TEXT Block Operators (2 files) - Issues #4, #5

- [regression_text_comma_after_parens.txt](regression_text_comma_after_parens.txt) ✓
  - **Issue**: [#4](https://github.com/jmf-pobox/txt2tex/issues/4) (CLOSED)
  - **Test**: `(not p => not q), (q => p)` → `¬ p ⇒ ¬ q, q ⇒ p`

- [regression_text_logical_operators.txt](regression_text_logical_operators.txt) ✓
  - **Issue**: [#5](https://github.com/jmf-pobox/txt2tex/issues/5) (CLOSED)
  - **Test**: `(p or q)` → `p ∨ q`, `(p and q)` → `p ∧ q`

### Set Operators (3 files)

- [regression_in_operator_simple.txt](regression_in_operator_simple.txt) ✓ - Simple `y in T`
- [regression_subset_operator.txt](regression_subset_operator.txt) ✓ - `subset` operator
- [regression_notin_operator.txt](regression_notin_operator.txt) ✓ - `notin` operator

### Feature Tests - Justification Formatting (6 files)

All justification formatting tests pass:

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
| Stale Tests (bad syntax) | 13 | Delete or fix syntax |
| Passing Tests | 12 | All PASS |
| **Total** | **26** | **12 PASS, 14 FAIL** |

---

## Recommended Actions

1. **Delete stale tests**: The 13 failing tests use deprecated syntax and don't test real functionality
2. **Close Bug #2**: bug2_multiple_pipes.txt now passes
3. **Close Bug #3**: bug3 files work correctly, only fail fuzz type-checking (not a txt2tex issue)

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

---

## References

- **[USER_GUIDE.md](../../docs/guides/USER_GUIDE.md)** - Documented syntax
- **[GitHub Issues](https://github.com/jmf-pobox/txt2tex/issues)** - Live bug tracking

---

**Last Updated**: 2025-11-29
**Active Bugs**: 1 (Issue #1)
**Test Results**: 12 PASS, 14 FAIL (13 due to bad syntax, 1 real bug)
