# Known Bugs

## High Priority

### Parser: Cannot handle prose mixed with inline math (periods cause failures)

**Severity**: High (blocks direct expression usage)
**Component**: Parser / inline expression handling
**Discovered**: 2025-01-14

**Description**:
The parser cannot handle sentences that mix mathematical expressions with prose endings (particularly periods). When an expression is written directly (not in a TEXT block), any trailing period causes a parse error.

**Example that FAILS**:
```
1 in {4, 3, 2, 1} is true.
```

Error: `Line 369, column 26: Expected identifier, number, '(', '{', '⟨', or lambda, got PERIOD`

**Workaround** (must use TEXT):
```
TEXT: 1 in {4, 3, 2, 1} is true.
```

**Why This Matters**:
- TEXT blocks were HIDING parser limitations
- Many "working" solutions only work because TEXT handles the prose
- Direct inline expressions (the proper way) fail with prose

**Impact**: Cannot properly assess true completeness without TEXT workaround

**Examples Affected**:
- Solution 19: All parts (a-d) require TEXT due to "is true" / "is undefined"
- Solution 20: All parts require TEXT due to "is the set..."
- Many others mixing math with explanatory prose

**Root Cause**:
Parser treats everything as a mathematical expression when not in TEXT block. Periods are not valid in expressions, so `expr.` fails. TEXT blocks use inline math detection which can handle mixed content.

**Proper Fix Needed**:
- Allow sentences with inline math: `The answer is {1, 2, 3}.`
- Distinguish between expression-only lines and prose lines
- Or: require explicit math delimiters for inline expressions

**Status**: Open - major parser limitation blocking proper inline usage

### TEXT blocks: Inline math with multiple pipes closes math mode prematurely

**Severity**: Medium
**Component**: Inline math detection in TEXT blocks
**Discovered**: 2025-01-14

**Description**:
When a TEXT block contains a complex expression with multiple pipe characters (`|`), the inline math detector incorrectly closes the math mode after the first pipe, leaving subsequent content (including `>` symbols) outside math mode. This causes garbled rendering in the PDF.

**Example**:
```
TEXT: (mu p : ran hd; q : ran hd | p /= q | p.2 > q.2)
```

**Generated LaTeX** (incorrect):
```latex
($\mu p \colon \ran hd \bullet \mu q \colon \ran hd \bullet p \neq q$| p.2 > q.2)
```

The `$` closes after `p \neq q` but should remain open through `p.2 > q.2`.

**Expected LaTeX**:
```latex
($\mu p \colon \ran hd \bullet \mu q \colon \ran hd \bullet p \neq q \mid p.2 > q.2$)
```

**Workaround**:
Use proper Z notation blocks (axdef, schema, etc.) instead of TEXT blocks for complex expressions. These work correctly:

```
axdef
where
  forall x : N; y : N | x > y
end
```

**Root Cause**:
The inline math detection logic treats pipes as potential boundaries of math expressions, but doesn't account for Z notation constructs (like mu expressions) that legitimately contain multiple pipes within a single math expression.

**Location**: Likely in inline_math.py or text block processing in latex_gen.py

**Test Case**: `examples/phase17_demo.txt` line 35

**Status**: Open - requires investigation of inline math detection logic

---

## Low Priority

### Misuse of TEXT blocks for mathematical expressions

**Severity**: Low (documentation/style issue, not a parser bug)
**Component**: examples/solutions.txt
**Discovered**: 2025-01-14

**Description**:
Many mathematical expressions in solutions.txt are incorrectly wrapped in TEXT blocks. TEXT should only be used for descriptive prose, not for mathematical expressions.

**Examples of Misuse**:
```
TEXT: false (as (true => false) <=> false)
TEXT: forall x : N | x > 0
TEXT: (mu a : N | a = a) = 0
```

**Should Be**:
```
false (as (true => false) <=> false)
forall x : N | x > 0
(mu a : N | a = a) = 0
```

