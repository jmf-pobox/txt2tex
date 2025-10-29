# Missing Tests List

**Date:** 2025-10-27  
**Last Updated:** 2025-10-27  
**Purpose:** Comprehensive list of features that need test coverage  
**Status:** ✅ **ALL TESTS CREATED** - No missing tests remaining

## Summary

**Total Missing Tests:** 0 feature categories ✅  
**Priority Breakdown:**
- ✅ COMPLETED: Citation syntax tests created and passing

---

## Missing Tests

### 1. Citation Syntax in TEXT Blocks (PRIORITY: MEDIUM) ✅ COMPLETED

**Feature Status:**
- ✅ **Documented** in USER-GUIDE.md (lines 70-82)
- ✅ **Implemented** in `src/txt2tex/latex_gen.py` (`_process_citations()` method, lines 1747-1778)
- ✅ **TESTED** - 14 comprehensive tests created and passing

**Feature Description:**
Citations in TEXT blocks using `[cite key]` syntax with optional locators.

**Documented Syntax:**
```
TEXT: The proof technique follows [cite simpson25a].
TEXT: This is discussed in [cite simpson25a slide 20].
TEXT: See the definition in [cite spivey92 p. 42].
TEXT: Multiple examples appear in [cite woodcock96 pp. 10-15].
```

**Expected LaTeX Output:**
- `[cite simpson25a]` → `\citep{simpson25a}`
- `[cite simpson25a slide 20]` → `\citep[slide 20]{simpson25a}`
- `[cite spivey92 p. 42]` → `\citep[p. 42]{spivey92}`
- `[cite woodcock96 pp. 10-15]` → `\citep[pp. 10-15]{woodcock96}`

**Implementation Location:**
- File: `src/txt2tex/latex_gen.py`
- Method: `_process_citations()` (lines 1747-1778)
- Called from: `_generate_paragraph()` (line 1339)
- Pattern: `r"\[cite\s+([a-zA-Z0-9_-]+)(?:\s+([^\]]+))?\]"`

**Suggested Test File:** `tests/test_text_formatting/test_citations.py`

**Test Cases Needed:**

```python
class TestCitationProcessing:
    """Tests for citation syntax processing in TEXT blocks."""

    def test_basic_citation(self) -> None:
        """Test basic citation without locator."""
        text = """TEXT: See [cite simpson25a] for details."""
        # Verify \citep{simpson25a} in output

    def test_citation_with_slide(self) -> None:
        """Test citation with slide locator."""
        text = """TEXT: See [cite simpson25a slide 20]."""
        # Verify \citep[slide 20]{simpson25a} in output

    def test_citation_with_page(self) -> None:
        """Test citation with page locator."""
        text = """TEXT: See [cite spivey92 p. 42]."""
        # Verify \citep[p. 42]{spivey92} in output

    def test_citation_with_page_range(self) -> None:
        """Test citation with page range locator."""
        text = """TEXT: See [cite woodcock96 pp. 10-15]."""
        # Verify \citep[pp. 10-15]{woodcock96} in output

    def test_citation_with_underscores_in_key(self) -> None:
        """Test citation key with underscores."""
        text = """TEXT: See [cite author_name_2025]."""
        # Verify \citep{author_name_2025} in output

    def test_citation_with_hyphens_in_key(self) -> None:
        """Test citation key with hyphens."""
        text = """TEXT: See [cite author-name-2025]."""
        # Verify \citep{author-name-2025} in output

    def test_multiple_citations_in_paragraph(self) -> None:
        """Test multiple citations in one paragraph."""
        text = """TEXT: See [cite simpson25a] and [cite spivey92 p. 42]."""
        # Verify both citations processed correctly

    def test_citation_not_in_text_block(self) -> None:
        """Test that citations are NOT processed outside TEXT blocks."""
        text = """PURETEXT: [cite simpson25a] should remain literal."""
        # Verify [cite simpson25a] appears literally (not converted)
```

**Implementation Notes:**
- Citation processing happens in `_process_citations()` which is called during paragraph generation
- The method uses regex to find and replace citation patterns
- Citations are only processed in TEXT blocks, not in PURETEXT or LATEX blocks
- The implementation supports any locator text after the citation key

**Why This Test Is Important:**
1. Feature is documented and actively used
2. Implementation exists but has no test coverage
3. Risk of regression if citation processing breaks
4. Complex regex pattern needs verification

**Estimated Effort:** 1-2 hours to create comprehensive test suite

---

## Test Coverage Statistics

**Current Status:**
- Features documented: ~100% (all major features in USER-GUIDE.md)
- Features implemented: ~100% (citation feature found implemented)
- Features tested: **100%** ✅ (all features now have test coverage)

**Gap Analysis:**
- ✅ **All gaps resolved:** Citation tests created and passing

**Action Items:**
1. ✅ Create `tests/test_text_formatting/test_citations.py` - COMPLETED
2. ✅ Add test cases listed above - COMPLETED (14 comprehensive tests)
3. ✅ Verify tests pass with existing implementation - COMPLETED (all 14 passing)
4. ✅ Update test coverage metrics - COMPLETED

**Test Results:**
- ✅ All 14 test cases passing
- ✅ Tests verify citation conversion in TEXT blocks
- ✅ Tests verify citations NOT processed in PURETEXT/LATEX blocks
- ✅ Tests verify various locator formats (page, slide, page ranges, complex)
- ✅ Tests verify citation keys with underscores, hyphens, numbers
- ✅ Tests verify multiple citations in same paragraph

---

## Additional Notes

### Verified Complete Coverage

The following feature categories have been verified to have comprehensive test coverage:
- ✅ Boolean operators (41 tests)
- ✅ Quantifiers (all variants)
- ✅ Mu operator (basic + expression part)
- ✅ Sets (86 tests)
- ✅ Relations (95 tests)
- ✅ Functions (comprehensive)
- ✅ Sequences (comprehensive)
- ✅ Z definitions (comprehensive)
- ✅ Proof trees (27 tests)
- ✅ Text blocks (including citations - 14 tests)
- ✅ Document structure

### Testing Methodology

For systematic validation:
1. Extract examples from USER-GUIDE.md
2. Find corresponding test files
3. Verify test functions exist
4. Run tests to confirm they pass
5. Document gaps in missing tests

**Result:** 100% coverage - all documented and implemented features now have test coverage.

**Test Count:** Increased from 999 to 1013 tests (14 new citation tests added)

