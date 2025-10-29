# QA Checks Documentation

## Overview

The `qa_check.sh` script performs systematic quality checks on generated PDFs and LaTeX files to catch rendering issues before they make it into final documents.

**Relationship to QA Process**: This script automates **Check #2 (Notation Correct)** from [QA_PLAN.md](QA_PLAN.md). Run this before manual solution-by-solution review to catch symbol rendering issues automatically.

## What the Script Checks

### 1. Garbled Characters in PDF (¿, ¡, —)
**What it checks**: Counts occurrences of garbled characters that indicate LaTeX rendering issues.

**Why it matters**: These characters appear when:
- Angle brackets `<>` are used in text mode (should be `\langle \rangle`)
- Relation operators `<->` appear outside math mode
- Unicode characters aren't properly handled

**Current status**: 40 garbled characters (down from 1400+)

### 2. Text "forall" Instead of Symbol (∀)
**What it checks**: Finds instances where "forall" appears as plain text instead of the universal quantifier symbol.

**Why it matters**: In formal notation, `forall` should render as `∀` (using `\forall` in LaTeX).

**Example issue**:
```
BAD:  forall x : N | x > 0
GOOD: ∀ x : N • x > 0
```

### 3. Text "emptyset" Instead of Symbol (∅)
**What it checks**: Finds instances where "emptyset" appears as plain text instead of the empty set symbol.

**Why it matters**: The empty set should render as `∅` (using `\emptyset` or `\empty` in LaTeX).

**Example issue**:
```
BAD:  {emptyset, {1}, {2}}
GOOD: {∅, {1}, {2}}
```

### 4. Runon Text (Missing Spaces)
**What it checks**: Detects lines with >80 characters where >95% are non-space characters.

**Why it matters**: Indicates missing spaces, often caused by:
- Superscripts eating following spaces
- Math mode boundaries consuming whitespace
- Missing space preservation in TEXT blocks

**Example issue**:
```
BAD:  x2−x+1denotesanaturalnumber
GOOD: x² - x + 1 denotes a natural number
```

### 5. LaTeX Source Issues

#### Bare Angle Brackets
**What it checks**: Finds `<` and `>` outside math mode or special commands.

**Why it matters**: These are special characters in LaTeX and must be:
- In math mode: `$<$`, `$>$`
- Or using proper commands: `\langle`, `\rangle`

#### Plain "forall" in LaTeX
**What it checks**: Finds `forall` without backslash in LaTeX source.

**Why it matters**: Should be `\forall` command to render as symbol.

#### Plain "emptyset" in LaTeX
**What it checks**: Finds `emptyset` without backslash in LaTeX source.

**Why it matters**: Should be `\emptyset` command to render as symbol.

## Running the Script

### Basic usage:
```bash
./qa_check.sh examples/solutions.pdf
```

### Check specific file:
```bash
./qa_check.sh my_document.pdf
```

### Integrate into workflow:
```bash
# After generating PDF
hatch run convert examples/solutions.txt
./qa_check.sh examples/solutions.pdf

# Or in Makefile
make && ./qa_check.sh examples/solutions.pdf
```

## Current Issues Found

### Solutions with Garbled Characters
- Solution 34-36: 3 chars each
- Solution 39: 2 chars
- Solution 40-43: 5-9 chars each
- Solution 48-52: 2-6 chars each

### Root Causes

#### 1. Solution 6(a) - Runon Text
**Source**: `TEXT: x^2 - x + 1 denotes a natural number`
**Problem**: Superscript `^2` eating space after `1`
**Result**: "1denotesanaturalnumber"
**Fix needed**: Improve superscript space handling in TEXT blocks

#### 2. Solution 19 - Missing Set Braces
**Source**: `TEXT: 1 in {4, 3, 2, 1} is true.`
**Problem**: Inline math detection eating curly braces
**Result**: "1 in 4, 3, 2, 1 is true"
**Fix needed**: Preserve braces in inline math patterns

#### 3. Solution 27 - Text "emptyset"
**Source**: `TEXT: {emptyset, {(0, 0)}, ...}`
**Problem**: Plain text "emptyset" not converted to symbol
**Result**: "emptyset" instead of "∅"
**Fix needed**: Convert `emptyset` → `$\emptyset$` in TEXT blocks

#### 4. Solution 36 - Multiple Issues
**Source**: TEXT blocks with axdef content:
```
TEXT: axdef
TEXT:   number_of_drivers : (Drivers <-> Cars) -> (Cars -> N)
TEXT: where
TEXT:   forall r : Drivers <-> Cars | ...
```

**Problems**:
- `number_of_drivers` → renders as "numbero fd rivers" (subscript issue)
- `<->` → renders as "¡-¿" (garbled angle brackets)
- `forall` → stays as text instead of symbol

**Root cause**: Mathematical content in TEXT blocks instead of proper axdef blocks

**Proper solution**: Should use actual axdef block:
```
axdef
  number_of_drivers : (Drivers <-> Cars) -> (Cars -> N)
where
  forall r : Drivers <-> Cars | number_of_drivers(r) = {c : ran r . c |-> #{d : Drivers | d |-> c in r}}
end
```

## Priority Fixes

### High Priority (Blocking Coverage)
1. **Relation types in quantifier domains** (Solution 36)
   - Currently using TEXT workaround
   - Needs parser support for `forall r : X <-> Y | P`

2. **emptyset keyword** (Solution 27)
   - Add to TEXT block operator conversion
   - Convert `emptyset` → `$\emptyset$`

### Medium Priority (Quality)
3. **Set braces in inline math** (Solution 19)
   - Inline math pattern eating braces
   - Need better pattern matching

4. **Superscript spacing** (Solution 6)
   - Space after number+superscript being consumed
   - May need explicit space preservation

### Low Priority (Workarounds Available)
5. **camelCase rendering** (Solution 36)
   - Multi-word identifiers in TEXT blocks
   - Workaround: Use proper axdef blocks

## Integration Workflow

### Development Cycle
```bash
# 1. Make changes
edit src/txt2tex/parser.py

# 2. Run tests
hatch run check

# 3. Regenerate PDF
hatch run convert examples/solutions.txt

# 4. QA check (automated notation verification)
./qa_check.sh examples/solutions.pdf

# 5. If issues found, investigate and fix
# 6. Repeat
```

### Solution Review Workflow

When reviewing solutions per [QA_PLAN.md](QA_PLAN.md):

```bash
# Step 1: Generate PDF
hatch run convert examples/solutions.txt

# Step 2: Run automated checks (supports Check #2: Notation Correct)
./qa_check.sh examples/solutions.pdf

# Step 3: Fix any automated issues found

# Step 4: Manual review (Check #1: Input Correct, Check #3: Formatting Correct)
# Review each solution manually in QA_PLAN.md checklist
```

### Pre-Commit Checklist
- [ ] All tests pass (`hatch run check`)
- [ ] PDF generates without errors
- [ ] QA script passes or issues documented
- [ ] Garbled character count not increased

## Expected Output

### Clean build:
```
==========================================
txt2tex Quality Assurance Check
==========================================

...

✓ All checks passed!
```

### Build with issues:
```
==========================================
txt2tex Quality Assurance Check
==========================================

...

✗ Found 60 issue(s)

Issues found:
  - 40 garbled characters
  - 12 text 'forall' (should be symbol)
  - 8 text 'emptyset' (should be symbol)
```

## Notes

- Script exits with code 0 if all checks pass, 1 if issues found
- Can be used in CI/CD pipelines
- Add new checks as patterns emerge
- Keep checks simple and fast (<5 seconds)
