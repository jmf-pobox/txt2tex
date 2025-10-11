# txt2tex

Convert whiteboard-style mathematical notation to LaTeX.

## Current Status: Phase 0 MVP ✅

**Simple propositional logic is working.** You can convert expressions like `p and q => r` to properly formatted LaTeX.

## Quick Start

```bash
# Convert a simple expression
PYTHONPATH=src python -m txt2tex.cli -e "p and q => r"

# Save to file
PYTHONPATH=src python -m txt2tex.cli -e "not p or q <=> p => q" -o output.tex

# Use fuzz package instead of zed-*
PYTHONPATH=src python -m txt2tex.cli -e "p => q" --fuzz

# Convert from file
echo "p and q => r" > input.txt
PYTHONPATH=src python -m txt2tex.cli input.txt
```

## What Works Now (Phase 0)

### Operators
- `and` → `\land`
- `or` → `\lor`
- `not` → `\lnot`
- `=>` → `\Rightarrow`
- `<=>` → `\Leftrightarrow`

### Features
- ✅ Correct operator precedence (not > and > or > => > <=>)
- ✅ Error messages with line/column positions
- ✅ Choice of LaTeX packages (zed-* or fuzz)
- ✅ File or expression input
- ✅ Output to file or stdout

### Examples

**Input:**
```
p and q => r
```

**Output:**
```latex
\documentclass{article}
\usepackage{zed-cm}
\usepackage{zed-maths}
\usepackage{amsmath}
\begin{document}

$p \land q \Rightarrow r$

\end{document}
```

**Complex example:**
```bash
$ PYTHONPATH=src python -m txt2tex.cli -e "not p or q <=> p => q"
```

Generates: `$\lnot p \lor q \Leftrightarrow p \Rightarrow q$`

## Operator Precedence

From highest to lowest:
1. `not` (highest)
2. `and`
3. `or`
4. `=>`
5. `<=>` (lowest)

This means `not p and q or r => s` is parsed as `((not p) and q) or r) => s`.

For clarity, use explicit parentheses: `(not p) and (q or r)`.

## Command-Line Options

```
usage: cli.py [-h] [-o OUTPUT] [--fuzz] [-e] input

positional arguments:
  input                 Input text (expression or file path)

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file (default: stdout)
  --fuzz                Use fuzz package instead of zed-* packages
  -e, --expr            Treat input as expression (not file)
```

## Error Messages

The lexer and parser provide clear error messages:

```bash
$ PYTHONPATH=src python -m txt2tex.cli -e "p @ q"
Error: Line 1, column 3: Unexpected character: '@'
```

```bash
$ PYTHONPATH=src python -m txt2tex.cli -e "p and"
Error: Line 1, column 6: Expected identifier, got EOF
```

## What's Coming Next

### Phase 1: Document Structure + Truth Tables (Next)
- Section headers: `=== Title ===`
- Solution markers: `** Solution N **`
- Part labels: `(a)`, `(b)`, `(c)`
- Truth tables with proper formatting

### Phase 2: Equivalence Chains
- `EQUIV:` blocks
- Justifications in `[brackets]`

### Phase 3: Quantifiers + Math
- `forall x : N | x > 0`
- `exists y : Z | y < 0`
- Superscripts: `x^2`
- Subscripts: `a_i`
- Set operators

### Phase 4: Z Notation
- Given types, free types, abbreviations
- Schemas and axiomatic definitions

### Phase 5: Proof Trees
- Indentation-based proof structures
- Natural deduction rules

## Development

### Requirements
- Python 3.10+
- hatch (for development)

### Setup

```bash
# Create hatch environment
hatch env create

# Run tests
hatch run test

# Run quality gates
hatch run type    # MyPy type checking
hatch run lint    # Ruff linting
hatch run format  # Ruff formatting
```

### Quality Standards

All code must pass:
- ✅ MyPy strict mode (zero errors)
- ✅ Ruff linting (zero violations)
- ✅ Ruff formatting
- ✅ All tests passing
- ✅ Test coverage maintained

See `CLAUDE.md` for detailed development standards.

## Project Structure

```
sem/
├── src/txt2tex/         # Source code
│   ├── tokens.py        # Token definitions
│   ├── lexer.py         # Tokenizer
│   ├── ast_nodes.py     # AST node types
│   ├── parser.py        # Parser with precedence
│   ├── latex_gen.py     # LaTeX generator
│   └── cli.py           # Command-line interface
├── tests/
│   └── test_phase0.py   # Test suite (22 tests)
├── examples/
│   ├── phase0_simple.txt    # Example input
│   └── phase0_simple.tex    # Example output
├── latex/               # LaTeX packages (zed-*)
├── pyproject.toml       # Python project config
├── DESIGN.md            # Architecture documentation
└── README.md            # This file
```

## Design Philosophy

**Phased approach**: Each phase delivers a complete, working end-to-end system that is immediately useful for a subset of problems.

**Quality first**: All code passes strict type checking (mypy), linting (ruff), and comprehensive tests before commit.

**Parser-based**: Unlike the previous regex-based approach, this uses a proper lexer → parser → AST → generator pipeline for correctness and maintainability.

See `DESIGN.md` for complete architectural details.

## License

MIT

## Credits

- **fuzz**: Mike Spivey's Z notation package
- **zed-***: Jim Davies' Z notation packages
