# Phase 10: Relations - Technical Design Document

## Overview

Phase 10 adds support for relational operators and relation calculus, a critical component of Z notation. This is the largest and most complex phase to date, introducing 11 operators and 4 functions with intricate precedence and parsing challenges.

**Priority**: ⚡ CRITICAL for upcoming homework
**Estimated effort**: 8-10 hours
**Test coverage**: Solutions 27-32

---

## 1. Token Definitions

### 1.1 New Token Types (Status: ✅ COMPLETED)

Already added to `src/txt2tex/tokens.py`:

```python
# Relation operators (Phase 10)
RELATION = auto()      # <-> (relation type)
MAPLET = auto()        # |-> (maplet constructor)
DRES = auto()          # <| (domain restriction)
RRES = auto()          # |> (range restriction)
NDRES = auto()         # <<| (domain subtraction)
NRRES = auto()         # |>> (range subtraction)
COMP = auto()          # comp or ; (relational composition)
SEMICOLON = auto()     # ; (relational composition)
CIRC = auto()          # o9 (forward/backward composition)
TILDE = auto()         # ~ (relational inverse postfix)
PLUS = auto()          # + (transitive closure postfix / arithmetic)
STAR = auto()          # * (reflexive-transitive closure postfix / arithmetic)
LIMG = auto()          # (| (relational image left)
RIMG = auto()          # |) (relational image right)

# Relation functions (Phase 10)
DOM = auto()           # dom (domain of relation)
RAN = auto()           # ran (range of relation)
INV = auto()           # inv (inverse of relation)
ID = auto()            # id (identity relation)
```

### 1.2 Design Rationale

**Separate tokens for `COMP` and `SEMICOLON`**: While both represent relational composition, they are syntactically distinct in the input. The lexer emits different tokens, but the parser treats them identically.

**Shared tokens for `PLUS` and `STAR`**: These already exist for arithmetic. Context determines whether they're arithmetic operators or relation postfix operators (transitive closures). The parser handles this disambiguation based on position.

**`TILDE` for inverse**: The `~` operator is a postfix operator for relational inverse. Similar to `+` and `*`, context determines usage.

---

## 2. Lexer Updates

### 2.1 Multi-Character Operator Scanning Strategy

**Critical challenge**: Several relation operators share prefixes, requiring careful longest-match-first scanning.

**Conflict groups**:
1. `<` family: `<<|` → `<|` → `<->` → `<=` → `<`
2. `|` family: `|>>` → `|->` → `|>` → `|)` → `|`
3. `(|` standalone (no conflicts)

**Scanning order** (must be checked in this order):

```python
# In _scan_operator() method:

# Three-character operators first
if self._peek() == '<' and self._peek(1) == '<' and self._peek(2) == '|':
    self._advance()
    self._advance()
    self._advance()
    return Token(TokenType.NDRES, '<<|', self.line, start_col)

if self._peek() == '|' and self._peek(1) == '>' and self._peek(2) == '>':
    self._advance()
    self._advance()
    self._advance()
    return Token(TokenType.NRRES, '|>>', self.line, start_col)

# Three-character operator for relation type
if self._peek() == '<' and self._peek(1) == '-' and self._peek(2) == '>':
    self._advance()
    self._advance()
    self._advance()
    return Token(TokenType.RELATION, '<->', self.line, start_col)

# Two-character operators
if self._peek() == '|' and self._peek(1) == '-' and self._peek(2) == '>':
    self._advance()
    self._advance()
    self._advance()
    return Token(TokenType.MAPLET, '|->', self.line, start_col)

if self._peek() == '<' and self._peek(1) == '|':
    self._advance()
    self._advance()
    return Token(TokenType.DRES, '<|', self.line, start_col)

if self._peek() == '|' and self._peek(1) == '>':
    self._advance()
    self._advance()
    return Token(TokenType.RRES, '|>', self.line, start_col)

if self._peek() == '(' and self._peek(1) == '|':
    self._advance()
    self._advance()
    return Token(TokenType.LIMG, '(|', self.line, start_col)

if self._peek() == '|' and self._peek(1) == ')':
    self._advance()
    self._advance()
    return Token(TokenType.RIMG, '|)', self.line, start_col)

if self._peek() == 'o' and self._peek(1) == '9':
    self._advance()
    self._advance()
    return Token(TokenType.CIRC, 'o9', self.line, start_col)

# Single-character operators (already exist, no changes needed)
# '<', '>', '|', '(', ')', '~', '+', '*', ';'
```

