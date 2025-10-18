# txt2tex

Convert plain text notation to high-quality LaTeX for formal methods and Z notation.

## What is txt2tex?

txt2tex converts mathematical specifications written in a simple plain text format to professionally typeset LaTeX documents. The primary advantage is that the input is plain text, not a markup language - you write expressions almost as you would on paper or a whiteboard.

Designed for:
- **Z notation** and formal specification languages
- **Mathematical proofs** with natural deduction trees
- **Academic assignments** requiring formal methods
- **Technical documentation** with precise mathematical notation

Write `forall x : N | x > 0` in plain text and get LaTeX: ∀ x : ℕ • x > 0

**Note**: The proof syntax requires some structure (indentation-based), but mathematical expressions use natural notation.

## Quick Start

### Prerequisites

- **Python 3.10+**
- **LaTeX distribution** (TeX Live 2020 or later recommended)
- **hatch** for development (optional for basic usage)

### Installation

```bash
# Clone the repository
cd /path/to/txt2tex/sem

# Install hatch (if not already installed)
pip install hatch

# Verify installation
hatch run cli --help
```

### Verify Your Setup

Test that txt2tex can convert a simple file:

```bash
# Create a test file
echo "=== Test ===" > test.txt
echo "TEXT: The statement forall x : N | x > 0 is true." >> test.txt

# Convert to PDF
hatch run convert test.txt

# Check output
ls -l test.pdf
```

You should see `test.pdf` created successfully.

### Your First Conversion

1. Create a file `example.txt`:

```
=== Propositional Logic ===

** Solution 1 **

(a) Truth table for p => q:

TRUTH TABLE:
p | q | p => q
T | T | T
T | F | F
F | T | T
F | F | T

(b) The propositions are equivalent:

EQUIV:
not (p and q)
<=> not p or not q [De Morgan]
```

2. Convert to PDF:

```bash
hatch run convert example.txt
```

3. Open `example.pdf` to see the beautifully formatted result.

## Usage

### Basic Workflow

**Method 1: Using hatch (recommended)**

```bash
# Convert txt to PDF
hatch run convert input.txt

# LaTeX only (no PDF compilation)
hatch run cli input.txt --latex-only

# Use fuzz package with type checking
hatch run convert input.txt --fuzz
```

**Method 2: Using the shell script**

```bash
# Convert txt to PDF
./txt2pdf.sh input.txt

# With fuzz type checking
./txt2pdf.sh input.txt --fuzz
```

The conversion process:
1. Parses your plain text input
2. Generates LaTeX with proper Z notation formatting
3. Copies LaTeX dependencies locally (portable)
4. Compiles to PDF

### VSCode/Cursor + LaTeX Workshop Setup

You can edit `.txt` files in txt2tex and view the generated `.tex` files side-by-side with LaTeX Workshop for real-time PDF preview.

#### 1. Install LaTeX Workshop Extension

In VSCode/Cursor:
- Open Extensions (Cmd+Shift+X)
- Search for "LaTeX Workshop"
- Install by James Yu

#### 2. Workspace Configuration

The project includes pre-configured settings:

- **`.vscode/settings.json`**: LaTeX Workshop configuration with correct TEXINPUTS/MFINPUTS paths
- **`.latexmkrc`**: Build configuration in `hw/` and `examples/` directories

These ensure LaTeX Workshop can find the local dependencies (`.sty` and `.mf` files).

#### 3. Workflow

**Option A: Watch mode** (automatic rebuild)

```bash
# Terminal 1: Watch for changes and rebuild
cd examples  # or hw/
while true; do
  inotifywait -e modify myfile.txt 2>/dev/null && \
  hatch run convert myfile.txt
  sleep 1
done
```

Then in VSCode/Cursor:
- Open `myfile.tex`
- LaTeX Workshop auto-compiles and shows PDF preview

**Option B: Manual rebuild** (simpler)

```bash
# 1. Edit your .txt file in examples/ or hw/
# 2. Convert when ready:
hatch run convert examples/myfile.txt
# 3. Open the generated .tex file in VSCode/Cursor
# LaTeX Workshop shows PDF preview automatically
```

#### 4. Troubleshooting LaTeX Workshop

**Error: "File `fuzz.sty' not found"**

1. Ensure dependencies were copied: Run `make` or `hatch run convert` at least once
2. Reload VSCode/Cursor: Cmd+Shift+P → "Reload Window"
3. Check files exist: Verify `hw/*.sty` and `hw/*.mf` files are present

### Using Make

For batch processing of examples:

```bash
# Build all examples
cd examples && make

# Build specific topic
cd 01_propositional_logic && make

# Parallel build
make -j4

# Clean auxiliary files (keep .tex and .pdf)
make clean

# Remove all generated files (keep only .txt)
make distclean
```

