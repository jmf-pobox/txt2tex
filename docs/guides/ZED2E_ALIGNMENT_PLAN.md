# txt2tex Alignment Plan: Toward Z Notation Standards (via fuzz)

## CRITICAL CONTEXT

**Primary Goal**: Implement fuzz features more completely to generate standards-compliant Z notation LaTeX.

**Package Architecture**:
- **fuzz** is the DEFAULT and ONLY supported package for validation
- fuzz.sty provides Z notation typesetting AND typechecking/validation
- The project uses fuzz.sty + zed-maths.sty + zed-proof.sty
- Optional `--zed` flag swaps fuzz.sty for zed-cm.sty (no validation)

**What "zed2e standards" means**:
- zed2e is a DOCUMENT: "The Z Notation: Reference Manual, Second Edition" by Mike Spivey
- It specifies how Z notation should be written (syntax, conventions, commands)
- Both fuzz.sty and zed-*.sty packages implement these standards
- Commands like `\also`, `\t1`, `\t2` are defined in fuzz.sty and work correctly

**This plan implements fuzz features, NOT a migration away from fuzz.**

**Indentation Strategy**:
- Use `\t1`, `\t2`, `\t3`, etc. for depth-based indentation in predicates
- `\t#` = horizontal skip of # × 2em (defined in fuzz.sty, zed-cm.sty, zed-lbr.sty)
- Use `\also` for vertical spacing between predicate groups (blank line separator)
- Depth tracking: increment when entering quantifier body, use for line breaks

---

## Design Principles

### Principle 1: **Whiteboard Fidelity with LaTeX Transparency**
*"Make the simple things invisible, the complex things explicit."*

**Philosophy**: Users write natural whiteboard notation, but the generated LaTeX should be recognizable and teachable. A student who learns txt2tex should be 70%+ prepared to write LaTeX with fuzz directly.

**Application**:
- ✅ **Automatic smart defaults**: Add `\quad` for indentation when users break lines
- ✅ **Automatic line breaks**: Convert newlines to `\\` in appropriate contexts
- ✅ **Automatic spacing**: Insert `~` in set comprehensions, function application
- ❌ **Don't hide LaTeX structure**: Keep environment boundaries clear (`schema...end`, not implicit)
- ❌ **Don't invent new operators**: Use Z notation conventions or ASCII approximations

**Examples**:
```
# User writes (clean, whiteboard-style):
axdef
  policy : P1 RESOURCE -> RESOURCE
where
  forall S : P1 RESOURCE |
    policy(S) in S and
    S subset RESOURCE
end

# We generate (readable, standard LaTeX):
\begin{axdef}
  policy : \power_1 RESOURCE \fun RESOURCE
\where
  \forall S : \power_1 RESOURCE @ \\
  \quad policy(S) \in S \land \\
  \quad S \subseteq RESOURCE
\end{axdef}
```

The LaTeX structure is transparent - someone reading our generated LaTeX learns the `\forall`, `\land`, `\power_1` conventions immediately.

---

### Principle 2: **Align Notation with Z Standards**
*"When whiteboard notation matches formal notation, prefer formal notation."*

**Philosophy**: Where Z notation has established conventions (like `\land`, `\lor`, `\forall`), our ASCII input should mirror these closely. This reduces cognitive load when students transition to reading research papers or formal specifications.

**Application**:
- ✅ **Use standard Z keywords**: `land`, `lor`, `lnot` (not `and`, `or`, `not`)
- ✅ **Use standard Z symbols where ASCII-friendly**: `forall`, `exists`, `cross`, `subset`
- ✅ **Preserve Z operator precedence**: Match zed2e exactly
- ✅ **Use Z terminology**: "maplet" not "pair", "dom" not "domain"
- ⚠️ **ASCII approximations only where necessary**: `|->` for `\mapsto`, `<->` for `\rel`

**Rationale**:
- Students learning `land` and `lor` are learning the actual Z notation names
- Reading `\land` in LaTeX or papers becomes immediate recognition
- Reduces "translation barrier" between whiteboard and formal specs

**Migration Impact**:
- **Breaking change**: `and` → `land`, `or` → `lor`, `not` → `lnot`
- **Estimated files affected**: ~150 test files, ~50 example files, USER_GUIDE.md
- **Migration strategy**: Automated script + phased rollout with deprecation warnings

---

### Principle 3: **Progressive Disclosure of Complexity**
*"Simple cases should be simple; complex cases should be explicit."*

**Philosophy**: Common patterns get smart defaults. Advanced users can override with explicit LaTeX hints. Never force complexity on beginners, never hide power from experts.

