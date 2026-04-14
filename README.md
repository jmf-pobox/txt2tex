# txt2tex

**Write math like you're at a whiteboard. Get LaTeX you can hand in.**

txt2tex converts plain-text mathematical notation into LaTeX. Write `forall x : N | x > 0` and get rendered output suitable for assignments, papers, and proofs.

---

## Why txt2tex?

**No lock-in.** txt2tex emits standard LaTeX. Take any generated `.tex` file to Overleaf, LaTeX Workshop, or any editor you already use. Nothing proprietary, nothing one-way. If txt2tex can't express something, open the `.tex` and finish it by hand.

**Use it for one question, not your whole assignment.** Run txt2tex on the notation-heavy parts and write the rest in plain LaTeX. There's no commitment — drop in where it helps, step out where it doesn't.

**Try an expression without creating a file.** Run `txt2tex -i` to open the REPL. Type an expression, see the LaTeX and a PDF preview. Useful for checking rendering or grabbing a snippet to paste elsewhere.

**[Reference Card (PDF)](docs/cheatsheet.pdf)** — two-page reference with every operator, block type, and proof syntax, plus side-by-side examples showing what you type and what txt2tex renders.

---

## Installation

### Quick Install (macOS / Linux)

```bash
curl -fsSL https://raw.githubusercontent.com/jmf-pobox/txt2tex/main/install.sh | sh
```

