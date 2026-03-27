# Claude Code: Project Context and Instructions

## 🚨 CRITICAL: Use Proper Workflow Commands

**Use the txt2tex CLI for conversions:**

```bash
# Convert txt to PDF (default behavior)
txt2tex examples/file.txt

# LaTeX only (no PDF compilation)
txt2tex examples/file.txt --tex-only

# Use zed-* packages instead of fuzz
txt2tex examples/file.txt --zed
```

The CLI handles:
- PDF generation with pdflatex/latexmk (default)
- Bundled .sty/.mf files copied automatically
- Fuzz typechecking when fuzz binary is available
- Cleanup of auxiliary files
- tex-fmt formatting (with `--format` flag)

## Project Overview

This is `txt2tex` - a tool to convert whiteboard-style mathematical notation to high-quality LaTeX that can be typechecked with fuzz and compiled to PDF.

**Goal**: Enable users to write mathematical proofs and solutions in plain ASCII (as they would on a whiteboard) and automatically convert them to properly formatted LaTeX documents.

## Key Documentation Files

Essential reading for understanding the project:

- **[CLAUDE.md](CLAUDE.md)** (this file) - Project context, workflow commands, coding standards, session management
- **[docs/DESIGN.md](docs/DESIGN.md)** - Architecture, design decisions, operator precedence, AST structure
- **[docs/guides/USER_GUIDE.md](docs/guides/USER_GUIDE.md)** - User-facing syntax guide, whiteboard notation reference
- **[docs/guides/PROOF_SYNTAX.md](docs/guides/PROOF_SYNTAX.md)** - Proof tree syntax and formatting rules
- **[docs/guides/FUZZ_VS_STD_LATEX.md](docs/guides/FUZZ_VS_STD_LATEX.md)** - Fuzz vs standard LaTeX differences (critical for understanding fuzz quirks)
- **[docs/guides/MISSING_FEATURES.md](docs/guides/MISSING_FEATURES.md)** - Missing Z notation features, implementation roadmap

**Note**: Always check FUZZ_VS_STD_LATEX.md when debugging LaTeX/PDF rendering issues - fuzz has different requirements than standard LaTeX.

## CRITICAL: Code Quality Standards (MANDATORY)

**🚨 ABSOLUTE REQUIREMENTS - NO EXCEPTIONS:**

### Required Quality Gates (Run After EVERY Code Change)
```bash
make type           # 1. ZERO MyPy errors (strict mode)
make type-pyright   # 2. ZERO Pyright errors (strict mode)
make lint           # 3. ZERO Ruff violations
make format         # 4. Perfect formatting
make test           # 5. ALL tests pass
make test-cov       # 6. Coverage maintained
```

### Code Standards (MANDATORY)
- **Type hints**: Full type annotations on all functions and methods
- **MyPy strict mode**: No Any types, no untyped definitions
- **Protocol inheritance**: All protocol implementations must explicitly inherit
- **Fail fast**: No defensive coding, raise exceptions on validation failure
- **No inline imports**: All imports at top of file, grouped by PEP 8
- **Direct imports**: Use `from __future__ import annotations`
- **88 character line limit**: Enforced by ruff
- **Double quotes**: For strings (enforced by ruff format)

### Prohibited Patterns
- ❌ No `type | None` parameters unless absolutely necessary
- ❌ No inline import statements
- ❌ No mock objects in production code (tests only)
- ❌ No defensive coding or fallback logic unless explicitly requested
- ❌ No `hasattr()` - use protocols instead
- ❌ No duck typing - use explicit protocol inheritance

### Micro-Commit Workflow (MANDATORY)
- **One change** = One commit (extract function, fix bug, add test)
- **Commit size limits**: 1-5 files, <100 lines preferred
- **Branch workflow**: ALL development on feature branches
- **Quality gates between commits**: Run all 5 commands above

### Communication Standards
- ❌ Never claim "fixed" without user confirmation
- ❌ No buzzwords, jargon, or superlatives
- ❌ No exaggeration or enthusiasm about unverified results
- ❌ **DO NOT CODE when asked yes/no questions** - just answer the question
- ✅ State what changed and why
- ✅ Explain what needs user verification
- ✅ Use plain, accurate language
- ✅ Modest, short commit messages
- ✅ Answer questions directly without over-engineering

### Solution Standards (MANDATORY)
- ✅ **Proper solution first**: Identify and implement the correct solution immediately
- ✅ **No compromises on false warnings**: False warnings train you to ignore logs - unacceptable
- ✅ **Industry standard tools**: Use professional tools (e.g., latexmk) not manual workarounds
- ❌ **No shortcuts or hacks**: Don't offer inferior alternatives to save time
- ❌ **No warning filters to hide problems**: Fix the root cause, don't mask symptoms

