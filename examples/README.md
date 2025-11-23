# txt2tex Examples

This directory contains example files organized by lecture topic from the course glossary. Each example demonstrates specific features of the txt2tex whiteboard-to-LaTeX conversion system.

## Quick Start

Build all examples with fuzz validation:

```bash
cd examples
make           # Build all examples in parallel
make reference # Build reference solutions
make fuzz      # Build fuzz test cases
```

## Directory Structure

### 01_propositional_logic (Lecture 1)
Basic propositional logic operators and constructs.

- `hello_world.txt` - Minimal example
- `basic_operators.txt` - Negation (not), conjunction (and), disjunction (or), implication (=>), equivalence (<=>)
- `truth_tables.txt` - Truth table construction
- `complex_formulas.txt` - Complex propositional formulas

### 02_predicate_logic (Lecture 2)
Predicate logic with quantifiers and declarations.

- `quantifiers.txt` - Universal (forall) and existential (exists) quantification
- `declarations.txt` - Type declarations and predicates
- `future/` - Examples using syntax not yet implemented (seq(T), pattern matching)

### 03_equality (Lecture 3)
Equality and unique quantification.

- `equality_operators.txt` - Basic equality (=, !=) and equality in predicates
- `unique_existence.txt` - Unique quantifier (exists1) and uniqueness conditions
- `mu_operator.txt` - Mu operator (μ) for selecting unique values
- `one_point_rule.txt` - Applications of the one-point rule in quantifier elimination

### 04_proof_trees (Lecture 4)
Natural deduction proof trees with inference rules.

- `simple_proofs.txt` - Basic implication and elimination proofs
- `nested_proofs.txt` - Multi-level proof nesting
- `minimal_nesting.txt` - Minimal nested proof example
- `contradiction.txt` - Proof by contradiction
- `excluded_middle.txt` - Excluded middle proofs
- `advanced_proof_patterns.txt` - Advanced proof patterns

### 05_sets (Lecture 5)
Set theory, types, and set operations.

- `set_basics.txt` - Basic set notation {}, membership (in, notin)
- `set_operations.txt` - Union, intersection, difference, power sets
- `cartesian_tuples.txt` - Cartesian products and ordered pairs
- `set_literals.txt` - Set literal notation with maplets
- `tuple_examples.txt` - Tuple construction and component selection
- `union_domain.txt` - Distributed union and intersection

### 06_definitions (Lecture 6)
Z notation definitions: basic types, free types, abbreviations.

- `free_types_demo.txt` - Free type definitions (Type ::= branch1 | branch2)
- `free_types_proper.txt` - Proper free type examples
- `abbrev_demo.txt` - Abbreviation definitions (==)
- `axdef_demo.txt` - Axiomatic definitions
- `schema_demo.txt` - Schema definitions
- `anonymous_schema.txt` - Anonymous schema expressions

### 07_relations (Lecture 7)
Relations, domain, range, and relational operators.

- `relation_operators.txt` - Relation types (X <-> Y), maplets (|->)
- `domain_range.txt` - Domain (dom) and range (ran) operators
- `restrictions.txt` - Domain restriction (<|), range restriction (|>)
- `maplets.txt` - Maplet construction and usage
- `relational_image.txt` - Relational image operator
- `relational_composition.txt` - Composition (;, comp)
- `range_examples.txt` - Range operation examples

### 08_functions (Lecture 8)
Functions, lambda expressions, and function types.

- `lambda_expressions.txt` - Lambda expressions (lambda x : T . body)
- `function_types.txt` - Partial (7->), total (->), injections, surjections, bijections
- `simple_functions.txt` - Basic function definitions

### 09_sequences (Lecture 9)
Sequences, bags, and sequence operations.

