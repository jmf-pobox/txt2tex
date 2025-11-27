# Missing Features

This document lists Z notation features not yet implemented in txt2tex.

**Status**: txt2tex is feature-complete for all homework solutions (1244 tests, 100% coverage).

---

## Schema Calculus Operators

These advanced operators are not implemented:

| Operator | zed2e Command | Purpose |
|----------|---------------|---------|
| Schema hiding | `\hide` | Hide components: `S \ (x, y)` |
| Schema projection | `\project` | Project components: `S \project (x, y)` |
| Precondition | `\pre` | Extract precondition: `pre S` |

**Priority**: Low - only needed for advanced schema calculus problems.

---

## Nice-to-Have Enhancements

These would improve output quality but are not blocking:

1. **Smart line breaking** - Automatically break long predicates at logical boundaries
2. **Configuration file** - `.txt2tex.toml` for project-specific formatting options

---

## Implemented Features

All of the following are complete:

- **Environments**: schema, axdef, gendef, zed, syntax, infrule
- **Formatting**: `\also` spacing, `\t` indentation, `~` spacing hints, `\\` line breaks
- **Keywords**: `land`, `lor`, `lnot`, `elem` (aligned with Z standards)
- **Operators**: All logic, set, relation, function, and sequence operators
- **zed consolidation**: Consecutive zed blocks merged with `\also`

