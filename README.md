# txt2tex

**Write math like you're at a whiteboard. Get submission-quality LaTeX.**

txt2tex converts your plain text mathematical notation into beautifully typeset LaTeX documents. Write `forall x : N | x > 0` and get professionally formatted output perfect for assignments, papers, and proofs.

---

## Why txt2tex?

**Avoid LaTeX complexity** - Write expressions naturally, without memorizing LaTeX commands  
**Get LaTeX beauty** - Professional typesetting that looks publication-ready  
**Unlock fuzz value** - Optional type checking catches errors before submission  

Perfect for:
- 🎓 **University students** writing formal methods assignments
- 📝 **Researchers** documenting Z notation specifications
- ✍️ **Anyone** who wants beautiful math typesetting without LaTeX learning curve

---

## Installation

There are two ways to use txt2tex:

- **End users**: Install via pip to use txt2tex on your own files
- **Developers/learners**: Clone the repo to work with examples or contribute

---

### For End Users (pip install)

#### Step 1: Install txt2tex

```bash
pip install txt2tex
```

Requires **Python 3.10+**. This gives you the `txt2tex` command.

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
git clone https://github.com/jmf-pobox/fuzz.git
cd fuzz && make
sudo cp fuzz /usr/local/bin/   # Or add to PATH
```

If fuzz is not installed, txt2tex will show a note but continue normally.

#### Verify Installation

Check that all dependencies are available:

```bash
txt2tex --check-env
```

Example output:

```
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

# Install hatch (Python project manager)
pip install hatch

# Enter a development shell (installs dependencies automatically)
hatch shell

# Now txt2tex works directly
txt2tex examples/01_propositional_logic/hello_world.txt
```

**Note:** Always run `hatch shell` first after cloning. This enters a virtual environment where `txt2tex` and all dev tools are available.

#### Development Commands

Inside `hatch shell`:

```bash
# Run all quality checks (lint, type check, tests)
hatch run check

# Run tests only
hatch run test

# Build all examples
cd examples && make

# Convert a file
txt2tex myfile.txt
```

You'll also need LaTeX and optionally fuzz (see Steps 2-3 above)

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

For complete syntax reference, see **[docs/guides/USER_GUIDE.md](docs/guides/USER_GUIDE.md)**.

### Your First Document

Create a file `example.txt`:

```
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

```
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

```
axdef
  length : PossiblePlaylist -> N
where
  length(<>) = 0 land
    forall pl : PossiblePlaylist | (forall ple : ((dom status) cross N) |
      length(<ple> ^ pl) = snd(ple) + length(pl))
end
```

Write multi-line expressions exactly as they should appear in the final PDF. No explicit formatting markers needed - natural breaks work automatically.

### Z Notation

Full support for Z notation structures:

```
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

```
PROOF:
  p => q
  p
    q [modus-ponens]
```

### Truth Tables and Equivalence Chains

```
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

### Automatic Type Checking

When the fuzz binary is installed (see [Installation](#installation)), txt2tex automatically runs type checking before PDF generation. This catches undefined variables, type mismatches, and specification errors.

If fuzz is not installed, you'll see a note but compilation continues normally.

---

## Complete Syntax Reference

For detailed syntax documentation, see **[docs/guides/USER_GUIDE.md](docs/guides/USER_GUIDE.md)**.

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
# After cloning and entering hatch shell:
cd txt2tex
hatch shell

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

**See [docs/development/IDE_SETUP.md](docs/development/IDE_SETUP.md) for complete setup instructions.**

---

## Troubleshooting

### "File `zed-cm.sty' not found"

Run `txt2tex` at least once - it copies dependencies locally. If using LaTeX Workshop, reload the window after first build.

### Parse Errors

txt2tex provides clear error messages with line numbers. Common issues:
- Unsupported syntax → See [docs/guides/USER_GUIDE.md](docs/guides/USER_GUIDE.md) for supported features
- Missing quantifier separator → Use `forall x : N | predicate` (note the `|`)