**Application**:
- ✅ **Level 1 (Beginner)**: Write `and`, `or`, let system handle spacing and breaks
- ✅ **Level 2 (Intermediate)**: Use blank lines for `\also` grouping in where clauses
- ✅ **Level 3 (Expert)**: Use `LATEX:` blocks for direct control
- ✅ **Level 4 (Expert+)**: Mix txt2tex with hand-written LaTeX

**Examples**:

**Level 1 - Simple (auto-formatting)**:
```
schema State
  count : N
where
  count >= 0
end
```
System automatically adds `\\` and `\t1` based on newlines.

**Level 2 - Explicit structure (user controls grouping)**:
```
schema State
  count : N
  total : N
where
  count >= 0

  total = sum(items)
end
```
Blank line → generates `\also` between predicate groups.

**Level 3 - Inline LaTeX control (direct formatting commands)**:
```
axdef
  policy : P1 RESOURCE -> RESOURCE
where
  forall S : P1 RESOURCE | \\
  \t1 policy(S) in S land \\
  \t1 S subset RESOURCE
end
```
User explicitly writes `\\` for line breaks and `\t1` for indentation. The `~` spacing hint is also available:
```
{~ x : N | x > 0 ~}
```

**Level 4 - LATEX blocks (full LaTeX escape hatch)**:
```
LATEX: \begin{schema}{State}
LATEX:   count : \nat \\
LATEX:   total : \nat
LATEX: \where
LATEX:   count \geq 0
LATEX: \also
LATEX:   total = \mathit{sum}(\mathit{items})
LATEX: \end{schema}
```

**Level 5 - Mixed mode (expert users)**:
```
schema State
  count : N
where
  count >= 0
end

LATEX: \bigskip

axdef
  total : N
where
  total = count * 2
end
```

---

## Strategic Alignment Goals

### Goal 1: **Make txt2tex the "Training Wheels" for Z Notation**
**Target**: A student proficient in txt2tex can read 80% of Z notation papers and write 60% of fuzz LaTeX without additional training.

**Success Metrics**:
- Student can identify `\forall`, `\exists`, `\land`, `\lor` immediately
- Student understands `\where` separates declarations from predicates
- Student knows `\also` adds spacing between predicate groups
- Student recognizes `\t1`, `\t2` as indentation hints

---

### Goal 2: **Generate "Textbook Quality" LaTeX**
**Target**: Generated LaTeX should be indistinguishable from examples in Spivey's "The Z Notation" or Woodcock & Davies' "Using Z".

**Success Metrics**:
- Proper use of `\also` for predicate spacing
- Appropriate `\t` indentation in nested predicates
- Correct `~` spacing in set comprehensions
- Line breaks at logical boundaries (after `\land`, `\implies`)

---

### Goal 3: **Preserve Accessibility**
**Target**: Keep the "whiteboard feel" - users shouldn't feel like they're writing code.

**Success Metrics**:
- Input syntax remains visually clean
- No backslashes or braces required in input
- Schema/axdef blocks feel like natural outlines
- Proof trees use indentation, not explicit formatting

---

## Complete zed2e Reserved Words and Keywords

### LaTeX Commands and Environments

From zed2e.pdf analysis, here are ALL reserved words, commands, and environments we must handle:

#### Environments (must support all)

| Environment | Status | Priority | Notes |
|------------|--------|----------|-------|
| `schema` | ✅ Implemented | - | Named schema boxes |
| `axdef` | ✅ Implemented | - | Axiomatic definitions |
| `gendef` | ✅ Implemented | - | Generic definitions |
| `zed` | ✅ Implemented | - | Unboxed paragraphs |
| `schema*` | ❌ Missing | ⭐⭐ Medium | Anonymous schema boxes |
| `syntax` | ✅ Implemented | - | Large free type definitions with alignment (Phase 28, Nov 2025) |
| `argue` | ❌ Missing | ⭐⭐ Medium | Multi-line equational reasoning |
| `infrule` | ❌ Missing | ⭐ Low | Inference rules (proof trees alternative) |

#### Special Commands (must support all)

| Command | Status | Priority | Notes |
|---------|--------|----------|-------|
| `\where` | ✅ Implemented | - | Separator in schema/axdef |
| `\also` | ✅ Implemented | - | Vertical spacing between predicates (Phase 1, Nov 2025) |
| `\t1`, `\t2`, ... `\tn` | ✅ Implemented | - | Indentation hints (Phase 1, Nov 2025) |
| `~` | ✅ Implemented | - | Spacing hint (thin space) - in set comprehensions, function application, given types |
| `\\` | ✅ Implemented | - | Line breaks (automatic, Phase 1, Nov 2025) |
| `\derive` | ❌ Missing | ⭐ Low | Horizontal line in inference rules |
| `\shows` | ❌ Missing | ⭐ Low | Turnstile in inference rules |

