# Claude Code: Project Context and Instructions

## 🚨 CRITICAL: Use Proper Workflow Commands

**NEVER manually invoke pdflatex!** Always use:

```bash
# Convert txt to PDF (THE CORRECT WAY)
hatch run convert examples/file.txt
# OR
./txt2pdf.sh examples/file.txt
```

The `txt2pdf.sh` script handles all the complexity:
- Sets PYTHONPATH correctly
- Generates LaTeX with txt2tex CLI
- Sets TEXINPUTS and MFINPUTS for fuzz/zed-* packages
- Compiles with pdflatex
- Cleans up auxiliary files

**DO NOT** manually run `pdflatex` with environment variables - you will forget steps and it will fail.

## Project Overview

This is `txt2tex` - a tool to convert whiteboard-style mathematical notation to high-quality LaTeX that can be typechecked with fuzz and compiled to PDF.

**Goal**: Enable users to write mathematical proofs and solutions in plain ASCII (as they would on a whiteboard) and automatically convert them to properly formatted LaTeX documents.

## Key Documentation Files

Essential reading for understanding the project:

- **[CLAUDE.md](CLAUDE.md)** (this file) - Project context, workflow commands, coding standards, session management
- **[STATUS.md](STATUS.md)** - Current implementation status, phase tracking, test counts, recent changes
- **[DESIGN.md](DESIGN.md)** - Architecture, design decisions, operator precedence, AST structure
- **[USER-GUIDE.md](USER-GUIDE.md)** - User-facing syntax guide, whiteboard notation reference
- **[PROOF_SYNTAX.md](PROOF_SYNTAX.md)** - Proof tree syntax and formatting rules
- **[QA_PLAN.md](QA_PLAN.md)** - Quality assurance checklist, testing procedures
- **[docs/FUZZ_VS_STD_LATEX.md](docs/FUZZ_VS_STD_LATEX.md)** - Fuzz vs standard LaTeX differences (critical for understanding fuzz quirks)
- **[docs/FUZZ_FEATURE_GAPS.md](docs/FUZZ_FEATURE_GAPS.md)** - Missing Z notation features, implementation roadmap

**Note**: Always check FUZZ_VS_STD_LATEX.md when debugging LaTeX/PDF rendering issues - fuzz has different requirements than standard LaTeX.

## CRITICAL: Code Quality Standards (MANDATORY)

**🚨 ABSOLUTE REQUIREMENTS - NO EXCEPTIONS:**

### Required Quality Gates (Run After EVERY Code Change)
```bash
hatch run type           # 1. ZERO MyPy errors (strict mode)
hatch run lint           # 2. ZERO Ruff violations
hatch run format         # 3. Perfect formatting
hatch run test           # 4. ALL tests pass
hatch run test-cov       # 5. Coverage maintained
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

**ALWAYS use these commands (defined in pyproject.toml):**

### Development Workflow
```bash
# LaTeX generation only (txt → tex)
hatch run cli <file>

# Full pipeline (txt → tex → pdf)
hatch run convert <file>
# OR directly:
./txt2pdf.sh <file>

# Quality gates (run after every change)
hatch run type           # Type checking with mypy
hatch run lint           # Linting with ruff
hatch run format         # Format code
hatch run test           # Run ALL tests
hatch run test-cov       # Run tests with coverage

# Run specific tests (use hatch run test with path arguments)
hatch run test tests/test_phase11d.py                           # Single file
hatch run test tests/test_phase11d.py -v                        # Verbose output
hatch run test tests/test_phase11d.py::TestPhase11dParsing     # Single test class
hatch run test tests/test_phase11d.py::TestPhase11dParsing::test_simple_lambda -v  # Single test method

# Combined quality check
hatch run check          # lint + type + test
hatch run check-cov      # lint + type + test-cov
```

### Direct Python Invocation (if needed)
```bash
# CLI (from sem/ directory)
PYTHONPATH=src python -m txt2tex.cli <file>

# Running tests
PYTHONPATH=src pytest tests
```

**Important**: The `txt2pdf.sh` script handles TEXINPUTS/MFINPUTS automatically. Don't manually invoke pdflatex unless debugging LaTeX compilation issues.

## Environment Setup

### Critical Dependencies

1. **fuzz**: Z notation typesetting system
   - Location: `/Users/jfreeman/Coding/fuzz/txt2tex/tex/`
   - Main file: `fuzz.sty`
   - Fonts: `oxsz*.mf`, `zarrow.mf`, `zletter.mf`, `zsymbol.mf`
   - When compiling: Use `TEXINPUTS=../tex//: MFINPUTS=../tex//: pdflatex ...`

2. **Instructor's Z packages** (in this `sem/` directory):
   - `zed-cm.sty` - Z notation in Computer Modern fonts
   - `zed-float.sty` - Floating Z notation environments
   - `zed-lbr.sty` - Line breaking rules for Z
   - `zed-maths.sty` - Mathematical operators for Z
   - `zed-proof.sty` - Proof tree formatting

3. **LaTeX Distribution**: TeX Live 2025
   - Platform: macOS (Darwin 24.6.0)

