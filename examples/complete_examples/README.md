# Complete Specification Examples

This directory contains complete, real-world specification examples extracted from course material and homework solutions.

## Purpose

These examples demonstrate how to combine multiple txt2tex features into cohesive specifications:
- Multiple definition types (given, free types, schemas, axdef)
- Functions operating on data structures
- Relations and relational operators
- Predicates and constraints
- Complete proofs
- Professional documentation

## What Makes These "Complete"

Unlike atomic examples that demonstrate single features, these specifications:
1. **Combine multiple concepts** - schemas, functions, relations, proofs
2. **Show real design decisions** - when to use axdef vs schema, function vs relation
3. **Non-trivial complexity** - realistic problem sizes and interactions
4. **Compile to professional PDFs** - submission-ready quality
5. **Based on actual course problems** - from instructor's reference solutions

## Examples in This Directory

### tv_programme_modeling.txt
TV programme scheduling system specification.

**Features demonstrated:**
- Given types (ShowId, EpisodeId)
- Axiomatic definitions with constraints
- Relational modeling (show_episodes: ShowId <-> EpisodeId)
- Domain and range operators
- Multi-line predicates with backslash continuation
- Real-world data modeling patterns

**Complexity:** ~50 lines, 3 given types, 2 axdef blocks

### music_streaming_service.txt
Music streaming service with playlists and playback tracking.

**Features demonstrated:**
- Complex type hierarchy (Person, Song, Artist, Album)
- Free types with generic parameters
- Sequences for ordered data (playlists)
- Recursive function definitions with pattern matching
- Schema composition
- State invariants

**Complexity:** ~80 lines, 5 given types, recursive functions, schemas

### family_relationships.txt
Family relationship modeling using relations.

**Features demonstrated:**
- Relation types (Person <-> Person)
- Symmetric and transitive relations
- Composition of relations (parentOf o9 parentOf)
- Domain restrictions
- Axiomatic definitions with relational predicates
- Social network modeling patterns

**Complexity:** ~40 lines, relations with constraints

### children_grandchildren_functions.txt
Functions computing relationships from base relations.

**Features demonstrated:**
- Function definitions using relational image
- Composition and restriction operators
- Generic function types
- Proofs of relationship properties
- Functional vs relational modeling

**Complexity:** ~60 lines, 4 function definitions, proof trees

### distributivity_proof.txt
Complete formal proof of set distributivity law.

**Features demonstrated:**
- Multi-step natural deduction proof
- Case analysis (or-elimination)
- Nested proof structure
- Justifications with multiple rules
- Equivalence chains (EQUIV blocks)
- Formal reasoning patterns

**Complexity:** ~70 lines, 15-step proof with 3 levels of nesting

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

## Building Examples

Compile any example:

```bash
# From sem/ directory
hatch run convert examples/complete_examples/tv_programme_modeling.txt

# With fuzz validation
hatch run convert examples/complete_examples/tv_programme_modeling.txt --fuzz

# Or use the script
./txt2pdf.sh examples/complete_examples/music_streaming_service.txt
```

Build all complete examples:

```bash
cd examples
make complete_examples
```

## Learning Path

**Recommended order for studying these examples:**

1. **tv_programme_modeling.txt** - Start here for basic relational modeling
2. **family_relationships.txt** - Learn relation composition and constraints
3. **children_grandchildren_functions.txt** - Functions built from relations
4. **music_streaming_service.txt** - Complex multi-type specifications
5. **distributivity_proof.txt** - Complete formal proofs

## See Also

- **examples/01-12/** - Feature-specific atomic examples
- **docs/tutorials/** - Step-by-step tutorials
- **docs/guides/USER_GUIDE.md** - Complete syntax reference
- **examples/reference/compiled_solutions.txt** - All 52 homework solutions
