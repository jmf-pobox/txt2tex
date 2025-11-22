# Complete Specification Examples

This directory contains complete, real-world specification examples extracted from course material.

## Purpose

These examples demonstrate how to combine multiple txt2tex features into cohesive specifications:
- Multiple definition types (given, free types, schemas, axdef)
- Functions operating on data structures
- Predicates and constraints
- Proof fragments
- Complete documentation

## What Makes These "Complete"

Unlike atomic examples that demonstrate single features, these specifications:
1. **Combine multiple concepts** - schemas, functions, proofs
2. **Show real design decisions** - why use axdef vs schema, when to use generic definitions
3. **Include full documentation** - comments explaining reasoning
4. **Compile to professional PDFs** - submission-ready quality
5. **Based on actual course problems** - from solutions.txt/solutions_full.pdf

## Examples in This Directory

Coming soon - examples will be extracted from course material including:
- Database/relation specifications
- State machine specifications
- Data structure specifications (stacks, trees, etc.)
- Algorithm correctness proofs
- System invariant proofs

Each example includes:
- **Source**: `.txt` file with inline comments
- **Generated**: `.tex` and `.pdf` files
- **Commentary**: Design decisions and feature choices explained

## How to Use These Examples

1. **Read the source**: Open the `.txt` file to see the txt2tex notation
2. **Review comments**: Understand why specific features were chosen
3. **Examine the PDF**: See the final typeset output
4. **Adapt patterns**: Use similar structures in your own work

## Compilation

```bash
# Compile any example
hatch run convert complete_examples/example_name.txt

# Or use the script
./txt2pdf.sh complete_examples/example_name.txt
```

## See Also

- **docs/tutorials/10_advanced.md** - Advanced patterns and techniques
- **All lecture directories** (01-09) - Feature-specific examples
- **docs/guides/USER_GUIDE.md** - Complete syntax reference
- **Previous**: 12_advanced/
