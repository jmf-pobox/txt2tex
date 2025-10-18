# GitHub Issues to Create

## Issue #1: Parser fails on prose mixed with inline math (periods)

**Labels**: bug, parser, high-priority, blocks-homework

**Title**: Parser: Prose with inline math and periods causes parse errors

**Body**:
```markdown
## Description
The parser fails when prose containing mathematical expressions is followed by periods, unless wrapped in a TEXT block.

## Test Case

**Location**: `tests/bugs/bug1_prose_period.txt`

**Input**:
```txt
=== Bug 1 Test: Prose with Period ===

1 in {4, 3, 2, 1} is true.
```

## Reproduction Steps

```bash
hatch run convert tests/bugs/bug1_prose_period.txt
```

## Expected Behavior
Should parse and render as: "1 ∈ {4, 3, 2, 1} is true."

## Actual Behavior
```
Error processing input: Line 3, column 26: Expected identifier, number, '(', '{', '⟨', or lambda, got PERIOD
```

## Workaround
Use TEXT blocks:
```txt
TEXT: 1 in {4, 3, 2, 1} is true.
```

## Impact
- **Severity**: HIGH
- **Blocks**: Natural writing style for homework problems
- **Component**: parser
- **Affects**: Students writing homework, anyone wanting to write prose with math

## Environment
- txt2tex commit: [current]
- Python version: 3.13
- OS: macOS

## Technical Details
- Root cause: Parser treats everything as mathematical expression outside TEXT blocks
- Periods are not valid in mathematical expressions
- Parser needs to handle prose context or require TEXT blocks
```

---

## Issue #2: TEXT blocks with multiple pipes close math mode prematurely

**Labels**: bug, latex-gen, medium-priority, TEXT-blocks

**Title**: TEXT blocks: Multiple pipes in expressions close math mode incorrectly

**Body**:
```markdown
## Description
When TEXT blocks contain expressions with multiple pipe `|` characters (like nested quantifiers), the inline math detection closes math mode prematurely, leaving some pipes outside math mode.

## Test Case

**Location**: `tests/bugs/bug2_multiple_pipes.txt`

**Input**:
```txt
=== Bug 2 Test: Multiple Pipes in TEXT ===

TEXT: Consider the expression (mu p : ran hd; q : ran hd | p /= q | p.2 > q.2).
```

## Reproduction Steps

```bash
hatch run convert tests/bugs/bug2_multiple_pipes.txt
pdftotext tests/bugs/bug2_multiple_pipes.pdf -
```

## Expected Behavior
All pipes should be in math mode:
```
Consider the expression (µ p: ran hd • (∀ q: ran hd • p ≠ q • p.2 > q.2)).
```

## Actual Behavior
Second pipe appears as text:
```
Consider the expression (µ p: ran hd • µ q: ran hd • p ̸= q| p.2 > q.2).
```
Note the `|` after `q` is outside math mode.

## Workaround
Use proper Z notation blocks (axdef, schema) instead of TEXT blocks for complex mathematical expressions.

## Impact
- **Severity**: MEDIUM
- **Blocks**: Solution 40(g) and similar complex expressions with nested quantifiers
- **Component**: latex-gen (inline math detection in TEXT blocks)
- **Affects**: TEXT blocks with mu-expressions containing nested quantifiers

## Environment
- txt2tex commit: [current]
- Python version: 3.13
- OS: macOS

## Technical Details
- Root cause: Inline math detection treats pipes as expression boundaries
- Multiple pipes confuse the pattern matching
- Needs smarter parsing of quantifier nesting levels
```

---

## Issue #3: Compound identifiers with operator suffixes fail

**Labels**: bug, lexer, medium-priority

**Title**: Lexer: Cannot use identifiers like R+, R* (operator suffixes)

**Body**:
```markdown
## Description
The lexer cannot handle identifiers that end with operator symbols like `+` or `*`. These are tokenized as identifier followed by operator, causing parse errors.

## Test Case

**Location**: `tests/bugs/bug3_compound_id.txt`

**Input**:
```txt
=== Bug 3 Test: Compound Identifier ===

abbrev
  R+ == {a, b : N | b > a}
end
```

## Reproduction Steps

```bash
hatch run convert tests/bugs/bug3_compound_id.txt
```

## Expected Behavior
Should define `R+` as an abbreviation for the relation.

## Actual Behavior
```
Error processing input: Line 4, column 6: Expected identifier, number, '(', '{', '⟨', or lambda, got ABBREV
```

## Workaround
None available. Cannot use identifiers with operator suffixes.

## Impact
- **Severity**: MEDIUM
- **Blocks**: Solution 31 (transitive closure R+)
- **Component**: lexer
- **Affects**: Anyone wanting to use standard mathematical notation like R+, R* for relation closures

## Environment
- txt2tex commit: [current]
- Python version: 3.13
- OS: macOS

## Technical Details
- Root cause: Lexer tokenizes as `IDENTIFIER("R")` followed by `PLUS` operator
- Need special handling for identifier+operator combinations
- May need context-aware lexing or lookahead
- Alternative: Allow quoted identifiers like `"R+"`
```

---

## How to Create These Issues

1. Go to GitHub repository Issues tab
2. Click "New Issue"
3. Select "Bug Report" template
4. Copy content from above for each issue
5. Create issue
6. Note the issue number
7. Update STATUS.md and other docs with issue numbers