### 2.2 Keyword Scanning for Relation Functions

In `_scan_identifier()`, add keyword checks for relation functions:

```python
KEYWORDS = {
    # ... existing keywords ...
    'dom': TokenType.DOM,
    'ran': TokenType.RAN,
    'inv': TokenType.INV,
    'id': TokenType.ID,
    'comp': TokenType.COMP,
}
```

**Note**: `comp` is both a keyword and an operator. When scanning identifiers, if `comp` appears, emit `TokenType.COMP`.

### 2.3 Implementation Location

File: `src/txt2tex/lexer.py`

Method: `_scan_operator()` (lines ~180-250)

The existing code already scans multi-character operators in longest-first order (e.g., `===` before `==`). We follow the same pattern.

---

## 3. Parser Updates

### 3.1 Operator Precedence Table

Updated precedence hierarchy (lowest to highest):

| Level | Operators | Associativity | Phase |
|-------|-----------|---------------|-------|
| 1 | `<=>` (iff) | Left | 0 |
| 2 | `=>` (implies) | Right | 0 |
| 3 | `or` | Left | 0 |
| 4 | `and` | Left | 0 |
| 5 | `not` | Prefix | 0 |
| 6 | Quantifiers (`forall`, `exists`, `exists1`, `mu`) | Prefix | 3, 6 |
| 7 | Set operators (`union`, `intersect`) | Left | 3 |
| **8** | **Relations** (`<->`, `|->`, `<|`, `|>`, `<<|`, `|>>`, `comp`, `;`, `o9`) | **Left** | **10** |
| 9 | Comparisons (`=`, `!=`, `<`, `>`, `<=`, `>=`, `in`, `notin`, `subset`) | Non-assoc | 3, 7 |
| 10 | Arithmetic (`+`, `-`) | Left | (future) |
| 11 | Arithmetic (`*`, `/`) | Left | (future) |
| 12 | Postfix (`~`, `+`, `*` for relations) | Postfix | 10 |
| 13 | Exponentiation (`^`) | Right | 3 |
| 14 | Application (function/relation application, `(|` ... `|)`) | Left | 10 |

**Key observations**:
- Relation operators sit between set operators and comparisons
- Postfix operators (`~`, `+`, `*`) have higher precedence than infix
- Relational image `(|` ... `|)` has highest precedence (application level)

### 3.2 Parser Methods to Modify

#### 3.2.1 Add `_parse_relation()` method

Insert between `_parse_set_operation()` and `_parse_comparison()`:

```python
def _parse_relation(self) -> Node:
    """Parse relation operators: <->, |->, <|, |>, <<|, |>>, comp, ;, o9.

    Precedence level 8 (between set operations and comparisons).
    """
    left = self._parse_comparison()

    while self._current_token.type in {
        TokenType.RELATION,    # <->
        TokenType.MAPLET,      # |->
        TokenType.DRES,        # <|
        TokenType.RRES,        # |>
        TokenType.NDRES,       # <<|
        TokenType.NRRES,       # |>>
        TokenType.COMP,        # comp
        TokenType.SEMICOLON,   # ;
        TokenType.CIRC,        # o9
    }:
        op = self._current_token
        self._advance()
        right = self._parse_comparison()
        left = BinaryOp(left, op.value, right)

    return left
```

**Call site**: Modify `_parse_set_operation()` to call `_parse_relation()` instead of `_parse_comparison()`.

#### 3.2.2 Update `_parse_postfix()` for relation postfix operators

The method already handles postfix operators. Add relation-specific postfix tokens:

