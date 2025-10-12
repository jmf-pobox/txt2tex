# txt2tex

Convert whiteboard-style mathematical notation to high-quality LaTeX for formal methods and Z notation.

## Current Status: Phase 8 ✅

**Production Ready!** Supports propositional logic, truth tables, equivalence chains, quantifiers, equality, proof trees, and **set comprehension**.

- 🎯 8 phases complete (Phase 0-8)
- ✅ 183 tests passing
- 📚 9 example files demonstrating all features
- 🔧 Makefile automation for building PDFs

## Quick Start

### Using the Shell Script (Easiest)

```bash
# Convert txt to PDF in one command
./txt2pdf.sh examples/phase8.txt

# Use fuzz package instead of zed-*
./txt2pdf.sh myfile.txt --fuzz
```

### Using Hatch CLI

```bash
# Convert and compile to PDF
hatch run cli input.txt

# Generate LaTeX only
hatch run cli input.txt --latex-only
```

### Using Make

```bash
# In examples/ directory - build all phase examples
cd examples && make

# Build specific phase
make phase8

# Parallel build
make -j4

# In hw/ directory - build solutions
cd hw && make
```

## User Guide: Text Format

### Document Structure

#### Sections
```
=== Section Title ===
```
Generates: `\section*{Section Title}`

#### Solutions
```
** Solution 1 **

Content here...
```
Generates: `\bigskip\noindent\textbf{Solution 1}\medskip`

#### Part Labels
```
(a) First part
(b) Second part
(c) Third part
```
Generates: `(a)\par\vspace{11pt}` with proper spacing

#### Text Paragraphs
```
TEXT: This is a plain text paragraph with => and <=> symbols.
```
Operators in TEXT are converted: `=>` → `$\Rightarrow$`, `<=>` → `$\Leftrightarrow$`

---

### Propositional Logic (Phase 0)

#### Operators
```
p and q          →  p ∧ q
p or q           →  p ∨ q
not p            →  ¬p
p => q           →  p ⇒ q
p <=> q          →  p ⇔ q
```

#### Precedence (highest to lowest)
1. `not` (unary)
2. `and`
3. `or`
4. `=>`
5. `<=>` (lowest)

#### Examples
```
not p and q      →  (¬p) ∧ q
p and q => r     →  (p ∧ q) ⇒ r
p => q => r      →  p ⇒ (q ⇒ r)  [right-associative]
```

---

### Truth Tables (Phase 1)

```
TRUTH TABLE:
p | q | p => q
T | T | T
T | F | F
F | T | T
F | F | T
```

Generates a centered LaTeX tabular environment with proper formatting.

---

### Equivalence Chains (Phase 2)

```
EQUIV:
p and q
<=> q and p [commutative]
<=> q and p [idempotent]
```

Generates `align*` environment with justifications:
```latex
\begin{align*}
p \land q \\
&\Leftrightarrow q \land p && \text{[commutative]} \\
&\Leftrightarrow q \land p && \text{[idempotent]}
\end{align*}
```

Operators in justifications (`and`, `or`, `not`, `=>`, `<=>`) are automatically converted to LaTeX symbols.

---

### Quantifiers (Phase 3, 6, 7)

#### Basic Quantifiers
```
forall x : N | x > 0           →  ∀ x : ℕ • x > 0
exists y : Z | y < 0           →  ∃ y : ℤ • y < 0
exists1 x : N | x = 5          →  ∃₁ x : ℕ • x = 5
mu x : N | x > 0               →  μ x : ℕ • x > 0
```

#### Multi-Variable Quantifiers (Phase 6)
```
forall x, y : N | x = y        →  ∀ x, y : ℕ • x = y
exists a, b, c : Z | a = b     →  ∃ a, b, c : ℤ • a = b
```

#### Nested Quantifiers
```
forall x : N | exists y : N | x = y
```

---

### Mathematical Notation (Phase 3, 7)

#### Subscripts and Superscripts
```
x_i              →  xᵢ
x^2              →  x²
2^n              →  2ⁿ
a_{n}            →  aₙ  (braces group multi-char subscripts)
x^{2n}           →  x²ⁿ (braces group multi-char superscripts)
```

#### Comparison Operators
```
x < y            →  x < y
x > y            →  x > y
x <= y           →  x ≤ y
x >= y           →  x ≥ y
x = y            →  x = y
x != y           →  x ≠ y
```

#### Set Operators (Phase 3, 7)
```
x in A           →  x ∈ A
x notin B        →  x ∉ B
A subset B       →  A ⊆ B
A union B        →  A ∪ B
A intersect C    →  A ∩ C
```

---

