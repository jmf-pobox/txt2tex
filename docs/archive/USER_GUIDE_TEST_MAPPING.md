# USER-GUIDE.md Test Mapping

**Date:** 2025-10-27  
**Purpose:** Map each USER-GUIDE.md syntax example to corresponding test cases

## Methodology

For each code example in USER-GUIDE.md:
1. Extract the example syntax
2. Find corresponding test file
3. Identify specific test function
4. Verify test passes
5. Mark as ✅ if found, ⚠️ if partial, ❌ if missing

---

## Document Structure Examples

### ✅ Sections
**USER-GUIDE:** `=== Title ===`  
**Test:** Document structure tests in `test_01_propositional_logic/test_operators.py`  
**Status:** ✅ Covered in document parsing tests

### ✅ Solutions
**USER-GUIDE:** `** Solution 1 **`  
**Test:** Document structure tests  
**Status:** ✅ Covered

### ✅ Part Labels
**USER-GUIDE:** `(a) First part`, `(b) Second part`  
**Test:** Document structure tests  
**Status:** ✅ Covered

---

## Text Block Examples

### ⚠️ TEXT: with inline operators
**USER-GUIDE:** 
```
TEXT: This is a plain text paragraph with => and <=> symbols.
TEXT: The set { x : N | x > 0 } contains positive integers.
TEXT: We know that forall x : N | x >= 0 is true.
```
**Test:** `tests/test_text_formatting/` - text block operator conversion  
**Status:** ⚠️ Need to verify citation syntax specifically

### ⚠️ TEXT: Citations
**USER-GUIDE:**
```
TEXT: The proof technique follows [cite simpson25a].
TEXT: This is discussed in [cite simpson25a slide 20].
TEXT: See the definition in [cite spivey92 p. 42].
```
**Test:** Not found - **MISSING TEST**  
**Status:** ❌ No citation tests found

### ✅ PURETEXT
**USER-GUIDE:**
```
PURETEXT: Simpson, A. (2025) "Lecture notes" & references.
```
**Test:** `tests/test_text_formatting/`  
**Status:** ✅ Covered

### ✅ LATEX
**USER-GUIDE:**
```
LATEX: \begin{center}\textit{Custom formatting}\end{center}
```
**Test:** `tests/test_text_formatting/`  
**Status:** ✅ Covered

---

## Propositional Logic Examples

### ✅ Basic Operators
**USER-GUIDE:** `p and q`, `p or q`, `not p`, `p => q`, `p <=> q`  
**Test:** `tests/test_01_propositional_logic/test_operators.py`  
**Status:** ✅ All operators tested

### ✅ TRUTH TABLE
**USER-GUIDE:**
```
TRUTH TABLE:
p | q | p => q
T | T | T
```
**Test:** `tests/test_01_propositional_logic/test_truth_tables.py`  
**Status:** ✅ Covered

### ✅ EQUIV:
**USER-GUIDE:**
```
EQUIV:
not (p and q)
<=> not p or not q [De Morgan]
```
**Test:** `tests/test_01_propositional_logic/test_equivalences.py`  
**Status:** ✅ Covered

---

## Predicate Logic Examples

### ✅ Universal Quantifier
**USER-GUIDE:** `forall x : N | x > 0`  
**Test:** `tests/test_02_predicate_logic/test_quantifiers.py::test_quantifier_forall_with_domain`  
**Status:** ✅ Verified

### ✅ Existential Quantifier
**USER-GUIDE:** `exists y : Z | y < 0`  
**Test:** `tests/test_02_predicate_logic/test_quantifiers.py`  
**Status:** ✅ Verified

### ✅ Exists1 Quantifier
**USER-GUIDE:** `exists1 x : N | x * x = 4`  
**Test:** `tests/test_02_predicate_logic/test_quantifiers.py::test_quantifier_exists1`  
**Status:** ✅ Verified

### ✅ Mu Operator (basic)
**USER-GUIDE:** `mu x : N | x * x = 4 and x > 0`  
**Test:** `tests/test_05_sets/test_set_operations.py::test_mu_operator`  
**Status:** ✅ Verified

