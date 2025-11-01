# txt2tex Implementation Status

**Last Updated:** 2025-11-01
**Current Phase:** Phase 35 (Sequence Filter Operator) ✓ COMPLETE

---

## Summary Statistics

| Status | Count | Percentage |
|--------|-------|------------|
| **Fully Working** | 52 | 100% |
| **Partially Working** | 0 | 0% |
| **Not Yet Implemented** | 0 | 0% |
| **Total** | 52 | 100% |

**Current Coverage:** 100% (52/52 solutions)
- All 52 solutions fully working
- Bug #3 resolved in Phase 31

**Previous Coverage:** ~98% (51/52 solutions - Phase 30)
**Recent Improvements:**
- Phase 19: Added space-separated application, completed Solutions 44-47
- Phase 20: Added semicolon-separated declarations for gendef/axdef/schema
- Phase 21: Fixed schema predicate separators, added subseteq operator (7→4 fuzz errors)
- Phase 22: Removed false blockers, completed Solutions 39, 48-52 (+6 solutions)
- **Phase 31**: Fixed Bug #3 (compound identifiers), completed Solution 31, achieved 100% (52/52) ✅

---

## Implementation Progress by Topic

| Topic | Solutions | Fully Working | Partial | Coverage |
|-------|-----------|---------------|---------|----------|
| Propositional Logic | 1-4 | 4 | 0 | 100% |
| Quantifiers | 5-8 | 4 | 0 | 100% |
| Equality | 9-12 | 4 | 0 | 100% |
| Deductive Proofs | 13-18 | 6 | 0 | 100% |
| Sets and Types | 19-26 | 8 | 0 | 100% |
| Relations | 27-32 | 6 | 0 | 100% |
| Functions | 33-36 | 4 | 0 | 100% |
| Sequences | 37-39 | 3 | 0 | 100% |
| Modeling | 40-43 | 4 | 0 | 100% |
| Free Types | 44-47 | 4 | 0 | 100% |
| Supplementary | 48-52 | 5 | 0 | 100% |
| **TOTAL** | **1-52** | **51** | **0** | **98.1%** |

---

## All Supported Features

### Expressions
- ✓ Boolean operators: `and`, `or`, `not`, `=>`, `<=>`
- ✓ Comparison: `<`, `>`, `<=`, `>=`, `=`, `!=`
- ✓ Arithmetic: `+`, `*`, `mod`, `-` (subtraction/negation)
- ✓ Subscript/Superscript: `x_i`, `x^2`

### Quantifiers
- ✓ Universal: `forall x : N | P`
- ✓ Existential: `exists x : N | P`
- ✓ Unique existence: `exists1 x : N | P`
- ✓ Definite description: `mu x : N | P`, `mu x : N | P . E`
- ✓ Lambda: `lambda x : N . E`
- ✓ Multiple variables: `forall x, y : N | P`
- ✓ Semicolon-separated bindings: `forall x : T; y : U | P`

### Sets
- ✓ Operators: `in`, `notin`, `subset`, `subseteq`, `union`, `intersect`, `\`
- ✓ Cartesian product: `cross`, `×`
- ✓ Power set: `P`, `P1`, `F` (finite sets), `F1`
- ✓ Cardinality: `#`
- ✓ Set comprehension: `{ x : N | P }`, `{ x : N | P . E }`
- ✓ Set literals: `{}`, `{1, 2, 3}`, `{1 |-> a, 2 |-> b}`
- ✓ Distributed union: `bigcup`
- ✓ Distributed intersection: `bigcap`

### Relations
- ✓ Relation type: `<->`
- ✓ Maplet: `|->`
- ✓ Domain/Range: `dom`, `ran`
- ✓ Restrictions: `<|`, `|>`, `<<|`, `|>>`
- ✓ Composition: `comp`, `o9` (Note: `;` is reserved for declaration separators)
- ✓ Inverse: `~`, `inv`
- ✓ Closures: `+` (transitive), `*` (reflexive-transitive)
- ✓ Identity: `id`
- ✓ Relational image: `R(| S |)`

### Functions
- ✓ Total function: `->`
- ✓ Partial function: `+->`
- ✓ Injections: `>->`, `>+>`, `-|>`
- ✓ Surjections: `-->>`, `+->>`
- ✓ Bijections: `>->>` (total), `>7->` (partial)
- ✓ Finite partial functions: `7 7->` (Phase 34)
- ✓ Function application: `f(x)`, `f(x, y)`
- ✓ Space-separated application: `f x`, `f x y` (left-associative)

### Sequences
- ✓ Literals: `⟨⟩`, `⟨a, b, c⟩` (Unicode) OR `<>`, `<a, b, c>` (ASCII)
- ✓ Concatenation: `⌢` (Unicode) OR ` ^ ` with spaces (ASCII, Phase 24)
- ✓ Filter: `s ↾ A` (sequence filter - Phase 35)
- ✓ Operators: `head`, `tail`, `last`, `front`, `rev`
- ✓ Indexing: `s(i)`, `⟨a, b, c⟩(2)`
- ✓ Generic sequence type: `seq(T)`, `iseq(T)`
- ✓ Pattern matching: `f(<>) = 0`, `f(<x> ^ s) = expr`

