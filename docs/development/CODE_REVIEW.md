## Code Review: txt2tex Source Code Analysis

### Executive Summary

This review analyzes the `src/txt2tex` codebase for code quality issues beyond what automated tools (ruff, mypy) catch. The codebase demonstrates good type safety and follows PEP 8 conventions.

**Completed improvements (2025-11-27/28):**
- Exception handling: specific types replace broad `except Exception`
- Type dispatch: `@singledispatchmethod` replaces isinstance chains
- Documentation: Google-style docstrings on public methods, Phase comments replaced
- `_process_inline_math` decomposed into 11 pipeline stages (see below)
- Fuzz-mode logic centralized into helper methods (see below)
- Overflow warning system for Z notation blocks (axdef, schema, zed, gendef)
- Line break continuation syntax (`\`) for conditionals and after `=` operator
- Linting standards tightened: ruff (S, BLE, A, ARG, ERA, PIE, RET, RSE, PERF, PTH, ISC, FBT, C90, PT, SLF)
- Extracted `_parse_free_branch()` helper to reduce `_parse_syntax_block` complexity

**Acceptable as-is:**
- Lexer/parser complexity is domain-appropriate (tokenizers and parsers are inherently branchy)
- Large file sizes reflect cohesive modules, not random sprawl

### File Size and Organization

Current state (~11,800 lines total):
- `latex_gen.py` ≈ 5,044 lines
- `parser.py` ≈ 4,124 lines (reduced by refactoring)
- `lexer.py` ≈ 1,220 lines
- `ast_nodes.py` ≈ 900 lines
- `errors.py` ≈ 135 lines
- `cli.py` ≈ 120 lines
- `constants.py` ≈ 70 lines

File splitting is **not recommended** - these are cohesive modules where the size reflects domain complexity, not poor organization.

### Fuzz-Mode Helper Methods

The fuzz vs standard LaTeX differences are now centralized in helper methods (reduced from 31 scattered usages to 20, with 8 in helpers):

| Helper | Purpose |
|--------|---------|
| `_get_bullet_separator()` | @ (fuzz) vs \\bullet (standard) |
| `_get_colon_separator()` | : (fuzz) vs \\colon (standard) |
| `_get_mid_separator()` | \| (fuzz) vs \\mid (standard) |
| `_get_type_latex(name)` | N/Z/N1 → \\nat/\\num vs \\mathbb{} |
| `_get_closure_operator_latex(op, operand)` | +/*/~ closure formatting |
| `_format_multiword_identifier(name)` | Underscore escape ± \\mathit{} |
| `_map_binary_operator(op, base)` | =>/<=> fuzz-specific mappings |

Remaining `self.use_fuzz` usages are context-specific parentheses decisions and structural choices that don't benefit from further abstraction.

### Overflow Warning Infrastructure

The `LaTeXGenerator` includes an overflow detection system:

| Method | Purpose |
|--------|---------|
| `_emit_warning()` | Format and collect warning messages |
| `_check_overflow()` | Measure line lengths, trigger warnings |
| `emit_warnings()` | Output collected warnings to stderr |

CLI flags: `--no-warn-overflow`, `--overflow-threshold N` (default: 140)

### Complexity Notes

Cyclomatic complexity measures branches, not maintainability. High CC in lexers/parsers is expected.

**C90 Configuration:** `max-complexity = 30` with targeted `noqa: C901` for inherently complex functions.

| Method | CC | Grade | Status |
|--------|-----|-------|--------|
| `Lexer._scan_token` | 166 | F | Domain-appropriate (token dispatch) |
| `Lexer._scan_identifier` | 97 | F | Domain-appropriate (100+ keywords) |
| `Parser._parse_postfix` | 40 | E | Grammar-driven operator dispatch |
| `Parser._parse_syntax_block` | 30 | D | Refactored (was 36, extracted helper) |
| `LaTeXGenerator._has_line_breaks` | 37 | E | AST visitor across node types |
| `LaTeXGenerator._generate_proof_node_infer` | 37 | E | Natural deduction scenarios |
| `LaTeXGenerator._process_inline_math` | ~15 | C | Decomposed into 11 stages (was 69) |

**Refactoring applied (2025-11-28):**
- Extracted `_parse_free_branch()` helper method (~60 lines × 3 → 1 shared helper)
- Reduced `_parse_syntax_block` from E (36) to D (30), removed noqa comment

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

### Enabled Linting Rules (2025-11-28)

The following ruff rule sets were enabled after systematic review:

| Rule Set | Description | Per-File Ignores |
|----------|-------------|------------------|
| S | flake8-bandit (security) | S101 in tests (assert is idiomatic) |
| BLE | flake8-blind-except | None |
| A | flake8-builtins | None |
| ARG | flake8-unused-arguments | ARG002 in latex_gen.py, parser.py (visitor patterns) |
| ERA | eradicate (commented code) | None (uses noqa for doc examples) |
| PIE | flake8-pie | None |
| RET | flake8-return | None |
| RSE | flake8-raise | None |
| PERF | perflint | None |
| PTH | pathlib preference | None |
| ISC | implicit string concat | None |
| FBT | flake8-boolean-trap | None (API changed to keyword-only args) |
| C90 | mccabe complexity | max-complexity=30, noqa on 4 functions |
| PT | pytest style | None |
| SLF | private member access | SLF001 in tests (testing internals) |
| T20 | print detection | T20 in cli.py, tests |

### Deferred Linting Rules (TRY, PL)

The following rules are documented for future consideration. They were assessed during the November 2025 linting standards review but deferred due to high violation counts relative to value.

#### TRY (tryceratops) - Exception Handling

| Rule | Violations | Description | Example |
|------|------------|-------------|---------|
| **TRY003** | 103 | Raise vanilla args | `raise ParserError(f"Expected {x}")` should use custom exception subclasses |

**Why deferred**: Would require creating many custom exception subclasses (e.g., `ExpectedTokenError`, `UnexpectedCharError`) instead of using f-string messages with `ParserError`/`LexerError`. The current approach provides clear error messages without the overhead of many exception types.

**Future consideration**: If exception handling becomes more complex (e.g., programmatic error recovery), custom exceptions would add value.

#### PL (pylint) - Code Structure

| Rule | Violations | Description | Typical Locations |
|------|------------|-------------|-------------------|
| **PLR2004** | 157 | Magic value comparison | `if len(suffix) == 2`, `if depth > 10` |
| **PLR0912** | 25 | Too many branches | Parser dispatch methods, lexer token handling |
| **PLR0915** | 13 | Too many statements | Complex generation methods |
| **PLR0911** | 11 | Too many return statements | Multi-case dispatch methods |
| **PLR0913** | 1 | Too many arguments | `make_proof_node()` test helper |
| **PLR1714** | 1 | Repeated equality comparison | Could use `in` operator |
| **PLW2901** | 1 | Redefined loop name | Loop variable reused |

**PLR2004 (Magic Values)** - 157 violations

These are comparisons like:
```python
if len(suffix) == 2:  # PLR2004: magic value 2
if depth > 10:        # PLR2004: magic value 10
```

**Why deferred**: Many of these are domain-specific thresholds (indent levels, string lengths) where named constants would add verbosity without clarity. Some could benefit from constants (e.g., `MAX_NESTING_DEPTH`).

**Future consideration**: Create a `constants.py` section for thresholds that appear multiple times or have semantic meaning.

**PLR0912/PLR0915/PLR0911 (Structural Complexity)** - 49 violations

These overlap significantly with C90 (mccabe complexity). Functions flagged include:
- `_scan_token` - lexer main dispatch (inherently branchy)
- `_parse_document_item` - parser main dispatch
- `_generate_proof_node_infer` - complex proof tree rendering

**Why deferred**: These functions are complex by design (dispatch over many token/node types). Splitting would fragment cohesive logic. Already addressed via C90 with max-complexity=30 and targeted noqa comments.

**PLR1714 (Repeated Equality)** - 1 violation

```python
# Current:
if x == "a" or x == "b" or x == "c":
# Suggested:
if x in ("a", "b", "c"):
```

**Future consideration**: Low-hanging fruit, easy fix.

**PLW2901 (Redefined Loop Name)** - 1 violation

A loop variable is reused in nested context. Generally safe but can be confusing.

**Future consideration**: Easy fix, rename inner variable.

### Refactoring Guardrails

When making changes:
- Run `hatch run check` after every micro-change
- Small commits (1-5 files, <100 LOC)
- Structure-only changes with identical observable behavior