#### Z Language Keywords (zed2e LaTeX commands)

**Logic operators:**
- `\lnot`, `\land`, `\lor`, `\implies`, `\iff` ✅ Implemented
- `\forall`, `\exists`, `\exists_1` ✅ Implemented

**Set operators:**
- `\power`, `\power_1`, `\finset`, `\finset_1` ✅ Implemented
- `\in`, `\notin`, `\subseteq`, `\subset` ✅ Implemented
- `\cup`, `\cap`, `\setminus`, `\bigcup`, `\bigcap` ✅ Implemented
- `\empty` ✅ Implemented

**Relation operators:**
- `\rel`, `\mapsto` ✅ Implemented
- `\dom`, `\ran`, `\id` ✅ Implemented
- `\dres`, `\rres`, `\ndres`, `\nrres` ✅ Implemented
- `\comp`, `\semi`, `\circ` ✅ Implemented (note: `\semi` for schemas, `\comp` for relations)
- `\inv`, `\plus`, `\star` ✅ Implemented
- `\limg`, `\rimg` ✅ Implemented (relational image)

**Function operators:**
- `\pfun`, `\fun` ✅ Implemented
- `\pinj`, `\inj` ✅ Implemented
- `\psurj`, `\surj`, `\bij` ✅ Implemented
- `\ffun`, `\finj` ✅ Implemented
- `\oplus` ✅ Implemented (override)

**Sequence operators:**
- `\seq`, `\seq_1`, `\iseq` ✅ Implemented
- `\langle`, `\rangle` ✅ Implemented
- `\cat`, `\dcat`, `\filter` ✅ Implemented

**Schema calculus operators:**
- `\hide` ❌ Missing (schema hiding)
- `\project` ❌ Missing (schema projection)
- `\pre` ❌ Missing (precondition)
- `\semi` ❌ Missing (schema composition - different from `\comp`)

**Other Z notation:**
- `\cross`, `\spot` (or `@`), `\mid` (or `|`) ✅ Implemented
- `\theta`, `\lambda`, `\mu`, `\Delta`, `\Xi` ✅ Implemented
- `\defs` ✅ Implemented
- `\nat`, `\num`, `\nat_1` ✅ Implemented
- `\#`, `\upto`, `\uplus` ✅ Implemented
- `\ldata`, `\rdata` ✅ Implemented (free type constructors)
- `\lbag`, `\rbag` ✅ Implemented (bag brackets)
- `\bsup`, `\esup` ❌ Missing (iteration notation, e.g., R^n)
- `\inbag`, `\partition`, `\disjoint` ⚠️ Check status

#### Style Parameters (configurable)

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `\zedindent` | `\leftmargini` | Indentation for math text |
| `\zedleftsep` | `1em` | Space between vertical line and math |
| `\zedtab` | `2em` | Unit of indentation for `\t` |
| `\zedbar` | `6em` | Length of horizontal bar in schema |
| `\zedskip` | `\medskip` | Vertical space for `\also` |

### Critical Missing Features

#### 1. `syntax` Environment (HIGH PRIORITY)

**Purpose**: Large free type definitions with alignment (like `eqnarray`)

**zed2e Example**:
```latex
\begin{syntax}
OP & ::= & plus | minus | times | divide
\also
EXP & ::= & const \ldata \nat \rdata \\
& | & binop \ldata OP \cross EXP \cross EXP \rdata
\end{syntax}
```

**Renders as**:
```
OP  ::=  plus | minus | times | divide

EXP ::=  const⟨N⟩
     |   binop⟨OP × EXP × EXP⟩
```

**Why we need it**:
- Free types in `zed` blocks don't align nicely for complex definitions
- The `&` separators create columns (like `eqnarray`)
- Industry standard for BNF-style syntax definitions
- Appears in Spivey's "The Z Notation" textbook

**txt2tex syntax** (proposed):
```
syntax
  OP ::= plus | minus | times | divide

  EXP ::= const<N>
       |  binop<OP cross EXP cross EXP>
end
```

**Implementation**: Phase 3, estimated 6-8 hours

---

#### 2. `schema*` Environment (MEDIUM PRIORITY)

**Purpose**: Anonymous schema boxes (no name at top)

**zed2e Example**:
```latex
\begin{schema*}
x, y: \nat
\where
x > y
\end{schema*}
```

**Why we need it**:
- Show result of schema expression expansion
- Inline schema definitions without polluting namespace

**txt2tex syntax** (proposed):
```
schema
  x, y : N
where
  x > y
end
```
(Already supported as "anonymous schema")

**Status**: ✅ Already implemented (we support anonymous schemas)