## Syntax Overview

### Document Structure

```
=== Section Title ===          → LaTeX section

** Solution 1 **               → Formatted solution heading

(a) First part                 → Part label with spacing
(b) Second part
```

### Text Blocks

```
TEXT: Normal prose with inline math: forall x : N | x > 0

PURETEXT: Raw text with LaTeX escaping: Author's "quote"

LATEX: \textbf{Custom LaTeX commands}

PAGEBREAK:                     → Inserts page break
```

### Mathematical Notation

```
# Propositional Logic
p and q                        → p ∧ q
p or q                         → p ∨ q
not p                          → ¬p
p => q                         → p ⇒ q
p <=> q                        → p ⇔ q

# Quantifiers
forall x : N | x > 0           → ∀ x : ℕ • x > 0
exists y : Z | y < 0           → ∃ y : ℤ • y < 0

# Sets
x in A                         → x ∈ A
A subset B                     → A ⊆ B
A union B                      → A ∪ B

# Set Comprehension
{ x : N | x > 0 }              → { x : ℕ | x > 0 }
```

### Z Notation Basics

```
# Given types
given Person, Company

# Free types
Status ::= active | inactive | pending

# Abbreviations
Pairs == N cross N

# Axiomatic definitions
axdef
  population : N
where
  population > 0
end

# Schemas
schema State
  count : N
where
  count >= 0
end
```

**For complete syntax reference, see [USER-GUIDE.md](USER-GUIDE.md)**

## Command Reference

### CLI Options

```
usage: txt2tex [-h] [-o OUTPUT] [--fuzz] [--latex-only] [-e] input

positional arguments:
  input                 Input text (expression or file path)

options:
  -h, --help            Show help message
  -o OUTPUT             Output file path
  --fuzz                Use fuzz package (with type checking)
  --latex-only          Generate LaTeX only (skip PDF)
  -e, --expr            Treat input as expression, not file
```

### Examples

```bash
# Basic conversion
hatch run convert input.txt

# Expression mode
hatch run cli -e "p and q => r"

# LaTeX only
hatch run cli input.txt --latex-only -o output.tex

# With fuzz type checking
hatch run convert input.txt --fuzz
```

## Known Issues

### Active Bugs (5 confirmed)