### Key Difference: fuzz vs zed-* packages

The project has been using **fuzz** (`../tex/fuzz.sty`) which provides its own Z notation support. The instructor's materials use **zed-*** packages. These are different implementations:
- **fuzz**: Mike Spivey's Z notation package (what we've been using)
- **zed-***: Alternative Z notation packages (instructor's preference)

**Decision needed**: The new system should support both, or choose one. The current txt2tex_v3.py generates LaTeX that uses fuzz.

## Previous Work

### Version History

1. **txt2tex_v1.py** - Initial attempt (not in current directory)
2. **txt2tex_v2.py** - Iteration (not in current directory)
3. **txt2tex_v3.py** - Current implementation (in parent directory: `/Users/jfreeman/Coding/fuzz/txt2tex/`)

### txt2tex_v3.py Architecture (Current - Regex-based)

**Location**: `/Users/jfreeman/Coding/fuzz/txt2tex/txt2tex_v3.py`

**Approach**: Pure regex/string replacement
- Dictionary of operator mappings (`self.ops`)
- Regex patterns for structural elements
- Character-by-character iteration for escaping
- No parser, no AST, no semantic understanding

**Key Issues Fixed** (chronologically):
1. ✅ Solution spacing (added `\bigskip`, `\noindent`)
2. ✅ Line spacing between parts (added `\medskip`)
3. ✅ Implication symbol `[=>]` in justifications
4. ✅ "De Morgan" corruption (word boundaries)
5. ✅ `[<=>]` operator ordering
6. ✅ `[or and true]` position-based replacement
7. ✅ Bullet symbol `|` → `\bullet`
8. ✅ Superscript handling `x^2` → `$x^{2}$`

**Current Problems with Regex Approach**:
- Fragile: Each fix creates new edge cases
- Context-blind: Can't distinguish math from prose reliably
- Order-dependent: Replacement order matters critically
- Hard to maintain: Growing complexity with each feature
- No semantic understanding: Just pattern matching

### Test Files

**Input**: `/Users/jfreeman/Coding/fuzz/txt2tex/solutions_complete.txt`
- Whiteboard-style notation
- ~27 pages when rendered

**Reference**: `/Users/jfreeman/Coding/fuzz/txt2tex/solutions.pdf`
- Correctly formatted PDF from instructor
- Target for comparison

**Generated**:
- `/Users/jfreeman/Coding/fuzz/txt2tex/solutions_complete.tex` (intermediate LaTeX)
- `/Users/jfreeman/Coding/fuzz/txt2tex/solutions_complete.pdf` (27 pages, ~180KB)

## Compilation and Testing

### Verifying Output

```bash
# Generate and compile to PDF in one step
./txt2pdf.sh examples/phase5.txt

# Extract text from PDF for verification
pdftotext examples/phase5.pdf -

# Compare with reference
# (manual visual comparison with solutions.pdf)
```

### LaTeX Environment Variables (handled by txt2pdf.sh)

- `TEXINPUTS=../tex//:` - Tells LaTeX to search `../tex/` for style files (fuzz)
- `TEXINPUTS=./latex//:` - Also searches local latex/ directory for zed-* packages
- `MFINPUTS=../tex//:` - Tells METAFONT to search `../tex/` for fonts
- `-interaction=nonstopmode` - Don't stop on LaTeX errors (check .log file)

## Input Format (Whiteboard Notation)

### Structural Elements

```
=== Section Title ===         → \section*{Section Title}

** Solution N **              → \textbf{Solution N} with spacing

(a) Text here                 → Part label with \medskip after
(b) Another part

TRUTH TABLE:                  → \begin{tabular}...\end{tabular}
p | q | p and q
T | T | T

EQUIV:                        → \begin{align*}...\end{align*}
p and q
<=> q and p [commutative]

PROOF:                        → \begin{itemize} with indentation
  premise
    conclusion
```

### Operators

```
and    → \land
or     → \lor
not    → \lnot
=>     → \Rightarrow
<=>    → \Leftrightarrow
forall → \forall
exists → \exists
 | → \bullet (in quantified predicates)
x^2    → $x^{2}$ (in prose)
```

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

## Git Repository

- **Current**: Not in version control
- **Needed**: Initialize git in `/Users/jfreeman/Coding/fuzz/txt2tex/sem/`

## User's Preferences

From conversation:
1. ✅ "OK to require non-ASCII symbols in txt format" - User is willing to type Unicode directly
2. ✅ "Want to write like on a whiteboard" - Natural, minimal syntax
3. ✅ "Willing to hunt down very small issues in LaTeX" - Doesn't need 100% perfection
4. ✅ "Want fuzz validation as a feature" - Typechecking is important
5. ✅ "Need submission-ready PDFs" - High quality output required

## Next Steps (As of Session Pause)

1. ❌ **Pause regex approach** - Acknowledged it's fragile
2. ⏳ **Design proper rewrite** - Need parser-based approach
3. ⏳ **Set up sem/ directory** - New project location
4. ⏳ **Initialize git** - Version control
5. ⏳ **Create documentation**:
   - CLAUDE.md (this file) ✅
   - DESIGN.md (software design)
   - README.md (user-facing)

## Important Notes for Claude

### When Compiling LaTeX
Always use the TEXINPUTS and MFINPUTS environment variables to ensure fuzz fonts and styles are found:
```bash
TEXINPUTS=../tex//: MFINPUTS=../tex//: pdflatex file.tex
```

### When Testing
Compare output against `/Users/jfreeman/Coding/fuzz/txt2tex/solutions.pdf` (reference).

### When Making Design Decisions
- Prioritize correctness over convenience
- User prefers robust solution over quick hacks
- Typechecking with fuzz is a core feature, not optional
- Output must be submission-quality

### Code Quality
User noticed we were "refining regex over and over again" and wants a proper architecture. They value understanding the approach, not just making it work.

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
   hatch run convert tests/bugs/bugN_short_name.txt
   ```

3. **Create GitHub issue**:
   - Use bug report template at `.github/ISSUE_TEMPLATE/bug_report.md`
   - Include test case location and exact error/output
   - See `.github/ISSUES_TO_CREATE.md` for examples

4. **Update documentation**:
   - Add bug to STATUS.md bug tracking table
   - Reference issue number and test case file

5. **Link in code** (if fixing):
   - Reference issue number in commit messages
   - Link to test file from code comments

**Known Bugs**: See [STATUS.md#bug-tracking](STATUS.md#bug-tracking) for active bugs with test cases.

**Bug Test Cases**: All bugs have minimal reproducible test cases in `tests/bugs/` - see [tests/bugs/README.md](tests/bugs/README.md).

## File Locations

```
/Users/jfreeman/Coding/fuzz/txt2tex/
├── tex/                          # fuzz package and fonts
│   ├── fuzz.sty
│   ├── oxsz*.mf
│   └── z*.mf
├── txt2tex_v3.py                 # Current implementation (regex-based)
├── solutions_complete.txt        # Test input
├── solutions.pdf                 # Reference output
├── solutions_complete.tex        # Generated LaTeX
├── solutions_complete.pdf        # Generated PDF
└── sem/                          # NEW PROJECT DIRECTORY
    ├── zed-cm.sty               # Instructor's Z packages
    ├── zed-float.sty
    ├── zed-lbr.sty
    ├── zed-maths.sty
    ├── zed-proof.sty
    ├── test.tex                  # Instructor's example
    ├── glossary.pdf              # Reference material
    ├── CLAUDE.md                 # This file
    ├── DESIGN.md                 # Software design (to create)
    └── README.md                 # User documentation (to create)
```

## Measuring Completeness

**CRITICAL: Run this measurement at the END of EVERY phase of work.**

The primary measure of project completeness is how much of the instructor's reference solutions we can successfully represent and render.

### Reference Files

- **Instructor's PDF**: `examples/solutions_full.pdf` (230K, complete solutions)
- **Our TXT file**: `examples/solutions.txt` (work in progress)
- **Generated PDF**: `examples/solutions.pdf` (auto-generated from solutions.txt)

### Completeness Measurement Process

```bash
# 1. Generate PDF from current solutions.txt
hatch run convert examples/solutions.txt

# 2. Visual comparison
open examples/solutions.pdf examples/solutions_full.pdf

# 3. Count coverage
# - Count solution numbers in solutions_full.pdf (total solutions)
# - Count solution numbers in solutions.txt (implemented solutions)
# - Calculate percentage: (implemented / total) * 100

# 4. Identify gaps
# - Which solutions are empty stubs?
# - Which features are needed to complete them?
# - What syntax is missing?
```

### Recording Measurements

After each phase, record:
1. **Phase completed**: e.g., "Phase 11d: Lambda expressions"
2. **Solutions count**: e.g., "18 of 52 solutions complete (35%)"
3. **New solutions added**: e.g., "Added Solutions 13-18 (proofs with => intro)"
4. **Blocking issues**: e.g., "Solutions 33-36 need function override syntax"

### Current Status

**Last measured**: Phase 11d (Lambda expressions)
**Solutions implemented**: Partial (exact count TBD - need to measure)
**Total solutions**: 52 (Solutions 1-52 in solutions_full.pdf)
**Coverage**: ~35% estimated (needs verification)

**Known gaps**:
- Schema composition operators (not yet implemented)
- Function override syntax (not yet implemented)
- Sequence notation (not yet implemented)
- Free type induction (partially implemented)

### Improvement Strategy

1. After each phase, try to add 2-5 more solutions to solutions.txt
2. Focus on solutions that use newly implemented features
3. Keep solutions.txt rendering successfully (don't break it)
4. Document which solutions are blocked by missing features

## Session Management

User mentioned: "I can exit our session and resume our session from the sem directory if that will make things easier."

If starting fresh from `/Users/jfreeman/Coding/fuzz/txt2tex/sem/`:
1. Remember fuzz is in `../tex/`
2. Test files are in parent directory `../`
3. Use workflow commands at the top of this document
4. Reference this document for context
- always run hatch run check before each micro-commit and solve 100% of any issues reported
- there are no pre-existing issues that should be used to justify anyting
- success is defined as 100%. Do not ask to settle for lower standards of success.