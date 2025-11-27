# Missing Features

This document lists Z notation features not yet implemented in txt2tex.

**Status**: Feature-complete for typical specifications (1,244 tests, 100% pass rate).

---

## Schema Calculus Operators (Low Priority)

These advanced operators that transform schemas into new schemas are not implemented:

| Operator | LaTeX Command | Purpose |
|----------|---------------|---------|
| Schema hiding | `\hide` | Hide components: `S \hide (x, y)` |
| Schema projection | `\project` | Project to components |
| Schema composition | `\semi` | Sequential composition: `S1 ; S2` |
| Schema negation | `\lnot` | Schema-level negation |
| Schema piping | `\pipe` | Schema piping (>>) |

**Note**: Schemas-as-predicates (e.g., `S1 land S2`) ARE supported. Only operators that return new schemas are missing.

---

## LET Construct (Medium Priority)

Local definitions in expressions/predicates:

```
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
2. **Semicolon**: Reserved for declarations, not available for composition (use `comp` or `o9`)
3. **Tuple projection**: Only named fields (`x.field`), not numeric (`.1`, `.2`)

---

## Implemented Features

All fundamental Z notation is complete:

- **Paragraphs**: given, axdef, schema, gendef, zed, free types, abbreviations
- **Expressions**: lambda, mu, if/then/else, set comprehension, sequences, bags, tuples
- **Predicates**: forall, exists, exists1, schemas-as-predicates, pre
- **Operators**: All logic, set, relation, function, and sequence operators
- **Formatting**: `\also`, `\t` indentation, `~` spacing, line breaks