- `sequence_basics.txt` - Sequence types and literals (⟨⟩, <>, ⟨a,b,c⟩)
- `concatenation.txt` - Sequence concatenation (⌢, ^) and cons patterns
- `sequence_operations.txt` - Length (#), head, tail, last, front, reverse
- `pattern_matching.txt` - Pattern matching with sequences in recursive definitions
- `bags.txt` - Bag types and bag literals ([[x]], [[a,b,c]])

### complete_examples/
Complete real-world specifications:

- `tv_programme_modeling.txt` - TV programme modeling example

### fuzz_tests/
Test cases for fuzz validation and edge cases:

- `test_field_projection_bug.txt` - Demonstrates parser bug with field projection on function applications (see issue #13)
- `test_zed.txt` - Zed notation test
- `test_mod.txt` - Modulo operator test
- `test_mod2.txt` - Extended modulo tests
- `test_nested_super.txt` - Nested schema tests

### reference/
Reference solutions from course materials:

- `compiled_solutions.txt` - Complete solution set (Solutions 1-52)
- `compiled_solutions.tex/pdf` - Generated LaTeX and PDF output
- **Status**: All solutions pass fuzz validation with zero errors

## Build System

The Makefile provides targets for building examples with full fuzz validation:

```bash
# Build all examples (excluding reference/ and infrastructure/)
make

# Build specific directories
make 01                      # Build 01_propositional_logic/
make 02                      # Build 02_predicate_logic/
make fuzz                    # Build fuzz_tests/
make reference               # Build reference/compiled_solutions.pdf

# Shortcuts
make all                     # Build all examples
make clean                   # Remove generated files (.tex, .pdf)
make list                    # List all available targets

# Parallel builds (faster)
make -j4                     # Build with 4 parallel jobs
```

All builds include:
1. LaTeX generation from .txt
2. LaTeX formatting with tex-fmt
3. **Type checking with fuzz** (validates Z notation)
4. PDF compilation

## Validation Status

**All 141 examples build successfully with fuzz validation enabled.**

- ✅ Zero fuzz validation errors
- ✅ All type declarations complete
- ✅ All specifications semantically correct
- ✅ Reference solutions fully validated

## Usage

Convert any .txt file to PDF:

```bash
# From sem/ directory
hatch run convert examples/01_propositional_logic/basic_operators.txt

# With fuzz validation (recommended)
hatch run convert examples/01_propositional_logic/basic_operators.txt --fuzz

# Or using the shell script
./txt2pdf.sh examples/01_propositional_logic/basic_operators.txt
```

## File Naming Convention

- Use descriptive names reflecting content (e.g., `lambda_expressions.txt`)
- Avoid generic names like `test1.txt` or `phase*.txt`
- Source files: `.txt` only (LaTeX `.tex` and PDF are generated)
- Test files for debugging: `*_test.txt` in `fuzz_tests/`

## Contributing Examples

When adding new examples:

1. Place in the appropriate lecture directory
2. Use clear, descriptive filenames
3. Include a header comment explaining the example's purpose
4. Test conversion with `hatch run convert <file> --fuzz`
5. Ensure fuzz validation passes (zero errors)
6. Update this README if adding a new category

## Example Format

See existing files for format details. Key elements:

- Section headers: `=== Section Name ===`
- Solutions: `** Solution N **`
- Parts: `(a)`, `(b)`, etc.
- Text blocks: `TEXT: prose here`
- Truth tables: `TRUTH TABLE:` followed by ASCII table
- Equivalences: `EQUIV:` with chain of equivalences
- Proofs: `PROOF:` with indented inference rules
- Z notation: `axdef`, `schema`, `given`, etc.

## Known Issues

- **Field Projection on Function Applications** (issue #13): Parser incorrectly handles `f(x).field` in quantifier bodies. Workaround: use intermediate bindings. See `fuzz_tests/test_field_projection_bug.txt` for test case.

## Quality Standards

All examples must:
- Generate valid LaTeX
- Compile to PDF
- Pass fuzz type checking (when using Z notation)
- Use proper Z notation syntax compatible with fuzz

The build system enforces these standards automatically.
