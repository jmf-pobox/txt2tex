# TODO: Centralize Fuzz-Mode Logic

Refactoring to centralize `self.use_fuzz` branches into helper methods.

## Overview

31 `self.use_fuzz` branches scattered across `latex_gen.py` for:
- Type names (N, Z, N1)
- Separators (bullet, colon, mid)
- Closure operators (+, *, ~)
- Binary operators (=>, <=>)
- Identifier formatting (mathit wrapping)
- Parentheses decisions
- Document structure

## Plan

### Phase 1: Simple separator helpers
- [ ] `_get_bullet_separator() -> str` - @ vs \bullet (5 usages)
- [ ] `_get_colon_separator() -> str` - : vs \colon (2 usages)
- [ ] `_get_mid_separator() -> str` - | vs \mid (2 usages)

### Phase 2: Type name helper
- [ ] `_get_type_latex(name: str) -> str` - N/Z/N1 mappings (3 usages)

### Phase 3: Closure operator helper
- [ ] `_get_closure_operator_latex(op: str) -> str` - +/*/~ (3 usages)

### Phase 4: Identifier formatting helper
- [ ] `_format_multiword_identifier(escaped: str) -> str` - mathit wrapping (3 usages)

### Phase 5: Binary operator helper
- [ ] `_map_binary_operator(op: str, base_latex: str) -> str` - =>/<=>/iff (1 block)

### Phase 6: Update CODE_REVIEW.md
- [ ] Document completed refactoring
- [ ] Remove from "Remaining Refactoring Opportunities"

## Workflow

1. Create feature branch `refactor/centralize-fuzz-mode`
2. For each phase:
   - Add helper method
   - Replace usages one at a time
   - Run `hatch run check` after each change
   - Commit when green
3. Update CODE_REVIEW.md
4. Merge to main, delete branch

## Status

- [ ] Branch created
- [ ] Phase 1 complete
- [ ] Phase 2 complete
- [ ] Phase 3 complete
- [ ] Phase 4 complete
- [ ] Phase 5 complete
- [ ] Phase 6 complete
- [ ] Merged to main