### Set Comprehension (Phase 8)

#### Set by Predicate
```
{ x : N | x > 0 }              →  { x : ℕ | x > 0 }
```

#### Set by Expression
```
{ x : N | x > 0 . x^2 }        →  { x : ℕ | x > 0 • x² }
```

The bullet (`•`) separates the predicate from the expression.

#### Multi-Variable Sets
```
{ x, y : N | x = y }           →  { x, y : ℕ | x = y }
```

#### Set Without Domain
```
{ x | x in A }                 →  { x | x ∈ A }
```

#### Complex Examples
```
forall x : N | x in { y : N | y > 0 }
{ x : N | x > 0 and x <= 10 }
```

---

### Z Notation (Phase 4)

#### Given Types
```
given Person, Company
```
Generates: `\begin{zed}[Person, Company]\end{zed}`

#### Free Types
```
Status ::= active | inactive | pending
```

#### Abbreviations
```
Pairs == N x N
```

#### Axiomatic Definitions
```
axdef
  population : N
where
  population > 0
end
```

#### Schemas
```
schema State
  count : N
where
  count >= 0
end
```

---

### Proof Trees (Phase 5)

Natural deduction proofs using indentation-based syntax:

```
PROOF:
  p and q => p [=> intro from 1]
    [1] p and q [assumption]
    :: p [and elim 1]
      :: p and q [from 1]
```

#### Proof Syntax
- **Indentation**: 2 spaces per level
- **Assumptions**: `[1]`, `[2]`, etc. for labeled assumptions
- **Justifications**: `[rule name]` after expression
- **Discharge**: `[=> intro from 1]` references assumption `[1]`
- **Siblings**: `::` prefix for parallel premises
- **References**: `[from 1]` refers to assumption `[1]`

#### Supported Rules
- `and intro`, `and elim 1`, `and elim 2`
- `or intro 1`, `or intro 2`, `or elim`
- `=> intro`, `=> elim`
- `false intro`, `false elim`
- Case analysis: `case p:` and `case q:`

#### Example: Complex Proof
```
PROOF:
  p or q => r [=> intro from 1]
    [1] p or q [assumption]
    :: r [or elim]
      :: p or q [from 1]
      case p:
        :: r [from 2]
          [2] p [assumption]
      case q:
        :: r [from 3]
          [3] q [assumption]
```

---

## Features by Phase

### ✅ Phase 0: Propositional Logic
- Basic operators: `and`, `or`, `not`, `=>`, `<=>`
- Correct precedence and associativity
- Parentheses for grouping

### ✅ Phase 1: Document Structure
- Section headers: `=== Title ===`
- Solution blocks: `** Solution N **`
- Part labels: `(a)`, `(b)`, `(c)`
- Truth tables: `TRUTH TABLE:`
- Proper spacing with `\bigskip`, `\medskip`

### ✅ Phase 2: Equivalence Chains
- `EQUIV:` environment
- Justifications in brackets: `[rule name]`
- Automatic alignment with `align*`
- Operator conversion in justifications

### ✅ Phase 3: Mathematical Notation
- Quantifiers: `forall`, `exists`
- Subscripts: `x_i`, `a_{n}`
- Superscripts: `x^2`, `2^{10}`
- Set operators: `in`, `notin`, `subset`, `union`, `intersect`
- Comparison: `<`, `>`, `<=`, `>=`, `=`, `!=`

### ✅ Phase 4: Z Notation Basics
- Given types: `given A, B`
- Free types: `Type ::= branch1 | branch2`
- Abbreviations: `Name == Expression`
- Axiomatic definitions: `axdef ... where ... end`
- Schemas: `schema Name ... where ... end`

### ✅ Phase 5: Proof Trees
- Natural deduction proofs
- Indentation-based structure
- Assumption discharge with labels
- Multiple inference rules
- Case analysis with `or-elim`
- LaTeX `\infer` macro generation

### ✅ Phase 6: Multi-Variable Quantifiers
- Comma-separated variables: `forall x, y : N`
- Shared domain across variables
- Works with all quantifiers

### ✅ Phase 7: Equality & Special Operators
- Equality: `=`, `!=` in all contexts
- Unique existence: `exists1`
- Mu operator: `mu x : N | pred`
- Full equality reasoning support

### ✅ Phase 8: Set Comprehension
- Set by predicate: `{ x : N | pred }`
- Set by expression: `{ x : N | pred . expr }`
- Multi-variable: `{ x, y : N | pred }`
- Optional domain: `{ x | pred }`
- Nested set comprehensions

---

## Command-Line Reference

### txt2pdf.sh Script

