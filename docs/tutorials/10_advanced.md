# Tutorial: Advanced Features

**Advanced Topics**

Learn conditional expressions, subscripts, generic instantiation, text blocks, and other advanced features.

**Prerequisites:** Tutorials 1-9  
**Examples:** `examples/11_text_blocks/`, `examples/12_advanced/`

---

## Conditional Expressions

**if-then-else syntax:**

```
if condition then expr1 else expr2
```

**Example:**
```
axdef
  abs : Z -> N
where
  forall x : Z | abs(x) = if x >= 0 then x else -x
end
```

**Nested conditionals:**
```
if x > 0 then 1
else if x = 0 then 0
else -1
```

**Note:** See `examples/12_advanced/future/if_then_else.txt` (requires division operator `/` which is not yet implemented)

## Subscripts and Superscripts

**Subscripts:** Use underscore (_)
```
x_1, x_2, x_i
```

**Superscripts (relation iteration only):** Use caret (^)
```
R^2   # Relation composed with itself (R o9 R)
R^n   # N-fold relation composition
```

**Note:** Arithmetic exponentiation (x^2, n^3) is NOT supported by fuzz. Use manual multiplication:
```
x * x        # For x squared
n * n * n    # For n cubed
```

**Note:** Combining subscripts with arithmetic exponentiation is not supported (e.g., `x_i^2` would fail fuzz validation). Use manual multiplication for the squared part.

## Generic Type Instantiation

Apply type parameters to polymorphic types:

```
seq[N]              (sequence of naturals)
P[X]                (power set of X)
emptyset[Z]         (empty set of integers)
```

**Complex types:**
```
seq[N cross N]      (sequence of pairs)
P[seq[N]]           (set of sequences)
```

**Note:** See `examples/12_advanced/future/generic_instantiation.txt` (requires prime notation `x'` which is not yet implemented)

## Text Blocks

### TEXT Directive

Normal prose with smart typography:

```
TEXT: This is explanatory text with "smart quotes" and inline math like (x * x).
```

**Note:** Arithmetic exponentiation (x^2) is not supported in TEXT blocks - use multiplication instead.

### PURETEXT Directive

Verbatim text without processing:

```
PURETEXT: Characters like " and ' remain literal.
```

### LATEX Directive

Raw LaTeX commands:

```
LATEX: \noindent Custom formatting here.
LATEX: \vspace{1cm}
```

### PAGEBREAK

Force page breaks:

```
PAGEBREAK
```

**See:** `examples/11_text_blocks/`

## Bibliography Management

**Directives:**
```
BIBLIOGRAPHY: references.bib
BIBLIOGRAPHY_STYLE: plainnat
```

**Citations:**
```
TEXT: As shown in [cite spivey92], Z notation is powerful.
```

**See:** `examples/11_text_blocks/bibliography_example.txt`

## Complete Example

```
=== Advanced Features Demo ===

** Example 1: Conditional Expression **

axdef
  max : N cross N -> N
where
  forall a, b : N | max(a, b) = if a >= b then a else b
end

** Example 2: Subscripted Variables **

axdef
  x_1, x_2, x_3 : N
where
  x_1 = 1
  x_2 = 2
  x_3 = x_1 + x_2
end

TEXT: We have x_3 = 3.

** Example 3: Generic Instantiation **

axdef
  numbers : seq[N]
  pairs : seq[N cross N]
where
  numbers = <1, 2, 3>
  pairs = <(1, 2), (3, 4)>
end

** Example 4: Mixed Text Blocks **

TEXT: This uses smart quotes and inline math like n^2.

PURETEXT: This preserves literal "quotes" and characters.

LATEX: \medskip

TEXT: Custom spacing inserted above.
```

## Document Structure Tips

### Organizing Large Specifications

1. **Use sections:** `=== Section Title ===`
2. **Use subsections:** `** Problem N **`
3. **Add TEXT blocks:** Explain reasoning
4. **Use PAGEBREAK:** Separate major sections
5. **Group definitions:** Use zed blocks or schemas

### Style Guidelines

1. **Be consistent:** Choose ASCII or Unicode and stick to it
2. **Document assumptions:** Use TEXT blocks
3. **Name meaningfully:** Choose clear identifiers
4. **Indent properly:** Follow PROOF_SYNTAX.md
5. **Type everything:** All variables need types

## Advanced Patterns

### Pattern 1: State Machine

```
Status ::= init | running | stopped | error

schema System
  state : Status
  data : seq N
where
  state in {init, running, stopped, error}
end
```

### Pattern 2: Invariant Preservation

```
schema Operation
  System
  System'
where
  # data' >= # data
  state' in {running, stopped}
end
```

### Pattern 3: Generic Container

```
gendef [T]
  schema Container_T
    elements : seq T
    capacity : N
  where
    # elements <= capacity
  end
end
```

## Summary

You've learned:
- ✅ Conditional expressions (if-then-else)
- ✅ Subscripts and superscripts
- ✅ Generic type instantiation
- ✅ Text blocks (TEXT, PURETEXT, LATEX)
- ✅ Bibliography management
- ✅ Document structure and style

**Next Steps:**
- Study examples in `examples/` directories for integration patterns
- Consult [USER_GUIDE.md](docs/guides/USER_GUIDE.md) for comprehensive reference
- Practice with course problems

---

**Congratulations!** You've completed the txt2tex tutorial series. You're now ready to write formal specifications and generate beautiful LaTeX documents.