### Other Features
- ✓ Tuples: `(a, b)`, projection `.1`, `.2`
- ✓ Bags: `[[x]]`, `[[a, b, c]]`, `bag(T)`
- ✓ Ranges: `m..n` → `{m, m+1, ..., n}`
- ✓ Override: `f ++ g`
- ✓ Conditional expressions: `if condition then expr1 else expr2`
- ✓ Multi-word identifiers: `cumulative_total`, `not_yet_viewed`
- ✓ Digit-starting identifiers: `479_courses`, `123_abc_456`

### Z Notation Structures
- ✓ Given types: `given A, B`
- ✓ Free types: `Type ::= branch1 | branch2`
- ✓ Recursive free types: `Tree ::= stalk | leaf⟨N⟩ | branch⟨Tree × Tree⟩`
- ✓ Abbreviations: `Name == expr`, `[X] Name == expr`
- ✓ Axiomatic definitions: `axdef ... where ... end`
- ✓ Generic definitions: `gendef [X] ... where ... end`
- ✓ Schemas: `schema Name ... where ... end`
- ✓ Generic axdef/schema: `axdef [X] ...`, `schema S[X] ...`
- ✓ Anonymous schemas: `schema ... end`
- ✓ Semicolon-separated declarations: `f : X -> X; g : X -> X` (renders on separate lines)

### Document Structure
- ✓ Sections: `=== Title ===`
- ✓ Solutions: `** Solution N **`
- ✓ Part labels: `(a)`, `(b)`, `(c)`
- ✓ Text blocks: `TEXT:`, `PURETEXT:`, `LATEX:`
- ✓ Citations in TEXT: `[cite key]`, `[cite key locator]` (Harvard style)
- ✓ Page breaks: `PAGEBREAK:`
- ✓ Truth tables: `TRUTH TABLE:`
- ✓ Equivalence chains: `EQUIV:`
- ✓ Proof trees: `PROOF:`

---

## Features by Phase (Implementation History)

### ✅ Phase 0: Propositional Logic
- Basic operators: `and`, `or`, `not`, `=>`, `<=>`
- Correct precedence and associativity
- Parentheses for grouping

### ✅ Phase 1: Document Structure
- Section headers: `=== Title ===`
- Solution blocks: `** Solution N **`
- Part labels: `(a)`, `(b)`, `(c)`
- Truth tables: `TRUTH TABLE:`
- Proper spacing with `\bigskip`, `\medskip`

### ✅ Phase 2: Equivalence Chains
- `EQUIV:` environment
- Justifications in brackets: `[rule name]`
- Automatic alignment with `align*`
- Operator conversion in justifications

### ✅ Phase 3: Mathematical Notation
- Quantifiers: `forall`, `exists`
- Subscripts: `x_i`, `a_{n}`
- Superscripts: `x^2`, `2^{10}`
- Set operators: `in`, `notin`, `subset`, `union`, `intersect`
- Comparison: `<`, `>`, `<=`, `>=`, `=`, `!=`

### ✅ Phase 4: Z Notation Basics
- Given types: `given A, B`
- Free types: `Type ::= branch1 | branch2`
- Abbreviations: `Name == Expression`
- Axiomatic definitions: `axdef ... where ... end`
- Schemas: `schema Name ... where ... end`

### ✅ Phase 5: Proof Trees
- Natural deduction proofs
- Indentation-based structure
- Assumption discharge with labels
- Multiple inference rules
- Case analysis with `or-elim`
- LaTeX `\infer` macro generation

### ✅ Phase 6: Multi-Variable Quantifiers
- Comma-separated variables: `forall x, y : N`
- Shared domain across variables
- Works with all quantifiers

### ✅ Phase 7: Equality & Special Operators
- Equality: `=`, `!=` in all contexts
- Unique existence: `exists1`
- Mu operator: `mu x : N | pred`
- Full equality reasoning support

### ✅ Phase 8: Set Comprehension
- Set by predicate: `{ x : N | pred }`
- Set by expression: `{ x : N | pred . expr }`
- Multi-variable: `{ x, y : N | pred }`
- Optional domain: `{ x | pred }`
- Nested set comprehensions
- Inline math in TEXT paragraphs

### ✅ Phase 9: Generic Parameters
- Generic abbreviations: `[X] Name == expr`
- Generic axiomatic definitions: `axdef [T] ... end`
- Generic schemas: `schema Name[X, Y] ... end`
- Multiple type parameters: `[X, Y, Z]`
- Backwards compatible with non-generic definitions

### ✅ Phase 10a: Basic Relation Operators
- Relation type: `<->` (X ↔ Y)
- Maplet constructor: `|->` (x ↦ y)
- Domain restriction: `<|` (S ◁ R)
- Range restriction: `|>` (R ▷ T)
- Composition: `;` and `comp` (R ; S, R ∘ S)
- Domain and range functions: `dom`, `ran`

