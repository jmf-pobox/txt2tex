# Documentation Naming Standards

**Last Updated:** 2025-10-27  
**Purpose:** Define consistent naming conventions for all documentation files

---

## Naming Conventions

### Core Documentation (Primary User-Facing)

**Pattern:** `TITLE_CASE_WITH_UNDERSCORES.md`

**Examples:**
- `STATUS.md` - Implementation status and roadmap
- `DESIGN.md` - Architecture and design decisions  
- `USER_GUIDE.md` - Syntax reference
- `PROOF_SYNTAX.md` - Proof tree syntax reference
- `QA_PLAN.md` - Quality assurance procedures
- `QA_CHECKS.md` - QA checklist

**Rationale:** Short, clear, easy to reference. Underscores work reliably across all systems.

---

### Reference Documentation (Secondary)

**Pattern:** `UPPERCASE_WITH_UNDERSCORES.md`

**Examples:**
- `FUZZ_FEATURE_GAPS.md` - Missing fuzz features
- `FUZZ_VS_STD_LATEX.md` - Fuzz vs standard LaTeX differences
- ~~`MISSING_TESTS.md`~~ - Archived (all tests complete, see `docs/archive/MISSING_TESTS.md`)
- `IDE_SETUP.md` - IDE configuration guide

**Rationale:** Uppercase indicates reference/supplementary documentation. Easily distinguishable from core docs.

---

### Historical/Archived Documentation

**Pattern:** `NAME_TYPE.md` in `docs/archive/`

**Examples:**
- `archive/VALIDATION_REPORT.md` - Historical validation reports
- `archive/TEST_VALIDATION_REPORT.md` - Test validation reports
- `archive/FEATURE_COMPARISON.md` - Comparison reports
- `archive/DOCUMENTATION_REORGANIZATION_PLAN.md` - Completed planning docs

**Rationale:** Archive contains completed work, old plans, and historical records.

---

## Naming Standards Status

✅ **All naming standards implemented** (2025-10-27)

- ✅ `USER-GUIDE.md` → `USER_GUIDE.md` (renamed for consistency)
- ✅ All references updated across documentation
- ✅ Consistent naming for all active documentation files

---

## Guidelines for New Documentation

1. **No hyphens** in filenames - use underscores instead
2. **Core docs** use Title_Case_With_Underscores
3. **Reference docs** use UPPERCASE_WITH_UNDERSCORES
4. **Reports/Plans** go to `archive/` when work is complete
5. **Be descriptive** but concise (aim for 2-4 words)
6. **Consistent abbreviations** - use same abbreviation across files (e.g., `QA`, `USER_GUIDE`)

---

## Archive Policy

**Move to `docs/archive/` when:**
- Work is complete and no longer actively referenced
- Report/documentation is historical record
- Planning document for completed work
- Superseded by newer version

**Keep in `docs/` when:**
- Actively referenced
- Needed for ongoing work
- User-facing documentation
- Current reference material

---

## File Organization Summary

### Active Documentation (`docs/`)

```
docs/
├── STATUS.md              # Core: Implementation status
├── DESIGN.md              # Core: Architecture
├── USER_GUIDE.md         # Core: Syntax reference
├── PROOF_SYNTAX.md      # Core: Proof syntax
├── QA_PLAN.md           # Core: QA procedures
├── QA_CHECKS.md         # Core: QA checklist
├── FUZZ_FEATURE_GAPS.md # Reference: Feature gaps
├── FUZZ_VS_STD_LATEX.md # Reference: Fuzz differences
└── IDE_SETUP.md         # Reference: IDE configuration
```

### Archived Documentation (`docs/archive/`)

```
docs/archive/
├── VALIDATION_REPORT.md
├── TEST_VALIDATION_REPORT.md
├── FEATURE_COMPARISON.md
├── USER_GUIDE_TEST_MAPPING.md
├── DOCUMENTATION_REORGANIZATION_PLAN.md
└── [historical phase plans, etc.]
```

---

## References

For historical records of the naming standardization work, see:
- `docs/archive/NAMING_ANALYSIS.md` - Detailed analysis performed 2025-10-27 (historical record)
- `docs/archive/NAMING_IMPLEMENTATION_SUMMARY.md` - Implementation summary and verification (historical record)

---

## Summary

**Active Documentation:** 11 files in `docs/`  
**Archived Documentation:** 15 files in `docs/archive/` (includes NAMING_ANALYSIS.md, NAMING_IMPLEMENTATION_SUMMARY.md)  

**Transitory files archived (2025-10-27):**
- All validation reports moved to archive
- All planning documents moved to archive
- All one-time comparison/mapping documents moved to archive

**Current naming status:**
- ✅ Consistent naming for all active files (100%)
- ✅ All naming standards implemented (2025-10-27)

