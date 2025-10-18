# Phase 11 Implementation Plan

## Overview

Phase 11 (Functions) is broken into **4 sub-phases** to make this implementation manageable:

- **Phase 11a**: Function types (2-3 hours) - Critical for homework
- **Phase 11b**: Function application (1-2 hours) - Important
- **Phase 11c**: Lambda and override (2-3 hours) - Nice-to-have
- **Phase 11d**: Integration & testing (1-2 hours) - Essential

**Total estimated time**: 6-10 hours (minimal 2-3 hours for Phase 11a only)

---

## Phase 11a: Function Types (Critical)

**Priority**: ⚡ CRITICAL for homework generic functions
**Estimated time**: 2-3 hours
**Status**: Ready to implement

### What We're Building

Function type operators needed for generic function definitions in homework:

**Function Type Operators**:
- `->` - Total function (X -> Y)
- `+->` - Partial function (X +-> Y)
- `>->` - Total injection (X >-> Y)
- `>+>` - Partial injection (X >+> Y)
- `-->>` - Total surjection (X -->> Y)
- `+->>` - Partial surjection (X +->> Y)
- `>->>` - Bijection (X >->> Y)

### Implementation Tasks

#### Lexer (`src/txt2tex/lexer.py`)

1. Add multi-character operator scanning in order of length (longest-first):
   ```python
   # Check 4-character operators first
   if '>' and '-' and '>' and '>': return BIJECTION  # >->>
   if '+' and '-' and '>' and '>': return PSURJ      # +->>
   if '-' and '-' and '>' and '>': return TSURJ      # -->>

   # Then 3-character operators
   if '>' and '+' and '>': return PINJ               # >+>
   if '>' and '-' and '>': return TINJ               # >->
   if '+' and '-' and '>': return PFUN               # +->

   # Finally 2-character operators
   if '-' and '>': return TFUN                       # ->
   ```

   **CRITICAL**: Must check longer operators before shorter ones to avoid conflicts!

2. Update docstring to mention Phase 11 support

#### Parser (`src/txt2tex/parser.py`)

1. Add function type precedence level:
   - Function types should have **same precedence as relations** (level 6)
   - Both are type constructors in Z notation
   - Left-associative: `X -> Y -> Z` means `X -> (Y -> Z)`

2. Update `_parse_relation()` to include function types:
   ```python
   def _parse_relation(self) -> Expr:
       """Parse relation and function type operators (precedence 6)."""
       left = self._parse_set_op()

       while self._match(
           # Phase 10 relation operators
           TokenType.RELATION, TokenType.MAPLET, TokenType.DRES,
           TokenType.RRES, TokenType.NDRES, TokenType.NRRES,
           TokenType.CIRC, TokenType.COMP, TokenType.SEMICOLON,
           # Phase 11 function type operators
           TokenType.TFUN, TokenType.PFUN, TokenType.TINJ, TokenType.PINJ,
           TokenType.TSURJ, TokenType.PSURJ, TokenType.BIJECTION,
       ):
           op_token = self._advance()
           right = self._parse_set_op()
           left = BinaryOp(
               operator=op_token.value,
               left=left,
               right=right,
               line=op_token.line,
               column=op_token.column,
           )

       return left
   ```

3. Update parser grammar in docstring:
   ```
   relation   ::= set_op ( ('<->' | '|->' | '<|' | '|>' | '<<|' |
                            '|>>' | 'o9' | 'comp' | ';' |
                            '->' | '+->' | '>->' | '>+>' |
                            '-->>' | '+->>' | '>->>') set_op )*
   ```

#### Generator (`src/txt2tex/latex_gen.py`)

Add LaTeX mappings for function types:
```python
# Function type operators (Phase 11a)
'->': r'\fun',          # Total function
'+->': r'\pfun',        # Partial function
'>->': r'\inj',         # Total injection
'>+>': r'\pinj',        # Partial injection
'-->>': r'\surj',       # Total surjection
'+->>': r'\psurj',      # Partial surjection
'>->>': r'\bij',        # Bijection
```

Add to precedence dictionary:
```python
'->': 6,
'+->': 6,
'>->': 6,
'>+>': 6,
'-->>': 6,
'+->>': 6,
'>->>': 6,
```

Update docstring to mention Phase 11a.

#### Tokens (`src/txt2tex/tokens.py`)

Add new token types:
```python
# Phase 11a: Function types
TFUN = "TFUN"          # -> (total function)
PFUN = "PFUN"          # +-> (partial function)
TINJ = "TINJ"          # >-> (total injection)
PINJ = "PINJ"          # >+> (partial injection)
TSURJ = "TSURJ"        # -->> (total surjection)
PSURJ = "PSURJ"        # +->> (partial surjection)
BIJECTION = "BIJECTION"  # >->> (bijection)
```

#### Tests (`tests/test_phase11a.py`)

