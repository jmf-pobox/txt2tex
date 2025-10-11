# txt2tex: Whiteboard to LaTeX Converter

Convert whiteboard-style mathematical notation to typechecked, high-quality LaTeX.

## Quick Start

```bash
# Convert whiteboard notation to PDF
txt2tex mysolution.txt -o mysolution.pdf

# Generate LaTeX only (for inspection)
txt2tex mysolution.txt --latex-only -o mysolution.tex

# Validate with fuzz but don't compile PDF
txt2tex mysolution.txt --validate-only
```

## What is txt2tex?

txt2tex lets you write mathematical proofs and solutions the way you would on a whiteboard, using simple ASCII notation. It automatically converts your text to properly formatted LaTeX and generates submission-ready PDFs.

**Before txt2tex** (you write this):
```
** Solution 1 **

(a) forall x : N | x^2 >= 0

TRUTH TABLE:
p | q | p => q
T | T | T
T | F | F
```

**After txt2tex** (automatically generated):
```latex
\bigskip
\noindent
\textbf{Solution 1}

(a) $\forall x : \nat \bullet x^{2} \geq 0$

\begin{center}
\begin{tabular}{|c|c|c|}
$p$ & $q$ & $p \Rightarrow q$ \\
\hline
T & T & T \\
T & F & F \\
\end{tabular}
\end{center}
```

## Features

- ✅ **Natural syntax**: Write like you would on a whiteboard
- ✅ **Type checking**: Integrated fuzz validation catches errors early
- ✅ **High quality**: Submission-ready PDFs with proper typography
- ✅ **Clear errors**: Line-specific error messages point to exact problems
- ✅ **Fast**: Near-instant conversion for typical documents
- ✅ **Flexible**: Support for propositional logic, predicate logic, and Z notation

## Installation

### Requirements

- Python 3.10 or higher
- LaTeX distribution (TeX Live 2025 or MacTeX)
- fuzz package (for Z notation) or zed-* packages

### Install txt2tex

```bash
# From source
git clone https://github.com/yourusername/txt2tex.git
cd txt2tex
pip install -e .

# Or with pip (when published)
pip install txt2tex
```

### Verify Installation

```bash
txt2tex --version
txt2tex --check-deps
```

## Writing Whiteboard Notation

### Document Structure

```
=== Section Title ===

** Solution 1 **

(a) First part of the solution
(b) Second part of the solution

** Solution 2 **

(a) Another solution
```

**Generates**:
- `===` creates section headings
- `**` creates bold solution titles
- `(a)`, `(b)` create labeled parts with spacing

### Logical Operators

You can use ASCII or Unicode characters:

| Operator | ASCII | Unicode | LaTeX |
|----------|-------|---------|-------|
| And | `and` | `∧` | `\land` |
| Or | `or` | `∨` | `\lor` |
| Not | `not` | `¬` | `\lnot` |
| Implies | `=>` | `⇒` | `\Rightarrow` |
| Iff | `<=>` | `⇔` | `\Leftrightarrow` |
| For all | `forall` | `∀` | `\forall` |
| Exists | `exists` | `∃` | `\exists` |

**Examples**:

```
p and q             → $p \land q$
not (p or q)        → $\lnot (p \lor q)$
p => q              → $p \Rightarrow q$
p <=> (q and r)     → $p \Leftrightarrow (q \land r)$
```

### Quantifiers

```
forall x : N | x^2 >= 0
exists y : Z | y < 0
```

**Generates**: `$\forall x : \nat \bullet x^{2} \geq 0$`

### Mathematics

#### Inline Math

Math is automatically detected in context:

```
The expression x^2 - x + 1 denotes a natural number.
```

**Generates**: `The expression $x^{2} - x + 1$ denotes a natural number.`

#### Superscripts and Subscripts

```
x^2             → x²
a_n             → aₙ
x^10            → x¹⁰
base^exp        → base^exp (automatically wrapped in math mode)
```

### Truth Tables

```
TRUTH TABLE:
p | q | p and q
T | T | T
T | F | F
F | T | F
F | F | F
```

**Generates**: LaTeX tabular environment with proper formatting.

### Equivalence Chains