| Priority | Issue | Description | Workaround |
|----------|-------|-------------|------------|
| HIGH | [#1](https://github.com/jmf-pobox/txt2tex/issues/1) | Parser fails on prose with periods | Use TEXT blocks |
| MEDIUM | [#2](https://github.com/jmf-pobox/txt2tex/issues/2) | Multiple pipes in TEXT close math mode | Use axdef/schema |
| MEDIUM | [#3](https://github.com/jmf-pobox/txt2tex/issues/3) | Cannot use R+, R* identifiers | None available |
| MEDIUM | [#4](https://github.com/jmf-pobox/txt2tex/issues/4) | Comma after parenthesized math not detected | Avoid comma after parens |
| MEDIUM-HIGH | [#5](https://github.com/jmf-pobox/txt2tex/issues/5) | Logical operators (or, and) not converted | Use axdef/schema |

**For bug details and test cases, see [tests/bugs/README.md](tests/bugs/README.md)**

**To report a bug:** Follow the workflow in [tests/bugs/README.md](tests/bugs/README.md#adding-new-bugs)

### Known Limitations

**Parser Limitations:**
- Prose mixed with inline math outside TEXT blocks causes parse errors
- Identifiers with operator suffixes (R+, R*) not supported
- TEXT block inline math detection has edge cases with commas and logical operators

**Unimplemented Features:**
- Schema decoration (S', ΔS, ΞS)
- Some advanced Z notation operations

**For detailed implementation status, see [STATUS.md](STATUS.md)**

## Development

### Running Tests

```bash
# All tests (845 passing)
hatch run test

# With coverage
hatch run test-cov

# Specific test directory
hatch run test tests/01_propositional/

# Verbose output
hatch run test -v
```

### Quality Gates

All code must pass:

```bash
hatch run type           # MyPy strict mode (zero errors)
hatch run lint           # Ruff linting (zero violations)
hatch run format         # Ruff formatting
hatch run test           # All tests passing
```

### Project Structure

```
sem/
├── src/txt2tex/              # Source code
│   ├── lexer.py              # Tokenization
│   ├── parser.py             # Parsing to AST
│   ├── latex_gen.py          # LaTeX generation
│   └── cli.py                # Command-line interface
├── tests/                    # Test suite (845 tests)
│   ├── 01_propositional/     # Organized by lecture
│   ├── 02_quantifiers/
│   ├── ...
│   └── bugs/                 # Bug test cases
├── examples/                 # Example files
├── hw/                       # Homework solutions
├── latex/                    # LaTeX packages
│   ├── zed-cm.sty           # Z notation packages
│   ├── zed-maths.sty
│   └── zed-proof.sty
├── txt2pdf.sh               # Conversion script
└── pyproject.toml           # Python project config
```

### Implementation Status

**For detailed implementation progress, see [STATUS.md](STATUS.md)**

### Architecture

txt2tex uses a proper compiler pipeline:

```
Text → Lexer → Tokens → Parser → AST → Generator → LaTeX → PDF
```

This provides semantic understanding, precise error messages, and maintainability.

**For architecture details, see [DESIGN.md](DESIGN.md)**

## Project Documentation

- **[README.md](README.md)** (this file) - Setup, usage, getting started
- **[USER-GUIDE.md](USER-GUIDE.md)** - Complete syntax reference organized by topic
- **[STATUS.md](STATUS.md)** - Implementation status, solution coverage, roadmap
- **[DESIGN.md](DESIGN.md)** - Architecture and design decisions
- **[CLAUDE.md](CLAUDE.md)** - Development context and workflows
- **[QA_PLAN.md](QA_PLAN.md)** - Quality assurance process
- **[tests/bugs/README.md](tests/bugs/README.md)** - Bug reports and test cases

## Troubleshooting

### LaTeX Compilation Errors

**Missing packages:**
```
! LaTeX Error: File `zed-cm.sty' not found.
```

**Solution**: Use `txt2pdf.sh` or `make` - they copy dependencies locally automatically.

For manual compilation:
```bash
export TEXINPUTS=.:./latex//:
export MFINPUTS=.:./latex//:
pdflatex file.tex
```

### Parse Errors

**Unexpected character:**
```
Error: Line 5, column 10: Unexpected character: '@'
```

**Solution**: Check for unsupported characters. See [USER-GUIDE.md](USER-GUIDE.md) for supported syntax.

**Expected token:**
```
Error: Line 3, column 15: Expected '|' after quantifier binding
```

**Solution**: Verify quantifier syntax: `forall x : N | predicate`

### LaTeX Workshop in VSCode/Cursor

**Error: "File `fuzz.sty' not found" when opening .tex files**

1. Run build once to copy dependencies: `make` or `hatch run convert file.txt`
2. Reload VSCode/Cursor: Cmd+Shift+P → "Reload Window"
3. Verify files: Check that `hw/*.sty` and `hw/*.mf` files exist

The workspace includes pre-configured `.latexmkrc` and `.vscode/settings.json` files.

## LaTeX Packages

### Default: zed-* packages (Jim Davies)

```latex
\usepackage{zed-cm}       % Computer Modern fonts
\usepackage{zed-maths}    % Mathematical operators
\usepackage{zed-proof}    % Proof tree macros
```

- Works on any LaTeX installation
- No custom fonts required
- Excellent proof tree support

### Optional: fuzz (Mike Spivey)

```bash
hatch run convert input.txt --fuzz
```

```latex
\usepackage{fuzz}         % Z notation fonts/styling (replaces zed-cm)
\usepackage{zed-maths}    % Mathematical operators (same)
\usepackage{zed-proof}    % Proof tree macros (same)
```

- Historical standard for Z notation
- Custom Oxford fonts
- Includes type checking with `fuzz` command
- **Note**: Identifiers with underscores not supported by fuzz type checker

## Examples

The `examples/` directory contains working examples organized by topic:

```bash
# View available topics
ls examples/

# Build specific example
hatch run convert examples/01_propositional_logic/hello_world.txt

# Build all examples
cd examples && make
```

Example topics include:
- **01_propositional_logic/** - Basic operators, truth tables
- **02_predicate_logic/** - Quantifiers and set comprehension
- **03_equality/** - Equality reasoning
- **04_proof_trees/** - Natural deduction proofs
- **05_sets/** - Set notation and operations
- **06_definitions/** - Z notation schemas and axdefs
- **07_relations/** - Relation operators
- **08_functions/** - Function types and lambda expressions
- **09_sequences/** - Sequence notation and operations
- And more...

## Contributing

Contributions welcome! Please:

1. Read [DESIGN.md](DESIGN.md) and [CLAUDE.md](CLAUDE.md) for context
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
6. **Tests**: Add comprehensive tests
7. **Example**: Create example file
8. **Docs**: Update README, USER-GUIDE, and STATUS

## License

MIT

## Credits

- **Mike Spivey**: fuzz package for Z notation
- **Jim Davies**: zed-* packages for Z notation
- **Anthropic Claude**: Development assistant

## Contact

For bugs, feature requests, or questions, please open an issue on [GitHub](https://github.com/jmf-pobox/txt2tex/issues).

---

**Last Updated**: 2025-10-18
