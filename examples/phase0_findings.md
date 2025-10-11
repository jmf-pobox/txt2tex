# Phase 0 Test Results: Solutions 1-3

## Executive Summary

**Phase 0 can handle most propositional logic from Solutions 1-3, but has two limitations:**

1. ❌ **No parentheses support** - Cannot override operator precedence
2. ❌ **Single expression only** - Cannot process multi-line documents

## What Works ✅

### Basic Operators with Correct Precedence

| Input | LaTeX Output |
|-------|--------------|
| `p and q => r` | `$p \land q \Rightarrow r$` |
| `not p or q` | `$\lnot p \lor q$` |
| `p <=> q` | `$p \Leftrightarrow q$` |

### true/false as Identifiers

| Input | LaTeX Output |
|-------|--------------|
| `true => false <=> false` | `$true \Rightarrow false \Leftrightarrow false$` |
| `false => true` | `$false \Rightarrow true$` |

### Complex Nesting (Precedence-Based)

| Input | LaTeX Output |
|-------|--------------|
| `not not p or p` | `$\lnot \lnot p \lor p$` |
| `not p or not q or r` | `$\lnot p \lor \lnot q \lor r$` |
| `not p or p and not p or q` | `$\lnot p \lor p \land \lnot p \lor q$` |

### Long Chains

| Input | LaTeX Output |
|-------|--------------|
| `p => q => r => s` | `$p \Rightarrow q \Rightarrow r \Rightarrow s$` |
| `p <=> q <=> r` | `$p \Leftrightarrow q \Leftrightarrow r$` |

## What Doesn't Work ❌

### Parentheses (Not Supported)

These expressions from Solution 3 **fail** because they need parentheses:

```
p => (q => r)                    ❌ Line 12(c)
not p or (q => r)                ❌ Line 13(c)
not p or (not q or r)            ❌ Line 14(c)
(not p or not q) or r            ❌ Line 15(c)
not (p and q) or r               ❌ Line 16(c)
(p and q) => r                   ❌ Line 17(c)
```

**Why needed:** To override precedence. For example:
- `not (p and q)` means "negate the result of (p and q)"
- Without parens, `not p and q` means "(not p) and q" due to precedence

### Multi-Line Documents (Phase 1 Feature)

Phase 0 processes **one expression at a time**. These don't work:

```
Solution 1      ❌ (document structure)
(a)             ❌ (part labels)
(b)             ❌ (part labels)
```

**Workaround:** Use `-e` flag to test individual expressions:
```bash
PYTHONPATH=src python -m txt2tex.cli -e "not not p or p"
```

## Coverage Analysis

### Solution 1: Simple Evaluations
- **Total expressions:** 4
- **Can handle:** 4/4 (100%) ✅
- **Note:** All are simple, no parentheses needed

```bash
# All work:
PYTHONPATH=src python -m txt2tex.cli -e "true => false <=> false"
PYTHONPATH=src python -m txt2tex.cli -e "false => false <=> true"
PYTHONPATH=src python -m txt2tex.cli -e "false => true <=> true"
```

### Solution 2: Truth Tables
- **Can handle:** 0% ❌
- **Reason:** Tables are Phase 1 feature

### Solution 3: Equivalence Chains
- **Total unique expressions:** ~47
- **Can handle without parens:** ~18 (38%)
- **Need parentheses:** ~29 (62%) ❌

**Expressions that DO work:**

```bash
# Part (a) - works
PYTHONPATH=src python -m txt2tex.cli -e "p => not p"
PYTHONPATH=src python -m txt2tex.cli -e "not p or not p"
PYTHONPATH=src python -m txt2tex.cli -e "not p"

# Part (b) - works
PYTHONPATH=src python -m txt2tex.cli -e "not p => p"
PYTHONPATH=src python -m txt2tex.cli -e "not not p or p"
PYTHONPATH=src python -m txt2tex.cli -e "p or p"

# Some from (e), (f) - work
PYTHONPATH=src python -m txt2tex.cli -e "p and q <=> p"
PYTHONPATH=src python -m txt2tex.cli -e "not p or q"
PYTHONPATH=src python -m txt2tex.cli -e "p => q"
```

**Expressions that DON'T work (need parens):**

All expressions in parts (c), (d), (e), (f) that contain parentheses fail.

## Recommendation

**To fully support Solutions 1-3, Phase 0 needs parentheses.**

### Estimated Scope
- Add `LPAREN`, `RPAREN` tokens to lexer
- Add parenthesized expression parsing to parser
- ~30-50 lines of code
- 1-2 hours with tests

### Benefit
- **Coverage jumps from 38% → 100%** for Solution 3 expressions
- Essential for propositional logic (can't express many equivalences without parens)
- Natural part of Phase 0 scope

## Test Files Created

1. `phase0_complex.txt` - All 47 expressions (many fail due to parens)
2. `phase0_no_parens.txt` - Simplified versions (multi-line, doesn't work)
3. Individual tests via `-e` flag ✅

## Next Steps

**Option 1:** Add parentheses support to Phase 0 (recommended)
- Small enhancement
- High value for coursework
- Still within "simple propositional logic" scope

**Option 2:** Proceed to Phase 1 as-is
- Accept 38% coverage of Solution 3
- Add parens later if needed

**Option 3:** Create test suite of individual expressions
- Document which 18 expressions currently work
- Use for regression testing