```
EQUIV:
p and (q or r)
<=> (p and q) or (p and r)  [distributivity]
<=> (q and p) or (r and p)  [commutativity]
```

**Generates**: LaTeX align* environment with justifications.

**Justifications**: Text in `[...]` is treated as justification and formatted appropriately.

### Proof Trees

Use indentation to show structure:

```
PROOF:
  p and q
    p           [and-elimination-1]
    q           [and-elimination-2]
  q and p       [and-introduction]
```

Each indentation level (2 spaces) represents a nesting level in the proof tree.

### Z Notation

#### Given Types

```
given Person, Company
```

**Generates**: `\begin{zed}[Person, Company]\end{zed}`

#### Free Types

```
Status ::= active | inactive | suspended
```

**Generates**: Free type definition in Z notation

#### Abbreviations

```
Name == seq Char
```

**Generates**: `\begin{zed}Name == \seq Char\end{zed}`

#### Axiomatic Definitions

```
axdef
  max : N cross N -> N
where
  forall x, y : N | max(x, y) >= x and max(x, y) >= y
end
```

**Generates**: `\begin{axdef}...\end{axdef}` block

#### Schemas

```
schema Birthday
  known : P Person
  birthday : Person -> Date
where
  dom birthday = known
end
```

**Generates**: `\begin{schema}{Birthday}...\end{schema}` block

## Command Line Options

```bash
txt2tex [OPTIONS] INPUT

Options:
  -o, --output PATH         Output file (PDF or .tex)
  --latex-only             Generate LaTeX without compiling
  --validate-only          Run fuzz validation only
  --no-validation          Skip fuzz validation
  --use-zed                Use zed-* packages instead of fuzz
  --keep-intermediate      Keep intermediate LaTeX file
  -v, --verbose            Verbose output
  --debug-tokens           Show token stream (for debugging)
  --debug-ast              Show abstract syntax tree (for debugging)
  --help                   Show help message
  --version                Show version
  --check-deps             Check if dependencies are installed
```

### Examples

```bash
# Basic conversion
txt2tex homework.txt -o homework.pdf

# See generated LaTeX
txt2tex homework.txt --latex-only -o homework.tex

# Check for errors without generating PDF
txt2tex homework.txt --validate-only

# Use zed packages instead of fuzz
txt2tex homework.txt --use-zed -o homework.pdf

# Debug: see what tokens are generated
txt2tex homework.txt --debug-tokens

# Keep intermediate files for inspection
txt2tex homework.txt -o homework.pdf --keep-intermediate
```

## Configuration

Create a `.txt2texrc` file in your home directory or project root:

```yaml
# Package preference
use_fuzz: true              # or use zed-* packages

# Validation
run_fuzz_validation: true
strict_validation: false    # Treat warnings as errors

# Operator aliases (if you want custom syntax)
operator_aliases:
  implies: ["=>", "→", "⇒"]
  iff: ["<=>", "↔", "⇔"]

# Formatting
latex_indent: 2
wrap_width: 80
```

## Error Messages

txt2tex provides clear, actionable error messages:

```
Error on line 42, column 15:
  forall x in N | x^2 >= 0
              ^
Expected ':' after variable in quantifier
Did you mean: forall x : N | x^2 >= 0
```

### Common Errors

#### "Expected ':' after variable"
```
❌ forall x in N | x > 0
✅ forall x : N | x > 0
```

#### "Undefined variable"
```
❌ forall x : N | y > 0    (y not defined)
✅ forall x : N | x > 0
```

#### "Mismatched parentheses"
```
❌ (p and q or r
✅ (p and q) or r
```

#### "Ambiguous expression"
```
❌ p or q and r            (unclear precedence)
✅ p or (q and r)          (explicit precedence)
   (p or q) and r
```

## Tips and Best Practices

### 1. Use Explicit Parentheses

While txt2tex understands operator precedence, explicit parentheses make your intent clear:

```
✅ (p and q) or r
✅ p and (q or r)
⚠️  p and q or r          (works, but less clear)
```

### 2. Consistent Spacing

Use spaces around operators for readability:

```
✅ p and q
❌ p and q  (works, but inconsistent)
```

### 3. Test Early

Run validation frequently during writing:

