# txt2tex Examples

This directory contains example `.txt` files for every feature in txt2tex. Each file demonstrates specific notation or constructs and compiles to a type-checked PDF.

## Quick start

```bash
# Convert one file to PDF (fuzz type-checked)
txt2tex examples/00_getting_started/hello_world.txt

# Build all examples (from the examples/ directory)
cd examples
make           # Build everything, in parallel
make fuzz      # Build fuzz_tests/ only
make clean     # Remove generated .tex and .pdf files
```

The build system generates `.tex`, runs fuzz type-checking on Z notation, and compiles to `.pdf`. All three outputs are produced in the same directory as the source file.

---

## 00_getting_started (5 examples)

The five-minute on-ramp. Start here.

| File | Demonstrates |
|------|-------------|
| `hello_world.txt` | Minimal document: section header, TEXT block, one formula |
| `basic_z_notation.txt` | given types, abbreviations (`==`), axdef, and a simple schema |
| `decorated_identifiers.txt` | Prime (`'`), input (`?`), and output (`!`) identifier decoration |
| `first_proof.txt` | PROOF block, assumption annotations, `land elim` / `=>` intro |
| `string_literals.txt` | Single-quoted string literals and how they render in Z expressions |

---

## 01_propositional_logic (4 examples)

| File | Demonstrates |
|------|-------------|
| `hello_world.txt` | Minimal propositional logic document |
| `basic_operators.txt` | `land`, `lor`, `lnot`, `=>`, `<=>` |
| `truth_tables.txt` | TRUTH TABLE block with ASCII grid |
| `complex_formulas.txt` | Multi-operator propositional formulas |

---

## 02_predicate_logic (2 examples)

| File | Demonstrates |
|------|-------------|
| `quantifiers.txt` | given types, free types, abbreviations, axdef, schema |
| `declarations.txt` | Generic (polymorphic) type parameters: `[X]`, `[X, Y]`, gendef |

---

## 03_equality (6 examples)

| File | Demonstrates |
|------|-------------|
| `equality_operators.txt` | `=`, `!=` in predicates |
| `unique_existence.txt` | `exists1` unique quantifier |
| `mu_operator.txt` | `mu x : T \| P` — selecting the unique value satisfying a predicate |
| `mu_with_expression.txt` | `mu x : T \| P . expr` — mu with a separate output expression |
| `one_point_rule.txt` | Quantifier elimination via the one-point rule |
| `bullet_separator.txt` | `.` separator in set comprehensions and mu; contrasts filter vs. selector |

---

## 04_proof_trees (9 examples)

Natural deduction proofs using the PROOF block.

| File | Demonstrates |
|------|-------------|
| `simple_proofs.txt` | Basic implication and `land` elimination |
| `nested_proofs.txt` | Multi-level proof nesting |
| `minimal_nesting.txt` | Smallest valid nested proof |
| `contradiction.txt` | Proof by contradiction (`lnot` intro / elim) |
| `excluded_middle.txt` | Law of excluded middle |
| `advanced_proof_patterns.txt` | Multi-step proof trees with complex rule applications |
| `infrule_modus_ponens.txt` | Modus ponens as an explicit inference rule |
| `shows_operator.txt` | `\|-` (shows) operator |
| `pattern_matching.txt` | Pattern matching in proof conclusions |

---

## 05_sets (7 examples)

| File | Demonstrates |
|------|-------------|
| `set_basics.txt` | `{}`, `elem`, `notin`, membership predicates |
| `set_operations.txt` | `union`, `inter`, set difference, `P` (power set) |
| `cartesian_tuples.txt` | `cross` product and ordered pairs |
| `set_literals.txt` | Set literal notation with maplets |
| `tuple_examples.txt` | Tuple construction and component selection (`.1`, `.2`) |
| `strict_subset.txt` | `psubset` (strict subset) and `subset` comparisons |
| `union_domain.txt` | Distributed union and domain operations |

---

## 06_definitions (9 examples)

Z paragraphs: given types, free types, abbreviations, axdef, schema.

