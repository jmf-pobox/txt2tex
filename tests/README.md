# txt2tex Test Suite

This directory contains 845 tests organized by lecture topic and functionality. Tests are structured to match the course glossary organization, making it easy to find tests for specific features.

## Directory Structure

### Lecture-Based Tests (01-09)

Tests organized by glossary lectures, following the course progression:

#### test_01_propositional_logic/ (Lecture 1)
Propositional logic operators and truth tables.

- `test_operators.py` - Basic operators (not, and, or, =>, <=>)
- `test_truth_tables.py` - Truth table parsing, generation, and multi-line documents
- `test_equivalences.py` - Equivalence chains (EQUIV blocks)

**Key features tested**: Boolean operators, truth table construction, document structure, paragraph handling

#### test_02_predicate_logic/ (Lecture 2)
Predicate logic with quantifiers.

- `test_quantifiers.py` - Universal (forall) and existential (exists) quantification
- `test_nested_quantifiers.py` - Complex nested quantifier expressions

**Key features tested**: Quantifiers, type declarations, predicates with multiple bindings

#### test_03_equality/ (Lecture 3)
Equality operators and unique quantification.

- `test_equality_operators.py` - Equality (=, !=), unique existence (exists1), mu operator

**Key features tested**: Equality comparison, unique quantifier, definite description (mu), one-point rule

#### test_04_proof_trees/ (Lecture 4)
Natural deduction proof trees.

- `test_proof_trees.py` - Proof tree structure, inference rules, indentation
- `test_proof_tree_coverage.py` - Case analysis, nested proofs, edge cases

**Key features tested**: PROOF blocks, assumption management, rule citations, case analysis

#### test_05_sets/ (Lecture 5)
Set theory and operations.

- `test_set_operations.py` - Basic operations (in, union, intersect, difference, power sets)
- `test_set_comprehension.py` - Set comprehension syntax, period handling
- `test_tuples.py` - Tuple construction, projection (.1, .2), Cartesian products
- `test_set_literal_maplets.py` - Set literals with maplets ({1 |-> a, 2 |-> b})

**Key features tested**: Set notation, comprehension, tuples, maplets, cartesian products

#### test_06_definitions/ (Lecture 6)
Z notation definitions and type systems.

- `test_generic_parameters.py` - Generic types ([X], [X, Y])
- `test_generic_instantiation.py` - Generic type instantiation
- `test_free_types.py` - Free type definitions (Type ::= branch1 | branch2)
- `test_anonymous_schemas.py` - Anonymous schema expressions
- `test_semicolon_bindings.py` - Semicolon-separated bindings (forall x:T; y:U)

**Key features tested**: Given types, free types, abbreviations, axiomatic definitions, schemas, generic parameters

#### test_07_relations/ (Lecture 7)
Relations and relational operators.

- `test_relation_operators.py` - Relation types (<->), domain (dom), range (ran), restrictions (<|, |>)
- `test_relation_composition.py` - Composition (;, comp), inverse (~, inv), closures (+, *)
- `test_relational_image.py` - Relational image operator (R(| S |))

**Key features tested**: Relation types, maplets, domain/range, restrictions, composition, inverse, identity

#### test_08_functions/ (Lecture 8)
Functions and function types.

- `test_function_types.py` - All function arrows (->, +->, >->, >+>, -->>, +->>, >->>)
- `test_function_application.py` - Function application (f(x), f(x,y))
- `test_partial_functions.py` - Partial function features
- `test_lambda_expressions.py` - Lambda expressions (lambda x:T . E)
- `test_space_separated_application.py` - Space-separated application (f x y)

**Key features tested**: Total/partial functions, injections, surjections, bijections, lambda, application syntax

#### test_09_sequences/ (Lecture 9)
Sequences and bags.

- `test_sequences.py` - Sequence types, literals (⟨⟩, <>), operations (head, tail, rev), concatenation (⌢, ^), tuple projection, ASCII brackets, pattern matching
- Includes bag tests ([[x]], [[a,b,c]]), sequence operators, indexing

**Key features tested**: Sequence literals (Unicode and ASCII), concatenation, pattern matching, bags, sequence operations

### Special Purpose Tests

#### test_advanced_features/
Cross-cutting features not tied to a single lecture.

- `test_range_override_indexing.py` - Range operator (..), override (++), indexing
- `test_conditional_expressions.py` - Conditional expressions (if-then-else)
- `test_digit_identifiers.py` - Identifiers starting with digits (479_courses)

