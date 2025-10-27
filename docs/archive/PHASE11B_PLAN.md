# Phase 11b: Function Application

## Overview

Implement function application syntax for Z notation, enabling expressions like `f(x)`, `g(x, y)`, and generic instantiation like `seq N`.

## Motivation

Function application is fundamental to Z notation specifications:
- Apply functions to arguments: `f(x)`, `square(n)`
- Generic type instantiation: `seq N`, `P X`, `bag Item`
- Relational image: `R(S)` (applying relation to set)
- Enable Solutions 5, 28-29, 35-36 and many others

## Syntax

### Input Format (txt2tex)
```
f(x)                    # Single argument
g(x, y, z)              # Multiple arguments
seq N                   # Generic instantiation (space-separated)
f(g(h(x)))              # Nested application
parent(john)            # Predicate application
height(m)               # Function application in expressions
```

### LaTeX Output
```latex
f(x)                    # Standard: f(x)
g(x, y, z)              # Multi-arg: g(x, y, z)
\seq N                  # Generic: \seq~N (or other LaTeX command)
f(g(h(x)))              # Nested: f(g(h(x)))
parent(john)            # Predicate: parent(john)
height(m)               # In expr: height(m)
```

## Design Decisions

### 1. Parsing Strategy
- **Function application is identified by**: `IDENTIFIER LPAREN`
- **Precedence level**: Very high (similar to subscript/superscript)
- **Associativity**: Left-to-right (for chaining: `f(x)(y)`)
- **Argument parsing**: Comma-separated expression list

### 2. Generic Instantiation
Two possible approaches:
- **Approach A**: Treat `seq N` as special syntax (requires keyword list)
- **Approach B**: Treat as implicit application (more general but ambiguous)

**Decision**: Start with explicit parentheses only: `seq(N)`
- Simpler parsing (no ambiguity with variable references)
- Can add space-separated syntax later if needed
- Consistent with function application pattern

### 3. Distinguishing from Grouping Parentheses
```
(x + y)         # Grouping: LPAREN starts expression
f(x + y)        # Application: IDENTIFIER immediately before LPAREN
```

Key: Check if LPAREN follows an identifier in primary expression parsing.

### 4. Multiple Arguments
```
f(x, y, z)      # Parse as: FunctionApp(f, [x, y, z])
```
Arguments are comma-separated expressions.

## Implementation Steps

### Step 1: Add AST Node (parser.py)
```python
@dataclass
class FunctionApp:
    """Function application: f(x) or f(x, y, z)"""
    name: str              # Function name
    args: list[Expr]       # Argument list
```

### Step 2: Update Parser (parser.py)
Modify `_parse_primary()` to handle function application:
```python
def _parse_primary(self) -> Expr:
    # ... existing code for numbers, identifiers, etc.

    # Check for identifier (could be function application)
    if self._current_token().type == TokenType.IDENTIFIER:
        name = self._current_token().value
        self._advance()

        # Check for function application: identifier(...)
        if self._current_token().type == TokenType.LPAREN:
            self._advance()  # consume '('
            args = self._parse_argument_list()
            self._expect(TokenType.RPAREN)
            return FunctionApp(name=name, args=args)

        # Just an identifier
        return Identifier(name)
```

Add helper for argument lists:
```python
def _parse_argument_list(self) -> list[Expr]:
    """Parse comma-separated argument list: x, y, z"""
    args = []

    # Empty argument list: f()
    if self._current_token().type == TokenType.RPAREN:
        return args

    # Parse first argument
    args.append(self._parse_expression())

    # Parse remaining arguments
    while self._current_token().type == TokenType.COMMA:
        self._advance()  # consume ','
        args.append(self._parse_expression())

    return args
```

### Step 3: Update LaTeX Generator (latex_gen.py)
```python
def _generate_expr(self, expr: Expr) -> str:
    # ... existing cases ...

    if isinstance(expr, FunctionApp):
        return self._generate_function_app(expr)

def _generate_function_app(self, app: FunctionApp) -> str:
    """Generate LaTeX for function application."""
    func_name = app.name

    # Check for special Z notation functions with LaTeX commands
    special_functions = {
        'seq': r'\seq',
        'iseq': r'\iseq',
        'bag': r'\bag',
        'id': r'\id',
        'dom': r'\dom',
        'ran': r'\ran',
        # Add more as needed
    }

    if func_name in special_functions:
        # Generic instantiation: \seq~N
        if len(app.args) == 1:
            arg_latex = self._generate_expr(app.args[0])
            return f"{special_functions[func_name]}~{arg_latex}"

    # Standard function application: f(x, y, z)
    args_latex = ', '.join(self._generate_expr(arg) for arg in app.args)
    return f"{func_name}({args_latex})"
```

