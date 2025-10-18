# Garbled Character Elimination: Implementation Plan

## Objective
Eliminate all garbled characters in generated PDFs (from 1441 to 0) by fixing parser bugs and implementing missing features.

## Current State
- **40 garbled characters** (¿, ¡, —) remaining in solutions.pdf (down from 1441)
- **243 TEXT blocks** in solutions.txt
- Root cause: TEXT blocks used as workarounds for missing/broken features

## Completed Fixes

### Phase 17.1: Sequence Literal Fix ✅
**Completed**: 2025-10-15

**Problem**: TEXT blocks containing sequence literals like `<>`, `<x>`, `<a, b>` were rendering as garbled characters (¡¿) in PDFs.

**Root Cause**: LaTeX treats `<` and `>` as special characters in text mode, causing incorrect rendering.

**Solution**: Added `_convert_sequence_literals()` method in `latex_gen.py`:
- Detects sequence patterns: `<>`, `<x>`, `<a, b, c>`
- Converts to math mode: `<x>` → `$\langle x \rangle$`
- Carefully avoids operators: `<=>`, `<->`, `<`, `>`
- Processes sequences BEFORE operator conversion to avoid conflicts

**Impact**:
- Reduced garbled characters from ~1400 to 40
- All 773 tests continue passing
- No regressions introduced

**Files Modified**:
- `src/txt2tex/latex_gen.py`: Added sequence literal conversion to `_generate_paragraph()`

## Implementation Phases

### Phase 1: Fix Nested Quantifier Parser Bug
**Objective**: Enable inline parsing of nested quantifiers with multiple pipes

**Problem**: Parser fails on `mu x : T | forall y : U | P1 | P2` due to pipe ambiguity

**Affected**: 9 TEXT blocks (lines 762, 840, 863, 912, 930, 946, 995, 1003, 1069)

**Implementation**:
1. Add quantifier depth tracking to parser
2. Disambiguate pipe tokens based on context
3. Add tests for nested quantifiers
4. Convert 9 TEXT blocks to inline syntax
5. Verify PDF renders correctly

**Success Criteria**:
- Parser handles nested quantifiers
- 9 TEXT blocks eliminated
- All 599 tests pass
- Quality gates pass (type, lint, format)

**Estimated Time**: 4-6 hours

---

### Phase 2: Implement Pattern Matching Equations
**Objective**: Support standalone function definitions with pattern matching

**Problem**: Parser doesn't support equations like `f(<>) = 0` outside quantifiers

**Affected**: 22 TEXT blocks (lines 803-804, 894, 958-985, 1000-1014, 1121-1141)

**Examples**:
```
viewed(<>) = <>
viewed(<x> ^ s) = if x.3 = yes then <x> ^ viewed(s) else viewed(s)
```

**Implementation**:
1. Extend parser to recognize pattern matching in axdef predicates
2. Support multiple equations for same function
3. Generate proper LaTeX for pattern-matched definitions
4. Add tests for pattern matching
5. Convert 22 TEXT blocks to inline syntax
6. Verify PDF renders correctly

**Success Criteria**:
- Pattern matching equations parse correctly
- 22 TEXT blocks eliminated
- All tests pass
- Quality gates pass

**Estimated Time**: 6-8 hours

---

### Phase 3: Fix Axdef Syntax Issues
**Objective**: Enable proper axdef usage for all function definitions

**Problem**: Some features may be missing from axdef/schema parsing

**Affected**: 79 TEXT blocks in axdef/schema contexts

**Implementation**:
1. Identify specific syntax issues blocking axdef usage
2. Fix parser/generator for those issues
3. Convert TEXT blocks to proper axdef syntax
4. Verify PDF renders correctly

**Success Criteria**:
- All axdef syntax works
- Up to 79 TEXT blocks eliminated
- All tests pass
- Quality gates pass

**Estimated Time**: 4-6 hours

---

### Phase 4: Verify and Measure
**Objective**: Confirm all garbled characters eliminated

**Actions**:
1. Regenerate PDF: `hatch run convert examples/solutions.txt`
2. Count garbled characters: `pdftotext examples/solutions.pdf - | grep -o "[¿¡—]" | wc -l`
3. Result must be 0
4. If not 0, identify remaining issues and add Phase 5 to fix them

**Success Criteria**:
- Garbled character count = 0
- All TEXT blocks either eliminated or rendering correctly
- Release quality achieved

**Estimated Time**: 1 hour

---

## Total Timeline
**15-21 hours** across 4 phases

## Quality Gates (Apply to All Phases)
- `hatch run type` - zero errors
- `hatch run lint` - zero violations
- `hatch run format` - clean formatting
- `hatch run test` - all tests pass
- `hatch run test-cov` - coverage maintained

## Execution Strategy
- Start with Phase 1 (quickest win, validates approach)
- Continue with Phase 2 (major feature, highest TEXT reduction)
- Proceed to Phase 3 (remaining workarounds)
- Complete with Phase 4 (measurement)
- Commit after each phase passes quality gates
- If any phase encounters blockers, document and continue to next phase

## Risk Mitigation
- Test incrementally after each feature
- Keep baseline PDF for comparison
- Document any new blockers discovered
- If garbled characters remain after Phase 4, identify root cause and add additional phases until count = 0