---

#### 3. `argue` Environment (MEDIUM PRIORITY)

**Purpose**: Multi-line equational reasoning with justifications

**zed2e Example**:
```latex
\begin{argue}
S \dres (T \dres R) \\
\t1 = \id S \comp \id T \comp R \\
\t1 = \id (S \cap T) \comp R & law about $\id$ \\
\t1 = (S \cap T) \dres R.
\end{argue}
```

**Why we need it**:
- Alternative to `EQUIV:` blocks
- Better for long left-hand sides
- Optional justifications in second column (with `&`)

**txt2tex equivalent**: Our `EQUIV:` blocks already handle this use case

**Decision**: ⚠️ Low priority - our `EQUIV:` syntax is simpler and covers the same use case

---

#### 4. `infrule` Environment (LOW PRIORITY)

**Purpose**: Inference rules for natural deduction

**zed2e Example**:
```latex
\begin{infrule}
\Gamma \shows P
\derive[x \notin freevars(\Gamma)]
\Gamma \shows \forall x @ P
\end{infrule}
```

**Why we might skip it**:
- Our `PROOF:` trees use different formatting
- Inference rules are less common than proof trees
- zed-specific display style (not standard in textbooks)

**Decision**: ⚠️ Low priority - our proof tree syntax is better for pedagogical use

---

## Alignment Plan: Phased Migration

### Phase 1: **Non-Breaking Improvements** (Week 1-2)
*Add features without changing syntax*

#### 1.1 Automatic Line Breaking and Indentation
**Implementation**: Detect newlines in `where` clauses; generate `\\` and `\t1`/`\t2`

**Before**:
```latex
\where
\forall S : \power_1 RESOURCE \bullet policy(S) \in S \land S \subseteq RESOURCE
```

**After**:
```latex
\where
\forall S : \power_1 RESOURCE @ \\
\t1 policy(S) \in S \land \\
\t1 S \subseteq RESOURCE
```

**Files to modify**:
- `src/txt2tex/latex_generator.py` - Add line break detection
- `tests/test_axdef.py` - Update expected LaTeX output

**Backward compatibility**: ✅ Fully compatible - enhances output, doesn't break input

---

#### 1.2 Add `\also` Support
**Implementation**: Detect blank lines between predicates in `where` clause

**Input**:
```
schema State
  count : N
  total : N
where
  count >= 0

  total = count * 2
end
```

**Generated**:
```latex
\begin{schema}{State}
  count : \nat \\
  total : \nat
\where
  count \geq 0
\also
  total = count \times 2
\end{schema}
```

**Files to modify**:
- `src/txt2tex/parser.py` - Detect blank line tokens
- `src/txt2tex/latex_generator.py` - Generate `\also`

**Backward compatibility**: ✅ Fully compatible - only affects output

---

#### 1.3 Add `~` Spacing Hints
**Implementation**: Insert `~` in set comprehensions, schema brackets, function application

**Generated**:
```latex
$\{~ x : \nat \mid x > 0 \bullet x^{2} ~\}$
[~ NAME, DATE ~]
f~x
```

**Files to modify**:
- `src/txt2tex/latex_generator.py` - Add spacing in specific contexts

**Backward compatibility**: ✅ Fully compatible - refinement only

---

#### 1.4 Consolidate `zed` Environments
**Implementation**: Group consecutive `zed` blocks with `\also`

**Before**:
```latex
\begin{zed}
  [NAME, DATE]
\end{zed}

\begin{zed}
  REPORT ::= ok | unknown
\end{zed}
```

**After**:
```latex
\begin{zed}
  [NAME, DATE]
\also
  REPORT ::= ok | unknown
\end{zed}
```

**Files to modify**:
- `src/txt2tex/latex_generator.py` - Track consecutive zed blocks

**Backward compatibility**: ✅ Fully compatible - cosmetic improvement

---

### Phase 2: **Breaking Changes - Keyword Alignment** (Week 3-4)
*Align keywords with Z notation standards*

#### 2.1 Migrate Logic Operators
**Changes**:
- `and` → `land` (logical and)
- `or` → `lor` (logical or)
- `not` → `lnot` (logical not)

**Rationale**:
- Matches LaTeX commands exactly (`\land`, `\lor`, `\lnot`)
- Students learn Z notation keywords directly
- Reduces "translation layer" when reading papers
- Common in formal methods pedagogy

**Migration Strategy**:

**Step 1: Deprecation warnings** (Week 3)
```python
# In lexer.py
if token.value == "and":
    warnings.warn(
        "Keyword 'and' is deprecated; use 'land' instead. "
        "Will be removed in v2.0.",
        DeprecationWarning
    )
```

