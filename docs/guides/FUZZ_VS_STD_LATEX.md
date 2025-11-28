# Fuzz vs Standard LaTeX: Key Differences

**Purpose**: This document captures important differences between fuzz (Mike Spivey's Z notation typesetter) and standard LaTeX that affect txt2tex code generation.

**Last Updated**: 2025-11-27

---

## Quick Reference

| Feature | Standard LaTeX | Fuzz | Impact on txt2tex |
|---------|----------------|------|-------------------|
| Natural numbers | `\mathbb{N}` | `\nat` | Context-aware generation |
| Integers | `\mathbb{Z}` | `\num` | Context-aware generation |
| Implication (`=>`) | `\Rightarrow` | `\implies` | Use `\implies` in fuzz mode |
| Equivalence (`<=>`) | `\Leftrightarrow` | `\iff` (predicates) or `\Leftrightarrow` (EQUIV) | Context-aware in fuzz mode |
| Semicolon (`;`) | Can be operator | **NOT** for composition | Removed from relational operators |
| Multiple declarations | Any format | **Requires** line breaks (`\\`) | Generator adds `\\` between declarations |
| Operator precedence | Standard | **Different** for `#`, etc. | Add parens around function app in fuzz mode |

---

## Type Names

### Natural Numbers
**Standard LaTeX**: `\mathbb{N}` (blackboard bold)
**Fuzz**: `\nat` (special fuzz command)

**txt2tex behavior**:
```python
if name == "N":
    return r"\nat" if self.use_fuzz else r"\mathbb{N}"
```

### Integers
**Standard LaTeX**: `\mathbb{Z}` (blackboard bold)
**Fuzz**: `\num` (special fuzz command)

**txt2tex behavior**:
```python
if name == "Z":
    return r"\num" if self.use_fuzz else r"\mathbb{Z}"
```

**Reference**: `latex_gen.py` - identifier generation

---

## Logical Operators

### Implication (`=>`)

**Standard LaTeX**: `\Rightarrow` (arrow symbol)
**Fuzz**: `\implies` (logical connective)

**txt2tex behavior**:
```python
# In _generate_binary_op():
if self.use_fuzz and node.operator == "=>":
    op_latex = r"\implies"
```

**Why**: Fuzz uses `\implies` for logical implication to match mathematical logic conventions, distinguishing it from meta-level reasoning.

### Equivalence (`<=>`)

**Standard LaTeX**: `\Leftrightarrow` (double arrow symbol)
**Fuzz**: Context-dependent
- **Predicates** (schemas, axioms, proofs): `\iff` (logical "if and only if")
- **EQUIV blocks**: `\Leftrightarrow` (equational reasoning)

**txt2tex behavior**:
```python
# In _generate_binary_op():
if self.use_fuzz:
    if node.operator == "<=>" and not self._in_equiv_block:
        op_latex = r"\iff"
    # Otherwise uses \Leftrightarrow
```

**Why**: Fuzz distinguishes between:
- `\iff` - logical connective in predicates (same level as `\land`, `\lor`, `\implies`)
- `\Leftrightarrow` - meta-level equivalence for equational reasoning (EQUIV chains)

This matches the fuzz package conventions where predicates use logical connectives (`\implies`, `\iff`) while equational reasoning uses arrows (`\Rightarrow`, `\Leftrightarrow`).

**Reference**: `latex_gen.py` - binary operator generation

---

## Operator Precedence Differences

### Unary Operators Before Function Application

**Issue discovered**: In fuzz, `# s(i)` is interpreted as `(# s)(i)` not `#(s(i))`

**Standard LaTeX/Z**: `#` binds tightly, `# s(i)` means "cardinality of s(i)"
**Fuzz**: `#` binds less tightly than application, `# s(i)` means "apply (# s) to i"

**txt2tex solution**: Add parentheses around function applications when they're operands of unary operators in fuzz mode:

```python
# In _generate_unary() for fuzz mode:
if self.use_fuzz and isinstance(node.operand, FunctionApp):
    operand = f"({operand})"  # Generates: # (s(i))
```

**Reference**: `latex_gen.py` - unary operator generation

**Example**:
```
Input:  # s(i)
Fuzz:   # (s(i))    ← Parentheses required
LaTeX:  \# s(i)     ← No parentheses needed
```

### Cardinality with Function-Like Operators

**Issue**: In fuzz, `#` also binds less tightly than function-like unary operators (e.g., `dom`, `ran`, `head`, `squash`)

**Standard LaTeX/Z**: `# dom R` might be ambiguous
**Fuzz**: `# dom R` is parsed as `(# dom) R`, not `# (dom R)`

**txt2tex solution**: Add parentheses around function-like operators when they're operands of `#` in fuzz mode:

```python
# Function-like operators that need parentheses with #
function_like_ops = {
    "dom", "ran", "inv", "id",
    "head", "tail", "last", "front", "rev",
    "P", "P1", "F", "F1", "bigcup", "bigcap",
}
if self.use_fuzz and node.operator == "#" and isinstance(node.operand, UnaryOp):
    if node.operand.operator in function_like_ops:
        operand = f"({operand})"  # Generates: # (squash f)
```

**Reference**: `latex_gen.py` - cardinality with function-like operators

**Example**:
```
Input:  # head s
Fuzz:   # (\head s)     ← Parentheses required
LaTeX:  \# \head s      ← No parentheses needed
```

---

## Semicolons in Declarations

### Multiple Declarations Must Use Line Breaks

**Issue discovered**: When declarations are joined with semicolons on one line, fuzz doesn't render them on separate lines in the PDF.

**Standard LaTeX**:
```latex
\begin{gendef}[X]
  f: X \fun X; g: X \fun X    % On one line - might work
\end{gendef}
```

**Fuzz requirement**:
```latex
\begin{gendef}[X]
  f: X \fun X \\              % Line break required
  g: X \fun X                 % Last one has no \\
\end{gendef}
```

**txt2tex solution**: Always generate line breaks between declarations:

```python
for i, decl in enumerate(node.declarations):
    # ... generate declaration ...
    if i < len(node.declarations) - 1:
        lines.append(f"  {var_latex}: {type_latex} \\\\")  # Add \\
    else:
        lines.append(f"  {var_latex}: {type_latex}")      # Last one: no \\
```

**Reference**: `latex_gen.py` - gendef, axdef, schema generation

**PDF Result**:
```
[X ]
f :X →X        ← Each declaration
g :X →X        ← on its own line
```

---

## Semicolons as Operators

### Relational Composition

**Standard Z Notation**: Both `;` and `\circ` can represent relational composition
**Fuzz**: Does NOT support `;` for relational composition
**Alternative**: Use `o9` or `comp`

**txt2tex decision**:
- **REMOVED** semicolon from relational operators in parser
- Semicolon is now **exclusively** used for declaration separators
- Users must use `o9` or `comp` for relational composition

**Reference**: `parser.py` - operator handling

**Reason**: Ambiguity between:
- `R ; S` (relational composition - now unsupported)
- `f : X -> X; g : X -> X` (declaration separator - supported)

**User syntax**:
```
✅ CORRECT: R o9 S    → R ∘ S
✅ CORRECT: R comp S  → R ∘ S
❌ WRONG:   R ; S     → Parse error (semicolon reserved for declarations)
```

---

## Nested Sequence Types

### Parentheses Required for Nested Special Functions

**Issue**: Fuzz requires parentheses around nested sequence/bag/power operators

**Example**:
```
Input:  seq1 seq X
Fuzz:   \seq_1 (\seq X)    ← Parentheses required
LaTeX:  \seq_1 \seq X      ← Might work without
```

**txt2tex solution**: Detect nested special functions and add parentheses:

```python
# Pattern: (seq1(seq))(X) needs to become: \seq_1 (\seq X)
if (
    isinstance(inner_func, Identifier)
    and inner_func.name in special_functions
    and len(node.function.args) == 1
    and isinstance(node.function.args[0], Identifier)
    and node.function.args[0].name in special_functions
):
    # Add parentheses around inner function
    return f"{outer_latex} ({inner_latex} {args_latex})"
```

**Reference**: `latex_gen.py` - nested function handling

---

## Tuple Projection

### Named Field Projection: Supported ✅

**Fuzz grammar**: `Expression-4 . Var-Name` where `Var-Name ::= Ident`

Fuzz DOES support tuple projection when using **named fields** (identifiers):

```
tuple.fieldname    ✅ Supported - Var-Name is an identifier
record.status      ✅ Supported - Var-Name is an identifier
person.name        ✅ Supported - Var-Name is an identifier
```

**Example with schemas**:
```z
Entry == [name: NAME, course: Course, grade: N]

% Access fields by name:
e.name      ← Works in fuzz
e.course    ← Works in fuzz
e.grade     ← Works in fuzz
```

### Numeric Positional Projection: NOT Supported ❌

**Problem**: Fuzz grammar requires `Var-Name` which must be an **identifier**, not a number.

Fuzz does NOT support numeric positional projection:

```
e.1        ❌ NOT supported - "1" is a Number, not Var-Name
e.2        ❌ NOT supported - "2" is a Number, not Var-Name
e.3        ❌ NOT supported - "3" is a Number, not Var-Name
(r(i)).1   ❌ NOT supported - violates grammar
```

**Standard Z Mathematical Toolkit** provides projection functions only for pairs:
- `first : X × Y → X` where `first(x,y) = x`
- `second : X × Y → Y` where `second(x,y) = y`

No standard functions exist for 3-tuples, 4-tuples, or n-tuples.

### txt2tex Behavior

**txt2tex generates** the numeric projection syntax when requested, but:
- Fuzz validation will report syntax errors
- Solutions using numeric projections must be wrapped in TEXT blocks

**User workarounds**:
1. Use schemas with named fields instead of anonymous tuples
2. Define custom projection functions for n-tuples
3. Wrap numeric projections in TEXT blocks (renders as plain text, no type checking)

**Example**: When using `e.1`, `(r(i1)).1`, `(r(i1)).3`, wrap in TEXT blocks to avoid fuzz type errors.

**See also**: [MISSING_FEATURES.md](MISSING_FEATURES.md) for missing features

---

## Identifiers with Underscores

### NOT Supported by Fuzz

**Standard Z/LaTeX**: `cumulative_total`, `not_yet_viewed` work fine
**Fuzz**: Does **NOT** recognize underscores in identifiers

**Recommended alternatives for fuzz-compatible code**:
1. **camelCase with initial capital** (for schemas/types): `CumulativeTotal`, `NotYetViewed`
2. **camelCase with initial lowercase** (for variables): `cumulativeTotal`, `notYetViewed`
3. **Single word** (when possible): `total`, `viewed`

**txt2tex behavior**: Generates underscores in LaTeX, but fuzz type checking will fail

**Note**: See [MISSING_FEATURES.md](MISSING_FEATURES.md) for known limitations

---

## Mu Expressions (Definite Description)

### Syntax Requirements

**Issue discovered**: Mu expressions require special handling in fuzz mode.

**Standard LaTeX**: May work with various formats
**Fuzz requirement**: Parentheses around the **entire mu expression**

**txt2tex solution**: In fuzz mode, wrap entire mu expression in parentheses:

```python
# For mu x : N | predicate:
if node.quantifier == "mu" and self.use_fuzz:
    return f"({quant_latex} {vars} : {domain} | {body})"
```

**Reference**: `latex_gen.py` - mu expression generation

**Examples**:

Input:
```
mu n : N | n > 0
```

Fuzz mode generates:
```latex
(\mu n : \nat | n > 0)
```

With expression part:
```
mu n : N | n elem S . f(n)
```

Generates:
```latex
(\mu n : \nat | n \in S @ f(n))
```

**Key points**:
- Parentheses wrap the ENTIRE mu expression, not just the schema text
- Use `|` for predicate separator (not `@`)
- Use `@` only when there's an expression part after the predicate
- The error "Opening parenthesis expected at symbol `\mu`" means fuzz is expecting `(` before `\mu`

---

## Key Lessons for Future Development

### 1. Always Test with Fuzz

When implementing new features, test both modes:
```bash
# Fuzz mode (default - type checking enabled)
hatch run convert file.txt

# zed-* packages mode (no fuzz type checking)
hatch run convert file.txt --zed
```

**Important**: Create minimal test cases in /tmp first before modifying production code.

### 2. Check Operator Precedence

When adding new operators, verify fuzz precedence matches expectations. If not, add parentheses in fuzz mode.

### 3. Line Breaks in Boxes

Fuzz boxes (gendef, axdef, schema) require explicit `\\` line breaks between declarations. Don't rely on semicolons alone.

### 4. Limited Operator Set

Fuzz supports a specific set of Z notation operators. Check the fuzz manual before assuming an operator is supported.

### 5. Type Checking is Strict

Fuzz type checking is much stricter than LaTeX. Code that "looks right" in PDF may fail fuzz validation.

### 6. Test Minimal Examples First

When debugging fuzz errors, create minimal test cases with raw LaTeX to isolate the issue before modifying the generator.

---

## Zed Blocks (Unboxed Paragraphs)

### Purpose

Zed blocks (`\begin{zed}...\end{zed}`) are unboxed Z notation paragraphs. Unlike `axdef` and `schema`, they don't render with a visual box in the PDF.

### Common Uses

1. **Standalone predicates**: Global constraints that don't need visual boxing
2. **Type declarations**: Basic type introductions
3. **Quantified statements**: Universal or existential claims
4. **Abbreviations**: Simple definitions without declarations

### Syntax Difference

**txt2tex input:**
```
zed
  forall x : N | x >= 0
end
```

**LaTeX output:**
```latex
\begin{zed}
  \forall x : \nat \mid x \geq 0
\end{zed}
```

### Fuzz Mode Considerations

- Content is typechecked by fuzz like any other Z notation
- Type annotations (e.g., `N` → `\nat`) apply normally
- Quantifiers must follow fuzz syntax requirements
- No special fuzz-specific handling needed for the environment itself

### When to Use zed vs axdef

**Use `zed`** when:
- Content is a single predicate/expression
- No visual box needed in PDF
- No separate declaration section needed

**Use `axdef`** when:
- Need declaration and where sections
- Want visual box in PDF
- Defining global constants with types

---

## Testing Strategy

### Dual-Mode Testing

For critical features, create tests for both modes:

```python
def test_feature_standard_latex(self) -> None:
    """Test feature in standard LaTeX mode."""
    gen = LaTeXGenerator(use_fuzz=False)
    # ... test standard LaTeX output ...

def test_feature_fuzz_mode(self) -> None:
    """Test feature in fuzz mode."""
    gen = LaTeXGenerator(use_fuzz=True)
    # ... test fuzz-specific output ...
```

**Example**: `tests/test_06_definitions/test_semicolon_declarations.py`

### Manual Fuzz Verification

After code changes, verify with actual fuzz:
```bash
cd /tmp
cat > test.tex << 'EOF'
\documentclass{article}
\usepackage{fuzz}
\begin{document}
% ... your test case ...
\end{document}
EOF

TEXINPUTS=.:/path/to/fuzz//: pdflatex test.tex
pdftotext test.pdf -  # Check rendering
```

---

## References

- **Fuzz Package**: Available at [github.com/jmf-pobox/fuzz](https://github.com/jmf-pobox/fuzz)
- **Missing Features**: [MISSING_FEATURES.md](MISSING_FEATURES.md) - Features not yet implemented
- **txt2tex Implementation**: `src/txt2tex/latex_gen.py` and `src/txt2tex/parser.py`

---

## Future Considerations

### Potential Features

1. **Fuzz-only mode**: Flag to reject all non-fuzz-compatible syntax at parse time
2. **Compatibility warnings**: Warn users when they use features that won't work with fuzz
3. **Automatic conversion**: Convert underscores to camelCase when fuzz mode is enabled
4. **Precedence table**: Document all operator precedence differences between fuzz and standard Z

### Known Limitations

See [MISSING_FEATURES.md](MISSING_FEATURES.md) for complete list of fuzz features not yet supported by txt2tex.