### Step 4: Add Tests (test_phase11b.py)
Create comprehensive tests:
- Single argument: `f(x)`
- Multiple arguments: `g(x, y, z)`
- Nested application: `f(g(x))`
- Generic instantiation: `seq(N)`
- In expressions: `f(x) + g(y)`
- In quantifiers: `forall x : N | f(x) > 0`
- In proofs and equivalences
- Edge cases: `f()`, `f(x, y, z, w, v)`

### Step 5: Create Example (phase11b.txt)
Demonstrate all features in example file.

### Step 6: Quality Gates
- All tests pass (`hatch run test:pytest -xvs tests/test_phase11b.py`)
- Type checking passes (`hatch run type:check`)
- Linting passes (`hatch run lint:check`)
- Example compiles to PDF (`make phase11b` in examples/)
- No regressions (all existing tests still pass)

## Test Cases

### Basic Application
```
Input:  f(x)
Parse:  FunctionApp(name='f', args=[Identifier('x')])
LaTeX:  f(x)
```

### Multiple Arguments
```
Input:  g(x, y, z)
Parse:  FunctionApp(name='g', args=[Identifier('x'), Identifier('y'), Identifier('z')])
LaTeX:  g(x, y, z)
```

### Nested Application
```
Input:  f(g(h(x)))
Parse:  FunctionApp(name='f', args=[FunctionApp(name='g', args=[FunctionApp(name='h', args=[Identifier('x')])])])
LaTeX:  f(g(h(x)))
```

### Generic Instantiation
```
Input:  seq(N)
Parse:  FunctionApp(name='seq', args=[Identifier('N')])
LaTeX:  \seq~N
```

### In Expressions
```
Input:  f(x) + g(y)
Parse:  BinaryOp(left=FunctionApp(...), op=PLUS, right=FunctionApp(...))
LaTeX:  f(x) + g(y)
```

### In Quantifiers
```
Input:  forall x : N | f(x) > 0
Parse:  Quantifier(quant=FORALL, vars=[...], pred=BinaryOp(...))
LaTeX:  \forall x : N \bullet f(x) > 0
```

### In Set Membership
```
Input:  x in f(S)
Parse:  BinaryOp(left=Identifier('x'), op=IN, right=FunctionApp(...))
LaTeX:  x \in f(S)
```

## LaTeX Mappings

### Special Z Functions
```
seq(N)      → \seq~N
iseq(N)     → \iseq~N
bag(X)      → \bag~X
```

### Standard Functions
```
f(x)        → f(x)
g(x, y)     → g(x, y)
parent(p)   → parent(p)
height(m)   → height(m)
```

## Examples from Solutions

### Solution 5
```
Input:
exists d : Dog | gentle(d) and well_trained(d)

LaTeX:
\exists d : Dog \bullet gentle(d) \land well\_trained(d)
```

### Solution 28
```
Input:
dom(R) = {0, 1, 2}
ran(R) = {1, 2, 3}

LaTeX:
\dom R = \{0, 1, 2\}
\ran R = \{1, 2, 3\}
```

### Solution 35
```
Input:
children(p) = parentOf(| {p} |)
number_of_grandchildren(p) = # (parentOf comp parentOf)(| {p} |)

LaTeX:
children(p) = parentOf(\limg \{p\} \rimg)
number\_of\_grandchildren(p) = \# (parentOf \comp parentOf)(\limg \{p\} \rimg)
```

## Integration Points

### Phase Dependencies
- **Phase 0-2**: Expression parsing (foundation)
- **Phase 3**: Identifiers and basic expressions
- **Phase 11a**: Function types (conceptually related)

### Affects
- **Expression parsing**: New primary expression type
- **Precedence handling**: High precedence binding
- **Type checking**: (Future) argument type validation

## Edge Cases

1. **Empty arguments**: `f()` - valid in some contexts
2. **Whitespace**: `f (x)` vs `f(x)` - currently require no space
3. **Chaining**: `f(x)(y)` - application returning function
4. **With operators**: `f(x + y)` vs `f(x) + y` - precedence matters
5. **With quantifiers**: `forall x : N | f(x) > 0` - predicate vs application

## Known Limitations (Future Work)

1. **Space-separated generics**: `seq N` (without parentheses)
   - Would require distinguishing from two identifiers
   - More complex parsing and ambiguity resolution

2. **Function composition application**: `(f comp g)(x)`
   - Requires expressions as function names
   - More general than identifier-only application

3. **Curried application**: `f x y` (Haskell-style)
   - Not standard Z notation
   - Would conflict with existing syntax

## Success Criteria

- [ ] All test cases pass
- [ ] phase11b.txt compiles to PDF
- [ ] Can parse Solution 5 predicate applications
- [ ] Can parse Solution 28 dom/ran applications
- [ ] No regressions in existing tests
- [ ] Type checking passes
- [ ] Linting passes
- [ ] Documentation updated

## Next Steps After Phase 11b

Consider:
- **Phase 11c**: Lambda expressions
- **Phase 11d**: Function operations (override, iteration)
- **Arithmetic operators**: Would unlock more solutions
- **Set literals**: Essential for many solutions
