# Tutorial 0: Getting Started with txt2tex

Welcome to txt2tex! This tutorial will get you up and running with your first formal specification document.

## What is txt2tex?

txt2tex is a tool that converts whiteboard-style mathematical notation into beautiful LaTeX documents. It allows you to write formal specifications naturally, as you would on a whiteboard, and automatically generates typeset PDF output.

**Key features:**
- Write math notation naturally (forall, =>, and, or, etc.)
- Automatic conversion to LaTeX
- Type checking with fuzz (optional but recommended)
- PDF generation in one command
- Support for Z notation formal methods

## Installation

### Prerequisites

1. **Python 3.8+** - The txt2tex tool is written in Python
2. **LaTeX distribution** - For PDF generation (TeX Live recommended)
3. **fuzz** (optional) - For Z notation type checking

### Installing txt2tex

```bash
# Clone the repository
cd /path/to/txt2tex

# Install with hatch (development mode)
hatch env create

# Verify installation
hatch run cli --help
```

## Your First Document

Let's create a simple document that demonstrates basic propositional logic.

### Step 1: Create a file

Create a new file called `my_first_spec.txt`:

```
=== My First Specification ===

** Example 1: Simple Implication **

TEXT: If p and q are both true, then p is true.

(p and q) => p
```

### Step 2: Compile to PDF

```bash
hatch run convert my_first_spec.txt
```

This command:
1. Converts your txt notation to LaTeX
2. Runs pdflatex to generate a PDF
3. Cleans up temporary files

### Step 3: View the output

```bash
open my_first_spec.pdf
```

You'll see a nicely formatted PDF with:
- Section heading
- Explanatory text
- Mathematical formula with proper symbols (∧, ⇒)

## Understanding the Syntax

### Document Structure

**Section headers:** Use `===` to create sections

```
=== Section Title ===
```

**Subsections:** Use `**` for problem/solution numbers

```
** Solution 1 **
** Problem 2 **
```

### Text Blocks

**TEXT directive:** Add explanatory prose

```
TEXT: This is a paragraph of explanation.
```

Features:
- Smart quote conversion ("quotes" becomes "quotes")
- Inline math notation (x^2 renders properly)
- Proper paragraph spacing

### Mathematical Notation

**Propositional operators:**

```
p and q          →  p ∧ q
p or q           →  p ∨ q
not p            →  ¬p
p => q           →  p ⇒ q
p <=> q          →  p ⇔ q
```

**Quantifiers:**

```
forall x : N | x >= 0       →  ∀x : ℕ • x ≥ 0
exists y : Z | y < 0        →  ∃y : ℤ • y < 0
```

## Basic Workflow

### 1. Write in txt format

Write your specification using whiteboard-style notation.

### 2. Convert to PDF

```bash
hatch run convert your_file.txt
```

### 3. Check for errors

If there are errors:
- Check the LaTeX log: `your_file.log`
- Fix syntax issues in your txt file
- Recompile

### 4. Iterate

Edit your txt file and recompile until you're satisfied.

## Common Patterns

### Pattern 1: Statement and Proof

```
** Problem 1 **

TEXT: Prove that p and q implies p.

PROOF:
  p and q [premise]
  p [and elim left]
```

### Pattern 2: Definition with Examples

```
** Definition **

axdef
  square : N -> N
where
  forall n : N | square(n) = n * n
end

TEXT: For example, square(3) = 9 and square(5) = 25.
```

### Pattern 3: Truth Table

```
** Truth Table for And **

TRUTH TABLE:
p | q | p and q
T | T | T
T | F | F
F | T | F
F | F | F
```

## Example: Complete Document

Here's a complete document combining multiple features:

```
=== Propositional Logic Basics ===

TEXT: This document demonstrates basic propositional logic operators.

** Example 1: Conjunction **

TEXT: The conjunction operator 'and' is true only when both operands are true.

p and q

TEXT: Truth table:

TRUTH TABLE:
p | q | p and q
T | T | T
T | F | F
F | T | F
F | F | F

** Example 2: Implication **

TEXT: Implication p => q means "if p then q".

PROOF:
  p and (p => q) [premise]
  p [and elim left]
  p => q [and elim right]
  q [=> elim]

TEXT: This proof shows modus ponens: from p and p => q, we conclude q.
```

Save this as `basics.txt` and compile:

```bash
hatch run convert basics.txt
open basics.pdf
```

## Tips for Beginners

1. **Start simple:** Begin with basic operators before complex notation
2. **Check examples:** Browse `examples/` directory for patterns
3. **Compile often:** Catch errors early by compiling frequently
4. **Read error messages:** LaTeX errors often point to the problem line
5. **Use TEXT blocks:** Explain your reasoning in prose
6. **Follow conventions:** Look at existing examples for style

## Common Mistakes

### Mistake 1: Missing end keyword

```
❌ Wrong:
axdef
  x : N

✅ Correct:
axdef
  x : N
end
```

### Mistake 2: Incorrect operator spacing

```
❌ Wrong:
p=>q

✅ Correct:
p => q
```

### Mistake 3: Forgetting TEXT prefix

```
❌ Wrong:
This is explanatory text.

✅ Correct:
TEXT: This is explanatory text.
```

## Next Steps

Now that you can create and compile basic documents:

1. **Explore examples:** Browse `examples/01_propositional_logic/`
2. **Try truth tables:** Practice with `examples/01_propositional_logic/truth_tables.txt`
3. **Learn proof trees:** See `examples/04_proof_trees/simple_proofs.txt`
4. **Read Tutorial 1:** Learn propositional logic in depth

## Quick Reference

### Compilation Commands

```bash
# Full pipeline (txt → tex → pdf)
hatch run convert file.txt

# LaTeX generation only
hatch run cli file.txt

# View PDF (macOS)
open file.pdf

# View PDF (Linux)
xdg-open file.pdf
```

### File Structure

```
your_document.txt      # Your source file
your_document.tex      # Generated LaTeX (intermediate)
your_document.pdf      # Final PDF output
your_document.log      # LaTeX compilation log
```

### Getting Help

- **Examples:** `examples/` directory has 60+ example files
- **User Guide:** `docs/USER_GUIDE.md` - complete syntax reference
- **README:** Each example directory has a README
- **Status:** `docs/STATUS.md` - implementation status and known issues

## Troubleshooting

### Problem: Command not found

**Solution:** Ensure you're using hatch:
```bash
hatch run convert file.txt
```

### Problem: LaTeX errors

**Solution:** Check the .log file:
```bash
cat your_file.log | grep -i error
```

### Problem: Missing symbols

**Solution:** Ensure fuzz packages are installed and TEXINPUTS is set (handled automatically by `hatch run convert`).

### Problem: Syntax errors

**Solution:** Compare your syntax with examples in the `examples/` directory.

## Summary

You've learned:
- ✅ How to install and run txt2tex
- ✅ Basic document structure (sections, TEXT blocks)
- ✅ Simple mathematical notation
- ✅ The compilation workflow
- ✅ Common patterns and mistakes

**Next Tutorial:** [Tutorial 1: Propositional Logic](TUTORIAL_01.md)

Learn about boolean operators, truth tables, and logical equivalences.

---

**Questions?** Consult the [User Guide](docs/USER_GUIDE.md) or explore the [examples directory](examples/).