## Workflow Commands

**ALWAYS use `make` targets (defined in Makefile, backed by uv):**

### Development Workflow
```bash
# Full pipeline (txt → tex → pdf) - DEFAULT
txt2tex <file>

# LaTeX generation only (txt → tex)
txt2tex <file> --tex-only

# With tex-fmt formatting
txt2tex <file> --format

# Quality gates (run after every change)
make type           # Type checking with mypy
make type-pyright   # Type checking with pyright
make lint           # Linting with ruff
make format         # Format code
make test           # Run ALL tests
make test-cov       # Run tests with coverage

# Run specific tests
make test ARGS="tests/test_08_functions/test_lambda_expressions.py"                                          # Single file
make test ARGS="tests/test_08_functions/test_lambda_expressions.py -v"                                       # Verbose output
make test ARGS="tests/test_08_functions/test_lambda_expressions.py::TestLambdaParsing"                       # Single test class
make test ARGS="tests/test_08_functions/test_lambda_expressions.py::TestLambdaParsing::test_simple_lambda -v" # Single test method

# Combined quality check
make check          # lint + format-check + type + type-pyright + test
make check-cov      # lint + format-check + type + type-pyright + test-cov
```

**Important**: The CLI copies bundled .sty/.mf files automatically and uses latexmk for bibliography handling when available.

## Environment Setup

### Critical Dependencies

1. **fuzz**: Z notation typesetting system
   - Location: `../tex/` (relative to project root)
   - Main file: `fuzz.sty`
   - Fonts: `oxsz*.mf`, `zarrow.mf`, `zletter.mf`, `zsymbol.mf`

2. **zed-* packages** (in `src/txt2tex/latex/` directory):
   - `zed-cm.sty` - Z notation in Computer Modern fonts
   - `zed-float.sty` - Floating Z notation environments
   - `zed-lbr.sty` - Line breaking rules for Z
   - `zed-maths.sty` - Mathematical operators for Z
   - `zed-proof.sty` - Proof tree formatting

3. **LaTeX Distribution**: TeX Live 2025
   - Platform: macOS (Darwin 24.6.0)

### Key Difference: fuzz vs zed-* packages

The project supports both **fuzz** and **zed-*** packages for Z notation:
- **fuzz**: Mike Spivey's Z notation package with type checking (default)
- **zed-***: Jim Davies' Z notation packages (use `--zed` flag)

## Compilation and Testing

### Verifying Output

```bash
# Generate and compile to PDF in one step
txt2tex examples/04_proof_trees/simple_proofs.txt

# Extract text from PDF for verification
pdftotext examples/04_proof_trees/simple_proofs.pdf -

# Verify output looks correct
# (manual visual inspection)
```

### LaTeX Package Handling

The CLI automatically copies bundled .sty and .mf files to the working directory before compilation:
- `fuzz.sty` - Z notation with Oxford fonts (default)
- `zed-*.sty` - Z notation with Computer Modern fonts (--zed flag)
- `*.mf` - METAFONT font definitions

Files are cleaned up after successful compilation unless `--keep-aux` is used.

## Input Format (Whiteboard Notation)

### Structural Elements

```
=== Section Title ===         → \section*{Section Title}

** Solution N **              → \textbf{Solution N} with spacing

(a) Text here                 → Part label with \medskip after
(b) Another part

TRUTH TABLE:                  → \begin{tabular}...\end{tabular}
p | q | p land q
T | T | T

EQUIV:                        → \begin{align*}...\end{align*}
p land q
<=> q land p [commutative]

PROOF:                        → \begin{itemize} with indentation
  premise
    conclusion
```

### Operators

```
land   → \land              (logical AND)
lor    → \lor               (logical OR)
lnot   → \lnot              (logical NOT)
=>     → \Rightarrow        (implication)
<=>    → \Leftrightarrow    (equivalence)
forall → \forall            (universal quantifier)
exists → \exists            (existential quantifier)
elem   → \in                (set membership)
 |     → \bullet            (in quantified predicates)
```

**Note:** Use `land`, `lor`, `lnot` (LaTeX-style). English `and`, `or`, `not` are NOT supported.

### Z Notation

```
given A, B                    → \begin{zed}[A, B]\end{zed}
Type ::= branch1 | branch2    → Free type definition
abbrev == expression          → Abbreviation

axdef                         → \begin{axdef}...\end{axdef}
  declarations
where
  predicates
end

schema Name                   → \begin{schema}{Name}...\end{schema}
  declarations
where
  predicates
end
```

