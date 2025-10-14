# Known Bugs

## High Priority

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

## Fixed

None yet.
