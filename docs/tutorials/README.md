# txt2tex Tutorial Series

A comprehensive guide to learning txt2tex and Z notation, organized progressively from basics to advanced topics.

## Overview

This tutorial series teaches you how to write formal specifications using txt2tex, a tool that converts whiteboard-style mathematical notation to beautiful LaTeX documents that can be typechecked with fuzz.

**Prerequisites:** Basic understanding of logic and mathematics. No prior experience with Z notation or formal methods required.

**Learning Path:** Follow the tutorials in order for a structured learning experience, or jump to specific topics as needed.

## Getting Started

- **[Tutorial 0: Getting Started](docs/tutorials/00_getting_started.md)** - Installation, first document, basic workflow

Start here if you're new to txt2tex. Learn how to install the tools, write your first document, and compile to PDF.

## Core Tutorials (Lectures 1-9)

These tutorials follow a structured curriculum covering fundamental concepts progressively:

### Lecture 1: Propositional Logic
- **[Tutorial 1: Propositional Logic](docs/tutorials/01_propositional_logic.md)**
  - Boolean operators (land, lor, lnot, =>, <=>)
  - Truth tables and equivalences
  - Tautologies and logical laws
  - **Examples:** `01_propositional_logic/`

### Lecture 2: Predicate Logic
- **[Tutorial 2: Predicate Logic](docs/tutorials/02_predicate_logic.md)**
  - Predicates and declarations
  - Universal quantifier (forall)
  - Existential quantifier (exists)
  - One-point rule and quantifier manipulation
  - **Examples:** `02_predicate_logic/`, `03_equality/`

### Lecture 3: Set Theory
- **[Tutorial 3: Sets and Types](docs/tutorials/03_sets_and_types.md)**
  - Set notation and literals
  - Set operations (union, intersect, difference)
  - Power sets and Cartesian products
  - Tuples and ordered pairs
  - **Examples:** `05_sets/`

### Lecture 4: Deductive Proofs
- **[Tutorial 4: Proof Trees](docs/tutorials/04_proof_trees.md)**
  - Natural deduction rules
  - Proof tree syntax (PROOF:, EQUIV:)
  - Introduction and elimination rules
  - Nested proofs and assumptions
  - **Examples:** `04_proof_trees/`

### Lecture 5: Z Notation Basics
- **[Tutorial 5: Z Notation Definitions](docs/tutorials/05_z_definitions.md)**
  - given types
  - Free type definitions
  - Abbreviations (==)
  - Axiomatic definitions (axdef)
  - Schema definitions
  - **Examples:** `06_definitions/`

### Lecture 6: Relations
- **[Tutorial 6: Relations](docs/tutorials/06_relations.md)**
  - Binary relations (↔ or <->)
  - Maplets (|->)
  - Domain and range
  - Relation operators (composition, inverse, restriction)
  - Relational image
  - **Examples:** `07_relations/`

### Lecture 7: Functions
- **[Tutorial 7: Functions](docs/tutorials/07_functions.md)**
  - Function types (→, +→, ⇸, ⤖, ↣, ⤀, ↠, ⤖)
  - Total and partial functions
  - Function application
  - Lambda expressions
  - Function composition
  - **Examples:** `08_functions/`

### Lecture 8: Sequences and Bags
- **[Tutorial 8: Sequences](docs/tutorials/08_sequences.md)**
  - Sequence notation (⟨⟩, <> )
  - Sequence operations (head, tail, concatenation)
  - Pattern matching with sequences
  - Bags (multisets)
  - **Examples:** `09_sequences/`

### Lecture 9: Advanced Z Notation
- **[Tutorial 9: Schemas and Composition](docs/tutorials/09_schemas.md)**
  - Schema notation
  - Schema composition and operations
  - State schemas and operations
  - Generic (polymorphic) definitions
  - Zed blocks
  - **Examples:** `10_schemas/`

## Advanced Topics

- **[Tutorial: Advanced Features](docs/tutorials/10_advanced.md)**
  - Conditional expressions (if-then-else)
  - Subscripts and superscripts
  - Generic type instantiation
  - Higher-order functions
  - Text blocks (TEXT, PURETEXT, LATEX)
  - Bibliography management
  - **Examples:** `11_text_blocks/`, `12_advanced/`

## Complete Examples

After completing the tutorials, explore complete formal specifications in `complete_examples/`:

- Full problem specifications from coursework
- Real-world modeling examples
- Integration of multiple features
- Design patterns and best practices

## Reference Materials

- **[USER_GUIDE.md](docs/guides/USER_GUIDE.md)** - Complete syntax reference
- **[PROOF_SYNTAX.md](docs/guides/PROOF_SYNTAX.md)** - Proof tree formatting rules
- **[DESIGN.md](docs/DESIGN.md)** - Architecture and design decisions
- **[STATUS.md](docs/development/STATUS.md)** - Current implementation status

## How to Use This Tutorial

### For Complete Beginners

1. Start with Tutorial 0 (Getting Started)
2. Work through Tutorials 1-4 (logic and proofs)
3. Continue with Tutorials 5-9 (Z notation)
4. Explore advanced topics as needed
5. Study complete examples for integration

### For Experienced Formal Methods Users

1. Skim Tutorial 0 for tool-specific workflow
2. Jump to relevant tutorials based on your needs
3. Consult USER_GUIDE.md for quick syntax reference
4. Explore advanced examples directly

### For Course Students

1. Follow tutorials aligned with lecture schedule (Tutorials 1-9)
2. Complete exercises in each example directory
3. Use complete_examples/ for assignment reference
4. Refer to PROOF_SYNTAX.md for proof formatting

## Learning Tips

1. **Try the examples:** Each tutorial references example files. Compile them and examine the output.

2. **Experiment:** Modify examples and see what happens. The fuzz typechecker will catch errors.

3. **Start simple:** Begin with basic operators and gradually add complexity.

4. **Read error messages:** fuzz provides helpful error messages. Learn to interpret them.

5. **Use the workflow:** Always use `hatch run convert` to get both LaTeX and PDF output.

6. **Consult USER_GUIDE.md:** When you encounter unfamiliar syntax, check the user guide.

7. **Study complete examples:** See how all features work together in real specifications.

## Compilation Workflow

```bash
# Convert a single example to PDF
hatch run convert examples/01_propositional_logic/hello_world.txt

# Generate LaTeX only (for debugging)
hatch run cli examples/file.txt

# View PDF output
open examples/01_propositional_logic/hello_world.pdf
```

## Getting Help

- **Examples directory:** Browse examples for syntax patterns
- **USER_GUIDE.md:** Complete syntax reference with examples
- **PROOF_SYNTAX.md:** Proof tree formatting and rules
- **README files:** Each example directory has a README explaining its contents

## Contributing

Found an error or have suggestions for improving the tutorials? Please file an issue or submit a pull request.

## License

These tutorials and examples are part of the txt2tex project. See the main project README for license information.

---

**Next Step:** Start with [Tutorial 0: Getting Started](docs/tutorials/00_getting_started.md) or jump to a specific topic using the links above.