```bash
txt2tex draft.txt --validate-only
```

### 4. Check Generated LaTeX

If output looks wrong, inspect the LaTeX:

```bash
txt2tex problem.txt --latex-only -o problem.tex
cat problem.tex
```

### 5. Unicode is Optional

Use whatever is comfortable:
- ASCII: `forall`, `exists`, `and`, `or`, `not`
- Unicode: `∀`, `∃`, `∧`, `∨`, `¬`

Both work identically.

## Examples

### Example 1: Simple Proof

**Input** (`simple.txt`):
```
** Solution 1 **

(a) Prove: (p and q) => p

This is obviously true. If both p and q hold, then p holds.

EQUIV:
(p and q) => p
<=> not (p and q) or p      [definition of =>]
<=> (not p or not q) or p   [De Morgan]
<=> not p or (not q or p)   [associativity]
<=> not p or (p or not q)   [commutativity]
<=> (not p or p) or not q   [associativity]
<=> true or not q           [excluded middle]
<=> true                    [or with true]
```

**Command**:
```bash
txt2tex simple.txt -o simple.pdf
```

**Output**: Properly formatted PDF with equivalence chain.

### Example 2: Truth Table

**Input** (`truth.txt`):
```
** Solution 2 **

(a) Truth table for p => q:

TRUTH TABLE:
p | q | p => q
T | T | T
T | F | F
F | T | T
F | F | T

The implication is false only when the antecedent is true and
the consequent is false.
```

**Command**:
```bash
txt2tex truth.txt -o truth.pdf
```

### Example 3: Z Notation

**Input** (`znotation.txt`):
```
given Person

Birthday == Person -> Date

schema AddBirthday
  Birthday
  Birthday'
  p? : Person
  d? : Date
where
  p? notin dom birthday
  birthday' = birthday union {p? |-> d?}
end
```

**Command**:
```bash
txt2tex znotation.txt -o znotation.pdf
```

## Troubleshooting

### LaTeX Errors

If pdflatex fails:

1. Check the LaTeX log:
```bash
txt2tex file.txt -o file.pdf --keep-intermediate
cat file.log
```

2. Verify fuzz is installed:
```bash
txt2tex --check-deps
kpsewhich fuzz.sty
```

3. Try with zed packages:
```bash
txt2tex file.txt --use-zed -o file.pdf
```

### Validation Errors

If fuzz reports errors:

1. Check line numbers in error message
2. Verify variable declarations
3. Check type consistency

```bash
# See full validation output
txt2tex file.txt --validate-only --verbose
```

### Unexpected Output

1. Check generated LaTeX:
```bash
txt2tex file.txt --latex-only -o file.tex
```

2. Look for malformed input:
```bash
txt2tex file.txt --debug-tokens
```

3. Compare with working examples in `examples/`

## FAQ

**Q: Can I mix ASCII and Unicode operators?**

A: Yes! Use whatever is more convenient.

**Q: How do I escape special characters?**

A: Most characters are handled automatically. If you need a literal `^`, use `\^`.

**Q: Can I use LaTeX directly?**

A: Not recommended. txt2tex generates LaTeX for you. If you need custom LaTeX, edit the generated `.tex` file.

**Q: Does txt2tex support proof trees with graphical rules?**

A: The current version supports simple indentation-based proofs. Full proof tree support is planned.

**Q: Can I convert existing LaTeX to txt2tex format?**

A: Not yet, but it's planned for a future release.

**Q: Is there syntax highlighting for editors?**

A: Not yet. VS Code extension is planned.

## Getting Help

- **Documentation**: See `docs/` directory
- **Examples**: See `examples/` directory
- **Issues**: https://github.com/yourusername/txt2tex/issues
- **Tutorial**: See `docs/TUTORIAL.md` for step-by-step guide

## Contributing

Contributions welcome! See `CONTRIBUTING.md` for guidelines.

## License

MIT License - See `LICENSE` file for details.

## Credits

- **fuzz**: Mike Spivey's Z notation package
- **zed-***: Alternative Z notation packages
- Inspired by the need to write math like on a whiteboard

## Changelog

See `CHANGELOG.md` for version history.

---

**Current Status**: In development. See `DESIGN.md` for architectural details.
