# Exact Errors for Each Failing File

Run this to reproduce:
```bash
cd /Users/jfreeman/Coding/fuzz/txt2tex/sem/examples
touch **/*.txt && make -k 2>&1 | grep "Error building"
```

## Quick Error Extraction Commands

```bash
# Get error for a specific file
cd /Users/jfreeman/Coding/fuzz/txt2tex/sem
hatch run convert examples/PATH/FILE.txt 2>&1 | head -20

# Check line around error
sed -n 'LINENUM-2,LINENUM+2p' examples/PATH/FILE.txt
```

## Known Errors (from last run)

1. **12_advanced/if_then_else.txt**
   - Error: Line 117, column 38: Unexpected character: '/'
   - Line: `safeDiv(x, y) = if y /= 0 then x / y else 0`
   - Issue: Division operator `/` at column 38

2. **04_proof_trees/contradiction.txt**
   - Error: Line 28 - Expected identifier, got RANGE
   - Line 28: `...` (ellipsis placeholder)
   - Issue: Parser doesn't support `...` syntax

3. **04_proof_trees/advanced_proof_patterns.txt**
   - Error: Line 70 - Unexpected character '/'
   - Need to check line 70

4. **04_proof_trees/excluded_middle.txt**
   - Error: Line 224 - Unexpected character '"'
   - Need to check line 224

5. **11_text_blocks/pagebreak.txt**
   - Error: Line 85 - Expected identifier
   - Line 85 is in a PROOF block
   - Need to check proof syntax

6. **11_text_blocks/combined_directives.txt**
   - Error: Fuzz type mismatch
   - Line 288: `dom docs \subseteq ran perms`
   - Type error: `P (P Permission)` vs `P User`

7. **08_functions/composition_pipelines.txt**
   - Error: Line 119, column 12 - Expected ':' in declaration
   - Line 119: Free type inside gendef block
   - `Result_X ::= ok_X⟨X⟩ | error_X⟨seq Char⟩`

8. **06_definitions/gendef_advanced.txt**
   - Multiple fuzz type errors
   - Higher-order functions don't type check
   - See previous fuzz.log for details

9. **08_functions/higher_order_functions.txt**
   - Multiple fuzz type errors
   - map/filter/fold type issues
   - Boolean type not declared

## Files That May Just Work

These might pass with no changes (need to test):
- `02_predicate_logic/phase_a_test.txt`
- `02_predicate_logic/phase_a_simple.txt`
- `03_equality/mu_with_expression.txt`
- `03_equality/bullet_separator.txt`
- `12_advanced/subscripts_superscripts.txt`
- `12_advanced/generic_instantiation.txt`

## Testing Priority

1. Test "may just work" files first (quick wins)
2. Fix division operator issue (affects multiple files)
3. Fix proof syntax issues (contradiction, etc.)
4. Simplify higher-order function examples
5. Final full build verification
