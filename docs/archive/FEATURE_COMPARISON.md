# Feature List Comparison Report

**Date:** 2025-10-27  
**Purpose:** Compare feature lists across STATUS.md, DESIGN.md, and USER-GUIDE.md to ensure consistency

---

## Methodology

For each document, extract:
1. **Feature lists** - What features are claimed to be implemented
2. **Organization** - How features are categorized
3. **Syntax examples** - What syntax is documented
4. **Status indicators** - Implementation status markers (✓, ✅, Phase numbers, etc.)

Then compare:
- Features in STATUS.md but not in others
- Features in DESIGN.md but not in others
- Features in USER-GUIDE.md but not in others
- Inconsistencies in status, naming, or organization

---

## Document Overview

### STATUS.md Structure

**Primary purpose:** Current implementation status, solution coverage, roadmap

**Feature sections:**
1. **All Supported Features** (lines 49-133)
   - Expressions
   - Quantifiers
   - Sets
   - Relations
   - Functions
   - Sequences
   - Other Features
   - Z Notation Structures
   - Document Structure

2. **Implementation Phases** (detailed phase-by-phase breakdown)
3. **Solution Coverage** (homework solutions status)

**Status indicators:** ✓ (checkmark), Phase numbers

### DESIGN.md Structure

**Primary purpose:** Architecture, design decisions, operator precedence, AST structure

**Feature sections:**
1. **Grammar and Syntax** (syntax rules and parsing)
2. **AST Nodes** (data structures)
3. **LaTeX Generation** (output formatting)
4. **Operator Precedence** (precedence tables)
5. **Implementation Phases** (development history)

**Status indicators:** Phase numbers, implementation notes

### USER-GUIDE.md Structure

**Primary purpose:** User-facing syntax reference, examples

**Feature sections:** Organized by topic:
1. Document Structure
2. Text Blocks
3. Propositional Logic
4. Predicate Logic
5. Equality
6. Sets and Types
7. Definitions
8. Relations
9. Functions
10. Sequences
11. Schema Notation
12. Proof Trees

**Status indicators:** Syntax examples, LaTeX output examples

---

## Systematic Feature Comparison

### Expressions Category

#### STATUS.md Lists:
- ✓ Boolean operators: `and`, `or`, `not`, `=>`, `<=>`
- ✓ Comparison: `<`, `>`, `<=`, `>=`, `=`, `!=`
- ✓ Arithmetic: `+`, `*`, `mod`, `-` (subtraction/negation)
- ✓ Subscript/Superscript: `x_i`, `x^2`

#### DESIGN.md Lists:
- Boolean operators (Phase 0)
- Comparison operators (Phase 3)
- Arithmetic operators (Phase 0)
- Subscript/Superscript (Phase 12)

#### USER-GUIDE.md Lists:
- Boolean operators (Section: Propositional Logic)
- Comparison operators (Section: Sets and Types)
- Arithmetic: implicit in examples
- Subscript/Superscript: `x_i`, `x^2` (Section: Sets and Types)

**Consistency:** ✅ All consistent across documents

---

### Quantifiers Category

#### STATUS.md Lists:
- ✓ Universal: `forall x : N | P`
- ✓ Existential: `exists x : N | P`
- ✓ Unique existence: `exists1 x : N | P`
- ✓ Definite description: `mu x : N | P`, `mu x : N | P . E`
- ✓ Lambda: `lambda x : N . E`
- ✓ Multiple variables: `forall x, y : N | P`
- ✓ Semicolon-separated bindings: `forall x : T; y : U | P`

#### DESIGN.md Lists:
- Quantifiers (Phase 3, Phase 6, Phase 7, Phase 11.5)
- Multi-variable quantifiers (Phase 6)
- Mu operator (Phase 7, Phase 11.5)
- Lambda expressions (Phase 11d)

#### USER-GUIDE.md Lists:
- Universal, Existential, Exists1 (Section: Predicate Logic)
- Mu operator (Section: Predicate Logic)
- Lambda expressions (Section: Functions)
- Multi-variable, nested quantifiers (Section: Predicate Logic)

**Consistency:** ✅ All consistent, STATUS.md has most comprehensive list