Create new test file with:

1. **Lexer tests** (7 tests):
   - Test each function type operator tokenizes correctly
   - Test longest-match-first: `>->>` before `>->` before `->`
   - Test in combination: `X -> Y -> Z`

2. **Parser tests** (7 tests):
   - Test each function type parses to BinaryOp
   - Test precedence with other operators
   - Test associativity (left-associative)
   - Test complex types: `X -> (Y +-> Z)`

3. **LaTeX generation tests** (7 tests):
   - Test each function type generates correct LaTeX
   - Test nested types: `(N -> N) -> N`
   - Test in context of declarations

4. **Integration tests** (5 tests):
   - End-to-end: text → tokens → AST → LaTeX
   - Complex example from homework
   - Multiple function types in one expression

**Total**: ~26 tests

#### Example (`examples/phase11a.txt`)

Create example file:
```
=== Phase 11a: Function Types ===

TEXT: Total functions:

f : X -> Y
g : N -> N

TEXT: Partial functions:

f : X +-> Y

TEXT: Injections:

f : X >-> Y
g : X >+> Y

TEXT: Surjections:

f : X -->> Y
g : X +->> Y

TEXT: Bijections:

f : X >->> Y

TEXT: Complex types:

f : (X -> Y) -> Z
g : X -> (Y +-> Z)
h : (N -> N) -> (N -> N)

TEXT: Generic function from homework:

axdef
  notin[X] : X <-> P X
where
  forall x : X; s : P X | x notin s <=> not (x in s)
end
```

### Completion Criteria

- [ ] Lexer scans all 7 function type operators correctly
- [ ] Longest-match-first prevents tokenization conflicts
- [ ] Parser handles function types at relation precedence level
- [ ] Left-associativity works correctly
- [ ] LaTeX generation produces correct Z notation macros
- [ ] 26+ tests passing
- [ ] Example compiles to PDF
- [ ] Type checking passes
- [ ] Linting passes
- [ ] Formatting passes
- [ ] Ready to commit

### Known Limitations

- Phase 11a does NOT include:
  - Function application syntax (`f x` or `f(x)`)
  - Lambda expressions (`lambda x : X . expr`)
  - Function override (`f oplus g`)
  - These are in Phase 11b and 11c

---

## Phase 11b: Function Application

**Priority**: Important (needed for Solutions 33-36)
**Estimated time**: 1-2 hours
**Dependencies**: Phase 11a complete

### What We're Building

Function application syntax:
- Juxtaposition: `f x` (function application by juxtaposition)
- Parenthesized: `f(x)` (explicit function application)
- Multiple arguments: `f x y` or `f(x, y)`

### Implementation Tasks

#### Parser

This is the complex part. Function application by juxtaposition is ambiguous:
- `f x` could be multiplication or function application
- Need context to disambiguate

**Design Decision**: Require parentheses for explicit application
- `f(x)` - function application
- `f x` - parsed as juxtaposition (multiplication) unless in specific context

**Alternative**: Parse as application in certain contexts (inside set comprehensions, after `:`)

#### Implementation Options

**Option A**: Only support parenthesized application
```python
def _parse_postfix(self) -> Expr:
    base = self._parse_atom()

    while True:
        if self._match(TokenType.LPAREN):
            # Function application
            self._advance()
            args = self._parse_argument_list()
            self._expect(TokenType.RPAREN)
            base = Application(function=base, arguments=args)
        elif self._match(TokenType.CARET, ...):
            # Existing postfix operators
            ...
        else:
            break

    return base
```

**Option B**: Context-aware juxtaposition
- More complex, defer to later if needed

**Recommendation**: Start with Option A (parenthesized only)

#### Tests

Add:
- Simple application: `f(x)`
- Multiple arguments: `f(x, y, z)`
- Nested application: `f(g(x))`
- Application of complex expressions: `(f comp g)(x)`

### Completion Criteria

- [ ] Parenthesized function application works
- [ ] Multiple arguments supported
- [ ] Nested applications parse correctly
- [ ] LaTeX generates correctly
- [ ] 10+ new tests passing
- [ ] Ready to commit

---

## Phase 11c: Lambda Expressions and Override

**Priority**: Nice-to-have
**Estimated time**: 2-3 hours
**Dependencies**: Phase 11b complete

### What We're Building

Advanced function features:
- Lambda expressions: `lambda x : X . expr`
- Function override: `f oplus {x |-> y}`

### Implementation Tasks

#### Lexer

Add keywords:
- `lambda` → LAMBDA token

Add operators:
- `oplus` → OPLUS token

#### Parser

1. Lambda expressions in `_parse_atom()`:
   ```python
   if self._match(TokenType.LAMBDA):
       self._advance()
       variables = self._parse_variable_list()
       self._expect(TokenType.COLON)
       domain = self._parse_expression()
       self._expect(TokenType.PERIOD)
       body = self._parse_expression()
       return Lambda(variables=variables, domain=domain, body=body)
   ```

