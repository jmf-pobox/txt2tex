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

## Quick Start

### Prerequisites

- **Python 3.10+**
- **LaTeX distribution** (TeX Live recommended)
- **hatch** (for running commands)

```bash
# Install hatch if needed
pip install hatch

# Verify installation
hatch run cli --help
```

### Your First Document

Create a file `example.txt`:

```
=== My First Proof ===

** Solution 1 **

(a) Show that p and q implies p:

TRUTH TABLE:
p | q | p and q => p
T | T | T
T | F | T
F | T | T
F | F | T

(b) Using natural deduction:

PROOF:
  p and q
    p [and-elim1]
```

Convert to PDF:

```bash
hatch run convert example.txt
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
p and q => r
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
  length(<>) = 0 and
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
not (p and q)
<=> not p or not q [De Morgan]
```

---

## Usage

### Basic Conversion

```bash
# Convert txt to PDF
hatch run convert input.txt

# Or use the shell script
./txt2pdf.sh input.txt
```

### With Type Checking (fuzz)

Validate your Z notation with Mike Spivey's fuzz type checker:

```bash
hatch run convert input.txt --fuzz
```

Fuzz catches type errors, undefined variables, and other specification issues before you submit.

### LaTeX Only (No PDF)

Generate LaTeX without compiling:

```bash
hatch run cli input.txt --latex-only -o output.tex
```

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

The `examples/` directory contains **48 working examples** organized by topic:

- **01_propositional_logic** (4 examples) - Truth tables, logical operators, propositional formulas
- **02_predicate_logic** (2 examples) - Quantifiers, type declarations
- **03_equality** (4 examples) - Equality operators, unique existence, mu operator, one-point rule
- **04_proof_trees** (5 examples) - Natural deduction proofs, nested proofs, pattern matching
- **05_sets** (6 examples) - Set operations, Cartesian products, tuples, set literals
- **06_definitions** (6 examples) - Free types, abbreviations, axiomatic definitions, schemas
- **07_relations** (7 examples) - Relation types, domain/range, restrictions, composition, relational image
- **08_functions** (4 examples) - Lambda expressions, function types, function definitions
- **09_sequences** (5 examples) - Sequence operations, concatenation, pattern matching, bags
- **fuzz_tests** (5 examples) - Additional fuzz type checking examples

```bash
# Build all examples
cd examples && make

# Build examples in a specific directory
cd examples && make 01_propositional_logic

# Build a specific example
hatch run convert examples/01_propositional_logic/hello_world.txt
```

---

## LaTeX Output Options

### Default: zed-* Packages

Works on any LaTeX installation, no custom fonts needed:
- Computer Modern fonts
- Excellent proof tree support
- Industry-standard Z notation rendering

### Optional: fuzz Package

Historical standard for Z notation with built-in type checking:
- Custom Oxford fonts
- Type validation during compilation
- Compatible with fuzz-based toolchains

Use `--fuzz` flag: `hatch run convert input.txt --fuzz`

**Note:** Fuzz doesn't support identifiers with underscores (use camelCase instead).

---

## IDE Integration (VSCode/Cursor)

### LaTeX Workshop Setup

1. Install **LaTeX Workshop** extension in VSCode/Cursor
2. Edit your `.txt` files
3. Run `hatch run convert myfile.txt` to generate `.tex`
4. LaTeX Workshop auto-compiles and shows PDF preview

The project includes pre-configured settings:
- `.vscode/settings.json` - LaTeX Workshop configuration
- `.latexmkrc` - Build settings for natbib citations

**See [docs/development/IDE_SETUP.md](docs/development/IDE_SETUP.md) for complete setup instructions.**

---

## Troubleshooting

### "File `zed-cm.sty' not found"

Run `hatch run convert` at least once - it copies dependencies locally. If using LaTeX Workshop, reload the window after first build.

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
- ✅ **100% solution coverage** (52 of 52 homework solutions working)
- ✅ **1145 tests** - Comprehensive test suite
- ✅ **Full Z notation** - Schemas, relations, functions, sequences
- ✅ **Proof trees** - Natural deduction with justifications
- ✅ **WYSIWYG line breaks** - Natural formatting controls PDF output
- ✅ **fuzz integration** - Optional type checking

**For detailed status, see [docs/development/STATUS.md](docs/development/STATUS.md)**

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
- Plus 7 more tutorials covering sets, proof trees, relations, functions, sequences, schemas, and advanced topics

### Development Documentation
- **[docs/development/STATUS.md](docs/development/STATUS.md)** - Implementation status and roadmap
- **[docs/development/IDE_SETUP.md](docs/development/IDE_SETUP.md)** - IDE configuration
- **[docs/development/QA_PLAN.md](docs/development/QA_PLAN.md)** - Quality assurance procedures
- **[docs/DESIGN.md](docs/DESIGN.md)** - Architecture and design decisions

---

## Contributing

Contributions welcome! Please:

1. Read [docs/DESIGN.md](docs/DESIGN.md) for architecture overview
2. Follow quality gates: `hatch run check` (type, lint, format, test)
3. Add tests for new features
4. Update documentation

---

## License

MIT

---

## Credits

- **Mike Spivey** - fuzz package for Z notation type checking
- **Jim Davies** - zed-* packages for Z notation typesetting

---

**Last Updated:** 2025-11-20