```python
def _parse_postfix(self) -> Node:
    """Parse postfix operators: ~ (inverse), + (trans closure), * (refl-trans closure)."""
    node = self._parse_primary()

    while self._current_token.type in {
        TokenType.TILDE,  # ~ for inverse
        TokenType.PLUS,   # + for transitive closure
        TokenType.STAR,   # * for reflexive-transitive closure
    }:
        op = self._current_token
        self._advance()
        node = UnaryOp(op.value, node, postfix=True)

    return node
```

**Note**: `PLUS` and `STAR` are already handled for arithmetic. The `postfix=True` flag distinguishes them from prefix operators.

#### 3.2.3 Update `_parse_unary()` for relation functions

Relation functions (`dom`, `ran`, `inv`, `id`) are prefix operators:

```python
def _parse_unary(self) -> Node:
    """Parse unary prefix operators: not, dom, ran, inv, id."""
    if self._current_token.type == TokenType.NOT:
        op = self._current_token
        self._advance()
        return UnaryOp(op.value, self._parse_unary())

    if self._current_token.type in {
        TokenType.DOM,
        TokenType.RAN,
        TokenType.INV,
        TokenType.ID,
    }:
        op = self._current_token
        self._advance()
        return UnaryOp(op.value, self._parse_postfix())

    return self._parse_postfix()
```

**Design decision**: `id` is typically used as `id S` (identity relation on set S), making it a prefix operator.

#### 3.2.4 Handle relational image `(|` ... `|)`

Relational image has the syntax: `R (| S |)` where `R` is a relation and `S` is a set.

This is similar to function application. Modify `_parse_primary()` or add special handling in `_parse_postfix()`:

```python
def _parse_postfix(self) -> Node:
    """Parse postfix operators including relational image."""
    node = self._parse_primary()

    while True:
        # Relational image: R (| S |)
        if self._current_token.type == TokenType.LIMG:
            self._advance()  # consume (|
            arg = self._parse_expression()
            if self._current_token.type != TokenType.RIMG:
                raise ParseError(f"Expected |) but got {self._current_token}")
            self._advance()  # consume |)
            node = RelationalImage(node, arg)

        # Other postfix operators
        elif self._current_token.type in {TokenType.TILDE, TokenType.PLUS, TokenType.STAR}:
            op = self._current_token
            self._advance()
            node = UnaryOp(op.value, node, postfix=True)

        else:
            break

    return node
```

**New AST node**: `RelationalImage(relation, argument)`

### 3.3 AST Node Updates

File: `src/txt2tex/ast_nodes.py`

Add new node type for relational image:

```python
@dataclass
class RelationalImage(Node):
    """Relational image: R (| S |)."""
    relation: Node
    argument: Node
```

**Alternative**: Reuse `Application(function, args)` node type, as relational image is semantically similar to function application. This avoids creating a new node type.

**Recommendation**: Use `Application` to keep AST simple. The LaTeX generator can distinguish based on context.

---

## 4. LaTeX Generation

### 4.1 Operator Mappings

File: `src/txt2tex/latex_generator.py`

In `_generate_binary_op()`, add mappings:

```python
OPERATOR_MAP = {
    # ... existing operators ...

    # Relation operators (Phase 10)
    '<->': r'\rel',
    '|->': r'\mapsto',
    '<|': r'\dres',
    '|>': r'\rres',
    '<<|': r'\ndres',
    '|>>': r'\nrres',
    'comp': r'\comp',
    ';': r'\comp',     # Semicolon is also composition
    'o9': r'\circ',
}
```

### 4.2 Postfix Operators

In `_generate_unary_op()`, handle postfix operators:

```python
def _generate_unary_op(self, node: UnaryOp) -> str:
    """Generate LaTeX for unary operators (prefix and postfix)."""
    operand = self._generate_node(node.operand)

    if node.postfix:
        # Postfix operators: ~, +, * (for relations)
        if node.op == '~':
            return f"{operand}^{{\\sim}}"
        elif node.op == '+':
            return f"{operand}^{{+}}"
        elif node.op == '*':
            return f"{operand}^{{*}}"
    else:
        # Prefix operators: not, dom, ran, inv, id
        if node.op == 'not':
            return f"\\lnot {operand}"
        elif node.op == 'dom':
            return f"\\dom {operand}"
        elif node.op == 'ran':
            return f"\\ran {operand}"
        elif node.op == 'inv':
            return f"{operand}^{{\\sim}}"  # Alternative to ~
        elif node.op == 'id':
            return f"\\id {operand}"

    # Fallback
    return f"{node.op} {operand}"
```

**Note**: Both `inv` and `~` map to `^{\sim}`. User can choose either syntax.

### 4.3 Relational Image

If using `Application` node for relational image, add special handling:

```python
def _generate_application(self, node: Application) -> str:
    """Generate LaTeX for function/relation application."""
    func = self._generate_node(node.function)

    # Check if this is relational image (heuristic: args wrapped in LIMG/RIMG)
    # For now, treat all application uniformly
    args = ', '.join(self._generate_node(arg) for arg in node.args)

    # Relational image uses (| ... |), regular application uses ( ... )
    # The parser already wrapped it correctly, so just generate
    return f"{func}(\\lvert {args} \\rvert)"
```

**Alternative**: If using dedicated `RelationalImage` node:

```python
def _generate_relational_image(self, node: RelationalImage) -> str:
    """Generate LaTeX for relational image: R (| S |)."""
    relation = self._generate_node(node.relation)
    argument = self._generate_node(node.argument)
    return f"{relation}(\\lvert {argument} \\rvert)"
```

---

## 5. Testing Strategy

### 5.1 Test Coverage Plan

File: `tests/test_phase10_relations.py`

**Test categories**:
1. **Lexer tests**: Verify correct tokenization of all operators
2. **Parser tests**: Verify correct precedence and associativity
3. **Generator tests**: Verify correct LaTeX output
4. **Integration tests**: Full txt-to-LaTeX conversion

### 5.2 Test Cases

#### 5.2.1 Lexer Tests

```python
def test_scan_relation_operators():
    """Test scanning of relation operators."""
    lexer = Lexer("x <-> y")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.IDENTIFIER
    assert tokens[1].type == TokenType.RELATION
    assert tokens[2].type == TokenType.IDENTIFIER

def test_scan_maplet():
    """Test scanning of maplet operator."""
    lexer = Lexer("x |-> y")
    tokens = lexer.tokenize()
    assert tokens[1].type == TokenType.MAPLET

def test_scan_domain_restriction():
    """Test scanning of domain restriction and subtraction."""
    lexer = Lexer("S <| R")
    tokens = lexer.tokenize()
    assert tokens[1].type == TokenType.DRES

    lexer = Lexer("S <<| R")
    tokens = lexer.tokenize()
    assert tokens[1].type == TokenType.NDRES

def test_scan_range_operators():
    """Test scanning of range operators."""
    lexer = Lexer("R |> T")
    tokens = lexer.tokenize()
    assert tokens[1].type == TokenType.RRES

    lexer = Lexer("R |>> T")
    tokens = lexer.tokenize()
    assert tokens[1].type == TokenType.NRRES

def test_scan_composition():
    """Test scanning of composition operators."""
    lexer = Lexer("R ; S")
    tokens = lexer.tokenize()
    assert tokens[1].type == TokenType.SEMICOLON

    lexer = Lexer("R comp S")
    tokens = lexer.tokenize()
    assert tokens[1].type == TokenType.COMP

def test_scan_inverse_and_closures():
    """Test scanning of postfix operators."""
    lexer = Lexer("R~ R+ R*")
    tokens = lexer.tokenize()
    assert tokens[1].type == TokenType.TILDE
    assert tokens[3].type == TokenType.PLUS
    assert tokens[5].type == TokenType.STAR

def test_scan_relational_image():
    """Test scanning of relational image brackets."""
    lexer = Lexer("R (| S |)")
    tokens = lexer.tokenize()
    assert tokens[1].type == TokenType.LIMG
    assert tokens[3].type == TokenType.RIMG

def test_scan_relation_functions():
    """Test scanning of relation function keywords."""
    lexer = Lexer("dom R ran S inv T id U")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.DOM
    assert tokens[2].type == TokenType.RAN
    assert tokens[4].type == TokenType.INV
    assert tokens[6].type == TokenType.ID
```