**Step 2: Accept both syntaxes** (Week 3)
```python
# Support both during transition
LOGICAL_AND = ["and", "land"]
LOGICAL_OR = ["or", "lor"]
LOGICAL_NOT = ["not", "lnot"]
```

**Step 3: Migration script** (Week 3)
```bash
#!/bin/bash
# migrate_keywords.sh
find . -name "*.txt" -type f -exec sed -i '' \
  -e 's/\band\b/land/g' \
  -e 's/\bor\b/lor/g' \
  -e 's/\bnot\b/lnot/g' \
  {} +
```

**Step 4: Migrate all files** (Week 3-4)
- Run migration script on `tests/`, `examples/`
- Manual review for edge cases (e.g., prose in TEXT: blocks)
- Update USER_GUIDE.md, tutorials, DESIGN.md

**Step 5: Remove deprecated keywords** (Week 4)
```python
# Only accept new syntax
LOGICAL_AND = "land"
LOGICAL_OR = "lor"
LOGICAL_NOT = "lnot"
```

**Files affected** (estimated):
- ~150 test files in `tests/`
- ~50 example files in `examples/`
- `docs/guides/USER_GUIDE.md`
- All tutorial files in `docs/tutorials/`
- `docs/DESIGN.md`
- `CLAUDE.md`

**Testing strategy**:
```bash
# Before migration - establish baseline
hatch run test-cov > baseline_results.txt

# After migration - ensure equivalence
hatch run test-cov > migrated_results.txt
diff baseline_results.txt migrated_results.txt
# Should show: 0 test failures, same coverage
```

---

#### 2.2 Special Cases: TEXT Blocks
**Problem**: `and`, `or`, `not` are English words used in prose

**Solution**: Keep smart detection in TEXT: blocks
```
TEXT: The system checks policies and resources.
→ "The system checks policies and resources." (English prose - no change)

TEXT: The predicate x > 0 and y > 0 holds.
→ "The predicate $x > 0 \land y > 0$ holds." (Math context - converted)
```

**Implementation**: Context-aware keyword detection
```python
def is_math_context(position: int, text: str) -> bool:
    """Check if 'and'/'or'/'not' appears in mathematical formula context."""
    # Look for nearby math operators: =, <, >, in, subset, etc.
    window = text[max(0, position-20):min(len(text), position+20)]
    return any(op in window for op in ["=", "<", ">", "in", "subset", "forall", "exists"])
```

---

### Phase 3: **Advanced Alignment** (Week 5-6)
*Optional enhancements for completeness*

#### 3.1 Schema Calculus Operators
**New operators**:
- `\hide` - Schema hiding: `S hide (x, y)`
- `\project` - Schema projection: `S project (x, y)`
- `\pre` - Precondition: `pre S`
- Schema composition (`;`) - Keep RESERVED for declarations

**Priority**: ⭐⭐ Medium (only if users request advanced schema operations)

---

#### 3.2 Smart Line Breaking
**Implementation**: Automatically break long predicates at logical boundaries

**Input**:
```
where
  forall x : N | x > 0 land x < 100 land even(x) implies prime(x + 1)
```

**Generated** (if line > 80 chars):
```latex
\where
\forall x : \nat @ \\
\t1 x > 0 \land \\
\t1 x < 100 \land \\
\t1 even(x) \implies \\
\t2 prime(x + 1)
```

**Priority**: ⭐⭐⭐ High (improves readability significantly)

---

#### 3.3 Configurable Formatting Options
**Implementation**: CLI flags and config file

```bash
# Command line
txt2tex --format-style=zed2e examples/file.txt
txt2tex --format-style=compact examples/file.txt
txt2tex --format-style=spivey examples/file.txt

# Config file: .txt2tex.toml
[formatting]
style = "zed2e"           # zed2e | compact | spivey | custom
generate_also = true      # Add \also between predicates
generate_tabs = true      # Add \t indentation hints
generate_spacing = true   # Add ~ spacing hints
consolidate_zed = true    # Merge consecutive zed blocks
max_line_length = 80      # Smart line breaking threshold
```

**Priority**: ⭐⭐⭐⭐ Very High (flexibility for different use cases)

---

## Migration Roadmap

### Week 1: Phase 1.1-1.2 (Non-Breaking) ✅ COMPLETE
- [x] Implement automatic line breaking with `\\` (commit 2b1c8f2, ece9f9a)
- [x] Implement automatic indentation with `\t1`, `\t2` (commit 2b1c8f2)
- [x] Add `\also` support for blank lines in `where` clauses (commit ece9f9a)
- [x] Update tests to expect enhanced output
- [x] Run full test suite - ensure 100% pass rate (1199 tests passing)