### ✅ Phase 10b: Extended Relation Operators
- Domain subtraction: `<<|` (S ⩤ R)
- Range subtraction: `|>>` (R ⩥ T)
- Composition: `o9` (R ∘ S)
- Inverse function: `inv` (inv R)
- Identity relation: `id` (id X)
- Postfix inverse: `~` (R⁻¹)
- Transitive closure: `+` (R⁺)
- Reflexive-transitive closure: `*` (R*)

### ✅ Phase 11a: Function Type Operators
- Total functions: `->` (X ⇸ Y)
- Partial functions: `+->` (X ⇀ Y)
- Total injections: `>->` (X ↣ Y)
- Partial injections: `>+>` or `-|>` (X ⤔ Y)
- Total surjections: `-->>` (X ↠ Y)
- Partial surjections: `+->>` (X ⤀ Y)
- Bijections: `>->>` (X ⤖ Y)
- Nested and complex function types

### ✅ Phase 11b: Function Application
- Standard application: `f(x)`, `g(x, y, z)`
- Nested application: `f(g(h(x)))`
- Generic instantiation: `seq(N)`, `P(X)`

### ✅ Phase 11c: Function Type Parsing
- Right-associative function types
- Complex nested types
- Integration with relation operators

### ✅ Phase 11d: Lambda Expressions
- Basic lambdas: `lambda x : N . x^2`
- Multi-variable: `lambda x, y : N . x + y`
- Nested lambdas
- Complex domain types

### ✅ Phase 11.5: Additional Operators
- Arithmetic: `+`, `*`, `mod`
- Power sets: `P`, `P1`
- Cartesian product: `cross` (×)
- Set difference: `\` (∖)
- Cardinality: `#`

### ✅ Phase 11.6: Tuple Expressions
- Multi-element tuples: `(a, b, c)`
- Tuples in expressions and comprehensions
- Nested tuples

### ✅ Phase 11.7: Set Literals
- Simple literals: `{1, 2, 3}`, `{a, b, c}`
- Empty set: `{}`
- Maplets: `{1 |-> a, 2 |-> b}`
- Nested sets

### ✅ Phase 11.8: Relational Image
- Basic: `R(| S |)`
- With compositions: `(R o9 S)(| A |)`
- In comprehensions: `parentOf(| {p} |)`
- Chained application

### ✅ Phase 11.9: Generic Type Instantiation
- Basic: `emptyset[N]`, `seq[N]`, `P[X]`
- Multiple parameters: `Type[A, B, C]`
- Complex parameters: `emptyset[N cross N]`
- Nested: `Type[List[N]]`
- Chained: `Type[N][M]`
- In domains: `forall x : P[N] | ...`
- Whitespace-sensitive parsing

### ✅ Phase 12: Sequences and Bags
- Sequence literals: `⟨⟩`, `⟨a, b, c⟩` (Unicode) or `<>`, `<a, b, c>` (ASCII)
- Concatenation: `⌢` (Unicode) or `^` after sequences (ASCII)
- Sequence operators: `head`, `tail`, `last`, `front`, `rev`
- Sequence types: `seq(N)`, `iseq(N)`
- Numeric tuple projection: `.1`, `.2`, `.3` (⚠️ **not fuzz-compatible** - use named fields instead)
- **Named field projection:** `e.name`, `record.status` (✅ fuzz-compatible)
- Bag literals: `[[a, b, c]]`
- Bag types: `bag(X)`

### ✅ Phase 13.1: Anonymous Schemas
- Schemas without names: `schema ... where ... end`
- Inline schema expressions
- Compatible with all schema features

### ✅ Phase 13.2: Range Operator
- Integer ranges: `m..n` → `m \upto n`
- In expressions: `1..10`, `1993..current`, `x.2..x.3`
- Set semantics: `{m, m+1, ..., n}`

### ✅ Phase 13.3: Override Operator
- Function/sequence override: `f ++ g` → `f \oplus g`
- Left-associative: `f ++ g ++ h`
- Same precedence as union
- Use in expressions: `dom (f ++ g)`, `(f ++ g)(x)`

### ✅ Phase 13.4: General Function Application
- Any expression can be applied: `(f ++ g)(x)`, `⟨a, b, c⟩(2)`
- Sequence indexing: `s(i)`
- Chained with projection: `f(x).1`
- Enables complex functional expressions

### ✅ Phase 14: ASCII Sequence Brackets & Pattern Matching
- ASCII alternative to Unicode: `<>` ≡ `⟨⟩`, `<a, b>` ≡ `⟨a, b⟩`
- ASCII concatenation: `<x> ^ s` ≡ `⟨x⟩ ⌢ s` (enhanced in Phase 24 with whitespace sensitivity)
- Smart disambiguation: `<x>` vs `x > y` based on whitespace
- Pattern matching support: `f(<>) = 0`, `f(<x> ^ s) = expr`
- Enables recursive function definitions on sequences

