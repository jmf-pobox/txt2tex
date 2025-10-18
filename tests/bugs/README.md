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
- **File**: [bug3_compound_id.txt](bug3_compound_id.txt)
- **Issue**: [#3](https://github.com/jmf-pobox/txt2tex/issues/3)
- **Priority**: MEDIUM
- **Status**: ACTIVE
- **Test Command**:
  ```bash
  hatch run convert tests/bugs/bug3_compound_id.txt
  ```
- **Expected**: Should define `R+` as an identifier
- **Actual**: `Error: Line 4, column 6: Expected identifier...` (lexer tokenizes as R followed by +)
- **Workaround**: None available
- **Impact**: Blocks Solution 31 (transitive closure R+)

### Bug 4: Comma after parenthesized math not detected in TEXT blocks
- **File**: [bug4_comma_after_parens.txt](bug4_comma_after_parens.txt)
- **Issue**: [#4](https://github.com/jmf-pobox/txt2tex/issues/4)
- **Priority**: MEDIUM
- **Status**: ACTIVE
- **Test Command**:
  ```bash
  hatch run convert tests/bugs/bug4_comma_after_parens.txt
  pdftotext tests/bugs/bug4_comma_after_parens.pdf -
  ```
- **Expected**: `The statements (¬ p ⇒ ¬ q), (q ⇒ p) are equivalent.`
- **Actual**: `The statements (not p => not q), (q ⇒ p) are equivalent.` (first expression not converted)
- **Workaround**: Avoid comma immediately after closing parenthesis in TEXT blocks
- **Impact**: Homework problems with multiple statements separated by commas

## Resolved Issues

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

### Bug 4: Nested quantifiers in mu expressions - RESOLVED ✓
- **Status**: RESOLVED in Phase 19
- **Test**: `mu p : ran s | forall q : ran s | p /= q | p.2 > q.2`
- **Result**: Now works correctly

### Issue 5: emptyset keyword not converted - RESOLVED ✓
- **Status**: RESOLVED
- **Test**: `TEXT: The set {emptyset, {1}, {2}} contains the empty set.`
- **Result**: Now correctly renders as {∅, {1}, {2}}

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
