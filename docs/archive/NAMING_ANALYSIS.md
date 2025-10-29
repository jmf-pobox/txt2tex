# Documentation File Naming Analysis

**Date:** 2025-10-27  
**Purpose:** Review docs/*.md naming conventions and identify transitory files

---

## Current Naming Patterns

### Pattern 1: UPPERCASE_WITH_UNDERSCORES
- `FUZZ_FEATURE_GAPS.md` - Reference documentation
- `FUZZ_VS_STD_LATEX.md` - Reference documentation
- `USER_GUIDE_TEST_MAPPING.md` - Validation report

### Pattern 2: Title Case
- `STATUS.md` - Core documentation
- `DESIGN.md` - Core documentation
- ~~`MISSING_TESTS.md`~~ - Archived (all tests complete)

### Pattern 3: Title-Case-With-Hyphens
- ~~`USER-GUIDE.md`~~ - Renamed to `USER_GUIDE.md` (2025-10-27)
- `DOCUMENTATION_REORGANIZATION_PLAN.md` - Planning document (inconsistent - underscores and hyphens)

### Pattern 4: Title Case With Spaces (in titles)
- `PROOF_SYNTAX.md` - Reference documentation
- `QA_PLAN.md` - Process documentation
- `QA_CHECKS.md` - Process documentation

---

## Recommended Naming Convention

### Rule 1: Core Documentation (Primary user-facing)
**Pattern:** Title Case (no separators)
- `STATUS.md` ✅
- `DESIGN.md` ✅  
- `USER-GUIDE.md` → Should be `USER_GUIDE.md` for consistency (hyphens problematic in some contexts)

### Rule 2: Reference Documentation (Secondary)
**Pattern:** UPPERCASE_WITH_UNDERSCORES
- `FUZZ_FEATURE_GAPS.md` ✅
- `FUZZ_VS_STD_LATEX.md` ✅
- `PROOF_SYNTAX.md` ✅
- `QA_PLAN.md` ✅
- `QA_CHECKS.md` ✅
- `MISSING_TESTS.md` → Should be `MISSING_TESTS.md` ✅ (already correct)

### Rule 3: Reports (Historical/Completed Work)
**Pattern:** UPPERCASE_WITH_UNDERSCORES + _REPORT suffix
- Archive or rename to clearly indicate status

### Rule 4: Setup/Configuration
**Pattern:** UPPERCASE_WITH_UNDERSCORES
- `IDE_SETUP.md` ✅

---

## Consistency Issues Found

1. ✅ **USER-GUIDE.md** → **USER_GUIDE.md** (COMPLETED 2025-10-27)
   - Renamed: `USER-GUIDE.md` → `USER_GUIDE.md`
   - Consistent with `PROOF_SYNTAX.md`, `QA_PLAN.md`
   - **Impact:** Hyphens can cause issues in some file systems and markdown linkers

2. **DOCUMENTATION_REORGANIZATION_PLAN.md** - Mixed naming
   - Has both underscore and looks like planning doc
   - Should be archived

---

## Transitory Files Analysis

### Files Used During Validation (Can Archive/Remove)

1. **VALIDATION_REPORT.md** ❌ ARCHIVE
   - Purpose: Early validation before reorganization
   - Status: Superseded by TEST_VALIDATION_REPORT.md
   - Recommendation: Archive (historical record)

2. **DOCUMENTATION_REORGANIZATION_PLAN.md** ❌ ARCHIVE
   - Purpose: Planning document for file reorganization
   - Status: Work complete, plan no longer needed
   - Recommendation: Archive (historical record)

3. **FEATURE_COMPARISON.md** ⚠️ DECISION NEEDED
   - Purpose: One-time comparison of STATUS/DESIGN/USER_GUIDE
   - Status: Completed, findings incorporated into docs
   - Recommendation: Archive (useful record but not active reference)

4. **TEST_VALIDATION_REPORT.md** ⚠️ KEEP OR ARCHIVE
   - Purpose: Comprehensive test-based validation report
   - Status: Completed validation
   - Value: Could be useful for future validation cycles
   - Recommendation: Keep if planning future validation cycles, archive if one-time

5. **USER_GUIDE_TEST_MAPPING.md** ❌ ARCHIVE
   - Purpose: One-time mapping of USER_GUIDE examples to tests
   - Status: Completed, work done
   - Recommendation: Archive (findings incorporated)

### Active Reference Files (Keep)

- `STATUS.md` ✅
- `DESIGN.md` ✅
- `USER_GUIDE.md` ✅ (renamed 2025-10-27)
- `FUZZ_FEATURE_GAPS.md` ✅
- `FUZZ_VS_STD_LATEX.md` ✅
- `PROOF_SYNTAX.md` ✅
- `QA_PLAN.md` ✅
- `QA_CHECKS.md` ✅
- ~~`MISSING_TESTS.md`~~ - Archived ✅
- `IDE_SETUP.md` ✅

---

## Recommended Actions

### Immediate: Archive Transitory Files

```bash
# Move to archive/
docs/VALIDATION_REPORT.md → docs/archive/VALIDATION_REPORT.md
docs/DOCUMENTATION_REORGANIZATION_PLAN.md → docs/archive/DOCUMENTATION_REORGANIZATION_PLAN.md
docs/FEATURE_COMPARISON.md → docs/archive/FEATURE_COMPARISON.md
docs/USER_GUIDE_TEST_MAPPING.md → docs/archive/USER_GUIDE_TEST_MAPPING.md
docs/TEST_VALIDATION_REPORT.md → docs/archive/TEST_VALIDATION_REPORT.md
```

### Optional: Fix Naming Consistency

1. **Rename USER-GUIDE.md → USER_GUIDE.md**
   - Update all references (README.md, CLAUDE.md, STATUS.md, tests/README.md)
   - Breaks external links if any exist

2. **Decision: Keep or archive TEST_VALIDATION_REPORT.md?**
   - If keeping: Move to docs/archive/
   - If archiving: Same as above

---

## Future Naming Guidelines

**For new documentation:**

1. **Core documentation** (user-facing): `TITLE_CITLE_CASE.md` with underscores
2. **Reference docs** (secondary): `UPPERCASE_WITH_UNDERSCORES.md`
3. **Reports** (historical): `NAME_REPORT.md` in archive/
4. **Plans** (transitory): `NAME_PLAN.md` in archive/
5. **No hyphens** in filenames (causes issues in some contexts)

---

## Decisions Made

1. ✅ **Archive transitory files:** COMPLETED
   - All validation and planning documents moved to `docs/archive/`
   
2. ✅ **Rename USER-GUIDE.md:** COMPLETED (2025-10-27)
   - Renamed to `USER_GUIDE.md` for consistency
   - All references updated across documentation

3. ✅ **TEST_VALIDATION_REPORT.md:** ARCHIVED
   - Moved to `docs/archive/` along with other transitory files
   - Historical record maintained for future reference

---

## Files Archived (2025-10-27)

The following files were moved to `docs/archive/`:
- `VALIDATION_REPORT.md`
- `DOCUMENTATION_REORGANIZATION_PLAN.md`
- `FEATURE_COMPARISON.md`
- `USER_GUIDE_TEST_MAPPING.md`
- `TEST_VALIDATION_REPORT.md`

**Rationale:** All were transitory files used during documentation reorganization and validation. Their work is complete and findings have been incorporated into active documentation.