#### 5.2.2 Parser Tests

```python
def test_parse_relation_type():
    """Test parsing relation type operator."""
    parser = Parser(Lexer("X <-> Y").tokenize())
    ast = parser.parse()
    assert isinstance(ast, BinaryOp)
    assert ast.op == '<->'

def test_parse_maplet():
    """Test parsing maplet constructor."""
    parser = Parser(Lexer("x |-> y").tokenize())
    ast = parser.parse()
    assert isinstance(ast, BinaryOp)
    assert ast.op == '|->'

def test_parse_domain_restriction():
    """Test parsing domain restriction."""
    parser = Parser(Lexer("S <| R").tokenize())
    ast = parser.parse()
    assert isinstance(ast, BinaryOp)
    assert ast.op == '<|'

def test_parse_composition():
    """Test parsing relational composition."""
    parser = Parser(Lexer("R ; S").tokenize())
    ast = parser.parse()
    assert isinstance(ast, BinaryOp)
    assert ast.op == ';'

def test_parse_inverse_postfix():
    """Test parsing inverse as postfix operator."""
    parser = Parser(Lexer("R~").tokenize())
    ast = parser.parse()
    assert isinstance(ast, UnaryOp)
    assert ast.op == '~'
    assert ast.postfix == True

def test_parse_transitive_closure():
    """Test parsing transitive closure."""
    parser = Parser(Lexer("R+").tokenize())
    ast = parser.parse()
    assert isinstance(ast, UnaryOp)
    assert ast.op == '+'
    assert ast.postfix == True

def test_parse_relation_function():
    """Test parsing relation functions as prefix."""
    parser = Parser(Lexer("dom R").tokenize())
    ast = parser.parse()
    assert isinstance(ast, UnaryOp)
    assert ast.op == 'dom'

def test_parse_relational_image():
    """Test parsing relational image."""
    parser = Parser(Lexer("R (| S |)").tokenize())
    ast = parser.parse()
    # Assuming we use Application node
    assert isinstance(ast, Application)

def test_parse_precedence_relation_vs_comparison():
    """Test precedence: relations bind tighter than comparisons."""
    # forall x : S <| R | P(x)
    # Should parse as: forall x : (S <| R) | P(x)
    parser = Parser(Lexer("forall x : S <| R | x = x").tokenize())
    ast = parser.parse()
    # Verify structure
    assert isinstance(ast, Quantifier)

def test_parse_complex_expression():
    """Test complex expression with multiple relation operators."""
    # dom(R ; S~) <| T
    parser = Parser(Lexer("dom(R ; S~) <| T").tokenize())
    ast = parser.parse()
    # Verify correct parsing structure
```

#### 5.2.3 Generator Tests