**Deliverable**: Enhanced LaTeX output, no input syntax changes ✅

---

### Week 2: Phase 1.3-1.4 (Non-Breaking) ✅ COMPLETE
- [x] Implement `~` spacing hints (implemented in latex_gen.py lines 1185-1220, 1311-1339, 3282-3284)
  - Set comprehensions: `{~ x : N | x > 0 ~}`
  - Function application: `\seq~N`, `\power~X`
  - Given types: `[~ X, Y ~]`
- [x] Consolidate consecutive `zed` environments (commit a240d6f)
- [x] Add regression tests for formatting features (13 tests in test_inline_math.py, 5 tests in test_iseq_cross_parentheses.py)
- [x] Update USER_GUIDE.md with output examples

**Deliverable**: "Textbook quality" LaTeX generation ✅ COMPLETE

---

### Week 3-4: Phase 2 - Keyword Migration ⚠️ ATTEMPTED, FAILED, WILL RETRY
**Goal**: Migrate `and`→`land`, `or`→`lor`, `not`→`lnot` to align with Z notation LaTeX commands

**What didn't work:**
- **Approach**: Regex-based detection to distinguish English vs mathematical context
- **Failure mode**: Cannot reliably identify when "and"/"or"/"not" are English prose vs logical operators
  - Example failure: "The system checks policies and resources" (English prose)
  - Example failure: "The predicate x > 0 and y > 0 holds" (mathematical operator in prose)
- **Root cause**: Regex pattern matching insufficient for semantic context analysis

**Next attempt strategy:**
- Use LLM-based context analysis to distinguish English from mathematical usage
- Process TEXT blocks with semantic understanding of mathematical expressions
- Maintain high accuracy to avoid breaking English prose

**Status**: Will retry with improved approach

**Related work completed** (commit 709390b):
- Successfully implemented keyword conversion for quantifiers in TEXT blocks (forall, exists, emptyset)
- This proves TEXT block processing is feasible

---

### Week 5-6: Phase 3 - Advanced Features (Part 1) ⏭️ SKIPPED
**Goal**: Inline LaTeX passthrough (`\\`, `\t1`-`\t9`, `~` in user input)

**Decision (Nov 25, 2025)**: Skipped due to complexity vs. value analysis

**Rationale**:
- **Auto-generation works well**: Phase 1 already provides automatic `\\`, `\t1`-`\t9`, and `~` spacing
- **LATEX: blocks provide escape hatch**: Users needing manual control can use `LATEX:` directive
- **Risk too high**: Lexer conflicts with `\` (SETMINUS) and `~` (postfix inverse) create maintenance burden
- **Use cases covered**: Beginners get auto-formatting, experts get `LATEX:` blocks

**Alternative approach**: Users can write:
```
LATEX: forall S : P1 RESOURCE @ \\
LATEX: \t3 policy(S) in S \land \\
LATEX: \t3 S \subseteq RESOURCE
```

This provides full manual control without lexer complexity.

**Deliverable**: N/A - Phase skipped

---

### Week 7-8: Phase 3 - Advanced Features (Part 2) ✅ COMPLETE
- [x] Implement `syntax` environment (commits d02166f, 0269c1a, 83bec4d, 586758a)
  - Lexer: Add `SYNTAX` token
  - Parser: Add `syntax...end` block with blank line grouping
  - AST: Add `SyntaxBlock` and `SyntaxDefinition` node types
  - LaTeX gen: Generate `\begin{syntax}...\end{syntax}` with `&` column alignment
- [x] Add tests for `syntax` environment (all 1199 tests passing)
- [x] Add `syntax` examples to `examples/06_definitions/syntax_demo.txt`
- [x] Update USER_GUIDE.md with `syntax` documentation

**Deliverable**: Full support for aligned free type definitions ✅ (Phase 28, November 2025)

---

### Week 9-10: Phase 3 - Advanced Features (Part 3)
- [ ] Implement smart line breaking
- [ ] Add formatting configuration options (.txt2tex.toml)
- [ ] Create example config files for different styles
- [ ] Consider schema calculus operators (`\hide`, `\project`, `\pre`) if requested
- [ ] Add `\bsup`/`\esup` iteration notation
- [ ] Tag release: `v2.0.0` (stable)

**Deliverable**: Production-ready Z notation alignment

---

## Success Criteria

### Technical Metrics
- ✅ **100% test pass rate** after each phase
- ✅ **Zero fuzz validation errors** on migrated examples
- ✅ **Coverage maintained** at current levels (>90%)
- ✅ **Generated LaTeX matches zed2e style** (manual inspection)

### Pedagogical Metrics
- ✅ **USER_GUIDE.md teaches Z notation** (uses `\land`, `\lor` terminology)
- ✅ **Generated LaTeX is teachable** (students can read and understand)
- ✅ **Smooth transition to fuzz/zed2e** (70%+ of knowledge transfers)

### User Experience Metrics
- ✅ **Input remains clean** (no backslashes, minimal syntax)
- ✅ **Clear error messages** (deprecation warnings are helpful)
- ✅ **Migration is automated** (script handles 95%+ of changes)

---

## Risk Mitigation

### Risk 1: Breaking Changes Disrupt Users
**Mitigation**:
- Phased rollout with deprecation warnings
- Accept both syntaxes during transition period
- Automated migration script
- Clear communication in release notes

### Risk 2: TEXT: Block Detection Fails
**Mitigation**:
- Conservative detection (prefer English over math)
- Manual escape hatch: `TEXT: The expression and is...` (force English)
- Extensive testing on real prose examples

### Risk 3: Generated LaTeX Breaks Existing Workflows
**Mitigation**:
- Formatting enhancements are optional (config flags)
- Default to conservative formatting
- Extensive regression testing
- Keep Phase 1 output backward-compatible

---

## Appendix A: Keyword Comparison

| Concept | Current txt2tex | Proposed txt2tex | zed2e LaTeX | Rationale |
|---------|----------------|------------------|-------------|-----------|
| Conjunction | `and` | `land` | `\land` | Direct correspondence |
| Disjunction | `or` | `lor` | `\lor` | Direct correspondence |
| Negation | `not` | `lnot` | `\lnot` | Direct correspondence |
| Implication | `=>` | `=>` | `\implies` | ASCII approximation (no change needed) |
| Equivalence | `<=>` | `<=>` | `\iff` | ASCII approximation (no change needed) |
| Universal | `forall` | `forall` | `\forall` | Already aligned ✅ |
| Existential | `exists` | `exists` | `\exists` | Already aligned ✅ |
| Membership | `in` | `in` | `\in` | Already aligned ✅ |
| Subset | `subset` | `subset` | `\subseteq` | Already aligned ✅ |
| Cartesian | `cross` | `cross` | `\cross` | Already aligned ✅ |

**Key insight**: Only 3 keywords need migration (`and`, `or`, `not`), but these are high-frequency and high-impact for pedagogical alignment.

---

## Appendix B: LaTeX Output Examples

### Before Alignment
```latex
\begin{axdef}
  policy : \power_1 RESOURCE \fun RESOURCE