| File | Demonstrates |
|------|-------------|
| `free_types_demo.txt` | `Type ::= branch1 \| branch2` — basic free type definitions |
| `free_types_proper.txt` | Recursive free types (trees, lists) |
| `gendef_basic.txt` | Generic function definitions with one type parameter |
| `gendef_advanced.txt` | Generic definitions with multiple type parameters |
| `abbrev_demo.txt` | Abbreviation definitions (`==`) |
| `axdef_demo.txt` | Axiomatic definitions with `where` constraints |
| `schema_demo.txt` | Vertical schema with declarations and predicate |
| `anonymous_schema.txt` | Anonymous schema expressions |
| `syntax_demo.txt` | Overview of all Z definition syntax forms |

---

## 07_relations (7 examples)

| File | Demonstrates |
|------|-------------|
| `domain_range.txt` | `dom` and `ran` operators |
| `maplets.txt` | All function-type arrow forms (`->`, `+->`, `>->`, `>->>`, etc.) |
| `range_examples.txt` | Range operator `m..n` in expressions, schemas, and comprehensions |
| `relation_operators.txt` | `<->`, `\|->`, `<\|`, `\|>`, `comp`, `o9`, `dom`, `ran` |
| `relational_composition.txt` | Generic type instantiation: `emptyset[T]`, `seq[T]`, nested generics |
| `relational_image.txt` | Relational image `R(\| S \|)` |
| `restrictions.txt` | Domain restriction `<\|`, range restriction `\|>`, and subtraction forms |

---

## 08_functions (8 examples)

| File | Demonstrates |
|------|-------------|
| `lambda_expressions.txt` | `lambda x : T . body` |
| `function_definitions_simple.txt` | Function type declarations and axiomatic definitions |
| `function_composition.txt` | Function composition operator |
| `composition_pipelines.txt` | Chained function composition |
| `finite_functions.txt` | Finite function types and literals |
| `higher_order_functions.txt` | Functions that take or return functions |
| `sequence_tuple_tests.txt` | Sequence and tuple function examples |
| `sequences_bags_tuples.txt` | Functions over sequences, bags, and tuples |

---

## 09_sequences (7 examples)

| File | Demonstrates |
|------|-------------|
| `sequence_basics.txt` | `seq N`, `iseq N`, Unicode `⟨⟩` and ASCII `<>` literals |
| `concatenation.txt` | Sequence concatenation (`^`, `⌢`) and cons patterns |
| `sequence_operations.txt` | `#`, `head`, `tail`, `last`, `front`, `rev` |
| `sequence_filter.txt` | `filter` / `↾` operator; also `bag_union` / `⊎` |
| `pattern_matching.txt` | Pattern matching with sequences in recursive definitions |
| `user_defined_squash.txt` | Axiomatic definition of a `squash` function using `gendef` |
| `bags.txt` | Bag types and `[[...]]` bag literals |

---

## 10_schemas (8 examples)

Schema calculus features beyond the basic vertical form.

| File | Demonstrates |
|------|-------------|
| `scoping_demo.txt` | Schema scoping and variable visibility |
| `zed_blocks.txt` | Multiple Z notation block types in one document |
| `also_blank_lines.txt` | `\also` generation from blank lines inside axdef/schema |
| `delta_xi_inclusion.txt` | `Delta S` / `Xi S` before/after-state convention; bare schema inclusion |
| `horizontal_defs.txt` | `Name defs Schema-Exp` and inline `[ decl \| pred ]` form |
| `schema_as_predicate.txt` | Including schemas in declaration part; schema conjunction with `land` |
| `schema_rename.txt` | Schema renaming `S[old/new]` per Z RM §3.11 |
| `theta_binding.txt` | `theta S` and `theta S'` expressions for state snapshots |

---

## 11_text_blocks (6 examples)

| File | Demonstrates |
|------|-------------|
| `text_smart.txt` | Smart inline math detection in TEXT blocks |
| `puretext.txt` | PURETEXT — raw prose, no math conversion |
| `latex_passthrough.txt` | LATEX block — raw LaTeX verbatim passthrough |
| `combined_directives.txt` | Mixing TEXT, PURETEXT, LATEX, and Z blocks |
| `pagebreak.txt` | PAGEBREAK directive |
| `bibliography_example.txt` | Bibliography and citation support |