### ✅ Mu Operator with Expression
**USER-GUIDE:** `mu x : N | x in S . f(x)`  
**Test:** `tests/test_edge_cases/test_parser_edge_cases.py::test_mu_with_expression`  
**Status:** ✅ Verified - **FOUND TEST**

### ✅ Multi-Variable Quantifiers
**USER-GUIDE:** `forall x, y : N | x = y`  
**Test:** `tests/test_02_predicate_logic/test_quantifiers.py`  
**Status:** ✅ Verified

### ✅ Nested Quantifiers
**USER-GUIDE:** `forall x : N | exists y : N | x = y`  
**Test:** `tests/test_02_predicate_logic/test_nested_quantifiers.py`  
**Status:** ✅ Verified

---

## Sets Examples

### ✅ Set Literals
**USER-GUIDE:** `{1, 2, 3}`, `{}`  
**Test:** `tests/test_05_sets/test_set_operations.py`  
**Status:** ✅ Verified

### ✅ Set Membership
**USER-GUIDE:** `x in A`, `x notin B`  
**Test:** `tests/test_05_sets/test_set_operations.py`  
**Status:** ✅ Verified

### ✅ Set Operations
**USER-GUIDE:** `A subset B`, `A union B`, `A intersect C`, `A \ B`  
**Test:** `tests/test_05_sets/test_set_operations.py`  
**Status:** ✅ Verified

### ✅ Power Sets
**USER-GUIDE:** `P S`, `P1 S`, `F S`, `P (A cross B)`  
**Test:** `tests/test_05_sets/test_set_operations.py`  
**Status:** ✅ Verified

### ✅ Set Comprehension
**USER-GUIDE:** 
- `{ x : N | x > 0 }`
- `{ x : N | x > 0 . x^2 }`
- `{ x, y : N | x = y }`
- `{ x | x in A }`
**Test:** `tests/test_05_sets/test_set_comprehension.py`  
**Status:** ✅ All variants verified

### ✅ Set Literals with Maplets
**USER-GUIDE:** `{1 |-> a, 2 |-> b, 3 |-> c}`  
**Test:** `tests/test_05_sets/test_set_literal_maplets.py`  
**Status:** ✅ Verified

---

## Relations Examples

### ✅ All Relation Operators
**USER-GUIDE:**
- `x |-> y` (maplet)
- `X <-> Y` (relation type)
- `dom R`, `ran R`
- `S <| R`, `R |> T` (restrictions)
- `S <<| R`, `R |>> T` (corestrictions)
- `R~`, `inv R` (inverse)
- `R(| S |)` (relational image)
- `R o9 S`, `R comp S` (composition)
- `R+`, `R*` (closures)
**Test:** `tests/test_07_relations/` (95 tests)  
**Status:** ✅ All operators verified

---

## Functions Examples

### ✅ Function Types
**USER-GUIDE:**
- `X -> Y` (total function)
- `X +-> Y` (partial function)
- `X >-> Y` (total injection)
- `X >+> Y` (partial injection)
- `X -->> Y` (total surjection)
- `X +->> Y` (partial surjection)
- `X >->> Y` (bijection)
**Test:** `tests/test_08_functions/test_function_types.py`  
**Status:** ✅ All 7 types verified

### ✅ Function Application
**USER-GUIDE:** `f(x)`, `f(x, y)`  
**Test:** `tests/test_08_functions/test_function_application.py`  
**Status:** ✅ Verified

### ✅ Space-Separated Application
**USER-GUIDE:** `f x`, `f x y`  
**Test:** `tests/test_08_functions/test_space_separated_application.py`  
**Status:** ✅ Verified

### ✅ Lambda Expressions
**USER-GUIDE:** `lambda x : N . E`  
**Test:** `tests/test_08_functions/test_lambda_expressions.py` (24 tests)  
**Status:** ✅ Verified

---

## Sequences Examples

### ✅ Sequence Literals
**USER-GUIDE:** `⟨⟩`, `⟨a, b, c⟩`, `<>`, `<a, b, c>`  
**Test:** `tests/test_09_sequences/test_sequences.py`, `test_ascii_sequences.py`  
**Status:** ✅ Verified