```bash
# Basic usage
./txt2pdf.sh input.txt                    # Creates input.pdf

# Use fuzz package
./txt2pdf.sh input.txt --fuzz

# Specify output
./txt2pdf.sh input.txt -o output.pdf
```

### Hatch CLI

```bash
# Convert to PDF (default)
hatch run cli input.txt

# LaTeX only
hatch run cli input.txt --latex-only

# Use fuzz package
hatch run cli input.txt --fuzz

# Expression mode
hatch run cli -e "p and q => r"

# Output to file
hatch run cli -e "p or q" -o output.tex
```

### Options

```
usage: txt2tex [-h] [-o OUTPUT] [--fuzz] [--latex-only] [-e] input

positional arguments:
  input                 Input text (expression or file path)

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file path
  --fuzz                Use fuzz package instead of zed-* packages
  --latex-only          Generate LaTeX only (skip PDF compilation)
  -e, --expr            Treat input as expression (not file)
```

---

## Examples

See the `examples/` directory for complete working examples:

- **phase0.txt** - Propositional logic basics
- **phase1.txt** - Document structure and truth tables
- **phase2.txt** - Equivalence chains with justifications
- **phase3.txt** - Quantifiers and mathematical notation
- **phase4.txt** - Z notation definitions
- **phase5.txt** - Natural deduction proof trees
- **phase6.txt** - Multi-variable quantifiers
- **phase7.txt** - Equality and special operators
- **phase8.txt** - Set comprehension

Build all examples:
```bash
cd examples
make          # Build all
make phase8   # Build specific phase
```

---

## Development

### Requirements
- Python 3.10+
- hatch (for development)
- LaTeX distribution (TeX Live recommended)
- zed-* packages (included in `latex/` directory)

### Setup

```bash
# Install hatch
pip install hatch

# Create development environment
hatch env create

# Run tests
hatch run test

# Run all quality gates
hatch run type       # MyPy type checking
hatch run lint       # Ruff linting
hatch run format     # Ruff formatting
```

### Quality Standards

All code must pass:
- ✅ MyPy strict mode (zero errors)
- ✅ Ruff linting (zero violations)
- ✅ Ruff formatting
- ✅ All tests passing (183 tests)
- ✅ Test coverage maintained

### Running Tests

```bash
# All tests
hatch run test

# Specific phase
hatch run test tests/test_phase8.py

# With coverage
hatch run test-cov

# Verbose
hatch run test -v
```

### Project Structure

```
sem/
├── src/txt2tex/              # Source code
│   ├── tokens.py             # Token definitions
│   ├── lexer.py              # Lexical analyzer
│   ├── ast_nodes.py          # AST node types
│   ├── parser.py             # Recursive descent parser
│   ├── latex_gen.py          # LaTeX generator
│   └── cli.py                # Command-line interface
├── tests/                    # Test suite
│   ├── test_phase0.py        # Phase 0 tests
│   ├── test_phase1.py        # Phase 1 tests
│   ├── ...
│   └── test_phase8.py        # Phase 8 tests (183 total)
├── examples/                 # Example files
│   ├── Makefile              # Build automation
│   ├── phase0.txt            # Through phase8.txt
│   ├── exercises.pdf         # Reference materials
│   ├── glossary.pdf
│   └── solutions.pdf
├── hw/                       # Homework solutions
│   ├── Makefile              # Build automation
│   └── solutions.txt
├── latex/                    # LaTeX packages
│   ├── zed-cm.sty           # Z notation packages
│   ├── zed-maths.sty
│   └── zed-proof.sty
├── txt2pdf.sh               # Convenience script
├── pyproject.toml           # Python project config
├── DESIGN.md                # Architecture documentation
├── CLAUDE.md                # Development context
└── README.md                # This file
```

---

## Design Philosophy

**Phased approach**: Each phase delivers a complete, working end-to-end system that is immediately useful for a subset of problems. This allows incremental development with regular user testing and feedback.

**Parser-based**: Unlike regex-based approaches, txt2tex uses a proper compiler pipeline:
```
Text → Lexer → Tokens → Parser → AST → Generator → LaTeX → PDF
```

This provides:
- **Correctness**: Semantic understanding of structure
- **Maintainability**: Clean architecture, easy to extend
- **Error messages**: Precise line/column error reporting
- **Testability**: Each component tested in isolation

**Quality first**: All code passes strict type checking (mypy), linting (ruff), formatting, and comprehensive tests before commit.

See `DESIGN.md` for complete architectural details and implementation notes.

---

## LaTeX Packages

