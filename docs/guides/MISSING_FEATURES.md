# Missing Features

This document lists Z notation features not yet implemented in txt2tex.

**Status**: Feature-complete for typical specifications (1,244 tests, 100% pass rate).

---

---

## LET Construct (Medium Priority)

Local definitions in expressions/predicates:

```text
LET double == lambda x : N . x * 2 @
quad(5)
```

**Workaround**: Use document-level abbreviations instead.

---

## Schema Renaming (Low Priority)

Component renaming syntax: `State[x'/x, y'/y]`

**Blocks**: Theta expressions (`\theta Schema`)

---

## Other Missing Features (Low Priority)

| Feature | Description |
|---------|-------------|
| Horizontal schema definitions | `Schema \defs Schema-Exp` syntax |
| User-defined operators | `%%inop`, `%%ingen` directives |
| Advanced directives | `%%type`, `%%tame`, `%%unchecked` |

---

## Known Limitations

1. **Superscript `^`**: Only for relation iteration (`R^n`), not arithmetic (`x^2`)
2. **Tuple projection**: Only named fields (`x.field`), not numeric (`.1`, `.2`)
3. **Multi-decl lambda without pipe-predicate**: `lambda s : Ship; c : Class . (s, c)` is not accepted. Z RM §3.12 SchemaText predicate is optional, but `_parse_quantifier_continuation` (reused for multi-decl lambda) requires a PIPE token before the body. Single-decl lambda (`lambda x : T . body`) and multi-decl lambda with a predicate (`lambda s : Ship; c : Class | P . E`) both work. No test forces this form yet; low priority.

---

## Implemented Features

All fundamental Z notation is complete:

- **Paragraphs**: given, axdef, schema, gendef, zed, free types, abbreviations
- **Expressions**: lambda, mu, if/then/else, set comprehension, sequences, bags, tuples
- **Predicates**: forall, exists, exists1, schemas-as-predicates, pre
- **Schema calculus**: composition (`;`), piping (`>>`), hiding (`hide`), projection (`project`)
- **Operators**: All logic, set, relation, function, and sequence operators
- **Formatting**: `\also`, `\t` indentation, `~` spacing, line breaks