**Proper TEXT Usage** (descriptive prose only):
```
TEXT: Note that cumulative_total is defined in part (d).
TEXT: (Assuming that pigs can't fly...)
TEXT: This is a true proposition because...
```

**Impact**:
- Minor: TEXT blocks work but aren't semantically correct
- Causes inline math detection issues with complex expressions (see bug above)
- Makes code harder to understand

**Resolution**:
- Document proper TEXT usage in README/DESIGN
- Eventually refactor solutions.txt to use direct expressions
- Low priority: doesn't affect functionality

**Status**: Open - documentation issue

---

## Medium Priority

### Parser: Juxtaposition not supported for function/type application

**Severity**: Medium (common Z notation pattern)
**Component**: Parser / function application
**Discovered**: 2025-01-14

**Description**:
The parser does not support juxtaposition (whitespace) for function or type application. Parentheses are required: `f(x)` not `f x`, `seq(Entry)` not `seq Entry`.

**Examples that FAIL**:
```
longest_viewed s          (function application)
seq Entry                 (type application)
g s = s |> {x : ran s}   (in expressions)
```

**Must Use**:
```
longest_viewed(s)
seq(Entry)
g(s) = s |> {x : ran s}
```

**Why This Matters**:
- Juxtaposition is standard in Z notation and mathematical writing
- Many solutions in solutions.txt use juxtaposition
- Requires manual conversion to parenthesized form

**Examples Affected**:
- Solution 40(g): `g s = s |> {x : ran s | x /= longest_viewed s}`
- Solution 40(h): `items (s x) = items x`
- Multiple type declarations: `seq Entry`, `seq Title`

**Workaround**:
Add explicit parentheses to all function and type applications.

**Proper Fix Needed**:
Implement juxtaposition parsing in `_parse_postfix()`. This is complex because:
- Need to distinguish `f x` (application) from `x y` (two variables)
- Need proper precedence with other operators
- May require lookahead or context-sensitive parsing

**Status**: Open - workaround available but verbose

---

### Parser: Nested quantifiers in mu expression predicates fail

**Severity**: Medium (blocks complex expressions)
**Component**: Parser / quantifier nesting
**Discovered**: 2025-01-14

**Description**:
Mu expressions with nested quantifiers in the predicate part cause parse errors. The parser cannot correctly handle multiple pipe characters (`|`) from nested quantified predicates.

**Example that FAILS**:
```
(mu p : ran s | p.3 = yes and forall q : ran s | p /= q and q.3 = yes | p.2 > q.2)
```

Error: `Line 767, column 95: Expected identifier, number, '(', '{', '⟨', or lambda, got FORALL`

**Structure**:
```
mu VAR : DOMAIN | PREDICATE | EXPRESSION
where PREDICATE contains: forall VAR : DOMAIN | PREDICATE
```

The three pipes confuse the parser about which belongs to the outer mu and which to the inner forall.

**Root Cause**:
Parser cannot distinguish:
- Pipe 1: Separates mu domain from predicate
- Pipe 2: Separates inner forall predicate
- Pipe 3: Separates mu predicate from expression

**Examples Affected**:
- Solution 40(g): `mu p : ran hd | forall q : ran hd | p /= q | p.2 > q.2`

**Workaround**:
Currently none. Must use TEXT blocks or restructure expressions.

**Proper Fix Needed**:
- Implement proper nesting of quantified predicates in mu expressions
- Use expression parsing context to track nesting depth
- Parse inner quantifiers completely before continuing outer predicate

**Status**: Open - significant parser enhancement required

---

### Lexer: Alternative function type notation not supported

**Severity**: Low (documentation issue)
**Component**: Lexer / function type tokens
**Discovered**: 2025-01-14

**Description**:
The notation `-|>` is not recognized as a function type operator. The lexer tokenizes it as `-` followed by `|>` (RRES - range restriction).

**Example**:
```
longest_viewed : seq(T) -|> T
```

