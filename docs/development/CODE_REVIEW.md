## Code Review: txt2tex Source Code Analysis

### Executive Summary

This review analyzes the `src/txt2tex` codebase for code quality issues beyond what automated tools (ruff, mypy) catch. The codebase demonstrates good type safety and follows PEP 8 conventions.

**Completed improvements (2025-11-27):**
- Exception handling: specific types replace broad `except Exception`
- Type dispatch: `@singledispatchmethod` replaces isinstance chains
- Documentation: Google-style docstrings on public methods, Phase comments replaced
- `_process_inline_math` decomposed into 11 pipeline stages (see below)

**Remaining considerations:**
- Duplicated fuzz-mode logic could be centralized

**Acceptable as-is:**
- Lexer/parser complexity is domain-appropriate (tokenizers and parsers are inherently branchy)
- Large file sizes reflect cohesive modules, not random sprawl

### File Size and Organization

Current state (~12,000 lines total):
- `parser.py` ≈ 4,200 lines
- `latex_gen.py` ≈ 4,750 lines
- `lexer.py` ≈ 1,200 lines
- `ast_nodes.py` ≈ 900 lines
- `errors.py` ≈ 135 lines
- `constants.py` ≈ 70 lines

File splitting is **not recommended** - these are cohesive modules where the size reflects domain complexity, not poor organization.

### Remaining Refactoring Opportunities

#### 1. Duplicated Fuzz-Mode Logic

`self.use_fuzz` branches appear repeatedly (dozens of sites) for type names, operator choices, and parentheses formatting.

Potential improvement: centralize in helper methods (e.g., `_get_type_latex`, `_map_operator`).

### Complexity Notes

Cyclomatic complexity measures branches, not maintainability. High CC in lexers/parsers is expected:

| Method | CC | Status |
|--------|-----|--------|
| `Lexer._scan_token` | 166 | Domain-appropriate |
| `Lexer._scan_identifier` | 97 | Domain-appropriate |
| `Parser._parse_postfix` | 41 | Matches grammar |
| `LaTeXGenerator._process_inline_math` | ~15 | Decomposed into pipeline (was 69) |

### Inline Math Pipeline Architecture

The `_process_inline_math` method was decomposed from a monolithic 627-line function (CC 69) into 11 discrete pipeline stages:

| Stage | Method | Purpose |
|-------|--------|---------|
| -1.5 | `_process_manual_markup` | `[operator]` -> LaTeX symbols |
| -1 | `_process_logical_formulas` | `p => q`, `p <=> q` |
| -0.5 | `_process_parenthesized_logic` | `(p lor q)` |
| -0.3 | `_process_standalone_keywords` | `lor`, `land`, `lnot`, `elem` |
| 0 | `_process_superscripts` | `x^2`, `a_i^2` |
| 0.5 | `_process_relational_image` | `R(\| S \|)` |
| 1 | `_process_set_expressions` | `{ x : N \| x > 0 }` |
| 2 | `_process_quantifiers` | `forall`, `exists`, `mu` |
| 2.5 | `_process_type_declarations` | `x : T -> U` |
| 2.75 | `_process_function_applications` | `f_name x <= 5` |
| 3 | `_process_simple_expressions` | `x > 1`, `f +-> g` |

Each stage follows the pattern: `def _process_X(self, text: str) -> str`. The main method orchestrates them:

```python
def _process_inline_math(self, text: str) -> str:
    result = text
    result = self._process_manual_markup(result)
    result = self._process_logical_formulas(result)
    # ... remaining 9 stages
    return result
```

**Benefits:**
- Each stage is testable in isolation
- Clear separation of concerns
- Easy to add/modify individual patterns
- Reduced cognitive load per function

### Code Quality Strengths

- Strong type annotations with mypy strict mode
- Frozen dataclass AST nodes (immutability)
- Clear pipeline: lexer → parser → generator
- Context-aware error formatting with source lines and hints
- Google-style docstrings on public methods
- Consistent naming following PEP 8

### Suppression Comments (All Legitimate)

5 `# noqa: RUF001/RUF003` comments for Unicode `×` character handling - these are legitimate since the codebase explicitly supports both ASCII `cross` and Unicode `×` as equivalent inputs.

### Refactoring Guardrails

When making changes:
- Run `hatch run check` after every micro-change
- Small commits (1-5 files, <100 LOC)
- Structure-only changes with identical observable behavior
