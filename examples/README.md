# txt2tex Examples

This directory contains example files demonstrating txt2tex features. Each example shows specific features of the whiteboard-to-LaTeX conversion system.

## Quick Start

Build all examples with fuzz validation:

```bash
cd examples
make           # Build all examples in parallel
make fuzz      # Build fuzz test cases
```

## Directory Structure

### 01_propositional_logic (4 examples)
Basic propositional logic operators and constructs.

- `hello_world.txt` - Minimal example
- `basic_operators.txt` - Negation (not), conjunction (and), disjunction (or), implication (=>), equivalence (<=>)
- `truth_tables.txt` - Truth table construction
- `complex_formulas.txt` - Complex propositional formulas

### 02_predicate_logic (4 examples)
Predicate logic with quantifiers and declarations.

- `quantifiers.txt` - Universal (forall) and existential (exists) quantification
- `multi_variable_quantifiers.txt` - Multiple variables in quantifiers
- `declarations.txt` - Type declarations and predicates
- `nested_quantifiers.txt` - Nested quantification examples

### 03_equality (6 examples)
Equality and unique quantification.

- `equality_operators.txt` - Basic equality (=, !=) and equality in predicates
- `unique_existence.txt` - Unique quantifier (exists1) and uniqueness conditions
- `mu_operator.txt` - Mu operator (μ) for selecting unique values
- `mu_with_expression.txt` - Mu with expression part
- `one_point_rule.txt` - Applications of the one-point rule in quantifier elimination
- `equality_proofs.txt` - Proofs using equality reasoning

### 04_proof_trees (8 examples)
Natural deduction proof trees with inference rules.

- `simple_proofs.txt` - Basic implication and elimination proofs
- `nested_proofs.txt` - Multi-level proof nesting
- `minimal_nesting.txt` - Minimal nested proof example
- `contradiction.txt` - Proof by contradiction
- `excluded_middle.txt` - Excluded middle proofs
- `case_analysis.txt` - Or-elimination with case analysis
- `advanced_proof_patterns.txt` - Advanced proof patterns
- `implication_introduction.txt` - Implication introduction rule

### 05_sets (7 examples)
Set theory, types, and set operations.

- `set_basics.txt` - Basic set notation {}, membership (in, notin)
- `set_operations.txt` - Union, intersection, difference, power sets
- `cartesian_tuples.txt` - Cartesian products and ordered pairs
- `set_literals.txt` - Set literal notation with maplets
- `tuple_examples.txt` - Tuple construction and component selection
- `set_comprehension.txt` - Set comprehension with predicates and expressions
- `distributed_union.txt` - Distributed union (bigcup) operator

### 06_definitions (8 examples)
Z notation definitions: basic types, free types, abbreviations.

- `given_types.txt` - Given type declarations
- `free_types_basic.txt` - Basic free type definitions (Type ::= branch1 | branch2)
- `free_types_recursive.txt` - Recursive free types (trees, lists)
- `free_types_generic.txt` - Generic free types
- `abbreviations.txt` - Abbreviation definitions (==)
- `axdef_basic.txt` - Axiomatic definitions
- `schema_basic.txt` - Schema definitions
- `anonymous_schema.txt` - Anonymous schema expressions

### 07_relations (7 examples)
Relations, domain, range, and relational operators.

- `relation_types.txt` - Relation types (X <-> Y), maplets (|->)
- `domain_range.txt` - Domain (dom) and range (ran) operators
- `restrictions.txt` - Domain restriction (<|), range restriction (|>)
- `domain_range_subtraction.txt` - Domain subtraction (<<|), range subtraction (|>>)
- `relational_image.txt` - Relational image operator (R(| S |))
- `composition.txt` - Relational composition (o9, comp)
- `closures.txt` - Transitive (+) and reflexive-transitive (*) closures

### 08_functions (8 examples)
Functions, lambda expressions, and function types.

- `lambda_basic.txt` - Basic lambda expressions (lambda x : T . body)
- `lambda_multi_variable.txt` - Multi-variable lambdas
- `function_types.txt` - Partial (+->), total (->), injections, surjections, bijections
- `function_application.txt` - Function application f(x)
- `space_separated_application.txt` - Space-separated application (f x y)
- `override.txt` - Function override (++)
- `generic_functions.txt` - Generic function definitions
- `recursive_functions.txt` - Recursive function definitions with pattern matching

### 09_sequences (7 examples)
Sequences, bags, and sequence operations.

- `sequence_literals.txt` - Sequence types and literals (⟨⟩, <>, ⟨a,b,c⟩)
- `concatenation.txt` - Sequence concatenation (⌢, ^) and cons patterns
- `sequence_operations.txt` - Length (#), head, tail, last, front, reverse
- `pattern_matching.txt` - Pattern matching with sequences in recursive definitions
- `sequence_comprehension.txt` - Sequence comprehension
- `bags.txt` - Bag types and bag literals ([[x]], [[a,b,c]])
- `ranges.txt` - Range operator (m..n)

### 10_schemas (2 examples)
Schema definitions and schema expressions.

- `scoping_demo.txt` - Schema scoping and variable visibility
- `zed_blocks.txt` - Multiple Z notation block types

### 11_text_blocks (6 examples)
Text blocks with inline mathematics and LaTeX integration.

- `text_smart.txt` - Smart inline math detection in TEXT blocks
- `puretext.txt` - PURETEXT directive (no math conversion)
- `latex_passthrough.txt` - LATEX directive for raw LaTeX
- `combined_directives.txt` - Combining different text block types
- `pagebreak.txt` - PAGEBREAK directive
- `bibliography_example.txt` - Bibliography and citations

### 12_advanced (3 examples)
Advanced features and edge cases.

- `subscripts_superscripts.txt` - Complex subscripts and superscripts
- `generic_instantiation.txt` - Generic type instantiation
- `if_then_else.txt` - Conditional expressions

### fuzz_tests/ (4 examples)
Test cases for fuzz validation and edge cases.

- `test_field_projection_bug.txt` - Field projection on function applications
- `test_zed.txt` - Zed notation edge cases
- `test_mod.txt` - Modulo operator
- `test_nested_super.txt` - Nested superscripts

### user_guide/ (61 examples)
Examples extracted from USER_GUIDE.md documentation, organized by feature.

- Comprehensive examples for every documented feature
- Used for documentation validation and testing

## Build System

The Makefile provides targets for building examples with full fuzz validation:

```bash
# Build all examples
make

# Build specific directories
make 01                      # Build 01_propositional_logic/
make 02                      # Build 02_predicate_logic/
make fuzz                    # Build fuzz_tests/

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

## Usage

Convert any .txt file to PDF:

```bash
# From project root
hatch run convert examples/01_propositional_logic/basic_operators.txt

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

1. Place in the appropriate directory
2. Use clear, descriptive filenames
3. Include a header comment explaining the example's purpose
4. Test conversion with `hatch run convert <file>`
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

See [tests/bugs/README.md](../tests/bugs/README.md) for complete bug tracking with test cases.

## Quality Standards

All examples must:
- Generate valid LaTeX
- Compile to PDF
- Pass fuzz type checking (when using Z notation)
- Use proper Z notation syntax compatible with fuzz

The build system enforces these standards automatically.