This installs txt2tex, checks for LaTeX and optional tools (fuzz, latexmk), and provides platform-specific guidance for anything missing. Windows users: see [Manual Install](#manual-install) below.

---

### Manual Install

#### Step 1: Install txt2tex

```bash
pip install txt2tex
```

Requires **Python 3.12+**. This gives you the `txt2tex` command.

#### Step 2: Install LaTeX (Required for PDF output)

txt2tex generates PDF by default. You need a LaTeX distribution:

| Platform | Install Command |
|----------|-----------------|
| **macOS** | Install [MacTeX](https://www.tug.org/mactex/) (includes everything) |
| **Ubuntu/Debian** | `sudo apt install texlive-latex-extra latexmk` |
| **Windows** | Install [MiKTeX](https://miktex.org/) or [TeX Live](https://www.tug.org/texlive/) |

**Required packages:** `adjustbox`, `natbib`, `geometry`, `amsfonts`, `hyperref`

If you only need LaTeX output (no PDF), use `txt2tex input.txt --tex-only` and skip this step.

#### Step 3: Install fuzz typechecker (Optional)

The fuzz typechecker catches specification errors (undefined variables, type mismatches) before PDF generation. This is **optional but recommended** for Z notation work.

```bash
git clone https://github.com/Spivoxity/fuzz.git
cd fuzz && ./configure && make
sudo make install   # Or copy 'fuzz' binary to PATH
```

If fuzz is not installed, txt2tex will show a note but continue normally.

#### Verify Installation

Check that all dependencies are available:

```bash
txt2tex --check-env
```

Example output:

```text
txt2tex environment check
========================================
✓ pdflatex: /usr/local/texlive/2025/bin/universal-darwin/pdflatex

LaTeX packages:
  ✓ adjustbox
  ✓ natbib
  ✓ geometry
  ✓ amsfonts
  ✓ hyperref

Optional tools:
  ✓ latexmk: /usr/local/texlive/2025/bin/universal-darwin/latexmk
  ✓ bibtex: /usr/local/texlive/2025/bin/universal-darwin/bibtex
  ✓ fuzz: /usr/local/bin/fuzz

========================================
Environment OK - ready for PDF generation
```

---

### For Developers (git clone)

To work with examples, run tests, or contribute:

```bash
# Clone the repository
git clone https://github.com/jmf-pobox/txt2tex.git
cd txt2tex

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --group dev

# Now txt2tex works directly
uv run txt2tex examples/01_propositional_logic/hello_world.txt
```

#### Development Commands

```bash
# Run all quality checks (lint, type check, tests)
make check

# Lint markdown only
make lint-md

# Run tests only
make test

# Build all examples
cd examples && make

# Convert a file
txt2tex myfile.txt
```

You'll also need LaTeX and optionally fuzz (see Steps 2-3 above).

#### Agent Team (ethos)

txt2tex uses [ethos](https://github.com/punt-labs/ethos) for its development
agent team — identities, roles, and Claude Code agent definitions live in
`.punt-labs/ethos/` and are loaded automatically when you start a Claude
Code session in this repo.

```bash
# One-shot: install ethos and regenerate .claude/agents/
make dev-setup

# Verify ethos and the dev toolchain are healthy
make dev-doctor

# Inspect the team
make ethos-team
```

The team is **`txt2tex`**: `jra` (principal — Jean-Raymond Abrial) leads,
`jms` (Spivey) is the read-only Z/fuzz consultant, and specialists
(`rmh` Python, `adb` infra, `ghr` docs, `mdm` CLI, `djb` security) report
to the principal. See [docs/development/AGENTS.md](docs/development/AGENTS.md)
for how to delegate work to them.

If you do not install ethos, txt2tex still works as a CLI — ethos is only
required for contributors using Claude Code to extend the tool.

---

## Quick Start

### Syntax at a Glance

txt2tex uses intuitive keywords that mirror mathematical notation:

| You Write | You Get | Meaning |
|-----------|---------|---------|
| `forall x : N \| P(x)` | ∀x : ℕ • P(x) | Universal quantifier |
| `exists y : Z \| Q(y)` | ∃y : ℤ • Q(y) | Existential quantifier |
| `p land q` | p ∧ q | Logical AND |
| `p lor q` | p ∨ q | Logical OR |
| `lnot p` | ¬p | Logical NOT |
| `p => q` | p ⇒ q | Implication |
| `x elem S` | x ∈ S | Set membership |
| `A union B` | A ∪ B | Set union |

**Note:** Use `land`, `lor`, `lnot` for logical operators (LaTeX-style keywords).

For complete syntax reference, see **[docs/guides/USER_GUIDE.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/guides/USER_GUIDE.md)**.

### Your First Document

Create a file `example.txt`:

```text
=== My First Proof ===

** Solution 1 **

(a) Show that p land q implies p:

TRUTH TABLE:
p | q | p land q => p
T | T | T
T | F | T
F | T | T
F | F | T

(b) Using natural deduction:

PROOF:
  p land q
    p [land-elim1]
```

Convert to PDF:

```bash
txt2tex example.txt
```

Open `example.pdf` to see your beautifully formatted output!

---

## What You Can Write

### Natural Mathematical Notation

Write expressions almost exactly as you would on paper:

```text
forall x : N | x >= 0
exists y : Z | y < 0
{ x : N | x mod 2 = 0 }
lambda x : N . x^2
p land q => r
A union B
R o9 S
f(x) + g(y)
```

txt2tex converts these to properly typeset LaTeX automatically.

### WYSIWYG Line Breaks

**What You See Is What You Get** - Natural line breaks in your input control line breaks in PDF output:

```text
axdef
  sumList : seq N -> N
where
  sumList(<>) = 0 land
    forall xs : seq N | (forall x : N |
      sumList(<x> ^ xs) = x + sumList(xs))
end
```

Write multi-line expressions exactly as they should appear in the final PDF. No explicit formatting markers needed - natural breaks work automatically.

### Z Notation

Full support for Z notation structures:

```text
given Person, Company

axdef
  population : N
where
  population > 0
end

schema State
  count : N
where
  count >= 0
end
```

### Proof Trees

Natural deduction proofs with simple indentation:

```text
PROOF:
  p => q
  p
    q [modus-ponens]
```

### Truth Tables and Equivalence Chains

```text
TRUTH TABLE:
p | q | p => q
T | T | T
T | F | F

EQUIV:
lnot (p land q)
<=> lnot p lor lnot q [De Morgan]
```

---

## Usage

### Generate PDF (default)

```bash
# Convert to PDF (uses fuzz package by default)
txt2tex input.txt

# Use zed-* packages instead of fuzz
txt2tex input.txt --zed

# Keep auxiliary files (.aux, .log) for debugging
txt2tex input.txt --keep-aux
```

### Generate LaTeX Only

```bash
# Generate LaTeX without compiling to PDF
txt2tex input.txt --tex-only
```

### Interactive Mode (REPL)

Test expressions interactively without creating files:

```bash
txt2tex -i                 # Start REPL
txt2tex --interactive      # Same as above
txt2tex -i --zed           # Use zed-* packages instead of fuzz
```

Example session:

```text
$ txt2tex -i
txt2tex interactive mode. Type .help for commands.

>>> forall x : N | x >= 0
LaTeX: $\forall x : \nat \spot x \geq 0$
[PDF opens in preview]

>>> EQUIV:
... p land q
... <=> q land p [commutative]
...
LaTeX: \begin{center}...
[PDF opens in preview]

>>> .quit
Goodbye!
```

**REPL Commands:**

| Command | Description |
|---------|-------------|
| `.help` | Show help message |
| `.latex` | Toggle LaTeX-only mode (no PDF preview) |
| `.clear` | Clear screen |
| `.quit` / `.exit` | Exit REPL |

Multi-line blocks (PROOF:, EQUIV:, schema, etc.) are detected automatically — press Enter twice to execute.

### Automatic Type Checking

When the fuzz binary is installed (see [Installation](#installation)), txt2tex automatically runs type checking before PDF generation. This catches undefined variables, type mismatches, and specification errors.

If fuzz is not installed, you'll see a note but compilation continues normally.

---

## Complete Syntax Reference

For detailed syntax documentation, see **[docs/guides/USER_GUIDE.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/guides/USER_GUIDE.md)**.

The guide covers:

- Document structure (sections, solutions, parts)
- Text blocks (with smart formula detection and citations)
- Propositional and predicate logic
- Sets, relations, functions, sequences
- Z notation (schemas, axiomatic definitions, free types)
- Proof trees and natural deduction

---

## Examples

The `examples/` directory contains **141 working examples** organized by topic. **To access examples, you need to clone the repository** (see [For Developers](#for-developers-git-clone) above).

- **01_propositional_logic** - Truth tables, logical operators, propositional formulas
- **02_predicate_logic** - Quantifiers, type declarations
- **03_equality** - Equality operators, unique existence, mu operator, one-point rule
- **04_proof_trees** - Natural deduction proofs, nested proofs, pattern matching
- **05_sets** - Set operations, Cartesian products, tuples, set literals
- **06_definitions** - Free types, abbreviations, axiomatic definitions, schemas
- **07_relations** - Relation types, domain/range, restrictions, composition, relational image
- **08_functions** - Lambda expressions, function types, function definitions
- **09_sequences** - Sequence operations, concatenation, pattern matching, bags
- **10_schemas** - Schema definitions, scoping, zed blocks
- **11_text_blocks** - TEXT, PURETEXT, citations, bibliography
- **12_advanced** - Conditionals, subscripts, generic instantiation
- **user_guide** - Examples from the user guide documentation

```bash
# After cloning:
cd txt2tex
uv sync --group dev

# Build all examples
cd examples && make

# Build examples in a specific directory
cd examples && make 01_propositional_logic

# Build a specific example
txt2tex examples/01_propositional_logic/hello_world.txt
```

All 141 examples pass fuzz typechecking and compile to PDF

---

## LaTeX Output Options

### Default: fuzz Package

The standard for Z notation with built-in type checking:

- Custom Oxford fonts
- Type validation during compilation
- Compatible with fuzz-based toolchains

**Note:** Fuzz doesn't support identifiers with underscores (use camelCase instead).

### Optional: zed-* Packages

Works on any LaTeX installation, no custom fonts needed:

- Computer Modern fonts
- Excellent proof tree support
- Industry-standard Z notation rendering

Use `--zed` flag: `txt2tex input.txt --zed`

---

## IDE Integration (VSCode/Cursor)

### LaTeX Workshop Setup

1. Install **LaTeX Workshop** extension in VSCode/Cursor
2. Edit your `.txt` files
3. Run `txt2tex myfile.txt` to generate PDF
4. Or use `txt2tex myfile.txt --tex-only` for LaTeX Workshop live preview

The project includes pre-configured settings:

- `.vscode/settings.json` - LaTeX Workshop configuration
- `.latexmkrc` - Build settings for natbib citations

**See [docs/development/IDE_SETUP.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/development/IDE_SETUP.md) for complete setup instructions.**

---

## Overleaf Workflow

If you prefer to edit LaTeX in [Overleaf](https://www.overleaf.com/), you can use txt2tex to generate the initial `.tex` file and then upload it for final editing:

### Step 1: Generate LaTeX

```bash
txt2tex input.txt --tex-only
```

This creates `input.tex` and copies the required style files to your directory.

### Step 2: Upload to Overleaf

Upload these files to your Overleaf project:

| File | Purpose |
|------|---------|
| `input.tex` | Your generated LaTeX document |
| `fuzz.sty` | Z notation package (omit if using `--zed`) |
| `zed-*.sty` | Z notation support packages (zed-cm, zed-float, zed-lbr, zed-maths, zed-proof) |
| `*.mf` | METAFONT files (oxsz*.mf, zarrow.mf, zletter.mf, zsymbol.mf) |

### Step 3: Compile in Overleaf

Set the compiler to **pdfLaTeX** in Overleaf's settings. The document should compile with all Z notation symbols rendering correctly.

This workflow lets you use txt2tex for the initial conversion, then make final adjustments directly in Overleaf's editor.

---

## Troubleshooting

### "File `zed-cm.sty' not found"

Run `txt2tex` at least once - it copies dependencies locally. If using LaTeX Workshop, reload the window after first build.

### Parse Errors

txt2tex provides clear error messages with line numbers. Common issues:

- Unsupported syntax → See [docs/guides/USER_GUIDE.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/guides/USER_GUIDE.md) for supported features
- Missing quantifier separator → Use `forall x : N | predicate` (note the `|`)

### Fuzz Type Errors

Fuzz catches genuine specification errors. Check:

- Undefined variables
- Type mismatches
- Invalid operator usage

**See [docs/guides/FUZZ_VS_STD_LATEX.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/guides/FUZZ_VS_STD_LATEX.md) for fuzz-specific requirements.**

---

## Known Limitations

**⚠️ Always proofread your output.** txt2tex makes design choices about how to render complex mathematical expressions. The generated LaTeX may not match your preferred formatting in all cases. Review your final PDF carefully.

A few edge cases require workarounds:

| Issue | Workaround |
|-------|------------|
| Prose with periods outside TEXT blocks | Wrap in `TEXT:` blocks |
| Identifiers like `R+`, `R*` | Use `RPlus`, `RStar` instead |
| Multiple pipes in TEXT blocks | Use `axdef`/`schema` for complex notation |

**For details and test cases, see [tests/bugs/README.md](https://github.com/jmf-pobox/txt2tex/blob/main/tests/bugs/README.md)**

---

## Project Status

**Current Implementation:**

- ✅ **Feature complete** for typical Z specifications
- ✅ **1280 tests** - Comprehensive test suite
- ✅ **Full Z notation** - Schemas, relations, functions, sequences
- ✅ **Proof trees** - Natural deduction with justifications
- ✅ **WYSIWYG line breaks** - Natural formatting controls PDF output
- ✅ **Interactive mode** - REPL for testing expressions
- ✅ **fuzz integration** - Optional type checking

**For missing features, see [docs/guides/MISSING_FEATURES.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/guides/MISSING_FEATURES.md)**

---

## Documentation

### User Guides

- **[docs/guides/USER_GUIDE.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/guides/USER_GUIDE.md)** - Complete syntax reference
- **[docs/guides/FUZZ_VS_STD_LATEX.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/guides/FUZZ_VS_STD_LATEX.md)** - Fuzz compatibility guide
- **[docs/guides/MISSING_FEATURES.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/guides/MISSING_FEATURES.md)** - Missing features
- **[docs/guides/PROOF_SYNTAX.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/guides/PROOF_SYNTAX.md)** - Proof tree notation

### Tutorials

- **[docs/tutorials/README.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/tutorials/README.md)** - Tutorial index and learning path
- **[docs/tutorials/00_getting_started.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/tutorials/00_getting_started.md)** - First steps
- **[docs/tutorials/01_propositional_logic.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/tutorials/01_propositional_logic.md)** - Logic basics
- **[docs/tutorials/02_predicate_logic.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/tutorials/02_predicate_logic.md)** - Quantifiers and predicates
- **[docs/tutorials/03_sets_and_types.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/tutorials/03_sets_and_types.md)** - Sets and types
- **[docs/tutorials/04_proof_trees.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/tutorials/04_proof_trees.md)** - Proof trees
- **[docs/tutorials/05_z_definitions.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/tutorials/05_z_definitions.md)** - Z definitions
- **[docs/tutorials/06_relations.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/tutorials/06_relations.md)** - Relations
- **[docs/tutorials/07_functions.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/tutorials/07_functions.md)** - Functions
- **[docs/tutorials/08_sequences.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/tutorials/08_sequences.md)** - Sequences
- **[docs/tutorials/09_schemas.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/tutorials/09_schemas.md)** - Schemas
- **[docs/tutorials/10_advanced.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/tutorials/10_advanced.md)** - Advanced topics

### Development Documentation

- **[docs/development/IDE_SETUP.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/development/IDE_SETUP.md)** - IDE configuration
- **[docs/DESIGN.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/DESIGN.md)** - Architecture and design decisions

---

## Contributing

Contributions welcome! See [For Developers](#for-developers-git-clone) for setup instructions.

1. Read [docs/DESIGN.md](https://github.com/jmf-pobox/txt2tex/blob/main/docs/DESIGN.md) for architecture overview
2. Follow quality gates: `make check` (lint, format, type, test)
3. Add tests for new features
4. Update documentation

---

## License

MIT

---

## Credits

### Acknowledgements

This tool was developed to support formal methods education. The notation and syntax are based on standard Z notation as described in:

- J.M. Spivey, *The Z Notation: A Reference Manual* (2nd ed.)
- J. Woodcock and J. Davies, *Using Z: Specification, Refinement, and Proof*

### Software Dependencies

- **Mike Spivey** - [fuzz](https://github.com/Spivoxity/fuzz) typechecker for Z notation
- **Jim Davies** - zed-* packages for Z notation typesetting

### Z Notation Resources

Online references for learning Z notation:

- **[The Z Notation: A Reference Manual](https://github.com/Spivoxity/zrm/blob/master/zrm-pub.pdf)** - J.M. Spivey, 2nd edition (free PDF on GitHub)
- **[The fuzz Manual](https://bitbucket-archive.softwareheritage.org/static/93/93ff4436-a8e5-4c1d-a3f1-774369ab2d00/attachments/fuzzman.pdf)** - Complete documentation for the fuzz type checker (PDF)
- **[ISO Z Standard](https://www.iso.org/standard/21573.html)** - ISO/IEC 13568:2002 formal specification
- **[Z Notation Wikipedia](https://en.wikipedia.org/wiki/Z_notation)** - Overview and history
- **[Community Z Tools](https://czt.sourceforge.net/)** - Open source Z tools and resources
