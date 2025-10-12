# Phase 10 Implementation Plan

## Overview

Phase 10 (Relations) is broken into **4 sub-phases** to make this large implementation manageable:

- **Phase 10a**: Critical subset (2-3 hours) - Option B from discussion
- **Phase 10b**: Extended operators (2-3 hours)
- **Phase 10c**: Advanced features (2-3 hours)
- **Phase 10d**: Integration & testing (1-2 hours)

**Total estimated time**: 8-10 hours

---

## Phase 10a: Critical Subset (Option B)

**Priority**: ⚡ CRITICAL for homework
**Estimated time**: 2-3 hours
**Status**: Ready to implement

### What We're Building

The minimal set of relation operators needed for upcoming homework:

**Operators**:
- `<->` - Relation type (X <-> Y)
- `|->` - Maplet constructor (x |-> y)
- `<|` - Domain restriction (S <| R)
- `|>` - Range restriction (R |> T)
- `comp` - Relational composition (R comp S)
- `;` - Relational composition alternative (R ; S)

**Functions**:
- `dom` - Domain of relation (dom R)
- `ran` - Range of relation (ran R)

### Implementation Tasks

#### Lexer (`src/txt2tex/lexer.py`)

1. Add multi-character operator scanning in `_scan_operator()`:
   ```python
   # Check in this order to avoid conflicts
   if '<' and '-' and '>': return RELATION  # <->
   if '|' and '-' and '>': return MAPLET   # |->
   if '<' and '|': return DRES              # <|
   if '|' and '>': return RRES              # |>
   ```

2. Add keywords in `_scan_identifier()`:
   ```python
   'dom': TokenType.DOM,
   'ran': TokenType.RAN,
   'comp': TokenType.COMP,
   ```

#### Parser (`src/txt2tex/parser.py`)

1. Add new precedence level between set operations and comparisons:
   ```python
   def _parse_relation(self) -> Node:
       """Parse relation operators (precedence level 8)."""
       left = self._parse_comparison()

       while current_token in {RELATION, MAPLET, DRES, RRES, COMP, SEMICOLON}:
           op = current_token
           advance()
           right = self._parse_comparison()
           left = BinaryOp(left, op, right)

       return left
   ```

2. Modify `_parse_set_operation()` to call `_parse_relation()` instead of `_parse_comparison()`

3. Handle `dom`/`ran` as prefix operators in `_parse_unary()`:
   ```python
   if current_token in {DOM, RAN}:
       op = current_token
       advance()
       return UnaryOp(op, _parse_postfix())
   ```

#### Generator (`src/txt2tex/latex_generator.py`)

Add LaTeX mappings:
```python
'<->': r'\rel',
'|->': r'\mapsto',
'<|': r'\dres',
'|>': r'\rres',
'comp': r'\comp',
';': r'\comp',
'dom': r'\dom',
'ran': r'\ran',
```

#### Tests (`tests/test_phase10_relations.py`)

Create new test file with:
- Lexer tests for 6 operators + 2 functions
- Parser tests for precedence
- Generator tests for LaTeX output
- Basic integration test

#### Example (`examples/phase10.txt`)

Create basic examples:
```
=== Phase 10a: Critical Relations ===

TEXT: Basic relation type and maplet:

X <-> Y
x |-> y

TEXT: Domain and range:

S <| R
R |> T

TEXT: Composition:

R ; S
R comp S

TEXT: Functions:

dom R
ran R
```

### Completion Criteria

- [ ] Lexer scans all 8 tokens correctly
- [ ] Parser handles relation precedence (between sets and comparisons)
- [ ] LaTeX generation produces correct symbols
- [ ] 10+ tests passing
- [ ] Example compiles to PDF
- [ ] Type checking passes
- [ ] Ready to commit

---

## Phase 10b: Extended Operators

**Priority**: Important
**Estimated time**: 2-3 hours
**Dependencies**: Phase 10a complete

### What We're Building

Extended relation operators:

**Operators**:
- `<<|` - Domain subtraction (S <<| R)
- `|>>` - Range subtraction (R |>> T)
- `o9` - Forward composition (R o9 S)
- `~` - Inverse postfix (R~)
- `+` - Transitive closure postfix (R+)
- `*` - Reflexive-transitive closure postfix (R*)

**Functions**:
- `inv` - Inverse prefix (inv R)
- `id` - Identity relation (id X)

### Implementation Tasks

#### Lexer

1. Add 3-character operators (must check before 2-character):
   - `<<|` (check before `<|`)
   - `|>>` (check before `|>`)
   - `o9` (new pattern)

2. Add keywords: `inv`, `id`

#### Parser

1. Handle postfix operators in `_parse_postfix()`:
   - `~`, `+`, `*` (reuse existing TILDE, PLUS, STAR tokens)
   - Set `postfix=True` flag in UnaryOp node