## User's Preferences

From conversation:
1. ✅ "Want to write like on a whiteboard"
2. ✅ "Willing to hunt down very small issues in LaTeX"
3. ✅ "Want fuzz validation as a feature" - Typechecking is important
4. ✅ "Need submission-ready PDFs" - High quality output required

⏳ **Create documentation**:
   - CLAUDE.md (this file) ✅
   - README.md (user-facing)
   - docs/DESIGN.md (software design)

## Important Notes for Claude

### When Making Design Decisions
- Prioritize correctness over convenience
- User prefers robust solution over quick hacks
- Typechecking with fuzz is a core feature, not optional
- Output must be submission-quality

### Recent Investigations (November 2025)

#### ARGUE Environment Investigation (RESOLVED)

**Question**: Should we use fuzz's `\begin{argue}` environment for ARGUE/EQUIV blocks?

**Investigation** (November 25, 2025):
- Systematically tested fuzz's `argue` environment for equational reasoning blocks
- Created test files to stress-test spacing and overflow scenarios
- Root cause analysis: `argue` uses `\hbox to0pt` (zero-width boxes) for justifications
- **Problem 1**: No minimum column spacing - expressions and justifications overlap when both are wide
- **Problem 2**: Cannot use `adjustbox` for conditional scaling - `\halign` incompatible with LR mode

**Attempted Fixes**:
- Created `argue-fixed.sty` with `\hspace{2em}` spacing - fixed spacing but not scaling
- Tried `\resizebox + minipage` - requires guessing content width, no conditional scaling

**Decision**: ✅ **Stick with array-based implementation**
- Uses standard LaTeX `\begin{array}{l@{\hspace{2em}}r}`
- Guaranteed 2em column spacing
- Works perfectly with `adjustbox{max width=\textwidth}` for conditional scaling
- All 1199 tests passing

**Documentation**: Complete analysis in DESIGN.md §6

**Key Insight**: The `adjustbox` package is critical for handling unpredictable content width in:
1. Truth tables (multi-column with complex headers)
2. ARGUE/EQUIV blocks (long expressions AND long justifications)
3. Proof trees (wide inference rules with multiple premises)

The argue environment's use of raw `\halign` makes conditional scaling impossible, which was the deciding factor.

## Debugging Tips

### Common LaTeX Errors

1. **Missing fonts**: Ensure `MFINPUTS=../tex//:` is set
2. **Missing fuzz.sty**: Ensure `TEXINPUTS=../tex//:` is set
3. **`#` in math mode**: The `#` character needs escaping, but not in Z notation cardinality `\# s`
4. **Spacing issues**: Often caused by improper math mode delimiters

### Verification Commands

```bash
# Check if fuzz is accessible
ls ../tex/fuzz.sty

# Verify PDF was generated
ls -lh output.pdf

# Extract and inspect text
pdftotext output.pdf - | less

# Check LaTeX log for errors
grep -i error output.log
```

## Bug Reporting Workflow

When you encounter a bug:

1. **Create minimal test case**:
   ```bash
   echo "=== Bug N Test: Description ===" > tests/bugs/bugN_short_name.txt
   echo "[minimal failing example]" >> tests/bugs/bugN_short_name.txt
   ```

2. **Verify it fails**:
   ```bash
   txt2tex tests/bugs/bugN_short_name.txt
   ```

3. **Create GitHub issue**:
   - Use bug report template at `.github/ISSUE_TEMPLATE/bug_report.md`
   - Include test case location and exact error/output
   - See `.github/ISSUES_TO_CREATE.md` for examples

4. **Update documentation**:
   - Reference issue number and test case file

5. **Link in code** (if fixing):
   - Reference issue number in commit messages
   - Link to test file from code comments

**Known Bugs**: See [tests/bugs/README.md](tests/bugs/README.md) for active bugs with test cases.

**Bug Test Cases**: All bugs have minimal reproducible test cases in `tests/bugs/` - see [tests/bugs/README.md](tests/bugs/README.md).

## Session Management

If starting fresh from the project root:
1. Remember fuzz is in `./latex/`
2. Test files are in parent directory `./tests/`
3. Use workflow commands at the top of this document
4. Reference this document for context
- always run make check before each micro-commit and solve 100% of any issues reported
- there are no pre-existing issues that should be used to justify anything
- success is defined as 100%. Do not ask to settle for lower standards of success.
- you should always find the root cause, which you can do it if you are patient and tenacious
- The user makes the decisions, you need to ask before making up rationales and decisions.
- Remember that .tex files should be committed even though they are generated they are first class assets.