---

## 12_advanced (3 examples)

| File | Demonstrates |
|------|-------------|
| `subscripts_superscripts.txt` | Complex subscript and superscript expressions |
| `generic_instantiation.txt` | Generic type instantiation: `emptyset[T]`, `seq[T]`, nested, chained |
| `if_then_else.txt` | Conditional expressions (`if P then e1 else e2`) |

---

## 13_equality_chains (1 example)

| File | Demonstrates |
|------|-------------|
| `equality_chain_basic.txt` | Multi-step equality chains with per-step justifications using `EQUAL:` |

---

## 14_relational_databases (6 examples)

Relational-database modelling in Z, including the schema-based relational calculus.

| File | Demonstrates |
|------|-------------|
| `algebra_basics.txt` | Relational algebra operators: `sigma`, `pi`, `rho`, `bowtie`, `div` |
| `bindings.txt` | Z binding literals `{\| name == e \|}` for relational-calculus queries |
| `foreign_keys.txt` | `pk` primary-key annotation; single and composite foreign-key constraints |
| `group_ungroup.txt` | GROUP / UNGROUP nested-relation operators |
| `primary_keys.txt` | `pk` attribute annotation; PK statement generated after schema box |
| `relational_calculus.txt` | Multi-declaration set comprehensions over schema projections; multi-decl forall |

---

## 15_schema_calculus (2 examples)

Schema-calculus operators in horizontal definitions.

| File | Demonstrates |
|------|-------------|
| `composition.txt` | Sequential schema composition `OpA ; OpB` |
| `piping_hiding.txt` | Schema piping `Send >> Receive` and `hide` |

---

## 16_multi_decl_calculus (1 example)

| File | Demonstrates |
|------|-------------|
| `q2d_demo.txt` | Multi-declaration Z constructs: `forall`, `exists`, `mu`, `lambda` with joint `decl; decl` form |

---

## 17_state_machines (1 example)

| File | Demonstrates |
|------|-------------|
| `turnstile.txt` | State schema, Init schema, two Delta operations (Coin, Push), one Xi query (IsLocked); `?`/`!` decoration |

---

## fuzz_tests/ (5 examples)

Edge cases used to validate fuzz type-checker integration. Not learning examples.

| File | Demonstrates |
|------|-------------|
| `test_field_projection_bug.txt` | Field projection on function applications |
| `test_zed.txt` | zed notation edge cases |
| `test_mod.txt` | Modulo operator |
| `test_mod2.txt` | Modulo in axiomatic definitions (`axdef` with `mod`) |
| `test_nested_super.txt` | Nested superscripts |

---

## user_guide/ (61 examples)

One example per section of [docs/guides/USER_GUIDE.md](../docs/guides/USER_GUIDE.md). Numbered to match the guide's section order. Used for documentation validation; not intended as standalone reading.

