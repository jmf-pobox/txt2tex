# txt2tex Bug Test Cases

This directory contains minimal reproducible test cases for known bugs in txt2tex.

## Purpose

Each bug has:
1. **Minimal test case**: Simplest input that triggers the bug
2. **Expected behavior**: What should happen
3. **Actual behavior**: What actually happens (error or incorrect output)
4. **GitHub issue reference**: Link to tracking issue

## Active Bugs

### Bug 1: Parser fails on prose mixed with inline math (periods)
- **File**: [bug1_prose_period.txt](bug1_prose_period.txt)
- **Issue**: [#1](https://github.com/jmf-pobox/txt2tex/issues/1)
- **Priority**: HIGH
- **Status**: ACTIVE
- **Test Command**:
  ```bash
  hatch run convert tests/bugs/bug1_prose_period.txt
  ```
- **Expected**: Should parse and render correctly
- **Actual**: `Error: Line 3, column 26: Expected identifier, number, '(', '{', '⟨', or lambda, got PERIOD`
- **Workaround**: Use TEXT blocks for prose with periods
- **Impact**: Blocks natural writing style, especially for homework problems

### Bug 2: TEXT blocks with multiple pipes close math mode prematurely
- **File**: [bug2_multiple_pipes.txt](bug2_multiple_pipes.txt)
- **Issue**: [#2](https://github.com/jmf-pobox/txt2tex/issues/2)
- **Priority**: MEDIUM
- **Status**: ACTIVE
- **Test Command**:
  ```bash
  hatch run convert tests/bugs/bug2_multiple_pipes.txt
  pdftotext tests/bugs/bug2_multiple_pipes.pdf -
  ```
- **Expected**: All pipes should be in math mode: `(µ p : ran hd • (∀ q : ran hd • p ≠ q • p.2 > q.2))`
- **Actual**: Second pipe appears as text: `p ̸= q| p.2 > q.2` (pipe outside math mode)
- **Workaround**: Use proper Z notation blocks (axdef, schema) instead of TEXT
- **Impact**: Solution 40(g) and similar complex expressions

### Bug 3: Compound identifiers with operator suffixes fail
- **Files**:
  - [bug3_compound_id.txt](bug3_compound_id.txt) - Full test with TEXT description
  - [bug3_test_simple.txt](bug3_test_simple.txt) - Minimal failing case
- **Issue**: [#3](https://github.com/jmf-pobox/txt2tex/issues/3)
- **Priority**: MEDIUM
- **Status**: ACTIVE
- **Test Command**:
  ```bash
  hatch run convert tests/bugs/bug3_compound_id.txt
  hatch run convert tests/bugs/bug3_test_simple.txt  # Both fail
  ```
- **Expected**: Should define `R+` as an identifier
- **Actual**: `Error: Line 4/5, column 6/1: Expected identifier...` (lexer tokenizes as R followed by +)
- **Workaround**: None available
- **Impact**: Blocks Solution 31 (transitive closure R+)

## Resolved Issues

These files document features that were previously broken but are now working correctly. They serve as regression tests to ensure the fixes remain stable.

### Bug 4: Comma after parenthesized math not detected in TEXT blocks - RESOLVED ✓
- **File**: [bug4_comma_after_parens.txt](bug4_comma_after_parens.txt)
- **Issue**: [#4](https://github.com/jmf-pobox/txt2tex/issues/4)
- **Status**: RESOLVED in commit 7f6a932
- **Test Command**:
  ```bash
  hatch run convert tests/bugs/bug4_comma_after_parens.txt
  pdftotext tests/bugs/bug4_comma_after_parens.pdf -
  ```
- **Result**: Both expressions now correctly converted:
  - `(not p => not q), (q => p)` → `¬ p ⇒ ¬ q, q ⇒ p` ✓
- **Fix**: Pattern -0.5 uses balanced parenthesis matching instead of greedy regex

### Bug 5: Logical operators (or, and) not converted in TEXT blocks - RESOLVED ✓
- **File**: [bug5_or_operator.txt](bug5_or_operator.txt)
- **Issue**: [#5](https://github.com/jmf-pobox/txt2tex/issues/5)
- **Status**: RESOLVED in commit b709351
- **Test Command**:
  ```bash
  hatch run convert tests/bugs/bug5_or_operator.txt
  pdftotext tests/bugs/bug5_or_operator.pdf -
  ```
- **Result**: All operators now correctly converted:
  - `(p or q)` → `p ∨ q` ✓
  - `(p and q)` → `p ∧ q` ✓
  - `((p => r) and (q => r))` → `(p ⇒ r) ∧ (q ⇒ r)` ✓
  - `((p or q) => r)` → `p ∨ q ⇒ r` ✓
- **Fix**: Added Pattern -0.5 to inline math detection using balanced parenthesis matching

### Nested quantifiers in mu expressions - RESOLVED ✓
- **Status**: RESOLVED in Phase 19
- **Test**: `mu p : ran s | forall q : ran s | p /= q | p.2 > q.2`
- **Result**: Now works correctly

### emptyset keyword not converted - RESOLVED ✓
- **Status**: RESOLVED
- **Test**: `TEXT: The set {emptyset, {1}, {2}} contains the empty set.`
- **Result**: Now correctly renders as {∅, {1}, {2}}

### IN operator disambiguation - RESOLVED ✓
- **Files**:
  - [bug_minimal_in.txt](bug_minimal_in.txt)
  - [bug_just_y_in_t.txt](bug_just_y_in_t.txt)
  - [bug_in_comparison.txt](bug_in_comparison.txt)
  - [bug_in_in_same.txt](bug_in_in_same.txt)
  - [bug_in_in_different.txt](bug_in_in_different.txt)
  - [bug_in_before_bullet.txt](bug_in_before_bullet.txt)
  - [bug_in_notin_combo.txt](bug_in_notin_combo.txt)
  - [bug_test_patterns.txt](bug_test_patterns.txt)
- **Status**: RESOLVED in Phase 18 (November 18, 2025)
- **Test**: Various combinations of `in` and `notin` operators in quantified expressions
- **Result**: Parser correctly disambiguates `in` as set membership vs part of words like "in_domain"
- **Fix**: Enhanced lexer to properly tokenize IN and NOTIN as operators

### Bullet separator with IN/NOTIN - RESOLVED ✓
- **Files**:
  - [bug_bullet_simple.txt](bug_bullet_simple.txt)
  - [bug_bullet_notin.txt](bug_bullet_notin.txt)
  - [bug_bullet_notin_paren.txt](bug_bullet_notin_paren.txt)
- **Status**: RESOLVED in Phase 18 (November 18, 2025)
- **Test**: Quantifiers with bullet separator followed by `in` or `notin` operators
- **Result**: Parser correctly handles bullet (.) as separator in quantified expressions
- **Examples**:
  - `forall x : N | x in S . x notin T` ✓
  - `forall x : N | x > 0 . x < 10` ✓
  - `forall x : N | x in S => x notin T` ✓ (no bullet, still works)
- **Fix**: Enhanced parser to recognize bullet separator and distinguish from period

### SUBSET operator - RESOLVED ✓
- **File**: [bug_subset_subset.txt](bug_subset_subset.txt)
- **Status**: RESOLVED in Phase 18 (November 18, 2025)
- **Test**: `forall S : P N | S subset T . S subset U`
- **Result**: Parser correctly handles `subset` operator in quantified expressions
- **Fix**: Added SUBSET token and proper operator precedence

### NOTIN operator - RESOLVED ✓
- **File**: [bug_notin_simple.txt](bug_notin_simple.txt)
- **Status**: RESOLVED in Phase 18 (November 18, 2025)
- **Test**: Various uses of `notin` operator
- **Result**: Parser correctly tokenizes and processes `notin` operator
- **Examples**:
  - `x notin S` ✓
  - `(x notin S)` ✓
  - `forall x : N | x notin S` ✓
  - `forall x : N | x > 0 . x notin S` ✓

## Test Cases (Never Bugs)

These files document specific edge cases or features that were tested during development. They were never actual bugs, but serve as regression tests for complex or subtle language features.

### Justification formatting tests
- **Files**:
  - [bug_caret_in_justification.txt](bug_caret_in_justification.txt)
  - [bug_empty_sequence_justification.txt](bug_empty_sequence_justification.txt)
  - [bug_nonempty_sequence_justification.txt](bug_nonempty_sequence_justification.txt)
  - [bug_spaces_in_justification.txt](bug_spaces_in_justification.txt)
  - [bug_word_justification.txt](bug_word_justification.txt)
- **Purpose**: Test that EQUIV justifications correctly render mathematical expressions and preserve spacing
- **Status**: All tests pass

### Semicolon separator in quantifiers
- **File**: [test_issue7_semicolon.txt](test_issue7_semicolon.txt)
- **GitHub**: [#7](https://github.com/jmf-pobox/txt2tex/issues/7)
- **Purpose**: Test semicolon separator for multiple variable declarations in quantifiers
- **Status**: Working correctly
- **Examples**:
  - `forall x : N; y : M | x > 0 and y > 0` ✓
  - `forall x, y : N; z : M | x + y > z` ✓
  - `forall s : ShowId; t_1, t_2 : Timestamp; e_1, e_2 : EpisodeId | s = s` ✓

### Bag syntax in free type constructors
- **File**: [bug_bag_in_free_type.txt](bug_bag_in_free_type.txt)
- **Purpose**: Test bag notation (double angle brackets) in free type definitions
- **Status**: Working correctly
- **Example**: `List ::= nil | join <<(ShowId cross EpisodeId) cross (N cross PlayedOrNot cross SavedOrNot) cross List>>` ✓

## Running Tests

### Test a specific bug:
```bash
hatch run convert tests/bugs/bug1_prose_period.txt
```

### Test all bugs at once:
```bash
for f in tests/bugs/bug*.txt; do
  echo "=== Testing $f ==="
  hatch run convert "$f" 2>&1 | grep -E "(Error|Success)"
done
```

### Verify bug is still active:
```bash
# Should fail
hatch run convert tests/bugs/bug1_prose_period.txt

# Should show garbled output
hatch run convert tests/bugs/bug2_multiple_pipes.txt
pdftotext tests/bugs/bug2_multiple_pipes.pdf -

# Should fail
hatch run convert tests/bugs/bug3_compound_id.txt
```

## Adding New Bugs

When you encounter a new bug:

1. **Create minimal test case**:
   ```bash
   echo "=== Bug N Test: Description ===" > tests/bugs/bugN_short_name.txt
   echo "[minimal failing example]" >> tests/bugs/bugN_short_name.txt
   ```

2. **Verify it fails**:
   ```bash
   hatch run convert tests/bugs/bugN_short_name.txt
   ```

3. **Create GitHub issue** using the bug report template

4. **Update this README** with the new bug entry

5. **Reference the issue** in STATUS.md

## Bug Reporting Workflow

1. Reproduce bug with minimal test case
2. Save test case to `tests/bugs/bugN_name.txt`
3. Run `hatch run convert tests/bugs/bugN_name.txt` to verify
4. Create GitHub issue with test case details
5. Link issue number in this README
6. Reference issue in STATUS.md

## Notes

- Keep test cases minimal (5-10 lines)
- One bug per file
- Include section header for context
- Document expected vs actual behavior
- Test cases serve as regression tests once bugs are fixed
