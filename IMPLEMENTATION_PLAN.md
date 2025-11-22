# Implementation Plan: Missing Parser Features

**Created**: 2025-01-22
**Status**: Ready for Implementation
**Goal**: Enable all 17 failing example files to compile successfully

---

## Executive Summary

This plan addresses 5 categories of missing features in the txt2tex parser:

1. **Proof Annotations** - Documentation only (no code changes)
2. **seq(T) Type Syntax** - LaTeX generation fix
3. **Extended Part Labels** - Lexer enhancement
4. **Ellipsis in Proofs** - New token support
5. **Top-Level Case Analysis** - Parser structural change

**Risk Assessment**:
- Low Risk: Features 1-3 (localized changes, documentation)
- Medium Risk: Feature 4 (new token type)
- Higher Risk: Feature 5 (AST structural change)

---

## Current Failing Files

Based on `make` output, these 17 files currently fail:

```
12_advanced/if_then_else.pdf
12_advanced/subscripts_superscripts.pdf
12_advanced/generic_instantiation.pdf
06_definitions/gendef_basic.pdf
06_definitions/gendef_advanced.pdf
08_functions/function_composition.pdf
08_functions/higher_order_functions.pdf
08_functions/composition_pipelines.pdf
11_text_blocks/combined_directives.pdf
11_text_blocks/pagebreak.pdf
04_proof_trees/contradiction.pdf
04_proof_trees/advanced_proof_patterns.pdf
04_proof_trees/excluded_middle.pdf
02_predicate_logic/phase_a_test.pdf
03_equality/mu_with_expression.pdf
03_equality/bullet_separator.pdf
```

**Note**: Several files regressed during debugging. Need to verify which are parser issues vs. my incorrect "TEXT:" prefix fixes.

---

## Feature 1: Proof Annotations (Documentation Only)

### Status
✅ **PARSER ALREADY SUPPORTS THIS** - No code changes needed!

### Background

The parser treats proof justifications as free-form text between `[` and `]`:

```python
# File: src/txt2tex/parser.py, lines 3565-3586
if self._match(TokenType.LBRACKET):
    just_parts: list[str] = []
    while not self._match(TokenType.RBRACKET):
        just_parts.append(self._current().value)
        self._advance()
    justification = self._smart_join_justification(just_parts)
```

### Currently Documented Annotations

From `docs/PROOF_SYNTAX.md` lines 82-91:
- `[assumption]`
- `[and elim]`, `[and intro]`
- `[or elim]`, `[or intro]`
- `[=> intro from N]`, `[=> elim]`
- `[premise]`

### Missing Annotations Used in Examples

These appear in `examples/04_proof_trees/*.txt` but are not documented:

1. `[not intro from N]` - Negation introduction, discharging assumption N
2. `[not elim]` - Negation elimination
3. `[false elim]` - Ex falso quodlibet (from false, derive anything)
4. `[contradiction]` or `[contradiction with X]` - Deriving false from p and not p
5. `[LEM]` - Law of Excluded Middle axiom (p or not p)
6. `[identity]` - Trivial identity step (p proves p)
7. `[double negation elim]` - Classical logic: not not p implies p
8. `[derived]`, `[from X]`, `[known fact]` - Informal justifications

### Implementation

**File**: `docs/PROOF_SYNTAX.md`
**Lines**: 82-91
**Change Type**: Documentation addition

**Action**: Add section listing all supported annotations:

```markdown
### 7. Justifications

Common natural deduction rules:
- `[assumption]` - marks assumptions
- `[premise]` - given fact

**Logical operators:**
- `[and elim]`, `[and elim left]`, `[and elim right]` - and elimination
- `[and intro]` - and introduction
- `[or elim]` - or elimination
- `[or intro]`, `[or intro left]`, `[or intro right]` - or introduction
- `[=> intro from N]` - implication introduction, discharging assumption [N]
- `[=> elim]` - implication elimination (modus ponens)
- `[not intro from N]` - negation introduction, discharging assumption [N]
- `[not elim]` - negation elimination
- `[false elim]` - ex falso quodlibet (from false, derive anything)
- `[double negation elim]` - classical: not not p => p

**Derived rules:**
- `[contradiction]` - deriving false from p and not p
- `[LEM]` - Law of Excluded Middle (p or not p axiom)
- `[identity]` - trivial identity (p proves p)

**Informal annotations:**
- `[from above]` - reference to earlier step
- `[from case]` - reference to case hypothesis
- `[derived]` - derived result
- `[known fact]` - external fact

Note: Justifications are free-form text. Any text in `[brackets]` is accepted.
```