```python
def test_generate_relation_operators():
    """Test LaTeX generation for relation operators."""
    cases = [
        ("X <-> Y", "X \\rel Y"),
        ("x |-> y", "x \\mapsto y"),
        ("S <| R", "S \\dres R"),
        ("R |> T", "R \\rres T"),
        ("S <<| R", "S \\ndres R"),
        ("R |>> T", "R \\nrres T"),
        ("R ; S", "R \\comp S"),
        ("R comp S", "R \\comp S"),
        ("R o9 S", "R \\circ S"),
    ]

    for input_txt, expected_latex in cases:
        parser = Parser(Lexer(input_txt).tokenize())
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate(ast)
        assert expected_latex in latex

def test_generate_postfix_operators():
    """Test LaTeX generation for postfix operators."""
    cases = [
        ("R~", "R^{\\sim}"),
        ("R+", "R^{+}"),
        ("R*", "R^{*}"),
    ]

    for input_txt, expected_latex in cases:
        parser = Parser(Lexer(input_txt).tokenize())
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate(ast)
        assert expected_latex in latex

def test_generate_relation_functions():
    """Test LaTeX generation for relation functions."""
    cases = [
        ("dom R", "\\dom R"),
        ("ran R", "\\ran R"),
        ("inv R", "R^{\\sim}"),  # or "\\inv R" depending on implementation
        ("id S", "\\id S"),
    ]

    for input_txt, expected_latex in cases:
        parser = Parser(Lexer(input_txt).tokenize())
        ast = parser.parse()
        generator = LaTeXGenerator()
        latex = generator.generate(ast)
        assert expected_latex in latex

def test_generate_relational_image():
    """Test LaTeX generation for relational image."""
    input_txt = "R (| S |)"
    expected = "R(\\lvert S \\rvert)"

    parser = Parser(Lexer(input_txt).tokenize())
    ast = parser.parse()
    generator = LaTeXGenerator()
    latex = generator.generate(ast)
    assert expected in latex
```

#### 5.2.4 Integration Tests

```python
def test_integration_solution_27():
    """Test full conversion of solution 27 (relations)."""
    # Read example file
    with open('examples/phase10.txt', 'r') as f:
        input_txt = f.read()

    # Convert to LaTeX
    converter = TxtToTex()
    latex = converter.convert(input_txt)

    # Verify key elements present
    assert '\\rel' in latex
    assert '\\mapsto' in latex
    assert '\\dres' in latex
    assert '\\comp' in latex
```

---

## 6. Example File

### 6.1 Create `examples/phase10.txt`

```
=== Phase 10: Relations ===

TEXT: This example demonstrates relational operators in Z notation.

TEXT: Basic relation type and maplet:

X <-> Y is the type of relations from X to Y
x |-> y constructs a maplet (ordered pair for relations)

TEXT: Domain and range operators:

S <| R restricts relation R to domain S (domain restriction)
R |> T restricts relation R to range T (range restriction)
S <<| R subtracts S from domain of R (domain subtraction)
R |>> T subtracts T from range of R (range subtraction)

TEXT: Relational composition:

R ; S composes relations R and S (apply R then S)
R comp S is alternative syntax for composition
R o9 S is forward composition (apply S then R)

TEXT: Inverse and closures:

R~ is the inverse of relation R
R+ is the transitive closure of R
R* is the reflexive-transitive closure of R

TEXT: Relational image:

R (| S |) is the relational image of set S under relation R

TEXT: Relation functions:

dom R returns the domain of relation R
ran R returns the range of relation R
inv R returns the inverse of relation R (same as R~)
id X returns the identity relation on set X

TEXT: Complex expression:

dom(R ; S~) <| T
```

### 6.2 Create `examples/phase10.tex` (expected output)

Run the converter after implementation to generate the expected LaTeX output.

---

## 7. Implementation Checklist

### Phase 10a: Critical Subset (Priority 1)
- [ ] Lexer: Scan `<->`, `|->`, `<|`, `|>`, `comp`, `;`
- [ ] Lexer: Scan `dom`, `ran` keywords
- [ ] Parser: Add `_parse_relation()` method
- [ ] Parser: Handle `dom`, `ran` as prefix operators
- [ ] Generator: Map 6 operators to LaTeX
- [ ] Tests: Basic lexer, parser, generator tests
- [ ] Example: Simple relation examples in `phase10.txt`

**Estimated time**: 2-3 hours

### Phase 10b: Extended Operators (Priority 2)
- [ ] Lexer: Scan `<<|`, `|>>`, `o9`
- [ ] Lexer: Scan `~`, `+`, `*` (reuse existing tokens)
- [ ] Parser: Handle postfix operators in `_parse_postfix()`
- [ ] Parser: Handle `inv`, `id` keywords
- [ ] Generator: Map extended operators to LaTeX
- [ ] Tests: Postfix operator tests, precedence tests
- [ ] Example: Extended examples in `phase10.txt`

