# txt2tex Examples

This directory contains example files organized by lecture topic from the course glossary. Each example demonstrates specific features of the txt2tex whiteboard-to-LaTeX conversion system.

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

*Examples to be added*

### 04_proof_trees
Natural deduction proof trees with inference rules.

- `simple_proofs.txt` - Basic implication and elimination proofs
- `nested_proofs.txt` - Multi-level proof nesting
- `minimal_nesting.txt` - Minimal nested proof example
- `pattern_matching.txt` - Pattern matching in proofs
- `solution40_test.txt` - Solution 40 from course materials
- `alignment_test.tex` - Alignment testing
- `deep_nesting_test.tex` - Deep proof tree nesting
- `fix_test.tex` - Proof tree fix testing

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

*Examples to be added*

### infrastructure/
LaTeX support files (not examples):
- `fuzz.sty` - Z notation typesetting system
- `zed-*.sty` - Instructor's Z packages
- `*.mf` - METAFONT font files
- `.latexmkrc` - LaTeX build configuration

### reference/
Reference materials and compiled outputs:
- `solutions_full.pdf` - Instructor's complete solution set
- `glossary.pdf` - Course symbol glossary
- `exercises.pdf` - Course exercises
- `instructors_test.pdf/tex` - Instructor's test file
- `compiled_solutions.txt/tex/pdf` - Previously compiled examples
- `solutions_fuzz.tex` - Solutions using fuzz package
- `test_solutions_*.txt` - Solution fragments (37-39, 44-47, 48-50, 51-52)

## Usage

Convert any .txt file to PDF:

```bash
# From sem/ directory
hatch run convert examples/01_propositional_logic/basic_operators.txt

# Or using the shell script
./txt2pdf.sh examples/01_propositional_logic/basic_operators.txt
```

## File Naming Convention

- Use descriptive names reflecting content (e.g., `lambda_expressions.txt`)
- Avoid generic names like `test1.txt` or `phase*.txt`
- Source files: `.txt` only (LaTeX `.tex` and PDF are generated)
- Test files for debugging: `*_test.txt`

## Contributing Examples

When adding new examples:

1. Place in the appropriate lecture directory
2. Use clear, descriptive filenames
3. Include a header comment explaining the example's purpose
4. Test conversion with `hatch run convert`
5. Update this README if adding a new category

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