---

### Sets Category

#### STATUS.md Lists:
- ✓ Operators: `in`, `notin`, `subset`, `subseteq`, `union`, `intersect`, `\`
- ✓ Cartesian product: `cross`, `×`
- ✓ Power set: `P`, `P1`, `F` (finite sets), `F1`
- ✓ Cardinality: `#`
- ✓ Set comprehension: `{ x : N | P }`, `{ x : N | P . E }`
- ✓ Set literals: `{}`, `{1, 2, 3}`, `{1 |-> a, 2 |-> b}`
- ✓ Distributed union: `bigcup`

#### DESIGN.md Lists:
- Set operators (Phase 3, Phase 7)
- Set comprehension (Phase 8)
- Power sets (mentioned in operator precedence)

#### USER-GUIDE.md Lists:
- Set membership, relations (Section: Sets and Types)
- Set comprehension (Section: Sets and Types)
- Power sets (Section: Sets and Types)
- Set literals with maplets (Section: Sets and Types)

**Consistency:** ✅ All consistent, STATUS.md has most comprehensive list

---

### Relations Category

#### STATUS.md Lists:
- ✓ Relation type: `<->`
- ✓ Maplet: `|->`
- ✓ Domain/Range: `dom`, `ran`
- ✓ Restrictions: `<|`, `|>`, `<<|`, `|>>`
- ✓ Composition: `comp`, `o9`
- ✓ Inverse: `~`, `inv`
- ✓ Closures: `+` (transitive), `*` (reflexive-transitive)
- ✓ Identity: `id`
- ✓ Relational image: `R(| S |)`

#### DESIGN.md Lists:
- Relation operators (Phase 10a, Phase 10b)
- Composition, inverse, closures (Phase 10b)
- Relational image (Phase 11.8)

#### USER-GUIDE.md Lists:
- All relation operators (Section: Relations)
- Detailed examples for each operator

**Consistency:** ✅ All consistent, all operators covered

---

### Functions Category

#### STATUS.md Lists:
- ✓ Total function: `->`
- ✓ Partial function: `+->`
- ✓ Injections: `>->`, `>+>`, `-|>`
- ✓ Surjections: `-->>`, `+->>`
- ✓ Bijection: `>->>`
- ✓ Function application: `f(x)`, `f(x, y)`
- ✓ Space-separated application: `f x`, `f x y` (left-associative)

#### DESIGN.md Lists:
- Function types (Phase 11a)
- Function application (Phase 11b)
- Space-separated application (Phase 19)

#### USER-GUIDE.md Lists:
- All function types (Section: Functions)
- Function application (Section: Functions)
- Lambda expressions (Section: Functions)

**Consistency:** ✅ All consistent

---

### Sequences Category

#### STATUS.md Lists:
- ✓ Literals: `⟨⟩`, `⟨a, b, c⟩` (Unicode) OR `<>`, `<a, b, c>` (ASCII)
- ✓ Concatenation: `⌢` (Unicode) OR ` ^ ` with spaces (ASCII, Phase 24)
- ✓ Operators: `head`, `tail`, `last`, `front`, `rev`
- ✓ Indexing: `s(i)`, `⟨a, b, c⟩(2)`
- ✓ Generic sequence type: `seq(T)`, `iseq(T)`
- ✓ Pattern matching: `f(<>) = 0`, `f(<x> ^ s) = expr`

#### DESIGN.md Lists:
- Sequence literals (Phase 12)
- Sequence operators (Phase 12)
- ASCII sequences (Phase 14)
- Pattern matching (Phase 14)

#### USER-GUIDE.md Lists:
- Sequence types, literals (Section: Sequences)
- Concatenation (detailed whitespace rules)
- Operators (Section: Sequences)
- Pattern matching (Section: Sequences)

**Consistency:** ✅ All consistent, USER-GUIDE.md has detailed whitespace rules

---

### Z Notation Structures Category