**Supported Notation**:
```
->    : total function (TFUN)
+->   : partial function (PFUN)
>->   : total injection (TINJ)
>+>   : partial injection (PINJ)
-->>  : total surjection (TSURJ)
+->>  : partial surjection (PSURJ)
>->>  : bijection (BIJECTION)
```

**Resolution**:
Use standard Z notation `+->` for partial functions instead of `-|>`.

**Impact**: Low - likely user notation issue, not missing feature

**Status**: Documented - use standard notation

---

### Parser: Compound identifiers with operator suffixes not supported

**Severity**: Medium (blocks specific solutions)
**Component**: Lexer / identifier tokenization
**Discovered**: 2025-01-14

**Description**:
The lexer cannot handle identifiers that include operator characters as suffixes, such as `R+` or `R*`. These are tokenized as two separate tokens (identifier + operator) rather than as a single compound identifier.

**Example that FAILS**:
```
R+ == {a, b : N | b > a}
```

Error: `Line 583, column 4: Expected identifier, number, '(', '{', '⟨', or lambda, got ABBREV`

**Why This Fails**:
- `R+` is tokenized as `R` (IDENTIFIER) followed by `+` (PLUS)
- Parser sees: `R` `+` `==` and expects an operand after `+`
- Cannot use compound identifiers in abbreviation names

**Context**:
In Z notation, `R+` and `R*` are typically postfix operators for transitive closure. However, Solution 31 explicitly defines relations named `R+` and `R*` (line 575 comment: "Requires compound identifiers with operators - R+, R*").

**Examples Affected**:
- Solution 31(c): `R+ == {a, b : N | b > a}`
- Solution 31(d): `R* == {a, b : N | b >= a}`

**Workaround**:
Currently none. These abbreviations cannot be expressed.

**Proper Fix Needed**:
- Option 1: Allow `+` and `*` as suffix characters in identifiers (complex, may break other parsing)
- Option 2: Special handling for operator-suffixed identifiers in specific contexts
- Option 3: Use different naming convention (e.g., `R_plus`, `R_star`)

**Status**: Open - not implemented, blocks Solution 31

---

## Fixed

### Parser: Prefix operators (id, dom, ran, etc.) not usable as standalone identifiers

**Severity**: High
**Component**: Parser / primary expression parsing
**Discovered**: 2025-01-14
**Fixed**: 2025-01-14

**Description**:
Keywords like `id`, `dom`, `ran`, `inv`, etc. were always treated as prefix operators, expecting an operand. This prevented their use as standalone identifiers in expressions like `R \ id`.

**Example that FAILED**:
```
siblingOf == (childOf o9 parentOf) \ id
```

Error: `Line 1, column 40: Expected identifier, number, '(', '{', '⟨', or lambda, got NEWLINE`

**Root Cause**:
In `_parse_primary()`, when the parser saw TokenType.ID (or DOM, RAN, etc.), it immediately tried to parse an operand with `_parse_atom()`. If no operand followed (like at end of line), parsing failed.

**Fix Applied**:
Modified `_parse_primary()` to check if a prefix operator is followed by a valid operand token. If not, treat it as a standalone identifier instead of a prefix operator.

**Code Change** ([parser.py:1628-1655](src/txt2tex/parser.py#L1628-L1655)):
```python
# Check if followed by a valid operand for prefix operator
# If not, treat as standalone identifier (e.g., "R \ id" not "id R")
if not self._match(
    TokenType.IDENTIFIER,
    TokenType.NUMBER,
    TokenType.LPAREN,
    # ... other primary tokens
):
    # Not followed by valid operand, treat as identifier
    return Identifier(
        name=op_token.value,
        line=op_token.line,
        column=op_token.column,
    )
```

**Test Results**: All 599 tests pass

**Examples Fixed**:
- Solution 30(b): `siblingOf == (childOf o9 parentOf) \ id`
- Any expression using `id`, `dom`, `ran`, `inv` as operands rather than operators
