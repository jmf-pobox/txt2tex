# Migration Scripts: `and`/`or`/`not` → `land`/`lor`/`lnot`

## Overview

This directory contains LLM-powered scripts to migrate txt2tex input files from English keywords (`and`, `or`, `not`) to LaTeX-style keywords (`land`, `lor`, `lnot`).

**Key Point**: The lexer supports **both** syntaxes indefinitely, so this migration is optional but recommended for better alignment with LaTeX/Z notation standards.

---

## Scripts

### 1. `migrate_keywords.py` - LLM-Powered Migration Tool

Uses Anthropic's Claude API to intelligently distinguish between mathematical expressions and English prose.

**Setup**:
```bash
# Install required package
pip install anthropic

# Set API key
export ANTHROPIC_API_KEY="your-key-here"
```

**Usage**:
```bash
# Preview changes (dry-run)
python scripts/migrate_keywords.py examples/file.txt --dry-run

# Apply changes (with backup)
python scripts/migrate_keywords.py examples/file.txt --apply

# Custom confidence threshold
python scripts/migrate_keywords.py examples/file.txt --apply --threshold 0.8
```

**How it works**:
1. Analyzes each line with 3-line context window (prev, current, next)
2. For each occurrence of `and`/`or`/`not`:
   - Sends context to Claude API
   - Gets probability score: is this math or English?
   - If probability >= threshold (default 0.7), replaces with `land`/`lor`/`lnot`
3. Creates timestamped backup before modifying file
4. Logs all decisions with confidence scores

**Example Output**:
```
Line 5: p and q => p
  [REPLACE] pos=2 "and" → "land" (confidence=0.95)
    Reasoning: Appears in formula with logical operators
  MODIFIED: p land q => p

Line 10: TEXT: This is true and never false.
  [KEEP] pos=17 "and" → "land" (confidence=0.15)
    Reasoning: In TEXT block, surrounded by English prose
```

---

### 2. `rollback_migration.py` - Restore from Backups

Safely restore files if migration causes issues.

**Usage**:
```bash
# List all backups
python scripts/rollback_migration.py --list

# Restore all files from a specific date
python scripts/rollback_migration.py --date 2025-01-26

# Restore single file (finds most recent backup)
python scripts/rollback_migration.py --file examples/file.txt

# Dry-run mode
python scripts/rollback_migration.py --date 2025-01-26 --dry-run
```

**Backup Format**:
```
examples/file.txt                        # Original file (modified)
examples/file.txt.backup.20250126-143022 # Backup with timestamp
```

---

## Migration Workflow

### Quick Start (Single File)

```bash
# 1. Preview
python scripts/migrate_keywords.py examples/phase1.txt --dry-run

# 2. Review output, check confidence scores

# 3. Apply
python scripts/migrate_keywords.py examples/phase1.txt --apply

# 4. Test compilation
hatch run convert examples/phase1.txt

# 5. Compare PDFs visually
open examples/phase1.pdf
```

### Batch Migration

```bash
# Migrate all files in a directory
for file in examples/01_propositional_logic/*.txt; do
    echo "Processing: $file"
    python scripts/migrate_keywords.py "$file" --apply
    hatch run convert "$file" || echo "FAILED: $file"
done
```

### Quality Gates

After each file or batch:
```bash
# 1. Run tests
hatch run test

# 2. Rebuild examples
cd examples && make

# 3. Visual spot-check (random sample)
open examples/*/phase*.pdf
```

---

## Migration Statistics

**Files to migrate**: 173 .txt files
- examples/: 146 files
- tests/bugs/: 26 files
- hw/: 1 file

**Estimated effort**: 2-3 days
- Setup + testing: 4 hours
- Core examples (146 files): 12 hours
- Test files (26 files): 2 hours
- Homework (1 large file): 1 hour
- Quality validation: 3 hours

---

## Design Decisions

### Why LLM-based?

**Problem**: Simple regex can't distinguish:
```
TEXT: This is true and valid.        # English "and" - keep
p and q => p                          # Math "and" - replace
```

**Solution**: Use Claude's understanding of:
- Syntax patterns (formulas vs prose)
- Context (surrounding operators, block types)
- Semantics (mathematical vs natural language)

### Why Support Both Syntaxes?

1. **Backward compatibility**: Existing files continue to work
2. **Gradual migration**: Migrate at your own pace
3. **No breaking changes**: Tests, examples, documentation unchanged
4. **User choice**: Use whichever style you prefer

### Default Threshold: 0.7

After testing on sample files:
- 0.5: Too aggressive, replaces some English prose
- 0.7: **Balanced** - catches clear math, leaves ambiguous cases
- 0.9: Too conservative, misses some obvious math

You can adjust with `--threshold` flag.

---

## Troubleshooting

### API Rate Limits

If you hit rate limits:
```python
# Edit migrate_keywords.py, add delay:
import time
time.sleep(0.5)  # 500ms between API calls
```

### False Positives (Math → English)

If script keeps English word in formula:
```bash
# Lower threshold
python scripts/migrate_keywords.py file.txt --apply --threshold 0.5
```

### False Negatives (English → Math)

If script replaces English prose:
```bash
# Raise threshold
python scripts/migrate_keywords.py file.txt --apply --threshold 0.9

# Or manually restore from backup
python scripts/rollback_migration.py --file file.txt
```

### Migration Verification

```bash
# Check what changed
git diff examples/file.txt

# Check backup exists
ls -la examples/*.backup.*

# Compare PDFs
diff <(pdftotext examples/file.txt.backup.* -) \
     <(pdftotext examples/file.txt -)
```

---

## Example Test File

See `scripts/test_migration_sample.txt` for a file with both mathematical expressions and English prose to test the script.

**Test it**:
```bash
cd scripts
python migrate_keywords.py test_migration_sample.txt --dry-run
```

**Expected behavior**:
- Mathematical expressions: Replace
- TEXT blocks: Keep English prose
- TRUTH TABLE headers: Replace
- Justifications: Context-dependent

---

## Future Work

### Optional Deprecation (Future Release)

If we want to eventually phase out old syntax:

**Phase 1** (current): Support both, recommend new
**Phase 2** (optional): Add deprecation warnings
```python
if value == "and":
    warnings.warn("Use 'land' instead of 'and'", DeprecationWarning)
```

**Phase 3** (optional, breaking): Remove old keywords

---

## Questions?

See:
- `docs/development/MIGRATION_GUIDE.md` - Detailed guide
- `docs/development/RESERVED_WORDS.md` - Keyword reference
- `docs/guides/USER_GUIDE.md` - User syntax guide

Or run:
```bash
python scripts/migrate_keywords.py --help
python scripts/rollback_migration.py --help
```