### ✅ Sequence Operators
**USER-GUIDE:** `head s`, `tail s`, `last s`, `front s`, `rev s`  
**Test:** `tests/test_09_sequences/test_sequences.py`  
**Status:** ✅ Verified

### ✅ Concatenation
**USER-GUIDE:** `s ⌢ t`, `s ^ t`  
**Test:** `tests/test_09_sequences/test_sequences.py`, `test_caret_whitespace.py`  
**Status:** ✅ Verified

### ✅ Bags
**USER-GUIDE:** `[[x]]`, `[[a, b, c]]`  
**Test:** `tests/test_09_sequences/test_sequences.py`  
**Status:** ✅ Verified

---

## Z Definitions Examples

### ✅ Given Types
**USER-GUIDE:** `given Person, Company`  
**Test:** `tests/test_06_definitions/` (Phase 4 tests)  
**Status:** ✅ Verified

### ✅ Free Types
**USER-GUIDE:** `Status ::= active | inactive | pending`  
**Test:** `tests/test_06_definitions/test_free_types.py`  
**Status:** ✅ Verified

### ✅ Abbreviations
**USER-GUIDE:** `Pairs == N cross N`  
**Test:** `tests/test_06_definitions/`  
**Status:** ✅ Verified

### ✅ Axdef
**USER-GUIDE:**
```
axdef
  population : N
where
  population > 0
end
```
**Test:** `tests/test_06_definitions/`  
**Status:** ✅ Verified

### ✅ Schema
**USER-GUIDE:**
```
schema State
  count : N
where
  count >= 0
end
```
**Test:** `tests/test_06_definitions/`  
**Status:** ✅ Verified

### ✅ Gendef
**USER-GUIDE:**
```
gendef [X]
  f : X -> X
where
  forall x : X | f(f(x)) = x
end
```
**Test:** `tests/test_06_definitions/test_generic_parameters.py`  
**Status:** ✅ Verified

### ✅ Semicolon Declarations
**USER-GUIDE:**
```
gendef [X, Y]
  fst : X cross Y -> X; snd : X cross Y -> Y
end
```
**Test:** `tests/test_06_definitions/test_semicolon_declarations.py`  
**Status:** ✅ Verified

---

## Proof Trees Examples

### ✅ PROOF:
**USER-GUIDE:**
```
PROOF:
p => q [=> intro]
  p [assumption]
  q [from p]
```
**Test:** `tests/test_04_proof_trees/test_proof_trees.py` (27 tests)  
**Status:** ✅ Verified

---

## Missing Tests Needed

Based on USER-GUIDE.md examples that don't have corresponding tests:

### 1. ❌ Citation Syntax in TEXT Blocks
**Missing Test:** Citation syntax `[cite key]`, `[cite key locator]`  
**USER-GUIDE Examples:**
- `[cite simpson25a]`
- `[cite simpson25a slide 20]`
- `[cite spivey92 p. 42]`
- `[cite woodcock96 pp. 10-15]`

**Suggested Test File:** `tests/test_text_formatting/test_citations.py`  
**Priority:** MEDIUM - Feature documented but not verified by tests

---

## Summary

### ✅ Verified Examples
- **Document structure**: Sections, solutions, parts
- **Text blocks**: TEXT, PURETEXT, LATEX (except citations)
- **Propositional logic**: All operators, truth tables, EQUIV chains
- **Predicate logic**: All quantifiers including mu with expression
- **Sets**: All operations, comprehensions, literals
- **Relations**: All operators (95 tests)
- **Functions**: All types and applications (comprehensive tests)
- **Sequences**: Literals, operators, concatenation, bags
- **Z definitions**: All types (given, free, abbrev, axdef, schema, gendef)
- **Proof trees**: PROOF syntax (27 tests)

### ❌ Missing Tests
1. **Citation syntax** - TEXT blocks with `[cite ...]` syntax

### Total Verification Status
- **Examples verified**: ~95%
- **Examples needing tests**: ~5% (1 major gap: citations)