### Default: zed-* packages (Jim Davies)
```latex
\usepackage{zed-cm}       % Computer Modern fonts
\usepackage{zed-maths}    % Mathematical operators
\usepackage{zed-proof}    % Proof tree macros (\infer)
```

Advantages:
- No custom fonts required
- Works on any LaTeX installation
- Excellent proof tree support
- Modular design

### Optional: fuzz (Mike Spivey)
```bash
./txt2pdf.sh input.txt --fuzz
```

```latex
\usepackage{fuzz}         % Z notation package
```

Advantages:
- Historical standard for Z notation
- Single package simplicity
- Custom fonts for Z notation

Both packages are compatible - generated LaTeX works with either.

---

## Troubleshooting

### LaTeX Compilation Errors

**Missing packages:**
```
! LaTeX Error: File `zed-cm.sty' not found.
```
Solution: The zed-* packages are included in `latex/`. Ensure `TEXINPUTS` is set correctly:
```bash
export TEXINPUTS=./latex//:
pdflatex file.tex
```

The `txt2pdf.sh` script handles this automatically.

**Missing fonts (fuzz package):**
```
! Font not found: oxsz10
```
Solution: Ensure `MFINPUTS` is set:
```bash
export MFINPUTS=./latex//:
```

### Parse Errors

**Unexpected character:**
```
Error: Line 5, column 10: Unexpected character: '@'
```
Solution: Check for unsupported characters. See User Guide for supported syntax.

**Expected token:**
```
Error: Line 3, column 15: Expected '|' after quantifier binding
```
Solution: Check quantifier syntax: `forall x : N | predicate`

### Running Examples

If examples don't compile, ensure you're in the correct directory:
```bash
cd examples
make phase8           # Builds phase8.pdf
```

Or use the shell script from any location:
```bash
./txt2pdf.sh examples/phase8.txt
```

---

## Contributing

Contributions are welcome! Please:

1. Read `DESIGN.md` and `CLAUDE.md` for architectural context
2. Follow the phased development approach
3. Maintain all quality gates (type, lint, format, tests)
4. Add tests for new features
5. Update documentation

### Adding a New Feature

1. **Design**: Document in `DESIGN.md`
2. **Lexer**: Add tokens to `tokens.py` and `lexer.py`
3. **AST**: Add nodes to `ast_nodes.py`
4. **Parser**: Add parsing rules to `parser.py`
5. **Generator**: Add LaTeX generation to `latex_gen.py`
6. **Tests**: Add comprehensive tests to `tests/test_phaseN.py`
7. **Example**: Add example to `examples/phaseN.txt`
8. **Docs**: Update this README

---

## Roadmap

### Completed (Phase 0-8)
✅ Propositional logic
✅ Document structure
✅ Truth tables
✅ Equivalence chains
✅ Quantifiers (single and multi-variable)
✅ Mathematical notation (subscripts, superscripts)
✅ Set operators
✅ Equality and special operators
✅ Z notation basics (given, free types, abbreviations, schemas)
✅ Natural deduction proof trees
✅ Set comprehension

### Future Phases (9-14)

**Phase 9: Generic Definitions**
- Generic parameters: `[X]`
- Generic functions and schemas

**Phase 10: Relations**
- Relation operators: `<->`, `|->`, `dom`, `ran`
- Domain/range restriction: `<|`, `|>`
- Composition: `comp`, `o9`
- Inverse: `~`, `+`, `*`

**Phase 11: Functions**
- Function types: `->`, `+->`, `>->`, `-->>`, `>->>`
- Function application
- Lambda expressions
- Function override

**Phase 12: Sequences**
- Sequence types: `seq`, `seq1`, `iseq`
- Sequence literals: `<a, b, c>`
- Sequence operators: `^`, `head`, `tail`, `rev`

**Phase 13: Schemas & State Machines**
- Schema decoration: `S'`, `S?`, `S!`
- Delta/Xi notation
- Schema composition and operations

**Phase 14: Free Types & Induction**
- Recursive type definitions
- Pattern matching
- Inductive proof structure

### Enhancements
- Inline math in TEXT paragraphs
- Arithmetic operators (`+`, `-`, `*`, `/`)
- Set literals: `{1, 2, 3}`
- Tuple notation: `(a, b, c)`
- Better error recovery
- IDE integration (LSP server)

---

## License

MIT

## Credits

- **Mike Spivey**: fuzz package for Z notation
- **Jim Davies**: zed-* packages for Z notation
- **Anthropic Claude**: Development assistant

## Contact

For bugs, feature requests, or questions, please open an issue on GitHub.

---

**Last Updated**: Phase 8 Complete (Set Comprehension)
**Version**: 0.8.0
**Status**: Production Ready for Phases 0-8