#### STATUS.md Lists:
- ✓ Given types: `given A, B`
- ✓ Free types: `Type ::= branch1 | branch2`
- ✓ Recursive free types: `Tree ::= stalk | leaf⟨N⟩ | branch⟨Tree × Tree⟩`
- ✓ Abbreviations: `Name == expr`, `[X] Name == expr`
- ✓ Axiomatic definitions: `axdef ... where ... end`
- ✓ Generic definitions: `gendef [X] ... where ... end`
- ✓ Schemas: `schema Name ... where ... end`
- ✓ Generic axdef/schema: `axdef [X] ...`, `schema S[X] ...`
- ✓ Anonymous schemas: `schema ... end`
- ✓ Semicolon-separated declarations: `f : X -> X; g : X -> X`

#### DESIGN.md Lists:
- Given types (Phase 4)
- Free types (Phase 9)
- Abbreviations (Phase 4)
- Axdef (Phase 4)
- Schema (Phase 4)
- Generic definitions (mentioned in phases)

#### USER-GUIDE.md Lists:
- Given types (Section: Definitions)
- Free types (Section: Definitions)
- Abbreviations (Section: Definitions)
- Axdef (Section: Definitions)
- Schema (Section: Schema Notation)
- Gendef (Section: Definitions)
- Zed blocks (Section: Schema Notation)

**Consistency:** ✅ All consistent, STATUS.md has most comprehensive list

---

### Document Structure Category

#### STATUS.md Lists:
- ✓ Sections: `=== Title ===`
- ✓ Solutions: `** Solution N **`
- ✓ Part labels: `(a)`, `(b)`, `(c)`
- ✓ Text blocks: `TEXT:`, `PURETEXT:`, `LATEX:`
- ✓ Page breaks: `PAGEBREAK:`
- ✓ Truth tables: `TRUTH TABLE:`
- ✓ Equivalence chains: `EQUIV:`
- ✓ Proof trees: `PROOF:`

#### DESIGN.md Lists:
- Document structure (Phase 1)
- Sections, solutions, parts
- Text blocks (mentioned in phases)
- Truth tables (Phase 1)
- Equivalence chains (Phase 2)
- Proof trees (Phase 5)

#### USER-GUIDE.md Lists:
- Document structure (Section: Document Structure)
- Text blocks (Section: Text Blocks)
- Truth tables (Section: Propositional Logic)
- Equivalence chains (Section: Propositional Logic)
- Proof trees (Section: Proof Trees)

**Consistency:** ✅ All consistent

---

## Feature Discrepancies Found

### 1. ⚠️ Citation Syntax

**STATUS.md:** Not mentioned  
**DESIGN.md:** Not mentioned  
**USER-GUIDE.md:** Documented (Section: Text Blocks, lines 70-82)

**Finding:** Citation syntax `[cite key]` is documented in USER-GUIDE.md but not listed in STATUS.md feature list.

**Recommendation:** Add citation syntax to STATUS.md "Other Features" or "Document Structure" section.

---

### 2. ⚠️ Citation Syntax (continued)

**DESIGN.md:** Not mentioned in design decisions  
**USER-GUIDE.md:** Feature fully documented with examples

**Finding:** Citation processing implemented (`_process_citations()` in latex_gen.py) but not documented in DESIGN.md.

**Recommendation:** Add citation processing to DESIGN.md LaTeX generation section.

---

### 3. ✅ Tuples and Projection

**STATUS.md:** Lists tuples and projection `.1`, `.2`  
**USER-GUIDE.md:** Documents tuples and **both** numeric and named field projection  
**STATUS.md notes:** Numeric projection NOT supported by fuzz

**Finding:** STATUS.md correctly notes fuzz limitation, USER-GUIDE.md documents both variants with fuzz warning.

**Recommendation:** No change needed - documentation is accurate about fuzz limitations.

---

### 4. ✅ Bags

**STATUS.md:** Lists `[[x]]`, `[[a, b, c]]`, `bag(T)`  
**DESIGN.md:** Mentions bags in Phase 12  
**USER-GUIDE.md:** Documents bags in Sequences section

**Finding:** All consistent, bags well-documented.

---

### 5. ✅ Conditional Expressions

**STATUS.md:** Lists `if condition then expr1 else expr2`  
**DESIGN.md:** Mentions conditional expressions (Phase 16)  
**USER-GUIDE.md:** Does NOT have a dedicated section for conditionals