### ✅ Phase 15: Underscore in Identifiers
- Multi-word identifiers: `cumulative_total`, `not_yet_viewed`
- Smart LaTeX rendering based on word length
- Simple subscripts: `a_i` → `a_i`
- Multi-char subscripts: `x_max` → `x_{max}`
- Multi-word identifiers: `cumulative_total` → `\mathit{cumulative\_total}`
- Backward compatible with existing subscript notation

### ✅ Phase 16: Conditional Expressions
- Basic conditionals: `if condition then expr1 else expr2`
- Nested conditionals in then/else branches
- Conditionals as operands in expressions
- Function definitions with conditionals: `abs(x) = if x > 0 then x else -x`
- Recursive functions: `f(s) = if s = <> then 0 else head s + f(tail s)`
- MINUS operator: `-` for subtraction and negation

### ✅ Phase 17: Semicolon-Separated Bindings
- Multiple binding groups: `forall x : N; y : N | P`
- Mixed comma and semicolon: `forall x, y : N; z : N | P`
- Nested scope for bindings
- Right-to-left nested quantifiers in LaTeX

### ✅ Phase 18: Digit-Starting Identifiers
- Identifiers can start with digits: `479_courses`, `123_abc_456`
- Smart lexing to distinguish from numbers
- Used in real-world database specifications
- LaTeX rendering with `\mathit{}`

### ✅ Phase 19: Space-Separated Application
- Left-associative application: `f x y` → `f(x)(y)`
- Works with identifiers: `dom R`, `ran S`
- Parenthesized expressions: `(f x) y`
- Generic instantiation distinguished: `seq[N]` vs `seq N`
- Completed Solutions 44-47 (free type induction)

### ✅ Phase 20: Semicolon-Separated Declarations
- Semicolon separators in declarations: `f : X -> X; g : X -> X`
- Supported in `gendef`, `axdef`, and `schema` blocks
- Both input formats (separate lines OR semicolons) render identically
- LaTeX output uses `\\` line breaks for proper rendering
- Each declaration appears on its own line in PDF
- Note: Semicolon (`;`) no longer supported for relational composition - use `o9` or `comp`

### ✅ Phase 21: Schema Separator and subseteq Operator
- Fixed predicate separator in schemas: Changed from `\land` to `\\`
- Fuzz requires `\\` separator (not conjunction operator `\land`) between predicates
- Fixed all 3 schema formatting errors in compiled_solutions.tex
- Added `subseteq` as alternative notation for `subset` (both → `\subseteq`)
- Reduced fuzz validation errors from 7 to 4 (all remaining are known fuzz limitations)

### ✅ Phase 22: False Blocker Removal and Solutions 48-52
- Removed 6 false blocker comments from compiled_solutions.txt
- Converted Solution 39 from TEXT to proper axdef blocks with camelCase
- Converted Solution 46 from TEXT to proper axdef blocks with pattern matching
- Converted Solution 51 from TEXT to proper Z notation using conditional expressions
- Converted Solution 52 from TEXT to proper axdef blocks with pattern matching and conditionals
- Solutions 48-50 already written with proper Z notation - verified compilation
- Coverage increased from 87% to 98% (45 → 51 solutions)

### ✅ Phase 24: Whitespace-Sensitive ^ Operator
- Implemented whitespace-based disambiguation for dual-meaning `^` operator
- Space before `^` → CAT token (sequence concatenation)
- No space before `^` → CARET token (exponentiation/superscript)
- Special error for common mistake `>^<` → helpful message directing to `> ^ <`
- Replaced context-based heuristic (checking prev char `>`) with whitespace check
- Fixes issue where `reverseSeq(s) ^ <x>` incorrectly tokenized as superscript
- 27 comprehensive tests covering all usage patterns
- Documentation updated in USER_GUIDE.md and DESIGN.md

### ✅ Phase 25: Justification Operator Conversion
- Extended `_escape_justification` method to convert relation and function operators
- Extended `_format_justification_label` method for PROOF tree justifications
- Added conversion for relation operators: `o9`, `|->`, `<->`, `<|`, `|>`, `<<|`, `|>>`
- Added conversion for function type operators: `->`, `+->`, `>->`, `-->>`, `>->>`, etc.
- Added conversion for relation functions: `dom`, `ran`, `comp`, `inv`, `id`
- 10 comprehensive tests covering all operator types in justifications
- Fixed user homework: `[definition of o9]` now renders as `[definition of ∘]`
- Documentation updated in USER_GUIDE.md (both EQUIV and PROOF sections)

### ✅ Phase 26: TEXT Block Operator Support
- Extended TEXT block processing to support all operators in prose
- Updated `_convert_operators_bare` to include all operators with length-based ordering
  - Added 4-character operators: `>->>`, `+->>`, `-->>` (bijection, partial/total surjection)
  - Added 3-character operators: `<=>`, `>+>` (equivalence, partial injection alt)
  - Added 2-character operators: `o9`, `++`, `⌢` (composition, override, concatenation)