\where
  \forall S : \power_1 RESOURCE \bullet policy(S) \in S \land S \subseteq RESOURCE
\end{axdef}
```

**Issues**:
- No line breaks (hard to read)
- No indentation hints
- Long predicate on single line

### After Alignment (Phase 1)
```latex
\begin{axdef}
  policy : \power_1 RESOURCE \fun RESOURCE
\where
  \forall S : \power_1 RESOURCE @ \\
  \t1 policy(S) \in S \land \\
  \t1 S \subseteq RESOURCE
\end{axdef}
```

**Improvements**:
- ✅ Line breaks at logical boundaries
- ✅ Indentation hints (`\t1`)
- ✅ Readable, matches zed2e style

### After Alignment (Phase 2 - Keywords)
```latex
\begin{axdef}
  policy : \power_1 RESOURCE \fun RESOURCE
\where
  \forall S : \power_1 RESOURCE @ \\
  \t1 policy(S) \in S \land \\
  \t1 S \subseteq RESOURCE
\end{axdef}
```

**Note**: LaTeX output unchanged - but now users write `land` in input (matching `\land` directly).

---

## Appendix C: Stakeholder Perspectives

### Perspective 1: **Mike Spivey** (Author of Z Notation, fuzz)
**Would approve of**:
- Using standard Z notation keywords (`\land`, `\lor`, `\forall`)
- Generating proper `\also`, `\t` formatting
- Preserving mathematical precision

**Would question**:
- Automatic line breaking (might prefer explicit control)
- Hiding LaTeX structure too much

**Our balance**: Automatic smart defaults, with `LATEX:` escape hatch for experts.

---

### Perspective 2: **Formal Methods Instructor**
**Would approve of**:
- Students learning real Z notation keywords
- Generated LaTeX being teachable
- Smooth transition to reading papers

**Would question**:
- Breaking changes mid-semester
- Learning curve for new syntax

**Our balance**: Provide migration script, maintain backward compatibility during transition.

---

### Perspective 3: **Undergraduate Student**
**Would approve of**:
- Clean, whiteboard-like input syntax
- Not having to learn LaTeX backslashes
- Clear error messages

**Would question**:
- Why `land` instead of `and`?
- Having to relearn syntax

**Our balance**: Document rationale in USER_GUIDE.md ("These keywords match the formal notation you'll see in papers"), provide clear examples.

---

## Conclusion

This alignment plan balances **fidelity to Z notation standards** with **accessibility for beginners**. By adopting Z notation keywords (`land`, `lor`, `lnot`) and generating zed2e-style LaTeX (with `\also`, `\t`, `~`), we create a system that:

1. **Teaches Z notation** - Students learn the real keywords, not a custom syntax
2. **Generates textbook-quality LaTeX** - Output matches published examples
3. **Preserves whiteboard simplicity** - Input remains clean and approachable
4. **Enables smooth transitions** - 70%+ of knowledge transfers to fuzz/zed2e

**Recommendation**: Proceed with phased migration, starting with non-breaking Phase 1 improvements. Gather feedback, then execute Phase 2 keyword migration with automated script and clear communication.

**Timeline**: 10 weeks to full alignment, with incremental value delivered every 2 weeks.

**Risk**: Low - changes are well-scoped, automated, and tested at each step.

**Reward**: High - txt2tex becomes the standard pedagogical tool for Z notation.

---

## Summary of Key Changes from Original Plan

### 1. Progressive Disclosure Levels (Now 5 Levels)

**Original**: 3 levels (Beginner, Intermediate, Advanced)

**Revised**: 5 levels with better progression:
- **Level 1**: Beginner - auto-formatting
- **Level 2**: Intermediate - structural control (blank lines → `\also`)
- **Level 3**: **NEW** - Inline LaTeX commands (`\\`, `\t3`, `~`)
- **Level 4**: Expert - `LATEX:` blocks
- **Level 5**: Expert+ - Mixed mode

**Rationale**: Level 3 fills the gap between "let the system handle it" and "write raw LaTeX". Users can insert `\\` for line breaks and `\t3` for indentation without escaping to full LaTeX blocks.

---

### 2. Complete zed2e Reserved Word Coverage

**Added comprehensive tables for**:
- All 8 environments (schema, axdef, gendef, zed, schema*, syntax, argue, infrule)
- All special commands (`\where`, `\also`, `\t1`, `~`, `\\`, `\derive`, `\shows`)
- All Z language keywords (100+ LaTeX commands)
- All style parameters (`\zedindent`, `\zedtab`, etc.)

**Status tracking**:
- ✅ Implemented (green check)
- ❌ Missing (red X)
- ⚠️ Partial (warning)

**Priority ratings**: ⭐ (Low) to ⭐⭐⭐⭐⭐ (Critical)

---

### 3. `syntax` Environment (HIGH PRIORITY)

**Why added**:
- Explicitly requested by user
- Appears in zed2e.pdf as standard environment
- Essential for complex free type definitions
- Used in Spivey's "The Z Notation" textbook

**Implementation**: Weeks 7-8 (Phase 3, Part 2)

**Estimated effort**: 6-8 hours

**Example**:
```
syntax
  OP ::= plus | minus | times | divide

  EXP ::= const<N>
       |  binop<OP cross EXP cross EXP>