**Key features tested**: Advanced operators, conditional syntax, extended identifier rules

#### test_text_formatting/
TEXT block formatting and inline math.

- `test_text_blocks.py` - Formula detection in TEXT, PURETEXT blocks, PAGEBREAK
- `test_inline_math.py` - Inline math expression wrapping in paragraphs

**Key features tested**: TEXT vs PURETEXT, inline math detection, paragraph formatting, page breaks

#### test_coverage/
Coverage-specific tests for comprehensive code testing.

- `test_latex_gen_coverage.py` - LaTeX generation coverage (merged from 3 files)
- `test_parser_coverage.py` - Parser coverage
- `test_identifier_coverage.py` - Identifier edge cases

**Key features tested**: Edge cases, error handling, code path coverage

#### test_edge_cases/
Error handling and boundary conditions.

- `test_parser_edge_cases.py` - Parser error handling
- `test_parser_structural.py` - Structural parsing edge cases
- `test_latex_gen_errors.py` - LaTeX generation error handling
- `test_nested_braces.py` - Nested braces and bracket handling

**Key features tested**: Parse errors, malformed input, boundary conditions

### Root Directory Tests

- `conftest.py` - pytest configuration and fixtures
- `__init__.py` - Package marker
- `test_cli.py` - Command-line interface tests

## Running Tests

### Run All Tests
```bash
hatch run test
```

### Run Specific Lecture Tests
```bash
# Lecture 1: Propositional logic
hatch run test tests/test_01_propositional_logic/

# Lecture 5: Sets
hatch run test tests/test_05_sets/

# Lecture 8: Functions
hatch run test tests/test_08_functions/
```

### Run Specific Test File
```bash
hatch run test tests/test_03_equality/test_equality_operators.py
```

### Run Specific Test
```bash
hatch run test tests/test_01_propositional_logic/test_operators.py::TestLexer::test_single_identifier
```

### Run with Verbose Output
```bash
hatch run test -v
hatch run test tests/test_04_proof_trees/ -v
```

### Run with Coverage
```bash
hatch run test-cov
```

## Test Statistics

- **Total Tests**: 845 (all passing)
- **Coverage**: 88.49% overall
  - parser.py: 88.91%
  - latex_gen.py: 80.61%
  - lexer.py: 94.56%

## Test Organization Principles

1. **Lecture-based**: Tests follow glossary lecture order (01-09) for easy navigation
2. **Feature grouping**: Related features tested together in same file
3. **Clear naming**: Descriptive test and file names (not "phase*")
4. **Progressive complexity**: Simple tests before complex tests
5. **Self-contained**: Each test file can run independently

## Adding New Tests

When adding new tests:

1. **Choose the right directory**: Place in appropriate lecture or special directory
2. **Follow naming conventions**: Use descriptive names (test_feature_name.py)
3. **Include docstrings**: Document what each test verifies
4. **Test incrementally**: Add tests as you implement features
5. **Run quality gates**: Ensure `hatch run check` passes

## Test File Structure

Standard test file structure:

```python
"""Tests for Feature X (Lecture N)."""

from __future__ import annotations

from txt2tex.ast_nodes import ...
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def parse_expr(text: str) -> Expr:
    """Helper to parse expression."""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


class TestFeatureParsing:
    """Test parsing of feature X."""

    def test_basic_case(self) -> None:
        """Test basic feature usage."""
        ...


class TestFeatureLaTeX:
    """Test LaTeX generation for feature X."""

    def test_latex_output(self) -> None:
        """Test LaTeX output format."""
        ...


class TestFeatureIntegration:
    """Integration tests for feature X."""

    def test_end_to_end(self) -> None:
        """Test complete pipeline."""
        ...
```

## Historical Note

This test suite was reorganized in October 2025 from a phase-based system (test_phase0.py through test_phase19.py) to the current lecture-based organization. The reorganization:

- Mapped 19 phase files to 9 lecture directories
- Merged 11 duplicate test files into 6 consolidated files
- Created 4 special-purpose directories for cross-cutting concerns
- Maintained 100% test compatibility (845 tests, all passing)
- Improved discoverability and maintainability

## References

- [USER-GUIDE.md](../USER-GUIDE.md) - Syntax guide for features tested here
- [DESIGN.md](../DESIGN.md) - Architecture behind the tested code
- [STATUS.md](../STATUS.md) - Current implementation status and coverage
- [glossary.pdf](../examples/reference/glossary.pdf) - Course symbol reference