2. Handle prefix operators in `_parse_unary()`:
   - `inv`, `id`

#### Generator

Add mappings:
```python
'<<|': r'\ndres',
'|>>': r'\nrres',
'o9': r'\circ',
'inv': r'^{\sim}',
'id': r'\id',
```

Handle postfix in `_generate_unary_op()`:
```python
if postfix:
    if op == '~': return f"{operand}^{{\\sim}}"
    if op == '+': return f"{operand}^{{+}}"
    if op == '*': return f"{operand}^{{*}}"
```

#### Tests

Add:
- Postfix operator tests
- 3-character operator scanning tests
- Precedence tests (postfix binds tighter than infix)

### Completion Criteria

- [ ] All 8 additional operators work
- [ ] Postfix operators have correct precedence
- [ ] 20+ total tests passing
- [ ] Example updated with extended operators
- [ ] Ready to commit

---

## Phase 10c: Advanced Features

**Priority**: Nice-to-have
**Estimated time**: 2-3 hours
**Dependencies**: Phase 10b complete

### What We're Building

Relational image syntax: `R (| S |)`

This is the most complex feature, requiring:
- Special bracket tokens `(|` and `|)`
- Application-like syntax handling
- Potential new AST node

### Implementation Tasks

#### Lexer

Add 2-character bracket operators:
```python
if '(' and '|': return LIMG  # (|
if '|' and ')': return RIMG  # |)
```

Must check `(|` before `(` and `|)` before `|`

#### Parser

Handle in `_parse_postfix()`:
```python
if current_token == LIMG:
    advance()  # consume (|
    arg = _parse_expression()
    expect(RIMG)  # expect |)
    node = Application(node, [arg])  # or RelationalImage(node, arg)
```

**Design decision**: Use existing `Application` node or create new `RelationalImage` node?
- **Recommendation**: Use `Application` for simplicity

#### Generator

Generate LaTeX:
```python
# For relational image
f"{relation}(\\lvert {argument} \\rvert)"
```

#### Tests

Add:
- Lexer tests for `(|` and `|)` tokens
- Parser tests for relational image syntax
- Complex expression tests: `R (| dom S |)`

### Completion Criteria

- [ ] Relational image syntax works
- [ ] Complex expressions parse correctly
- [ ] 30+ total tests passing
- [ ] Full example file with all operators
- [ ] Ready to commit

---

## Phase 10d: Integration & Testing

**Priority**: Essential
**Estimated time**: 1-2 hours
**Dependencies**: Phase 10a/b/c complete

### What We're Doing

Final integration, testing against real homework problems, and quality assurance.

### Tasks

1. **Integration tests**:
   - Test against solutions 27-32 from `solutions_complete.txt`
   - Verify PDF compilation
   - Visual comparison with reference PDF

2. **Quality gates**:
   ```bash
   hatch run type:check   # Type checking
   hatch run lint:check   # Linting
   hatch run test:pytest  # All tests
   ```

3. **Example compilation**:
   ```bash
   hatch run cli examples/phase10.txt > examples/phase10.tex
   TEXINPUTS=../../tex//: pdflatex examples/phase10.tex
   ```

4. **Documentation**:
   - Update DESIGN.md Phase 10 status to ✅
   - Add notes about any edge cases discovered
   - Document known limitations (if any)

5. **Git commit**:
   ```bash
   git add .
   git commit -m "Implement Phase 10: Relations

   Add support for relational operators and relation calculus:
   - 11 relation operators (binary and postfix)
   - 4 relation functions (prefix operators)
   - Relational image syntax
   - Comprehensive test coverage (30+ tests)
   - Examples demonstrating all features

   Critical for upcoming homework (Solutions 27-32).

   Generated with Claude Code
   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

### Completion Criteria

- [ ] All quality gates pass
- [ ] Examples compile to PDF
- [ ] Real homework problems convert correctly
- [ ] DESIGN.md updated
- [ ] Git commit created
- [ ] **Phase 10 complete!**

---

## Risk Mitigation

### High-Risk Areas

1. **Operator precedence bugs**: Relations between sets and comparisons
   - **Mitigation**: Extensive precedence tests in Phase 10a

2. **Multi-character scanning conflicts**: `<` vs `<|` vs `<<|`
   - **Mitigation**: Systematic lexer tests, longest-match-first

3. **Postfix ambiguity**: `+`/`*` for arithmetic vs closures
   - **Mitigation**: `postfix=True` flag, context-aware generation

### Monitoring

After each phase, verify:
- ✅ Type checking still passes
- ✅ All existing tests still pass
- ✅ No regressions in previous phases

---

## Next Steps

**Ready to start Phase 10a?**

The implementation is well-defined and the tasks are clear. Phase 10a should take 2-3 hours and will give us the critical subset needed for homework.

Shall I proceed with implementing Phase 10a?