**Testing**: Verify examples compile:
```bash
hatch run convert examples/04_proof_trees/contradiction.txt
hatch run convert examples/04_proof_trees/excluded_middle.txt
```

---

## Feature 2: seq(T) Type Syntax in LaTeX Generation

### Problem

Files use both `seq(T)` and `seq[T]` syntax:
- `seq(Entry)` - function application syntax
- `seq[N]` - generic instantiation syntax

Both parse correctly but generate incorrect LaTeX:
- `seq(Entry)` → renders as `seq(Entry)` instead of `\seq Entry`
- `seq[N]` → renders as `seq[N]` instead of `\seq N`

### Current Parsing

**Lexer**: `seq` is an IDENTIFIER, not a keyword

**Parser** handles both:
- `seq(T)` → `FunctionApp(function=Identifier("seq"), args=[T])`
- `seq[T]` → `GenericInstantiation(base=Identifier("seq"), type_params=[T])`

### LaTeX Generation Issue

**File**: `src/txt2tex/latex_gen.py`

Need to find methods:
```python
def _generate_function_app(self, node: FunctionApp) -> str:
    """Generate LaTeX for function application."""
    # Currently: seq(N) → "seq(N)"
    # Should be: seq(N) → "\seq N"

def _generate_generic_instantiation(self, node: GenericInstantiation) -> str:
    """Generate LaTeX for generic type instantiation."""
    # Currently: seq[N] → "seq[N]"
    # Should be: seq[N] → "\seq N"
```

### Implementation

**Step 1**: Find exact line numbers:
```bash
grep -n "def _generate_function_app" src/txt2tex/latex_gen.py
grep -n "def _generate_generic_instantiation" src/txt2tex/latex_gen.py
```

**Step 2**: Modify `_generate_function_app`:

```python
def _generate_function_app(self, node: FunctionApp) -> str:
    """Generate LaTeX for function application."""
    func_name = ""

    # Check if function is an identifier
    if isinstance(node.function, Identifier):
        func_name = node.function.name

        # Special case: seq(T), seq1(T), bag(T) should render as \seq T
        if func_name in ("seq", "seq1", "bag") and len(node.args) == 1:
            arg = self._generate_expr(node.args[0])
            return f"\\{func_name} {arg}"

        # Special case: iseq(T) for infinite sequences
        if func_name == "iseq" and len(node.args) == 1:
            arg = self._generate_expr(node.args[0])
            return f"\\iseq {arg}"

    # Regular function application: f(x, y)
    func = self._generate_expr(node.function)
    args = ", ".join(self._generate_expr(arg) for arg in node.args)
    return f"{func}({args})"
```

**Step 3**: Modify `_generate_generic_instantiation`:

```python
def _generate_generic_instantiation(self, node: GenericInstantiation) -> str:
    """Generate LaTeX for generic type instantiation."""
    base_name = ""

    # Check if base is an identifier
    if isinstance(node.base, Identifier):
        base_name = node.base.name

        # Special case: seq[T], seq1[T], bag[T] should render as \seq T
        if base_name in ("seq", "seq1", "bag") and len(node.type_params) == 1:
            param = self._generate_expr(node.type_params[0])
            return f"\\{base_name} {param}"

        # Special case: P[T] for power sets
        if base_name == "P" and len(node.type_params) == 1:
            param = self._generate_expr(node.type_params[0])
            return f"\\power {param}"

    # Regular generic instantiation: Container[N]
    base = self._generate_expr(node.base)
    params = ", ".join(self._generate_expr(p) for p in node.type_params)
    return f"{base}[{params}]"
```

### Testing

Create test file `tests/test_latex_gen_seq.py`:

```python
def test_seq_function_syntax():
    """Test seq(T) renders as \seq T"""
    input_text = "axdef\n  s : seq(N)\nwhere\n  true\nend"
    # Parse and generate LaTeX
    # Assert: contains "\seq N" not "seq(N)"

def test_seq_bracket_syntax():
    """Test seq[T] renders as \seq T"""
    input_text = "axdef\n  s : seq[N]\nwhere\n  true\nend"
    # Parse and generate LaTeX
    # Assert: contains "\seq N" not "seq[N]"
```

Verify examples compile:
```bash
hatch run convert examples/02_predicate_logic/phase_a_test.txt
hatch run convert examples/09_sequences/pattern_matching.txt
```

---

## Feature 3: Extended Part Labels

### Current Support

**File**: `src/txt2tex/lexer.py`, lines 151-163

Currently supports: `(a)`, `(b)`, ..., `(j)` (single lowercase letters, limited to a-j)

### Enhancement Needed

Support:
- All lowercase letters: `(a)` through `(z)`
- Multi-letter labels: `(aa)`, `(ab)`, ..., `(zz)`
- Roman numerals: `(i)`, `(ii)`, `(iii)`, `(iv)`, ..., `(x)`

### Implementation

**File**: `src/txt2tex/lexer.py`
**Lines**: 151-163
**Change Type**: Modify token recognition logic

**Before**:
```python
# Part label: (a), (b), (c), etc. - restrict to a-j for homework parts
# Phase 11b: Only match at start of line to avoid function app conflict
next_char = self._peek_char()
if (
    char == "("
    and "a" <= next_char <= "j"
    and self._peek_char(2) == ")"
    and start_column == 1
):
    self._advance()  # consume '('
    label = self._advance()  # consume letter
    self._advance()  # consume ')'
    return Token(TokenType.PART_LABEL, f"({label})", start_line, start_column)
```

**After**:
```python
# Part label: (a), (b), ..., (z), (aa), (ab), etc.
# Phase 11b: Only match at start of line to avoid function app conflict
if char == "(" and start_column == 1:
    # Look ahead to match part label pattern: (letters)
    temp_pos = self.pos + 1
    label_chars: list[str] = []

    # Collect consecutive lowercase letters
    while (temp_pos < len(self.text) and
           self.text[temp_pos].islower()):
        label_chars.append(self.text[temp_pos])
        temp_pos += 1

    # Check if followed by closing paren and we have at least one letter
    if (label_chars and
        temp_pos < len(self.text) and
        self.text[temp_pos] == ")"):
        # Valid part label - consume it
        self._advance()  # consume '('
        for _ in label_chars:
            self._advance()
        self._advance()  # consume ')'
        label = "".join(label_chars)
        return Token(TokenType.PART_LABEL, f"({label})", start_line, start_column)
```

**Notes**:
- Roman numerals like `(ii)` will be recognized as letter sequence "ii"
- This is acceptable since parser extracts content between parens
- No parser changes needed - `_parse_part()` already handles any string

### Testing

Create test cases:
```python
def test_single_letter_labels():
    """Test (a) through (z)"""
    for letter in "abcdefghijklmnopqrstuvwxyz":
        input_text = f"({letter}) Test content"
        # Assert: Parses as PART_LABEL token

def test_multi_letter_labels():
    """Test (aa), (ab), (xyz)"""
    for label in ["aa", "ab", "xyz"]:
        input_text = f"({label}) Test content"
        # Assert: Parses as PART_LABEL token

def test_roman_numerals():
    """Test (i), (ii), (iii), (iv)"""
    for roman in ["i", "ii", "iii", "iv", "v"]:
        input_text = f"({roman}) Test content"
        # Assert: Parses as PART_LABEL token

def test_not_at_start_of_line():
    """Test that (a) mid-line is not a label"""
    input_text = "  (a) test"  # Not at column 1
    # Assert: Parses as LPAREN + identifier + RPAREN
```

---

## Feature 4: Ellipsis Support in Proofs

### Current Status

**NOT IMPLEMENTED** - Parser does not recognize `...` as valid syntax.

### Problem

Files like `contradiction.txt` use ellipsis to indicate omitted steps:

```
PROOF:
  not P [assumption 1]
  ...
  Q [from not P]
```

This currently causes: `Line 28, column 3: Expected identifier, got RANGE` (because `..` is range operator)

### Design Decision Needed

**Option 1: Skip ellipsis (treat as comment)**
- Simplest implementation
- Matches semantic intent ("steps not shown")
- Lexer consumes `...` and returns `None`

