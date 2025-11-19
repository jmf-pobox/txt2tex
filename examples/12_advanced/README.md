# Advanced Features

This directory contains examples of advanced txt2tex features and syntax patterns.

## Topics Covered

- Conditional expressions (`if-then-else`)
- Subscripts and superscripts
- Multi-word identifiers
- Generic type instantiation
- Complex operator combinations
- Advanced formatting techniques

## Conditional Expressions

```
if x > 0 then x else -x                    [absolute value]
if s = <> then 0 else head s               [safe head with default]
if x > 0 then 1 else if x < 0 then -1 else 0  [nested conditionals]
```

Used in function definitions:
```
abs(x) = if x > 0 then x else -x
max(x, y) = if x > y then x else y
```

## Subscripts and Superscripts

```
x_i              →  xᵢ          [simple subscript]
x^2              →  x²          [simple superscript]
2^n              →  2ⁿ
a_{max}          →  a_{max}     [braces for multi-char subscripts]
x^{2n}           →  x^{2n}      [braces for multi-char superscripts]
```

## Multi-Word Identifiers

Underscores create readable variable names:
```
cumulative_total         [multi-word identifier]
not_yet_viewed
employee_count
```

**Smart rendering**:
- `a_i` → $a_i$ (simple subscript)
- `x_max` → $x_{max}$ (multi-char subscript)
- `cumulative_total` → $\mathit{cumulative\_total}$ (multi-word)

## Generic Type Instantiation

Apply type parameters to polymorphic types:
```
seq[N]                       [sequence of naturals]
P[X]                         [power set of X]
Type[A, B]                   [binary type constructor]
emptyset[N cross N]          [complex type parameters]
Container[seq[N]]            [nested instantiation]
```

**Note**: Type application requires square brackets with NO space: `seq[N]` not `seq [N]`.

## Examples in This Directory

Browse the `.txt` files to see:
- Conditional expression patterns
- Advanced subscript/superscript usage
- Multi-word identifier conventions
- Complex generic instantiations
- Operator precedence edge cases

## See Also

- **docs/USER_GUIDE.md** - Section "Additional Features"
- **docs/TUTORIAL_ADVANCED.md** - Comprehensive advanced guide
- **Previous**: 11_text_blocks/
- **Next**: complete_examples/