### Fuzz Type Errors

Fuzz catches genuine specification errors. Check:
- Undefined variables
- Type mismatches
- Invalid operator usage

**See [docs/guides/FUZZ_VS_STD_LATEX.md](docs/guides/FUZZ_VS_STD_LATEX.md) for fuzz-specific requirements.**

---

## Known Limitations

A few edge cases require workarounds:

| Issue | Workaround |
|-------|------------|
| Prose with periods outside TEXT blocks | Wrap in `TEXT:` blocks |
| Identifiers like `R+`, `R*` | Use `RPlus`, `RStar` instead |
| Multiple pipes in TEXT blocks | Use `axdef`/`schema` for complex notation |

**For details and test cases, see [tests/bugs/README.md](tests/bugs/README.md)**

---

## Project Status

**Current Implementation:**
- ✅ **Feature complete** for typical Z specifications
- ✅ **1261 tests** - Comprehensive test suite
- ✅ **Full Z notation** - Schemas, relations, functions, sequences
- ✅ **Proof trees** - Natural deduction with justifications
- ✅ **WYSIWYG line breaks** - Natural formatting controls PDF output
- ✅ **fuzz integration** - Optional type checking

**For missing features, see [docs/guides/MISSING_FEATURES.md](docs/guides/MISSING_FEATURES.md)**

---

## Documentation

### User Guides
- **[docs/guides/USER_GUIDE.md](docs/guides/USER_GUIDE.md)** - Complete syntax reference
- **[docs/guides/FUZZ_VS_STD_LATEX.md](docs/guides/FUZZ_VS_STD_LATEX.md)** - Fuzz compatibility guide
- **[docs/guides/FUZZ_FEATURE_GAPS.md](docs/guides/FUZZ_FEATURE_GAPS.md)** - Missing features
- **[docs/guides/PROOF_SYNTAX.md](docs/guides/PROOF_SYNTAX.md)** - Proof tree notation

### Tutorials
- **[docs/tutorials/README.md](docs/tutorials/README.md)** - Tutorial index and learning path
- **[docs/tutorials/00_getting_started.md](docs/tutorials/00_getting_started.md)** - First steps
- **[docs/tutorials/01_propositional_logic.md](docs/tutorials/01_propositional_logic.md)** - Logic basics
- **[docs/tutorials/02_predicate_logic.md](docs/tutorials/02_predicate_logic.md)** - Quantifiers and predicates
- **[docs/tutorials/03_sets_and_types.md](docs/tutorials/03_sets_and_types.md)** - Sets and types
- **[docs/tutorials/04_proof_trees.md](docs/tutorials/04_proof_trees.md)** - Proof trees
- **[docs/tutorials/05_z_definitions.md](docs/tutorials/05_z_definitions.md)** - Z definitions
- **[docs/tutorials/06_relations.md](docs/tutorials/06_relations.md)** - Relations
- **[docs/tutorials/07_functions.md](docs/tutorials/07_functions.md)** - Functions
- **[docs/tutorials/08_sequences.md](docs/tutorials/08_sequences.md)** - Sequences
- **[docs/tutorials/09_schemas.md](docs/tutorials/09_schemas.md)** - Schemas
- **[docs/tutorials/10_advanced.md](docs/tutorials/10_advanced.md)** - Advanced topics

### Development Documentation
- **[docs/development/IDE_SETUP.md](docs/development/IDE_SETUP.md)** - IDE configuration
- **[docs/DESIGN.md](docs/DESIGN.md)** - Architecture and design decisions

---

## Contributing

Contributions welcome! See [For Developers](#for-developers-git-clone) for setup instructions.

1. Read [docs/DESIGN.md](docs/DESIGN.md) for architecture overview
2. Follow quality gates: `hatch run check` (type, lint, format, test)
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

- **Mike Spivey** - [fuzz](https://github.com/jmf-pobox/fuzz) package for Z notation type checking
- **Jim Davies** - zed-* packages for Z notation typesetting

---

**Last Updated:** 2025-11-29