| File | Demonstrates |
|------|-------------|
| `01_document_structure.txt` | Section headers, solution blocks, part labels |
| `02_text_smart.txt` | Smart inline math in TEXT |
| `03_text_citations.txt` | Citations and references in TEXT |
| `04_puretext.txt` | PURETEXT block |
| `05_latex_passthrough.txt` | LATEX block |
| `06_bibliography_manual.txt` | Manual bibliography entries |
| `07_truth_table.txt` | TRUTH TABLE block |
| `08_equivalence_chains.txt` | EQUIV chains with per-step justifications |
| `09_quantifiers_basic.txt` | `forall`, `exists` |
| `10_quantifiers_bullet.txt` | Bullet separator in quantifiers |
| `11_mu_operator.txt` | `mu` operator |
| `12_multi_variable_quantifiers.txt` | Multiple variables in one quantifier |
| `13_nested_quantifiers.txt` | Nested quantification |
| `14_set_notation.txt` | Set literals, membership |
| `15_power_set.txt` | `P` (power set) |
| `16_cartesian_product.txt` | `cross` product |
| `17_field_projection.txt` | Tuple field projection (`.1`, `.2`) |
| `18_set_comprehension.txt` | `{ x : T \| P }` and `{ x : T \| P . e }` |
| `19_distributed_ops.txt` | Distributed union / intersection |
| `20_given_types.txt` | `given A, B` |
| `21_abbreviations.txt` | `Name == expr` |
| `22_free_types.txt` | `Type ::= branch1 \| branch2` |
| `23_gendef_basic.txt` | `gendef [X]` single-parameter definition |
| `24_gendef_multiple_decls.txt` | `gendef` with multiple declarations |
| `25_generic_free_type_workaround.txt` | Workaround for generic free types |
| `26_generic_schema.txt` | `schema Name[X]` |
| `27_relations_basic.txt` | `<->`, `\|->`, `dom`, `ran` |
| `28_restrictions.txt` | `<\|`, `\|>`, `<<\|`, `\|>>` |
| `29_relational_image.txt` | `R(\| S \|)` |
| `30_composition.txt` | `comp`, `o9` |
| `31_closures.txt` | `+` (transitive), `*` (reflexive-transitive) closures |
| `32_compound_identifiers.txt` | Multi-word identifiers |
| `33_function_types.txt` | `->`, `+->`, `>->`, `>->>`, etc. |
| `34_function_application.txt` | `f x`, `f(x)`, prefix vs. infix |
| `35_lambda_expressions.txt` | `lambda x : T . body` |
| `36_function_override.txt` | Function override `f (+) g` |
| `37_range_operator.txt` | `m..n` |
| `38_function_definitions.txt` | Axiomatic function definitions |
| `39_function_properties.txt` | Injectivity, surjectivity, bijectivity |
| `40_recursive_functions.txt` | Recursive function specifications |
| `41_higher_order_functions.txt` | Functions as arguments and return values |
| `42_sequence_literals.txt` | `⟨⟩`, `<>` |
| `43_concatenation.txt` | `^`, `⌢` |
| `44_sequence_filter.txt` | `filter`, `↾` |
| `45_sequence_functions.txt` | `head`, `tail`, `last`, `front`, `rev`, `#` |
| `46_pattern_matching.txt` | Pattern matching in function bodies |
| `47_bags.txt` | `bag T`, `[[...]]` literals |
| `48_zed_blocks.txt` | `zed ... end` paragraph form |
| `49_axdef_global_scope.txt` | `axdef` at global scope |
| `50_axdef_basic.txt` | `axdef` with `where` |
| `51_schema_basic.txt` | Vertical schema with declarations and predicate |
| `52_anonymous_schema.txt` | Anonymous schema expressions |
| `53_proof_simple.txt` | Simple PROOF block |
| `54_proof_case_analysis.txt` | Case analysis in proofs |
| `55_proof_distributivity.txt` | Distributivity proof |
| `56_conditional_expressions.txt` | `if P then e1 else e2` |
| `57_subscripts_superscripts.txt` | Subscripts and superscripts |
| `58_multi_word_identifiers.txt` | Identifiers with spaces (multi-word) |
| `59_comparison_operators.txt` | `<`, `>`, `<=`, `>=`, `!=` |
| `60_arithmetic_operators.txt` | `+`, `-`, `*`, `div`, `mod` |
| `61_generic_instantiation.txt` | Generic type instantiation |

---

## File naming conventions

- Source: `.txt` only. The `.tex` and `.pdf` files are generated — do not edit them.
- Descriptive names reflecting content (`lambda_expressions.txt`, not `test3.txt`).
- Files in `fuzz_tests/` may use `test_` prefix; all other directories avoid it.

## Contributing examples

1. Place the file in the appropriate numbered directory (or create a new one).
2. Use a clear, descriptive filename.
3. Add a header comment explaining what the example demonstrates.
4. Verify with `txt2tex <file>` — fuzz must report zero errors for any Z notation.
5. Update this README.

See [tests/bugs/README.md](../tests/bugs/README.md) for bug reproduction cases (separate from examples).
