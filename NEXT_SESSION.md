# Next Session: Fix Remaining 15 Example Files

## Goal
Make `cd examples && touch **/*.txt && make` succeed with 100% success rate.

## Progress So Far
**Fixed (3/18):**
- ✅ `10_schemas/zed_blocks.txt` - Removed duplicate declarations, added `given Char`, renamed `id` to `userId`
- ✅ `06_definitions/gendef_basic.txt` - Already working
- ✅ `08_functions/function_composition.txt` - Split comma-separated declarations

**Remaining (15/18):**
1. `12_advanced/if_then_else.txt` - CURRENTLY FAILING
2. `12_advanced/subscripts_superscripts.txt`
3. `12_advanced/generic_instantiation.txt`
4. `06_definitions/gendef_advanced.txt`
5. `08_functions/higher_order_functions.txt`
6. `08_functions/composition_pipelines.txt`
7. `11_text_blocks/combined_directives.txt`
8. `11_text_blocks/pagebreak.txt`
9. `04_proof_trees/contradiction.txt`
10. `04_proof_trees/advanced_proof_patterns.txt`
11. `04_proof_trees/excluded_middle.txt`
12. `02_predicate_logic/phase_a_test.txt`
13. `02_predicate_logic/phase_a_simple.txt`
14. `03_equality/mu_with_expression.txt`
15. `03_equality/bullet_separator.txt`

## Current Blocker: if_then_else.txt

**Error:** `Line 117, column 38: Unexpected character: '/'`

**Line 117 content:**
```
safeDiv(x, y) = if y /= 0 then x / y else 0
```

**Issue:** The `/` division operator at position 38 is not recognized by the parser.

**Need to determine:**
- What is the correct Z notation for division?
- Options: `div`, `÷`, `\div`, or something else?
- Check existing examples or documentation for division usage

## Key Patterns from Fixed Files

### Pattern 1: LaTeX Command Conflicts
**Problem:** Schema field names that are LaTeX commands cause errors
**Example:** `id : Type` generates `\id : Type` (LaTeX math command)
**Solution:** Rename to non-conflicting names: `id` → `userId`, `value` → `val`, etc.

### Pattern 2: Duplicate Type Declarations
**Problem:** `given Person` appears in multiple examples
**Solution:** Remove duplicate `given` statements, keep only first occurrence

### Pattern 3: Comma-Separated Declarations Not Supported
**Problem:** `f, g, h : N -> N` fails parsing
**Solution:** Split into individual lines:
```
f : N -> N
g : N -> N
h : N -> N
```

### Pattern 4: Relational Image Syntax
**Problem:** `enrolled~(| {c} |)` causes fuzz type errors
**Solution:** Simplify or use `(~enrolled)(| {c} |)` with extra parens

### Pattern 5: Char Type Not Declared
**Problem:** `seq Char` fails if `Char` not given
**Solution:** Add `given Char` at top of file

## Common Fuzz Type Errors

### Higher-Order Functions
Files like `higher_order_functions.txt` and `gendef_advanced.txt` have complex type issues:
- `map : (X -> Y) cross seq X -> seq Y` fails type checking
- Function types with cross products don't work as expected
- Nested function types are problematic

**Strategy:** Simplify or remove problematic higher-order function examples. Focus on examples that demonstrate the syntax without pushing fuzz type system limits.

### Boolean Type
- `B` type must be declared with `given B`
- Boolean literals `true` and `false` are not supported
- Use predicates instead: `x = y` not `equals(x, y) = true`

## Quick Wins (Likely Simple Fixes)

### phase_a_test.txt & phase_a_simple.txt
These were working before. Probably just need re-testing or minor syntax fixes.

### mu_with_expression.txt & bullet_separator.txt
These are specifically about mu quantifiers and bullet separators. Check if parser supports the syntax they're testing.

### contradiction.txt
Error: `Line 28 - Expected identifier, got RANGE`
Content: `...` (ellipsis placeholder)
**Fix:** Replace `...` with actual proof steps or remove the example

### pagebreak.txt
Error: `Line 85 - Expected identifier`
Line 85: `p [premise]`
**Fix:** Check if proof syntax is correct, may need adjustment

## Efficient Fixing Strategy

### Step 1: Run Quick Checks (5 min)
```bash
cd /Users/jfreeman/Coding/fuzz/txt2tex/sem
for f in phase_a_test phase_a_simple mu_with_expression bullet_separator; do
  hatch run convert examples/*/$f.txt 2>&1 | grep -E "(Success|Error)"
done
```

### Step 2: Fix Division Operator Issue (10 min)
- Search docs for correct division syntax
- Fix all occurrences in if_then_else.txt
- May affect other files

### Step 3: Batch Fix Higher-Order Functions (30 min)
Files: `gendef_advanced.txt`, `higher_order_functions.txt`, `composition_pipelines.txt`
- Remove or simplify map/filter/fold examples
- Keep only examples that pass fuzz type checking
- Document limitations in comments

### Step 4: Fix Proof Files (20 min)
Files: `contradiction.txt`, `advanced_proof_patterns.txt`, `excluded_middle.txt`
- Replace `...` with actual steps or remove
- Fix unexpected characters
- Ensure proof syntax matches parser expectations

### Step 5: Fix Remaining Files (20 min)
- `subscripts_superscripts.txt` - Check syntax
- `generic_instantiation.txt` - Likely type parameter issues
- `combined_directives.txt` - Type mismatch from before
- `pagebreak.txt` - Proof syntax issue

### Step 6: Final Build Verification (5 min)
```bash
cd examples && touch **/*.txt && make
```

## Critical Commands for Next Session

```bash
# Full build from scratch
cd /Users/jfreeman/Coding/fuzz/txt2tex/sem/examples
touch **/*.txt && make -k 2>&1 | grep "Error building"

# Test single file with fuzz
cd /Users/jfreeman/Coding/fuzz/txt2tex/sem
hatch run convert examples/PATH/FILE.txt --fuzz

# Quick syntax check (no fuzz)
hatch run convert examples/PATH/FILE.txt

# Check fuzz errors
cat examples/PATH/FILE.fuzz.log
```

## Success Criteria

✅ `cd examples && touch **/*.txt && make` completes with ZERO errors
✅ All .txt files generate .pdf outputs
✅ All examples pass fuzz type checking where applicable
✅ NO files moved to future/ directories

## Notes

- DO NOT move files to future/ - fix them properly
- If an example pushes fuzz limits, simplify the example, don't hide it
- The user created these files initially - I created the versions with errors
- 100% success is the only acceptable outcome