**Option 2: Explicit ellipsis nodes**
- Creates AST node for ellipsis
- LaTeX can render as `\ldots` or `\vdots`
- More visible in output

**Recommendation**: Option 1 (skip) for simplicity. Ellipsis means "I'm not showing these steps" so skipping is semantically correct.

### Implementation (Option 1: Skip)

**File**: `src/txt2tex/lexer.py`
**Location**: Before line 238 (before `..` range check)
**Change Type**: Add special case for three dots

**Code**:
```python
# Ellipsis marker: ... (skip in proofs for "steps omitted")
# Must check BEFORE range operator .. check
if char == "." and self._peek_char() == "." and self._peek_char(2) == ".":
    self._advance()  # consume first '.'
    self._advance()  # consume second '.'
    self._advance()  # consume third '.'
    # Skip to next line
    self._skip_whitespace()
    return None  # Skip ellipsis, continue scanning
```

**Important**: This must come **before** the range operator check at line ~238:
```python
# Range operator: 1 .. 10
if char == "." and self._peek_char() == ".":
    ...
```

### Implementation (Option 2: Explicit Node)

If we want visible ellipsis in proofs:

**Step 1**: Add token type in `src/txt2tex/tokens.py`:
```python
ELLIPSIS = auto()  # ... (omitted proof steps)
```

**Step 2**: Modify lexer to return token:
```python
if char == "." and self._peek_char() == "." and self._peek_char(2) == ".":
    self._advance()
    self._advance()
    self._advance()
    return Token(TokenType.ELLIPSIS, "...", start_line, start_column)
```

**Step 3**: Add AST node in `src/txt2tex/ast_nodes.py`:
```python
@dataclass(frozen=True)
class EllipsisNode(ASTNode):
    """Ellipsis marker (...) for omitted proof steps."""
    pass
```

**Step 4**: Handle in parser (`src/txt2tex/parser.py`, proof parsing section):
```python
# In _parse_proof_node or similar, around line 3590
if self._match(TokenType.ELLIPSIS):
    ellipsis_token = self._advance()
    # Create placeholder proof node
    ellipsis_node = ProofNode(
        expression=Identifier(name="...", line=ellipsis_token.line, column=ellipsis_token.column),
        justification="steps omitted",
        label=None,
        is_assumption=False,
        is_sibling=False,
        children=[],
        indent_level=current_indent,
        line=ellipsis_token.line,
        column=ellipsis_token.column,
    )
    children.append(ellipsis_node)
    self._skip_newlines()
    continue
```

**Step 5**: LaTeX generation in `src/txt2tex/latex_gen.py`:
```python
# When rendering proof node with "..." expression
if isinstance(node.expression, Identifier) and node.expression.name == "...":
    return "\\vdots"  # Vertical dots for omitted steps
```

### Testing

Create test file `tests/test_ellipsis.py`:

```python
def test_ellipsis_in_proof():
    """Test that ... is accepted in proofs"""
    input_text = """
PROOF:
  p [premise]
  ...
  q [conclusion]
"""
    # Assert: Parses without error

def test_ellipsis_not_range():
    """Test that ... doesn't conflict with .. range"""
    input_text = "x : 1 .. 10"  # Two dots
    # Assert: Parses as range

    input_text2 = "..."  # Three dots
    # Assert: Parses as ellipsis (or skips)
```

Verify examples:
```bash
git checkout HEAD -- examples/04_proof_trees/contradiction.txt
hatch run convert examples/04_proof_trees/contradiction.txt
```

---

## Feature 5: Top-Level Case Analysis in Proofs

### Current Limitation

Case analysis only works when indented under a proof step:

**Currently supported:**
```
PROOF:
conclusion [or elim]
  case p:
    step1
  case q:
    step2
```

**NOT supported:**
```
PROOF:
  case p:
    conclusion1
  case q:
    conclusion2
  final [or elim]
```

### Problem Files

- `examples/04_proof_trees/contradiction.txt` - Line 167: `CASE p:`
- `examples/04_proof_trees/excluded_middle.txt` - Line 38: `CASE p:`
- `examples/04_proof_trees/advanced_proof_patterns.txt` - Multiple top-level cases

