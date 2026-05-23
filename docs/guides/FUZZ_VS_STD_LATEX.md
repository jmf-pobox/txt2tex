# Fuzz vs Standard LaTeX: Key Differences

**Purpose**: This document captures important differences between fuzz (Mike Spivey's Z notation typesetter) and standard LaTeX that affect txt2tex code generation.

**Last Updated**: 2026-05-22

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

```text
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

```text
Input:  # head s
Fuzz:   # (\head s)     ← Parentheses required
LaTeX:  \# \head s      ← No parentheses needed
```

---

## Prefix-Operator Atomic-Argument Rule

### Z RM §3.7 Requirement

Prefix-generic operators (`\seq`, `\power`, `\dom`, `\ran`, `\bigcup`,
`\bigcap`, `\id`, `\inv`, etc.) take an *atomic* Expression0 as their
immediate right operand.  An atomic operand is an identifier, a
parenthesised expression `(...)`, or a brace expression `{...}`.

A nested prefix application is **not** atomic.  Fuzz rejects it with a
syntax error:

```text
\seq~\power X    →  fuzz: "Syntax error at \power"
\ran \bigcup (\ran s)  →  fuzz mis-parses as (\ran \bigcup)(\ran s)
```

**jms ruling (2026-05-22):** wrap the inner prefix application in parens
so the outer operator sees an atomic argument.

**txt2tex behaviour (fuzz mode only):** the generator wraps a `UnaryOp`
argument in parens whenever the outer operator is in
`_FUZZ_FUNCTION_LIKE_UNARY`.  The fix covers all combinations of
`seq`, `P`, `P1`, `F`, `F1`, `dom`, `ran`, `inv`, `id`, `bigcup`,
`bigcap` as outer or inner operator.

**What this means for you:** write the natural form in your `.txt` source
and txt2tex inserts the required parens automatically.

```text
Input:  seq (P X)
Fuzz:   \seq~(\power X)   ← parens inserted automatically
LaTeX:  \seq~\power X     ← bare form accepted in standard mode

Input:  ran (bigcup (ran s))
Fuzz:   \ran~(\bigcup~(\ran s))
LaTeX:  \ran \bigcup (\ran s)
```

**Reference:** `latex_gen.py` — `_generate_unary_op`,
`_generate_function_app`; `tests/test_prefix_paren_wrap.py` (engine
bug #133, jms ruling 2026-05-22).

---

## Negation of Non-Atomic Predicates

### Z RM §3.8.1 vs Fuzz Parser Restriction

**Z RM §3.8.1** permits the bare form `\lnot \exists_1 s @ P` — quantifiers
extend as far right as possible, so the parse is unambiguous.

**Fuzz** is stricter: its parser requires the operand of `\lnot` to be an
atomic predicate.  Presenting a quantifier or connective directly after
`\lnot` triggers:

```text
Opening parenthesis expected at symbol \exists_1
```

**jms ruling (2026-05-22)**: emit `\lnot (child)` whenever `child` is
non-atomic.  Atomic predicates in fuzz are:

1. A predicate name (identifier, e.g. `p`, `Inv`).
2. The constants `true` and `false`.
3. A relation application `e_1 R e_2` where `R` is an infix relation
   symbol (e.g. `x \in s`, `a = b`, `x < y`).
4. A schema reference (e.g. `\Xi S`, `S`).
5. An already-parenthesised predicate.

Quantifiers (`\forall`, `\exists`, `\exists_1`), binary connectives
(`\land`, `\lor`, `\implies`, `\iff`), and lambda expressions are
**non-atomic** and must be parenthesised when they appear as the operand
of `\lnot`.

**txt2tex behavior** (fuzz mode only):

```python
# In _generate_unary_op(), after existing BinaryOp wrapping:
if self.use_fuzz and node.operator == "lnot" and not _is_atomic_predicate(node.operand):
    operand = f"({operand})"
```

`_is_atomic_predicate(node)` returns `True` for `Identifier` and
`BinaryOp` nodes.  `BinaryOp` nodes are already parenthesised by
the preceding BinaryOp-wrap rule, so they are treated as atomic here to
prevent double-parenthesisation.  (`Number` is also accepted by the
helper for defensive symmetry, but a numeric literal is not a
well-formed predicate operand for `\lnot` and will never reach this
path in practice.)

**What this means for you**: no change to your `.txt` input is needed.
Write `lnot (exists1 s : N | s > 0)` exactly as you would on a
whiteboard. txt2tex inserts the parens fuzz requires automatically.

**Reference**: `latex_gen.py` — `_is_atomic_predicate`, `_generate_unary_op`

**Examples**:

```text
Input:  lnot (exists1 s : N | s > 0)
Fuzz:   \lnot (\exists_1 s : \nat @ s > 0)   ← parens required
LaTeX:  \lnot \exists_1 s : \nat @ s > 0     ← bare form accepted

Input:  lnot (a land b)
Fuzz:   \lnot (a \land b)   ← parens required
LaTeX:  \lnot a \land b     ← bare form parses, but binds as (\lnot a) \land b
                              — semantically different from the parenthesised form

Input:  lnot true
Fuzz:   \lnot true          ← no parens (atomic)
LaTeX:  \lnot true          ← same

Input:  lnot p
Fuzz:   \lnot p             ← no parens (atomic identifier)
LaTeX:  \lnot p             ← same
```

**Bug reference**: engine bug #132 (SEM Ex 51 part (b) repro).

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

```text
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

```text
✅ CORRECT: R o9 S    → R ∘ S
✅ CORRECT: R comp S  → R ∘ S
❌ WRONG:   R ; S     → Parse error (semicolon reserved for declarations)
```

---

## Relation Rename (`R[NEW/OLD]`) and Fuzz

### Fuzz rejects `R[NEW/OLD]` inside Z paragraphs

**Standard Z Notation (Z RM §3.11)**: `R[b/a]` is valid relational rename
syntax — `b` is the NEW attribute name, `a` is the OLD attribute name.

**Fuzz**: Inside a `\begin{zed}`, `\begin{axdef}`, or `\begin{schema}`
environment, fuzz parses `[...]` on an expression as a generic instantiation.
A `/` at bracket depth 0 is not part of any Z grammar rule fuzz recognises in
those contexts, so fuzz rejects the expression.

**txt2tex decision**:

- `R[NEW/OLD]` relational rename is classified as a `RelationRename` AST node,
  which is included in `_DAT_EXPRESSION_TYPES` alongside `Restrict`, `Project`,
  `Join`, etc.
- When a `RelationRename` node appears anywhere in an expression (including as
  an abbreviation RHS), the engine routes the entire abbreviation through inline
  math (`\noindent$...$`) instead of `\begin{zed}`.
- Fuzz never sees the `/` — it only processes the Z-paragraph content.

**User syntax**:

```text
✅ CORRECT: pi[id, isbn](Book[id/bookId])      → inline math, fuzz skips it
✅ CORRECT: B == pi[ship, class](Ship[ship/name])  → inline math, fuzz skips it
❌ WRONG:   axdef ... Book[id/bookId] ... end  → fuzz rejects /
```

**Context requirement**: `[NEW/OLD]` is only recognised as a relation rename
inside a *relational context* (argument to `sigma`, `pi`, or right operand of
`join`/`div`).  At the top level of an abbreviation RHS, wrap in `pi` to force
the context:

```text
// Correct: pi forces relational context so [ship/name] is RelationRename
B == pi[ship, class, launched](Ship[ship/name])
```

**Reference**: `latex_gen.py` — `_DAT_EXPRESSION_TYPES`; `parser.py` —
`_in_relational_context` flag.

---

## Nested Sequence Types

### Parentheses Required for Nested Special Functions

**Issue**: Fuzz requires parentheses around nested sequence/bag/power operators

**Example**:

```text
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

```text
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

```text
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

```text
mu n : N | n > 0
```

Fuzz mode generates:

```latex
(\mu n : \nat | n > 0)
```

With expression part:

```text
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

## Schema-Text Parallel Binding

Z RM §3.5 specifies that declarations within a schema text are *sequentially
scoped*: a later declaration's domain may reference names bound by earlier
ones. Example: `x : N; y : 1..x` — `y`'s domain depends on `x`.

Fuzz *parallel-binds* all co-declarations in a single schema text. A domain
that references a sibling's name is therefore rejected by fuzz, even though
it is valid Z.

txt2tex detects this case in `_collect_quantifier_chain` and
`_collect_lambda_chain` via `expr_free_vars` (`src/txt2tex/free_vars.py`).
When a dependency is found, the generator emits nested quantifiers for the
dependent portion rather than the collapsed Spivey form, satisfying fuzz
without changing the Z semantics. Set comprehensions with dependent extra
declarations produce a generator error — Z RM §3.10 has no split identity
for that case; the user must rewrite.

---

## Key Lessons for Future Development

### 1. Always Test with Fuzz

When implementing new features, test both modes:

```bash
# Fuzz mode (default - type checking enabled)
txt2tex file.txt

# zed-* packages mode (no fuzz type checking)
txt2tex file.txt --zed
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

```text
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
