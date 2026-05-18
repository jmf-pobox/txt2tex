# Tutorial 9: Schemas and Composition

<!-- markdownlint-disable-next-line MD036 -->
**Lecture 9: Advanced Z Notation**

Learn schema composition, state schemas, operations, and zed blocks.

**Prerequisites:** Tutorial 8  
**Examples:** `examples/10_schemas/`

---

## Schema Notation

**Schema:** Groups related variables with constraints

```text
schema Counter
  count : N
  limit : N
where
  count <= limit
end
```

**Components:** Access with dot notation

```text
c.count
c.limit
```

## State Schemas

Model system state:

```text
schema Library
  books : P Book
  borrowed : Book +-> Member
where
  dom borrowed subseteq books
end
```

## Operation Schemas

Model state changes using primed variables ('):

```text
schema BorrowBook
  Library
  Library'
  book? : Book
  member? : Member
where
  book? in books
  book? notin dom borrowed
  borrowed' = borrowed union {book? |-> member?}
  books' = books
end
```

**Conventions:**

- `x'` (primed) - value after operation
- `x?` (input) - operation input
- `x!` (output) - operation output

## Schema Inclusion and Δ/Ξ

**Phase 1.1 feature.** Schema inclusion brings the components of one schema
into the declaration list of another.  Three forms are supported.

### Bare inclusion

```text
schema LoggedInUser
  User
  sessionToken : N
where
  sessionToken > 0
end
```

`User` on its own line (no colon) is a bare schema inclusion.  It brings all
User components and constraints into LoggedInUser.

### Delta inclusion — before/after state

The Z RM §3.7 convention: `Delta S` abbreviates including both the before-state
`S` and the after-state `S'` simultaneously.  Use this for operation schemas that
modify state:

```text
schema Counter
  count : N
where
  count >= 0
end

schema IncrCounter
  Delta Counter
  increment? : N
where
  count' = count + increment?
end
```

LaTeX output: `\Delta Counter`

### Xi inclusion — read-only operation

The Z RM §5.2 convention: `Xi S` asserts the state is unchanged.  Use this for
query operations:

```text
schema ReadCount
  Xi Counter
  result! : N
where
  result! = count
end
```

LaTeX output: `\Xi Counter`

### Generic instantiation

Inclusions can carry type parameters:

```text
schema PushNat
  Delta Stack[N]
  value? : N
end
```

LaTeX output: `\Delta Stack[\nat]`

### Schema-as-predicate

Once schemas are included in the declaration list, their names can appear in the
`where` clause as predicates.  The conjunction `S1 land S2` applies both schema
predicates:

```text
schema A
  x : N
end

schema B
  y : N
end

schema AB
  A
  B
  z : N
where
  A land B
  z = x + y
end
```

### Disambiguation rule

The parser uses a one-pass lookahead scan to distinguish a bare inclusion from a
typed declaration:

- If a colon `:` appears before the next newline, parse as a typed declaration.
- Otherwise, parse as a schema inclusion.

This means `count, limit : N` (two variables sharing a type) is never confused
with `Counter` (a bare inclusion), even when both appear on the same line start.

**See:** `examples/10_schemas/delta_xi_inclusion.txt` and
`examples/10_schemas/schema_as_predicate.txt`

## Schema Composition

Combine schemas using operators:

**Conjunction:**

```text
SchemaA land SchemaB
```

**Disjunction:**

```text
SchemaA lor SchemaB
```

**Sequential composition:**

```text
SchemaA o9 SchemaB
```

## Zed Blocks

Group multiple definitions:

```text
zed
  given Person, Account

  Status ::= active | suspended | closed

  axdef
    maxAccounts : N
  where
    maxAccounts = 10
  end

  schema Bank
    accounts : Person +-> Account
  where
    forall p : Person | # (accounts(| {p} |)) <= maxAccounts
  end
end
```

**Note:** The zed block syntax shown above is aspirational. Currently txt2tex's `zed` blocks only wrap single expressions, not nested definitions with `where` clauses. See `examples/10_schemas/future/zed_blocks.txt` for the full example (requires parser enhancements).

## Scoping

**Global scope:** given types, axdef, free types  
**Schema scope:** schema components  
**Quantifier scope:** forall/exists variables  
**Lambda scope:** lambda parameters

**See:** `examples/10_schemas/scoping_demo.txt`

## Complete Example

```text
=== Banking System ===

given Customer, Account

Status ::= open | closed

schema Bank
  accounts : Customer +-> Account
  status : Account -> Status
where
  ran accounts subseteq dom status
end

schema OpenAccount
  Bank
  Bank'
  customer? : Customer
  account! : Account
where
  customer? notin dom accounts
  account! notin ran accounts
  accounts' = accounts union {customer? |-> account!}
  status' = status union {account! |-> open}
end

schema CloseAccount
  Bank
  Bank'
  account? : Account
where
  account? in ran accounts
  status(account?) = open
  status' = status ++ {account? |-> closed}
  accounts' = accounts
end
```

## Summary

You've learned:

- ✅ Schema notation and components
- ✅ State schemas for system modeling
- ✅ Operation schemas with primed variables
- ✅ Schema inclusion and composition
- ✅ Zed blocks for grouping definitions
- ✅ Scoping rules

**Next:** [Tutorial: Advanced Features](10_advanced.md)

---

**Practice:** Explore `examples/10_schemas/`