- Fixed `_process_inline_math` to use `_convert_operators_bare` for type signatures
  - Replaced manual `->` conversion with comprehensive operator handling
  - Prevents operator splitting (e.g., `+->` becoming `+\fun` instead of `\pfun`)
- Extended TEXT block operator replacement in `_generate_paragraph`
  - Added missing operators to `_replace_outside_math` calls
  - Maintained length-based ordering to prevent partial matches
- Created test_text_block_operators.py (23 comprehensive tests)
  - Tests relation, function, and sequence operators in TEXT blocks
  - Tests operator ordering (no partial matches)
  - Tests homework scenarios with mixed operators
- Result: All operators now convert correctly in TEXT blocks (prose)
- Homework verification: `o9` → `\circ` throughout solutions.tex (user's primary issue solved)

### ✅ Phase 27: Line Continuation with Backslash
- Implemented backslash continuation for multi-line expressions
- Added CONTINUATION token type to distinguish `\` + newline (continuation) from `\` alone (set difference)
- Modified lexer to recognize context-sensitive backslash handling:
  - `\` followed by newline → CONTINUATION token (line break marker)
  - `\` not followed by newline → SETMINUS token (set difference operator)
- Added `line_break_after: bool` field to BinaryOp AST node
- Modified parser to detect CONTINUATION tokens after operators and set flag
- Supported operators: `<=>`, `=>`, `or`, `and`
- Modified LaTeX generator to emit `\\` and `\quad` for line breaks
- LaTeX output: `expr1 op \\\n\quad expr2` (breaks line and indents continuation)
- Use case: Prevents long predicates from running off page margins
- Example input:
  ```
  forall s : ShowId | s in dom show_episodes and \
    e in show_episodes s
  ```
- Example output:
  ```
  \forall s : ShowId \bullet s \in \dom show\_episodes \land \\
  \quad e \in show\_episodes(s)
  ```
- Created test_line_breaks/ with 16 comprehensive tests
- Tests cover: basic continuation, multiple continuations, all operators, schemas, proofs, quantifiers
- Set difference still works: `A \ B` (no newline after backslash)
- User verification: Long homework predicates now fit within margins
- Test count: 1013 tests (all passing)

### ✅ Phase 31: Compound Identifiers (Bug #3 Fix)
- Fixed Bug #3: Parser now recognizes compound identifiers with postfix operators
- Added `_parse_compound_identifier_name()` helper method to combine identifier + postfix operator
- Modified parser lookahead to detect patterns like `R+ ==`, `S* ==`, `R~ ==`
- Updated abbreviation and schema name parsing to use compound identifier parsing
- Updated LaTeX generator to render compound names correctly:
  - `R+` → `R^+` (transitive closure)
  - `R*` → `R^*` (reflexive-transitive closure)
  - `R~` → `R^{-1}` (relational inverse)
- Context-aware: Same operator has different meaning in different contexts:
  - `R+ == expr` → R+ is the abbreviation name (compound identifier)
  - `S == R+` → R+ is transitive closure operator applied to R
- Created comprehensive test suite: 18 new tests in test_compound_identifiers.py
  - Covers: lexer behavior, parser behavior, LaTeX generation, integration, edge cases
- Completed Solution 31 (Relations) - the last remaining solution
- **Achievement**: 100% solution coverage (52/52) ✅
- Test count: 1078 tests (all passing)
- All quality gates pass: type, lint, format, test

### ✅ Phase 32: Distributed Intersection Operator
- Implemented `bigcap` distributed intersection operator (Phase 2 from original plan)
- Added `BIGCAP` token type to lexer
- Added "bigcap" keyword recognition in lexer
- Added `TokenType.BIGCAP` to parser's prefix operator lists (3 locations)
- Added `bigcap` → `\bigcap` mapping in LaTeX generator
- Created comprehensive test suite: 8 new tests in test_bigcap.py
  - Covers: lexer, parser, LaTeX generation, integration
  - Tests bigcap vs bigcup distinction
- Updated USER_GUIDE.md to document `bigcap S → ⋂ S` syntax
- Test count: 1078 tests (1070 + 8 new bigcap tests, all passing)
- All quality gates pass: type, lint, format, test

### ✅ Phase 33: Partial Bijection Operator
- Implemented `>7->` partial bijection operator (from glossary)
- Added `PBIJECTION` token type to lexer
- Added ">7->" operator recognition in lexer (4-character pattern)
- Added `TokenType.PBIJECTION` to parser's function type operator lists (2 locations)
- Added `>7->` → `\pbij` mapping in LaTeX generator
- Added to all replacement functions in latex_gen.py (6 locations)
- Created comprehensive test suite: 8 new tests in test_partial_bijections.py
  - Covers: lexer, parser, LaTeX generation, integration
  - Tests partial bijection vs bijection distinction
  - Tests right-associativity
- Test count: 1086 tests (1078 + 8 new partial bijection tests, all passing)
- All quality gates pass: type, lint, format, test

### ✅ Phase 34: Finite Partial Function Operator
- Implemented `7 7->` finite partial function operator (from glossary)
- Used in Solutions 36, 40, 41 (e.g., `records : Year 7 7-> Table`)
- Added `FINFUN` token type to lexer
- Added "7 7->" operator recognition in lexer (5-character pattern with space)
  - Special handling before general digit parsing to recognize `7 7->`
  - Distinguishes from plain number `7` and other digit patterns
- Added `TokenType.FINFUN` to parser's function type operator lists (2 locations)
- Added `7 7->` → `\ffun` mapping in LaTeX generator
- Added to all replacement functions in latex_gen.py (9 locations)
  - BINARY_OPS and PRECEDENCE dictionaries
  - _convert_operators_bare replacements list (2 locations)
  - _generate_paragraph TEXT block processing
  - _process_inline_math regex pattern
  - EQUIV label conversion (2 locations)
  - PROOF justification conversion
- Created comprehensive test suite: 11 new tests in test_finite_functions.py
  - Covers: lexer (operator vs plain number), parser, LaTeX generation, integration
  - Tests finite function vs partial function distinction
  - Tests right-associativity
  - Tests realistic usage from Solutions 36, 40, 41
- Test count: 1097 tests (1086 + 11 new finite function tests, all passing)
- All quality gates pass: type, lint, format, test

### ✅ Phase 35: Sequence Filter Operator
- Implemented `↾` sequence filter operator (from glossary)
- Used extensively in Solutions 40, 41 (e.g., `s ↾ {t : Title | condition}`)
- Added `FILTER` token type to lexer
- Added "↾" operator recognition in lexer (Unicode character U+21BE)
  - Placed with other sequence operators (`⟨`, `⟩`, `⌢`)
  - No ASCII alternative (like `⌢` for concatenation, Unicode-only)
- Added `TokenType.FILTER` to parser as binary infix operator (2 locations)
  - Added to `_parse_additive()` alongside CAT, PLUS, MINUS
  - Added to `_should_parse_space_separated_arg()` infix operator list
- Added `↾` → `\filter` mapping in LaTeX generator (3 locations)
  - BINARY_OPS dictionary
  - _convert_operators_bare replacements list
  - _generate_paragraph TEXT block processing
- Created comprehensive test suite: 10 new tests in test_sequence_filter.py
  - Covers: lexer (Unicode recognition), parser, LaTeX generation, integration
  - Tests filter vs range restriction distinction (↾ vs |>)
  - Tests left-associativity
  - Tests realistic usage from Solutions 40, 41
- Test count: 1107 tests (1097 + 10 new filter tests, all passing)
- All quality gates pass: type, lint, format, test

### ✅ Fuzz Mode: Context-Aware Equivalence Operator
- Fixed `<=>` operator to render context-sensitively in fuzz mode
- **EQUIV blocks**: `<=>` → `\Leftrightarrow` (equivalence in equational reasoning)
- **Predicates** (schemas, axioms, proofs): `<=>` → `\iff` (logical "if and only if")
- Non-fuzz mode: Always uses `\Leftrightarrow` for backward compatibility
- Matches fuzz package conventions where:
  - `\iff` is the logical connective for predicates (like `\land`, `\lor`, `\implies`)
  - `\Leftrightarrow` is meta-level equivalence for equational reasoning (like in EQUIV chains)
- Consistent with existing `=>` handling which uses `\implies` in fuzz mode
- All 1013 tests pass

---

## Syntax Requirements & Limitations

### Fuzz Type Checking

When using `--fuzz` flag, the fuzz type checker validates your Z notation before PDF compilation.

**Identifiers with underscores are NOT supported by fuzz**:
- `cumulative_total` will cause fuzz validation errors
- The fuzz type checker does not recognize underscores in identifiers

**Recommended conventions for fuzz-compatible code**:

Following the conventions used in the fuzz package test suite:

1. **camelCase with initial capital** (for schemas and types):
   ```
   ✅ BirthdayBook, AddBirthday, CheckSys
   ```

2. **camelCase with initial lowercase** (for multi-word functions/variables):
   ```
   ✅ cumulativeTotal instead of cumulative_total
   ✅ maxHeight instead of max_height
   ✅ childOf instead of child_of
   ```

3. **Single-word identifiers** (preferred when possible):
   ```
   ✅ total, height, known, birthday, working
   ```

4. **Subscripts** (for indexed variables and variants):
   ```
   ✅ x_i, x_max, a_1
   ✅ BirthdayBook1, CheckSys1 (variant/refinement schemas)
   ```

**Note**: Free types can use escaped underscores in constructor names (e.g., `REPORT ::= ok | already\_known`) as this is LaTeX syntax, not an identifier.

**If you don't need fuzz validation**:
- Use underscores freely: `cumulative_total`, `child_of`, etc.
- Generate PDF without `--fuzz` flag
- LaTeX rendering works perfectly with underscores

**LaTeX generation works correctly** with underscores for both modes:
- Without `--fuzz`: Generates `\mathit{cumulative\_total}` for pdflatex
- With `--fuzz`: Generates `cumulative_total` for fuzz package (but fuzz will reject it)

**Note**: This is a fuzz limitation, not a txt2tex limitation. The tool fully supports underscores in identifiers.

#### Fuzz Validation Status (Phase 21)

**Current status**: 4 fuzz validation errors in `compiled_solutions.tex` (all known fuzz limitations)

1. **Line 2555**: `\mu` operator - Opening parenthesis expected
   - **Issue**: Fuzz mu operator syntax differs from txt2tex output
   - **Limitation**: Known fuzz type checker limitation

2. **Line 2564**: `\mu` operator - Opening parenthesis expected
   - **Issue**: Fuzz mu operator syntax differs from txt2tex output
   - **Limitation**: Known fuzz type checker limitation

3. **Line 2633**: Syntax error at symbol "{"
   - **Issue**: Known fuzz type checker limitation
   - **Limitation**: Documented in docs/FUZZ_FEATURE_GAPS.md

4. **Line 2645**: Syntax error at symbol "{"
   - **Issue**: Known fuzz type checker limitation
   - **Limitation**: Documented in docs/FUZZ_FEATURE_GAPS.md

**Note**: All 4 errors are known limitations of the fuzz type checker, not bugs in txt2tex. The LaTeX compiles successfully to PDF despite these fuzz validation errors.

**✅ Solution 41 fully validated**: Previously had 3 numeric projection errors (`.1`, `.2`, `.3`). Now refactored with named field projection (`e.year`, `e.code`, `e.enrolled`) - all errors resolved, 100% fuzz-compatible.

### Function and Type Application

**Function application requires explicit parentheses** - juxtaposition (whitespace) is optional:

```
✅ Correct:   f(x), cumulative_total(s), dom(R)
✅ Also works: f x, cumulative_total s, dom R (Phase 19+)
```

**Type application also requires parentheses**:

```
✅ Correct:   seq(Entry), P(Person)
❌ Incorrect: seq Entry, P Person (parsed as space-separated application)
```

### Nested Quantifiers

**Nested quantifiers in `and`/`or` expressions must be parenthesized**:

```
✅ Correct:   forall x : N | x > 0 and (forall y : N | y > x)
❌ Incorrect: forall x : N | x > 0 and forall y : N | y > x
```

---

## Known Limitations

### Parser Limitations

#### 1. Cannot handle prose mixed with inline math
**Severity**: High
- **Problem**: Periods cause parse errors when expressions are not in TEXT blocks
- **Example FAILS**: `1 in {4, 3, 2, 1} is true.`
- **Workaround**: Use TEXT blocks: `TEXT: 1 in {4, 3, 2, 1} is true.`
- **Root Cause**: Parser treats everything as mathematical expression outside TEXT

#### 2. TEXT blocks with multiple pipes close math mode prematurely
**Severity**: Medium
- **Problem**: Complex expressions with multiple `|` characters render incorrectly
- **Example**: `TEXT: (mu p : ran hd; q : ran hd | p /= q | p.2 > q.2)`
- **Workaround**: Use proper Z notation blocks (axdef, schema) instead of TEXT
- **Root Cause**: Inline math detection treats pipes as expression boundaries

#### 3. Compound identifiers with operator suffixes
**Severity**: Medium
- **Problem**: Cannot use identifiers like `R+`, `R*`
- **Example**: `R+ == {a, b : N | b > a}` (Solution 31)
- **Workaround**: None - blocks Solution 31
- **Root Cause**: Lexer tokenizes as identifier + operator

### Unimplemented Features

**For the 52 Solutions**: All features needed are now implemented ✅

**Note**: Schema decoration (S', ΔS, ΞS) and schema composition operators are NOT needed for any of the 52 solutions. All supplementary solutions (48-52) use only currently implemented features.

---

## Bug Tracking

**See**: [GitHub Issues](https://github.com/jmf-pobox/txt2tex/issues) for complete bug tracking

**Test Cases**: All bugs have minimal reproducible test cases in `tests/bugs/`

### Active Bugs (4 confirmed)

| Priority | Issue | Component | Test Case | Blocks |
|----------|-------|-----------|-----------|--------|
| HIGH | [#1](https://github.com/jmf-pobox/txt2tex/issues/1): Parser fails on prose with periods | parser | [bug1_prose_period.txt](tests/bugs/bug1_prose_period.txt) | Homework, natural writing |
| MEDIUM | [#2](https://github.com/jmf-pobox/txt2tex/issues/2): Multiple pipes in TEXT blocks | latex-gen | [bug2_multiple_pipes.txt](tests/bugs/bug2_multiple_pipes.txt) | Solution 40(g) |
| MEDIUM | [#4](https://github.com/jmf-pobox/txt2tex/issues/4): Comma after parenthesized math not detected | latex-gen | [bug4_comma_after_parens.txt](tests/bugs/bug4_comma_after_parens.txt) | Homework prose |
| MEDIUM-HIGH | [#5](https://github.com/jmf-pobox/txt2tex/issues/5): Logical operators (or, and) not converted | latex-gen | [bug5_or_operator.txt](tests/bugs/bug5_or_operator.txt) | Homework 1(c) |

### Recently Resolved (3 fixed)

| Issue | Status | Fixed In |
|-------|--------|----------|
| [#3](https://github.com/jmf-pobox/txt2tex/issues/3): Compound identifiers with operators (R+, R*, R~) | ✅ RESOLVED | Phase 31 (Bug #3 fix) |
| Nested quantifiers in mu expressions | ✅ RESOLVED | Phase 19 |
| emptyset keyword not converted | ✅ RESOLVED | Recent update |

### Bug Reporting

Found a new bug? Follow the workflow:
1. Create minimal test case in `tests/bugs/bugN_name.txt`
2. Verify with `hatch run convert tests/bugs/bugN_name.txt`
3. Create [GitHub issue](https://github.com/jmf-pobox/txt2tex/issues/new?template=bug_report.md)
4. Reference test case in issue description

See [tests/bugs/README.md](../tests/bugs/README.md) for details.

---

## Roadmap to 100%

### Completed Milestones
1. ✓ Phase 0-2: Propositional Logic (Solutions 1-4)
2. ✓ Phase 3-8: Quantifiers & Sets (Solutions 5-24)
3. ✓ Phase 9: Generic Parameters (Solutions 25-26)
4. ✓ Phase 10: Relations (Solutions 27-32)
5. ✓ Phase 11: Functions (Solutions 33-36)
6. ✓ Phase 12: Sequences (Solutions 37-39)
7. ✓ Phase 13: Advanced Features (Range, Override, Indexing)
8. ✓ Phase 14: ASCII Sequence Brackets & Pattern Matching
9. ✓ Phase 15: Underscore in Identifiers
10. ✓ Phase 16: Conditional Expressions
11. ✓ Phase 17: Semicolon-Separated Bindings
12. ✓ Phase 18: Digit-Starting Identifiers (Solutions 40-41)
13. ✓ Phase 19: Space-Separated Application (Solutions 44-47)
14. ✓ Phase 20: Semicolon-Separated Declarations
15. ✓ Phase 21: Schema Separator and subseteq
16. ✓ Phase 22: False Blocker Removal (Solutions 39, 48-52)
17. ✓ Phase 24: Whitespace-Sensitive ^ Operator (concat vs exponent disambiguation)
18. ✓ Phase 25: Justification Operator Conversion (relation/function operators in justifications)
19. ✓ Phase 26: TEXT Block Operator Support (all operators in prose)

**Current:** 98.1% (51/52) - Phase 26 Complete

### Next Steps

**100% (52/52) Achievement**: ✅ Completed in Phase 31
- Fixed Bug #3: Compound identifiers with operator suffixes (R+, R*, R~)
- Completed Solution 31
- All 52 homework solutions now fully working

---

## Test Coverage

- **Total Tests:** 1107 passing (as of Phase 35, November 2025)

**Component Coverage:**
- parser.py: 86.17%
- latex_gen.py: 82.65%
- lexer.py: 92.10%
- Overall: 86.98%

**Test Organization:**
- Tests reorganized by glossary lectures (01-09)
- Test suite documentation: [tests/README.md](../tests/README.md)
- Bug test cases: [tests/bugs/](../tests/bugs/)

**Recent Test Additions:**
- Phase 12: 55 tests (sequences, bags, tuple projection)
- Phase 13: 26 tests (anonymous schemas, ranges, override, indexing)
- Phase 14: 21 tests (ASCII sequence brackets, pattern matching)
- Phase 15: 6 tests updated (underscore in identifiers)
- Phase 16: 19 tests (conditional expressions)
- Phase 17: 9 tests (semicolon-separated bindings)
- Phase 18: 14 tests (digit-starting identifiers)
- Phase 19: 10 tests (space-separated application)
- Phase 20: 20 tests (semicolon-separated declarations in gendef/axdef/schema)
- Phase 21: Covered by existing tests (schema separator and subseteq fixes)
- Phase 24: 27 tests (whitespace-sensitive ^ operator disambiguation)
- Phase 25: 10 tests (relation/function operator conversion in justifications)
- Phase 26: 23 tests (operator conversion in TEXT blocks)

---

## Verification Notes

All 51 "Fully Working" solutions have been verified with:
1. Successful parsing (no parser errors)
2. Correct LaTeX generation (matches Z notation standards)
3. PDF compilation (using fuzz package)
4. Manual inspection of output

All 52 solutions have been implemented and verified. Bug #3 (compound identifiers) was resolved in Phase 31.

---

## References

- [README.md](../README.md) - Project overview, setup, and usage
- [USER_GUIDE.md](USER_GUIDE.md) - User-facing syntax guide
- [DESIGN.md](DESIGN.md) - Architecture and design decisions
- [QA_PLAN.md](QA_PLAN.md) - Quality assurance process
- [tests/bugs/README.md](../tests/bugs/README.md) - Bug reports and test cases

