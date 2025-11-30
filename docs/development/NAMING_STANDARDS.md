# Documentation Naming Standards

**Last Updated:** 2025-11-30  
**Purpose:** Define consistent naming conventions for all documentation files

---

## Naming Conventions

### Core Documentation

**Pattern:** `UPPERCASE_WITH_UNDERSCORES.md`

**Examples:**
- `DESIGN.md` - Architecture and design decisions  
- `USER_GUIDE.md` - Syntax reference
- `PROOF_SYNTAX.md` - Proof tree syntax reference
- `FUZZ_VS_STD_LATEX.md` - Fuzz vs standard LaTeX differences

**Rationale:** Short, clear, easy to reference. Underscores work reliably across all systems.

---

### Tutorials

**Pattern:** `NN_lowercase_with_underscores.md`

**Examples:**
- `00_getting_started.md`
- `01_propositional_logic.md`
- `02_predicate_logic.md`

**Rationale:** Numbered prefix ensures correct ordering. Lowercase for readability.

---

## Guidelines for New Documentation

1. **No hyphens** in filenames - use underscores instead
2. **Reference docs** use `UPPERCASE_WITH_UNDERSCORES.md`
3. **Tutorials** use `NN_lowercase_with_underscores.md`
4. **Be descriptive** but concise (aim for 2-4 words)
5. **Consistent abbreviations** - use same abbreviation across files

---

## Current File Organization

```
docs/
├── DESIGN.md                    # Architecture and design decisions
├── development/                 # Developer documentation
│   ├── CODE_REVIEW.md
│   ├── IDE_SETUP.md
│   ├── NAMING_STANDARDS.md
│   ├── RESERVED_WORDS.md
│   └── TOOL-PyPI.md
├── guides/                      # Reference guides
│   ├── FUZZ_VS_STD_LATEX.md
│   ├── MISSING_FEATURES.md
│   ├── PROOF_SYNTAX.md
│   └── USER_GUIDE.md
└── tutorials/                   # Step-by-step tutorials
    ├── 00_getting_started.md
    ├── 01_propositional_logic.md
    ├── 02_predicate_logic.md
    ├── 03_sets_and_types.md
    ├── 04_proof_trees.md
    ├── 05_z_definitions.md
    ├── 06_relations.md
    ├── 07_functions.md
    ├── 08_sequences.md
    ├── 09_schemas.md
    ├── 10_advanced.md
    └── README.md
```

---

## Summary

**Total Documentation Files:** 18 files across 4 locations

| Location | Count | Purpose |
|----------|-------|---------|
| `docs/` | 1 | Core architecture |
| `docs/development/` | 5 | Developer guides |
| `docs/guides/` | 4 | Reference documentation |
| `docs/tutorials/` | 12 | Step-by-step tutorials |