2. Function override as binary operator (same precedence as relations):
   ```python
   # Add OPLUS to relation operators
   ```

#### Generator

Add LaTeX mappings:
```python
'lambda': r'\lambda',
'oplus': r'\oplus',
```

Handle Lambda node:
```python
def _generate_lambda(self, node: Lambda) -> str:
    vars_latex = ', '.join(node.variables)
    domain_latex = self._generate_expr(node.domain)
    body_latex = self._generate_expr(node.body)
    return f"\\lambda {vars_latex} : {domain_latex} \\bullet {body_latex}"
```

#### Tests

Add:
- Lambda expression tests
- Function override tests
- Complex combinations

### Completion Criteria

- [ ] Lambda expressions parse and generate correctly
- [ ] Function override works
- [ ] 10+ new tests passing
- [ ] Ready to commit

---

## Phase 11d: Integration & Testing

**Priority**: Essential
**Estimated time**: 1-2 hours
**Dependencies**: Phase 11a (minimum) or 11a/b/c complete

### What We're Doing

Final integration, testing against real homework problems, and quality assurance.

### Tasks

1. **Integration tests**:
   - Test against solutions 33-36 from instructor's materials
   - Verify generic function definitions work
   - Test complex function types in axdef blocks

2. **Quality gates**:
   ```bash
   hatch run type:check   # Type checking
   hatch run lint:check   # Linting
   hatch run format       # Auto-formatting
   hatch run test:pytest  # All tests pass
   ```

3. **Example compilation**:
   ```bash
   hatch run cli examples/phase11a.txt > examples/phase11a.tex
   env TEXINPUTS="../../tex//:" MFINPUTS="../../tex//:" pdflatex examples/phase11a.tex
   ```

4. **Documentation**:
   - Update README.md with Phase 11a status
   - Add "Function Types" section to user guide
   - Update version number (0.10.2 → 0.11.0)
   - Update test count
   - Update phases complete count

5. **Git commits**:
   ```bash
   # After Phase 11a
   git add .
   git commit -m "Implement Phase 11a: Function Types

   Add support for function type operators in Z notation:
   - 7 function type operators (-> +-> >-> >+> -->> +->> >->>)
   - Total, partial, injection, surjection, bijection
   - Correct precedence (same as relations, level 6)
   - Left-associative
   - Comprehensive test coverage (26+ tests)

   Critical for generic function definitions in homework.

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

### Completion Criteria

- [ ] All quality gates pass
- [ ] Examples compile to PDF
- [ ] Real homework problems convert correctly
- [ ] README.md updated with user guide section
- [ ] Git commit created
- [ ] **Phase 11a (minimum) complete!**

---

## Risk Mitigation

### High-Risk Areas

1. **Operator scanning conflicts**: `->` vs `+->` vs `>->` vs `>->>` vs `-->>` vs `+->>` vs `>+>`
   - **Mitigation**: Longest-match-first algorithm, systematic lexer tests
   - **Critical**: Must check 4-char before 3-char before 2-char!

2. **Parser precedence**: Functions at same level as relations
   - **Mitigation**: Extensive precedence tests
   - **Note**: Both are type constructors, so same level makes sense

3. **Ambiguity with existing operators**: `-` and `>` already exist
   - **Mitigation**: Multi-character scanning checks combinations first
   - **Test**: Ensure `X - > Y` (with spaces) still parses as subtraction

4. **Function application ambiguity** (Phase 11b): `f x` vs multiplication
   - **Mitigation**: Start with parenthesized-only approach
   - **Defer**: Complex juxtaposition rules can wait

### Monitoring

After each phase, verify:
- ✅ Type checking still passes
- ✅ All existing tests still pass (287 tests from Phase 10b)
- ✅ No regressions in previous phases
- ✅ Lexer scans previous constructs correctly

---

## Implementation Strategy

### Minimal Viable Phase 11 (For Homework)

**Just Phase 11a** is sufficient for the user's immediate homework needs:
- ✅ Generic function types in axdef blocks
- ✅ Function type declarations
- ✅ Type constructors in generic definitions

**Estimated time**: 2-3 hours

User can defer Phase 11b and 11c until they're actually needed.

### Full Phase 11 (For Complete Coverage)

**All phases** (11a + 11b + 11c + 11d):
- ✅ Function types
- ✅ Function application
- ✅ Lambda expressions
- ✅ Function override

**Estimated time**: 6-10 hours

---

## Next Steps

**Ready to start Phase 11a?**

The implementation is well-defined with:
- Clear operator precedence
- Systematic lexer scanning (longest-match-first)
- Integration with existing relation parsing
- Comprehensive test plan (26+ tests)

Phase 11a alone gives the user what they need for homework (generic function definitions).

Shall I proceed with implementing Phase 11a?
