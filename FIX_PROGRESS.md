# Fix Progress Tracker

## Goal
Make `cd examples && touch **/*.txt && make` succeed with 100% of files building.

## Files to Fix

### 10_schemas/zed_blocks.txt
- **Status**: IN PROGRESS
- **Error**: Multiple fuzz type errors
- **Issue**: Person multiply declared, Char not declared, relational image syntax error
- **Fix**: Remove duplicate Person declarations, add given Char, fix relational image
- **Changes Made**:
  - Converted all zed blocks with declarations to axdef
  - Removed abbreviations from zed blocks (not fully supported)
  - Simplified Example 10
  - CURRENT ISSUES:
    - Person declared in examples 3 and 8
    - Char not declared (examples 8)
    - Relational image syntax in example 7

### 12_advanced/if_then_else.pdf
- **Status**: PENDING
- **Error**: Unknown
- **Issue**: TBD

### 12_advanced/subscripts_superscripts.pdf
- **Status**: PENDING
- **Error**: Unknown
- **Issue**: TBD

### 12_advanced/generic_instantiation.pdf
- **Status**: PENDING
- **Error**: Unknown
- **Issue**: TBD

### 06_definitions/gendef_basic.pdf
- **Status**: PENDING
- **Error**: Unknown (was working before?)
- **Issue**: TBD

### 06_definitions/gendef_advanced.pdf
- **Status**: PENDING
- **Error**: Multiple fuzz type errors
- **Issue**: Complex higher-order functions, Boolean type issues

### 08_functions/function_composition.pdf
- **Status**: PENDING
- **Error**: Unknown (was fixed before?)
- **Issue**: TBD

### 08_functions/higher_order_functions.pdf
- **Status**: PENDING
- **Error**: Fuzz type errors with map/filter/fold
- **Issue**: Complex higher-order function types

### 08_functions/composition_pipelines.pdf
- **Status**: PENDING
- **Error**: Line 119 - Expected ':' in declaration
- **Issue**: Free type inside gendef

### 11_text_blocks/combined_directives.pdf
- **Status**: PENDING
- **Error**: Fuzz type mismatch
- **Issue**: Type error in Z notation

### 11_text_blocks/pagebreak.pdf
- **Status**: PENDING
- **Error**: Line 85 - Expected identifier
- **Issue**: Parser issue with PAGEBREAK directive

### 04_proof_trees/contradiction.pdf
- **Status**: PENDING
- **Error**: Line 28 - Expected identifier, got RANGE
- **Issue**: `...` placeholder not supported in proofs

### 04_proof_trees/advanced_proof_patterns.pdf
- **Status**: PENDING
- **Error**: Line 70 - Unexpected character '/'
- **Issue**: TBD

### 04_proof_trees/excluded_middle.pdf
- **Status**: PENDING
- **Error**: Line 224 - Unexpected character '"'
- **Issue**: TBD

### 02_predicate_logic/phase_a_test.pdf
- **Status**: PENDING
- **Error**: Unknown
- **Issue**: TBD

### 03_equality/mu_with_expression.pdf
- **Status**: PENDING
- **Error**: Unknown
- **Issue**: TBD

### 03_equality/bullet_separator.pdf
- **Status**: PENDING
- **Error**: Unknown
- **Issue**: TBD

## Notes

- Do NOT move files to future/ - fix them properly
- 100% success required
- Track all changes in this file

### 10_schemas/zed_blocks.txt - COMPLETE ✓
- Fixed all issues
- Changes: removed duplicate declarations, added given Char, renamed 'id' to 'userId' (LaTeX conflict), simplified relational constraints