### Current Implementation

**File**: `src/txt2tex/parser.py`
**Method**: `_parse_proof_tree`, lines 3507-3520

```python
def _parse_proof_tree(self) -> ProofTree:
    """Parse proof tree with Path C syntax (conclusion with supporting proof)."""
    start_token = self._advance()  # Consume 'PROOF:'
    self._skip_newlines()

    if self._at_end() or self._is_structural_token():
        raise ParserError("Expected proof node after PROOF:", self._current())

    # Parse the conclusion node (first top-level node)
    conclusion = self._parse_proof_node(base_indent=0, parent_indent=None)

    return ProofTree(
        conclusion=conclusion, line=start_token.line, column=start_token.column
    )
```

**Constraint**: `_parse_proof_node` expects a statement (expression), not a `case` keyword.

### AST Structure

```python
@dataclass(frozen=True)
class ProofTree(ASTNode):
    conclusion: ProofNode  # Single root node

@dataclass(frozen=True)
class ProofNode(ASTNode):
    expression: Expr
    children: list[ProofNode | CaseAnalysis]
    # ...

@dataclass(frozen=True)
class CaseAnalysis(ASTNode):
    case_expr: Expr  # The thing we're case-analyzing on (p, q, etc.)
    children: list[ProofNode]
    # ...
```

**Problem**: `ProofTree` requires a single `conclusion` node, but top-level cases don't have a conclusion until the end.

### Design Options

**Option 1: Synthetic Conclusion Node**
- Create a dummy conclusion that wraps the case analysis
- Maintains `ProofTree` structure
- LaTeX generation can skip rendering the dummy node

**Option 2: Extend ProofTree**
- Allow `ProofTree.conclusion` to be optional
- Add `ProofTree.cases: list[CaseAnalysis]`
- More accurate AST but requires changes to LaTeX generator

**Recommendation**: Option 1 (synthetic node) - minimal changes, maintains existing structure.

### Implementation (Option 1)

**File**: `src/txt2tex/parser.py`
**Method**: `_parse_proof_tree`, lines 3507-3520
**Change Type**: Modify logic to detect and handle top-level cases

**Modified Code**:
```python
def _parse_proof_tree(self) -> ProofTree:
    """Parse proof tree with Path C syntax (conclusion with supporting proof)."""
    start_token = self._advance()  # Consume 'PROOF:'
    self._skip_newlines()

    if self._at_end() or self._is_structural_token():
        raise ParserError("Expected proof node after PROOF:", self._current())

    # Check if first item is a case keyword (top-level case analysis)
    if self._match(TokenType.IDENTIFIER) and self._current().value == "case":
        # Parse all top-level cases
        cases: list[CaseAnalysis] = []

        while (not self._at_end() and
               not self._is_structural_token() and
               self._match(TokenType.IDENTIFIER) and
               self._current().value == "case"):
            case_analysis = self._parse_case_analysis(
                base_indent=0, parent_indent=None
            )
            cases.append(case_analysis)
            self._skip_newlines()

        # Check if there's a final conclusion after the cases
        final_conclusion_expr: Expr | None = None
        final_justification: str | None = None

        if not self._at_end() and not self._is_structural_token():
            # Parse potential final conclusion (e.g., "q [or elim]")
            final_conclusion_node = self._parse_proof_node(
                base_indent=0, parent_indent=None
            )
            final_conclusion_expr = final_conclusion_node.expression
            final_justification = final_conclusion_node.justification

        # Create synthetic conclusion node to wrap the cases
        # Use the final conclusion if present, otherwise placeholder
        if final_conclusion_expr is None:
            final_conclusion_expr = Identifier(
                name="[case_analysis]",
                line=start_token.line,
                column=start_token.column
            )
            final_justification = "case analysis"

        conclusion = ProofNode(
            expression=final_conclusion_expr,
            justification=final_justification,
            label=None,
            is_assumption=False,
            is_sibling=False,
            children=cases,
            indent_level=0,
            line=start_token.line,
            column=start_token.column,
        )
    else:
        # Standard proof: parse the conclusion node
        conclusion = self._parse_proof_node(base_indent=0, parent_indent=None)

    return ProofTree(
        conclusion=conclusion, line=start_token.line, column=start_token.column
    )
```

