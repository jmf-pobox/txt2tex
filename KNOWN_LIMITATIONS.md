# Known Limitations and Roadmap

**Last Updated:** 2025-10-15

## Summary

This document tracks known limitations in txt2tex, their root causes, and plans for resolution. Most limitations fall into two categories:
1. **Mathematical content in TEXT paragraphs** - Should use proper Z notation blocks instead
2. **Unimplemented features** - Tracked in DESIGN.md roadmap

## Current Status

- **latex_gen.py coverage**: 80.61% (153 uncovered lines out of 789)
- **Garbled characters in solutions.pdf**: 40 instances (down from 1400+)
- **Solutions working**: 39/52 (75%)

## PDF Garbling Issues

### Fixed

✅ **Sequence literals in TEXT blocks** (Phase 17.1)
**Completed**: 2025-10-15
- Problem: `<>`, `<x>`, `<a, b>` rendered as `¡¿`, `¡x¿`, `¡a, b¿`
- Root cause: LaTeX treats `<` and `>` as special characters in text mode
- Solution: Added `_convert_sequence_literals()` to detect and wrap sequences in math mode
- Impact: Reduced garbled characters from 1400+ to 40
- Files: `src/txt2tex/latex_gen.py` (lines 893-947, 880)

✅ **Simple inline expressions** (Phase 17 - Pattern 3)
- `p <=> x > 1` → `$p \Leftrightarrow x > 1$` ✓
- `f +-> g` → `$f \pfun g$` ✓
- `x > 1 and y < 5` → Both wrapped correctly ✓

### Unfixable in TEXT Paragraphs

❌ **Lambda expressions with `.` separator**
```
TEXT: children = {p : Person . p |-> parentOf(| {p} |)}
```
**Why garbled**: Uses `.` not `|`, so parser doesn't recognize as set comprehension.
**Proper syntax**: Should be in axdef block:
```
axdef
  children : Person -> P Person
where
  children = {p : Person . p |-> parentOf(| {p} |)}
end
```

❌ **Nested quantifiers in mu-expressions**
```
TEXT: (mu p : ran hd | forall q : ran hd | p /= q | p.2 > q.2 | p.1)
```
**Why garbled**: Multiple `|` delimiters cause parser ambiguity.
**Status**: Blocked - needs Phase 21 (Nested Quantifier Syntax).

❌ **Function types with complex domains**
```
TEXT: forall r : Drivers <-> Cars | ...
```
**Why garbled**: Relation type in quantifier domain.
**Status**: Works in axdef/schema blocks, TEXT support not prioritized.

### Migration Guide

If you have mathematical definitions in TEXT paragraphs:

**Before** (garbled):
```
TEXT: children = {p : Person . p |-> parentOf(| {p} |)}
```

**After** (correct):
```
axdef
  children : Person -> P Person
where
  children = {p : Person . p |-> parentOf(| {p} |)}
end
```

## Uncovered Code in latex_gen.py

### Exception Handlers (40 lines - Low Priority)

**Lines 963-968, 974, 1048-1051**: Exception handling in `_process_inline_math()`
- Pattern 1/2/3 parse failures
- **Coverage cost/benefit**: High effort, low value (error paths)
- **Plan**: Add tests only if bugs discovered

### Identifier Underscore Heuristics (15 lines)

**Lines 336-351, 368**: Phase 15 multi-word identifier detection
- Distinguishing `cumulative_total` (multi-word) from `x_1` (subscript)
- **Status**: Heuristic works well in practice
- **Plan**: Add tests when refining heuristic

### Rare Operators (10 lines)

**Lines 478-484, 634-641**: Operators rarely used in homework
- Finite sets: `F X`, `F1 Y`
- Distributed ops: `disjoint(S)`, `bigcap(S)`, `bigcup(S)`
- Partition: `partition(S)`
- **Status**: Implemented but untested
- **Plan**: Add tests when used in solutions

### Complex Proof Trees (98 lines - Specialized)

**Lines 1576-1673**: Or-elimination with case analysis and staggered layout
- Vertical spacing calculations for nested proof branches
- Horizontal `\hskip` adjustments for readability
- **Status**: Works for Solutions 13-18
- **Plan**: Add tests if layout issues arise

## Roadmap Blockers

### Phase 21: Nested Quantifiers

**Blocked solutions**: 40 (mu-expressions), 43 (complex predicates)

**Syntax ambiguity**:
```
forall x : X | P(x) || forall y : Y | Q(y) | R(x, y)
```
Uses `||` to separate nested quantifier scopes from predicates.

**Status**: Design phase - needs careful parser changes.

### Phase 22: Recursive Free Types

**Blocked solutions**: 50-52 (Tree induction, pattern matching)

**Example**:
```
free Tree ::= leaf | branch⟨Tree * Tree⟩
```

**Status**: Partially implemented - needs constructor pattern matching.

### Schema Composition

**Blocked solutions**: 47-49 (state machines)

**Example**:
```
schema S1 ; S2  # Sequential composition
schema S1 and S2  # Conjunction
```

**Status**: Not yet implemented.

## Measurement and Verification

### Coverage Targets

| Component | Current | Target | Priority |
|-----------|---------|--------|----------|
| parser.py | 88.91% | 90%+ | High |
| latex_gen.py | 80.61% | 85%+ | Medium |
| lexer.py | 94.56% | 95%+ | Low |
| Overall | 88.49% | 90%+ | High |

### PDF Quality Metrics

**Measurement process**:
```bash
# Count garbled characters
pdftotext examples/solutions.pdf - | grep -o "[¿¡—]" | wc -l

# Compare with reference
open examples/solutions.pdf examples/solutions_full.pdf
```

**Current**: 40 garbled characters (down from 1400+)
**Target**: <50 (only from unimplemented features) ✅ **TARGET ACHIEVED**

**Major improvement**: Sequence literal fix (Phase 17.1) reduced garbled characters by 97%.

### Solution Coverage

**Fully working**: 39/52 (75%)
**Partially working**: 4/52 (8%)
**Not implemented**: 9/52 (17%)

See [SOLUTION_STATUS.md](SOLUTION_STATUS.md) for details.

## Contributing

When adding features:
1. Update this file if fixing a limitation
2. Remove entries when limitation is resolved
3. Add tests to increase coverage
4. Update DESIGN.md roadmap if needed

## References

- [DESIGN.md](DESIGN.md) - Feature roadmap and implementation phases
- [SOLUTION_STATUS.md](SOLUTION_STATUS.md) - Per-solution implementation status
- [README.md](README.md) - User-facing documentation