end
```

---

### 4. Inline LaTeX Passthrough (Level 3)

**Why added**:
- User requested ability to write `\\` and `\t3` directly
- Bridges gap between auto-formatting and raw LaTeX
- Maintains LaTeX transparency (Principle 1)

**Implementation**: Weeks 5-6 (Phase 3, Part 1)

**Example**:
```
axdef
  policy : P1 RESOURCE -> RESOURCE
where
  forall S : P1 RESOURCE | \\
  \t1 policy(S) in S land \\
  \t1 S subset RESOURCE
end
```

Users write LaTeX commands directly, system passes them through.

---

### 5. Extended Timeline

**Original**: 6 weeks

**Revised**: 10 weeks

**Breakdown**:
- Weeks 1-2: Phase 1 (non-breaking auto-formatting)
- Weeks 3-4: Phase 2 (keyword migration)
- Weeks 5-6: Phase 3 Part 1 (inline LaTeX)
- Weeks 7-8: Phase 3 Part 2 (`syntax` environment)
- Weeks 9-10: Phase 3 Part 3 (advanced features, config)

**Rationale**: Adding Level 3 and `syntax` environment requires additional implementation time, but delivers significantly more value for advanced users.

---

## Next Steps

1. **Review and approve** this plan
2. **Prioritize** which features to implement first
3. **Begin Phase 1** with non-breaking auto-formatting improvements
4. **Run baseline tests** before any changes
5. **Incremental commits** throughout (micro-commit workflow)

**Question for user**: Should we proceed with Phase 1 (auto `\also`, `\t`, `~`) or start with Phase 3 Part 1 (inline LaTeX passthrough)?