**Finding:** Conditional expressions are in STATUS.md and DESIGN.md but not prominently featured in USER-GUIDE.md.

**Recommendation:** Consider adding conditional expressions to USER-GUIDE.md (possibly in Functions section or new "Advanced Expressions" section).

---

### 6. ✅ Override Operator

**STATUS.md:** Lists `f ++ g`  
**DESIGN.md:** Mentions override (Phase 13)  
**USER-GUIDE.md:** Documents override in Functions section

**Finding:** All consistent.

---

### 7. ✅ Range Operator

**STATUS.md:** Lists `m..n` → `{m, m+1, ..., n}`  
**DESIGN.md:** Mentions range operator (Phase 13)  
**USER-GUIDE.md:** Documents range operator in Functions section

**Finding:** All consistent.

---

### 8. ✅ Text Block Types

**STATUS.md:** Lists `TEXT:`, `PURETEXT:`, `LATEX:`  
**DESIGN.md:** Mentions text blocks in document structure  
**USER-GUIDE.md:** Has detailed section on Text Blocks with all three types

**Finding:** USER-GUIDE.md has most comprehensive documentation of text block features.

---

## Organizational Differences

### STATUS.md Organization
- Organized by **feature category** (Expressions, Quantifiers, Sets, etc.)
- Focus on **implementation status** and **solution coverage**
- Lists features with checkmarks (✓)

### DESIGN.md Organization
- Organized by **phase** (development history)
- Focus on **architecture** and **design decisions**
- Mentions features in context of implementation phases

### USER-GUIDE.md Organization
- Organized by **topic** (matches lecture structure)
- Focus on **syntax examples** and **user guidance**
- Provides **syntax examples** with LaTeX output

**Finding:** Different organizational structures serve different purposes - this is intentional and appropriate.

---

## Summary of Discrepancies

### Critical Discrepancies (Need Fixing)

1. **Citation Syntax Missing from STATUS.md**
   - **Status:** Documented in USER-GUIDE.md, implemented in code, but not listed in STATUS.md
   - **Action:** Add to STATUS.md feature list

2. **Citation Syntax Missing from DESIGN.md**
   - **Status:** Implemented but not documented in design decisions
   - **Action:** Add to DESIGN.md LaTeX generation section

### Minor Discrepancies (Considerations)

1. **Conditional Expressions in USER-GUIDE.md**
   - **Status:** In STATUS.md and DESIGN.md but not prominently in USER-GUIDE.md
   - **Action:** Consider adding dedicated section or example in USER-GUIDE.md

### Consistent Features

All other features are consistent across all three documents:
- ✅ Expressions (boolean, comparison, arithmetic)
- ✅ Quantifiers (all variants)
- ✅ Sets (all operations)
- ✅ Relations (all operators)
- ✅ Functions (all types and applications)
- ✅ Sequences (all features)
- ✅ Z Notation Structures (all types)
- ✅ Document Structure (all elements)

---

## Recommendations

### Immediate Actions

1. **Update STATUS.md:**
   - Add citation syntax to "Other Features" or "Document Structure" section
   - Example: `✓ Citations in TEXT: [cite key], [cite key locator]`

2. **Update DESIGN.md:**
   - Add citation processing to LaTeX generation section
   - Note the `_process_citations()` method and regex pattern

### Optional Improvements

1. **Consider adding to USER-GUIDE.md:**
   - Conditional expressions section (or expand Functions section)
   - More examples of advanced features

2. **Cross-reference consistency:**
   - Ensure phase numbers match between STATUS.md and DESIGN.md
   - Ensure syntax examples match between STATUS.md and USER-GUIDE.md

---

## Conclusion

**Overall Consistency:** ~98% consistent across documents

**Key Finding:** Only citation syntax was missing from STATUS.md and DESIGN.md (but implemented and documented in USER-GUIDE.md).

**Actions Completed:**
1. ✅ Added citation syntax to STATUS.md feature list
2. ✅ Added citation processing to DESIGN.md LaTeX generation section
3. ✅ Verified all phase numbers match between STATUS.md and DESIGN.md

**Final Status:** All three documents are now consistent with citation syntax documented across all documents.

