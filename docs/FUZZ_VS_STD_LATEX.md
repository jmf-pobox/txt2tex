# Fuzz vs Standard LaTeX: Key Differences

**Purpose**: This document captures important differences between fuzz (Mike Spivey's Z notation typesetter) and standard LaTeX that affect txt2tex code generation.

**Last Updated**: 2025-10-19

---

## Quick Reference

| Feature | Standard LaTeX | Fuzz | Impact on txt2tex |
|---------|----------------|------|-------------------|
| Natural numbers | `\mathbb{N}` | `\nat` | Context-aware generation |
| Integers | `\mathbb{Z}` | `\num` | Context-aware generation |
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

**Reference**: [latex_gen.py:368-373](../src/txt2tex/latex_gen.py:368-373)

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

**Reference**: [latex_gen.py:427-431](../src/txt2tex/latex_gen.py:427-431)

**Example**:
```
Input:  # s(i)
Fuzz:   # (s(i))    ← Parentheses required
LaTeX:  \# s(i)     ← No parentheses needed
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

**Reference**:
- [latex_gen.py:2086-2124](../src/txt2tex/latex_gen.py:2086-2124) - gendef
- [latex_gen.py:2044-2084](../src/txt2tex/latex_gen.py:2044-2084) - axdef
- [latex_gen.py:2126-2170](../src/txt2tex/latex_gen.py:2126-2170) - schema

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

**Reference**: [parser.py:1670-1683](../src/txt2tex/parser.py:1670-1683)

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

**Reference**: [latex_gen.py:712-733](../src/txt2tex/latex_gen.py:712-733)

---

## Tuple Projection

### NOT Supported by Fuzz

**Standard Z**: Tuple projection with `.1`, `.2`, etc.
**Fuzz**: Does **NOT** support tuple projection syntax

**txt2tex behavior**: Generates the syntax, but fuzz validation will fail

**User workaround**: Don't use tuple projection in fuzz mode, or define custom projection functions

**Note**: This is documented in [FUZZ_FEATURE_GAPS.md](FUZZ_FEATURE_GAPS.md)

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

**Reference**: [STATUS.md:359-367](../STATUS.md:359-367)

---

## Key Lessons for Future Development

### 1. Always Test with Fuzz

When implementing new features, test both modes:
```bash
# Standard LaTeX mode (default)
hatch run convert file.txt

# Fuzz mode (type checking enabled)
hatch run convert file.txt --fuzz
```

### 2. Check Operator Precedence

When adding new operators, verify fuzz precedence matches expectations. If not, add parentheses in fuzz mode.

### 3. Line Breaks in Boxes

Fuzz boxes (gendef, axdef, schema) require explicit `\\` line breaks between declarations. Don't rely on semicolons alone.

### 4. Limited Operator Set

Fuzz supports a specific set of Z notation operators. Check the fuzz manual before assuming an operator is supported.

### 5. Type Checking is Strict

Fuzz type checking is much stricter than LaTeX. Code that "looks right" in PDF may fail fuzz validation.

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

**Example**: [test_semicolon_declarations.py:280-335](../tests/test_06_definitions/test_semicolon_declarations.py:280-335)

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

- **Fuzz Manual**: [docs/fuzz/part*.pdf](../docs/fuzz/) - Official fuzz documentation
- **Fuzz Package**: `hw/fuzz.sty` - Local copy of fuzz.sty with font definitions
- **Feature Gaps**: [FUZZ_FEATURE_GAPS.md](FUZZ_FEATURE_GAPS.md) - Features from manual not yet implemented
- **txt2tex Implementation**:
  - [latex_gen.py](../src/txt2tex/latex_gen.py) - LaTeX generation with fuzz support
  - [parser.py](../src/txt2tex/parser.py) - Parser aware of fuzz limitations

---

## Future Considerations

### Potential Features

1. **Fuzz-only mode**: Flag to reject all non-fuzz-compatible syntax at parse time
2. **Compatibility warnings**: Warn users when they use features that won't work with fuzz
3. **Automatic conversion**: Convert underscores to camelCase when fuzz mode is enabled
4. **Precedence table**: Document all operator precedence differences between fuzz and standard Z

### Known Limitations

See [FUZZ_FEATURE_GAPS.md](FUZZ_FEATURE_GAPS.md) for complete list of fuzz features not yet supported by txt2tex.
