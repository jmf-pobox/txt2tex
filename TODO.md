# TODO: Centralize Fuzz-Mode Logic

**Status: COMPLETE** ✅

Refactoring to centralize `self.use_fuzz` branches into helper methods.

## Summary

Reduced `self.use_fuzz` usages from 31 to 20 by centralizing common patterns into 7 helper methods.

## Completed Phases

### Phase 1: Separator helpers ✅
- `_get_bullet_separator()` - @ vs \bullet
- `_get_colon_separator()` - : vs \colon
- `_get_mid_separator()` - | vs \mid

### Phase 2: Type name helper ✅
- `_get_type_latex(name)` - N/Z/N1 mappings

### Phase 3: Closure operator helper ✅
- `_get_closure_operator_latex(op, operand)` - +/*/~

### Phase 4: Identifier formatting helper ✅
- `_format_multiword_identifier(name)` - mathit wrapping

### Phase 5: Binary operator helper ✅
- `_map_binary_operator(op, base_latex)` - =>/<=>/iff

### Phase 6: Documentation ✅
- CODE_REVIEW.md updated
- Ready for merge

## Remaining Usages (Acceptable)

12 remaining usages are context-specific:
- 8 in helper methods (the centralized logic)
- Parentheses decisions for # operator precedence
- Lambda/quantifier parenthesization
- mu operator special handling
- IF-THEN-ELSE formatting
- Schema predicate line breaks
- Document-level package selection

These don't benefit from further abstraction.

