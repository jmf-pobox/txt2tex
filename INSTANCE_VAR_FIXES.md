# Instance Variable Type Annotations - Complete ✅

## What Was Fixed

Added type annotations for instance variables in all core classes to fix pyright "partially unknown" errors.

### Classes Fixed

**Parser** (parser.py:137-143):
```python
tokens: list[Token]
pos: int
last_token_end_column: int
last_token_line: int
_parsing_schema_text: bool
_in_comprehension_body: bool
```

**LaTeXGenerator** (latex_gen.py:221-227):
```python
use_fuzz: bool
toc_parts: bool
parts_format: str
_in_equiv_block: bool
_first_part_in_solution: bool
_in_inline_part: bool
```

**Lexer** (lexer.py:29-34):
```python
text: str
pos: int
line: int
column: int
_in_solution_marker: bool
```

**Exception Classes**:
- ParserError.token: Token
- LexerError.line: int
- LexerError.column: int

## Results

✅ **MyPy**: Still passes (0 errors in 87 files)
✅ **Pyright**: 94 → 89 errors (5 fixed)

## Remaining Pyright Errors (89)

### Source Code (44 errors)
All in `latex_gen.py` - "partially unknown" types for list operations:
- Line 282-287: Document generation list appends
- Line 1680-1740: Schema formatting list operations
- Line 1994-2048: Proof tree list operations
- Line 2835-2838: More list operations
- Line 3535-3792: Proof node list operations

These require explicit type annotations on local variables where pyright can't infer list element types.

### Tests (45 errors)
All `reportPrivateUsage` - tests accessing protected methods:
- `_generate_paragraph` (26 occurrences)
- `_generate_identifier` (9 occurrences)
- `_find_balanced_braces` (6 occurrences)
- `_calculate_tree_depth` (4 occurrences)

Solutions:
1. Make test helper methods public (remove `_` prefix)
2. Suppress warnings in test files
3. Move test helpers to dedicated test utility class

## Commit

`7f32d36` fix: add instance variable type annotations for pyright