**Estimated time**: 2-3 hours

### Phase 10c: Advanced Features (Priority 3)
- [ ] Lexer: Scan `(|`, `|)` for relational image
- [ ] Parser: Handle relational image syntax
- [ ] AST: Add `RelationalImage` node or reuse `Application`
- [ ] Generator: Generate relational image LaTeX
- [ ] Tests: Relational image tests, complex expressions
- [ ] Example: Advanced examples in `phase10.txt`

**Estimated time**: 2-3 hours

### Phase 10d: Integration and Testing (Final)
- [ ] Write comprehensive integration tests
- [ ] Test against solutions 27-32
- [ ] Run quality gates: `hatch run type:check`, `hatch run lint:check`
- [ ] Compile examples to PDF
- [ ] Update DESIGN.md Phase 10 status
- [ ] Git commit with detailed message

**Estimated time**: 1-2 hours

---

## 8. Risk Assessment

### 8.1 High-Risk Areas

1. **Operator precedence conflicts**: Relations sit between set operations and comparisons. Incorrect precedence will cause subtle parsing bugs.
   - **Mitigation**: Comprehensive precedence tests

2. **Multi-character operator scanning**: The longest-match-first approach is error-prone.
   - **Mitigation**: Systematic lexer tests for all operator combinations

3. **Postfix operator ambiguity**: `+` and `*` used for both arithmetic and relation closures.
   - **Mitigation**: Context-aware parsing, postfix flag in AST

4. **Relational image syntax**: The `(|` ... `|)` syntax conflicts with parentheses and pipe.
   - **Mitigation**: Careful lexer ordering, dedicated tokens

### 8.2 Medium-Risk Areas

1. **LaTeX package requirements**: Relation symbols require specific LaTeX packages (fuzz or zed-maths).
   - **Mitigation**: Verify LaTeX compilation with examples

2. **Test coverage**: Phase 10 introduces 15 new tokens and multiple precedence levels.
   - **Mitigation**: Systematic test plan covering all operators

### 8.3 Low-Risk Areas

1. **AST node reuse**: Most operators use existing `BinaryOp` and `UnaryOp` nodes.
2. **Token definitions**: Already completed with clear semantics.

---

## 9. Success Criteria

### 9.1 Functional Requirements

- ✅ All 11 relation operators tokenize correctly
- ✅ All 4 relation functions recognized
- ✅ Correct precedence and associativity
- ✅ LaTeX output matches expected symbols
- ✅ Complex expressions parse correctly

### 9.2 Quality Requirements

- ✅ Type checking passes: `hatch run type:check`
- ✅ Linting passes: `hatch run lint:check`
- ✅ All tests pass: `hatch run test:pytest`
- ✅ Example file compiles to PDF
- ✅ Test coverage > 95% for new code

### 9.3 Documentation Requirements

- ✅ DESIGN.md updated with Phase 10 completion status
- ✅ Example files demonstrate all operators
- ✅ Code comments explain precedence decisions

---

## 10. References

### 10.1 Z Notation Standards

- **Spivey, J. M.** (1992). *The Z Notation: A Reference Manual* (2nd ed.).
- **fuzz package documentation**: `/Users/jfreeman/Coding/fuzz/txt2tex/tex/fuzz.sty`

### 10.2 LaTeX Packages

- `fuzz.sty`: Provides `\rel`, `\mapsto`, `\dres`, `\rres`, `\ndres`, `\nrres`, `\comp`, `\dom`, `\ran`, `\id`, `\circ`
- `zed-maths.sty`: Alternative package with similar symbols

### 10.3 Test Materials

- Solutions 27-32 in `/Users/jfreeman/Coding/fuzz/txt2tex/solutions_complete.txt`
- Reference PDF: `/Users/jfreeman/Coding/fuzz/txt2tex/solutions.pdf`

---

**Document Version**: 1.0
**Last Updated**: 2025-10-12
**Author**: Claude Code (AI Assistant)