**Also modify**: `_parse_case_analysis` to accept `parent_indent=None` for top-level cases.

### LaTeX Generation Changes

**File**: `src/txt2tex/latex_gen.py`

Need to handle synthetic conclusion nodes specially:

```python
def _generate_proof_node(self, node: ProofNode, indent_level: int) -> str:
    """Generate LaTeX for a proof node."""

    # Check for synthetic top-level case analysis node
    if (isinstance(node.expression, Identifier) and
        node.expression.name == "[case_analysis]" and
        node.justification == "case analysis"):
        # Don't render the synthetic node itself, just its children
        lines = []
        for child in node.children:
            if isinstance(child, CaseAnalysis):
                lines.append(self._generate_case_analysis(child, indent_level))
            else:
                lines.append(self._generate_proof_node(child, indent_level))
        return "\n".join(lines)

    # Regular proof node rendering
    # ... existing code ...
```

### Testing

Create test file `tests/test_top_level_cases.py`:

```python
def test_top_level_case_analysis():
    """Test case analysis at proof root"""
    input_text = """
PROOF:
  case p:
    q [from p]
  case not p:
    q [from not p]
  q [or elim]
"""
    # Assert: Parses without error
    # Assert: AST has synthetic conclusion wrapping two cases

def test_top_level_cases_no_final_conclusion():
    """Test cases without explicit final step"""
    input_text = """
PROOF:
  case p:
    p [identity]
  case not p:
    p [from contradiction]
"""
    # Assert: Parses without error
    # Assert: Synthetic conclusion created
```

Verify examples:
```bash
git checkout HEAD -- examples/04_proof_trees/contradiction.txt
git checkout HEAD -- examples/04_proof_trees/excluded_middle.txt
hatch run convert examples/04_proof_trees/contradiction.txt
hatch run convert examples/04_proof_trees/excluded_middle.txt
```

---

## Implementation Phases

### Phase 1: Documentation & Low-Risk Fixes

**Duration**: 30 minutes
**Risk**: Low
**Files**: 2 files

1. ✅ Update `docs/PROOF_SYNTAX.md` - Add missing annotations
2. ✅ Modify `latex_gen.py` - Fix seq(T)/seq[T] rendering
3. ✅ Run tests: `hatch run type && hatch run lint && hatch run test`

**Success Criteria**:
- Documentation is complete
- seq(T) renders as `\seq T` in LaTeX
- All existing tests pass

### Phase 2: Lexer Enhancements

**Duration**: 1 hour
**Risk**: Medium
**Files**: 1 file + tests

4. ✅ Extend part labels in `lexer.py`
5. ✅ Add ellipsis support in `lexer.py`
6. ✅ Create test cases for new lexer features
7. ✅ Run quality checks: `hatch run check`

**Success Criteria**:
- Part labels (a)-(z), (aa)-(zz) work
- Ellipsis `...` is handled (skipped or parsed)
- No regressions in existing functionality

### Phase 3: Parser Structural Change

**Duration**: 2 hours
**Risk**: Higher
**Files**: 2 files (parser + latex_gen) + tests

8. ✅ Modify `_parse_proof_tree` for top-level cases
9. ✅ Update `_parse_case_analysis` to accept `parent_indent=None`
10. ✅ Modify LaTeX generation for synthetic nodes
11. ✅ Create comprehensive tests
12. ✅ Run full test suite: `hatch run test-cov`

**Success Criteria**:
- Top-level CASE statements parse correctly
- LaTeX output is correct
- All proof examples compile
- Test coverage maintained

### Phase 4: Validation & Cleanup

**Duration**: 1 hour
**Risk**: Low

13. ✅ Revert all TEXT: prefix hacks in example files
14. ✅ Restore original file content from git
15. ✅ Run full make: `cd examples && make`
16. ✅ Verify all 17 files compile successfully
17. ✅ Update `docs/STATUS.md` with results
18. ✅ Create git commit with micro-commit strategy

**Success Criteria**:
- `cd examples && make` succeeds with zero errors
- All .txt files generate .pdf outputs
- No TEXT: prefixes remain in examples
- Git history is clean with descriptive commits

---

## Rollback Plan

If any phase fails:

### Phase 1 Rollback
```bash
git checkout HEAD -- docs/PROOF_SYNTAX.md src/txt2tex/latex_gen.py
```

