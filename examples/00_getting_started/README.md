# Getting Started with txt2tex

This directory contains introductory examples to help you get started with txt2tex.

## Purpose

These examples demonstrate the basics of txt2tex syntax and workflow:

- Creating your first txt2tex document
- Converting to LaTeX and PDF
- Understanding the basic structure

## Examples

- `hello_world.txt` - Your first txt2tex document: a section header, a TEXT block, and one formula
- `first_proof.txt` - A simple natural deduction proof using PROOF: blocks
- `basic_z_notation.txt` - Introduction to Z notation: given types, abbreviations, axdef, and schemas

## Workflow

```bash
# Convert a .txt file to PDF
txt2tex examples/00_getting_started/hello_world.txt

# Generate LaTeX only (no LaTeX installation needed)
txt2tex examples/00_getting_started/hello_world.txt --tex-only
```

## Next Steps

After completing these examples, proceed to:

- **01_propositional_logic/** - Boolean operators and truth tables
- **docs/tutorials/01_propositional_logic.md** - Lecture 1 tutorial