### Phase 2 Rollback
```bash
git checkout HEAD -- src/txt2tex/lexer.py tests/test_lexer.py
```

### Phase 3 Rollback
```bash
git checkout HEAD -- src/txt2tex/parser.py src/txt2tex/latex_gen.py tests/test_proof*.py
```

### Complete Rollback
```bash
git reset --hard HEAD
```

---

## Testing Strategy

### Unit Tests

Create/modify these test files:
1. `tests/test_latex_gen_seq.py` - seq(T) rendering
2. `tests/test_lexer_labels.py` - Extended part labels
3. `tests/test_lexer_ellipsis.py` - Ellipsis tokens
4. `tests/test_proof_cases.py` - Top-level case analysis

### Integration Tests

Run full conversion on example files:
```bash
# After each phase
cd /Users/jfreeman/Coding/fuzz/txt2tex/sem
for f in examples/04_proof_trees/*.txt; do
  echo "Testing $f"
  hatch run convert "$f" || echo "FAILED: $f"
done
```

### Regression Tests

Ensure no existing functionality breaks:
```bash
hatch run test              # All unit tests
hatch run test-cov          # With coverage
cd examples && make         # All examples
```

---

## Success Metrics

### Quantitative
- ✅ 0 errors in `make` (currently 17 errors)
- ✅ 100% of proof tree examples compile
- ✅ Test coverage maintained or improved
- ✅ 0 lint or type errors

### Qualitative
- ✅ No TEXT: prefixes in example files
- ✅ Proof syntax matches documentation
- ✅ LaTeX output is correct and professional
- ✅ Code is maintainable and well-documented

---

## Risk Mitigation

### Risk: Breaking existing proof parsing
**Mitigation**:
- Run full test suite after each change
- Test with existing proof examples
- Keep changes minimal and localized

### Risk: LaTeX generation issues
**Mitigation**:
- Test LaTeX output visually by compiling PDFs
- Verify with fuzz type checker
- Compare with working examples

### Risk: Parser ambiguities
**Mitigation**:
- Add comprehensive test cases
- Document edge cases
- Use failing examples as test oracle

---

## Post-Implementation

### Documentation Updates

1. Update `docs/STATUS.md` with completion status
2. Update `docs/PROOF_SYNTAX.md` with new features
3. Update `docs/USER_GUIDE.md` if needed
4. Create `docs/IMPLEMENTATION_NOTES.md` with lessons learned

### Git Commits

Use micro-commit strategy:
```bash
git add docs/PROOF_SYNTAX.md
git commit -m "docs: add missing proof annotation documentation"

git add src/txt2tex/latex_gen.py
git commit -m "fix: render seq(T) and seq[T] as LaTeX \seq command"

git add src/txt2tex/lexer.py tests/test_lexer.py
git commit -m "feat: extend part labels to support (a)-(z) and (aa)-(zz)"

# ... etc
```

### Issue Tracking

Create GitHub issues for future enhancements:
1. Support for multi-line case labels
2. Better error messages for proof syntax
3. Proof tree visualization
4. Automatic proof checking

---

## Appendix: File Locations Reference

| Feature | File | Lines | Type |
|---------|------|-------|------|
| Proof annotations | `docs/PROOF_SYNTAX.md` | 82-91 | Doc |
| seq(T) function app | `latex_gen.py` | TBD | Code |
| seq[T] generic inst | `latex_gen.py` | TBD | Code |
| Part labels | `lexer.py` | 151-163 | Code |
| Ellipsis | `lexer.py` | ~238 | Code |
| Top-level cases | `parser.py` | 3507-3520 | Code |
| Case analysis method | `parser.py` | 3629+ | Code |

---

## Questions for User

Before proceeding with implementation:

1. **Ellipsis**: Skip (Option 1) or render as visible dots (Option 2)?
2. **seq syntax**: Standardize on seq[T] or support both seq(T) and seq[T]?
3. **Priority**: Which phase should I start with? (Recommend: Phase 1 → Phase 2 → Phase 3)
4. **Validation**: Should I revert TEXT: prefixes first or after all features are implemented?

---

**Status**: Ready for user approval
**Next Step**: User reviews plan and approves implementation
