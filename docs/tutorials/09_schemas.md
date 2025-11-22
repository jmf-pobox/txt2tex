# Tutorial 9: Schemas and Composition

**Lecture 9: Advanced Z Notation**

Learn schema composition, state schemas, operations, and zed blocks.

**Prerequisites:** Tutorial 8  
**Examples:** `examples/10_schemas/`

---

## Schema Notation

**Schema:** Groups related variables with constraints

```
schema Counter
  count : N
  limit : N
where
  count <= limit
end
```

**Components:** Access with dot notation
```
c.count
c.limit
```

## State Schemas

Model system state:

```
schema Library
  books : P Book
  borrowed : Book +-> Member
where
  dom borrowed subseteq books
end
```

## Operation Schemas

Model state changes using primed variables ('):

```
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

## Schema Inclusion

Include one schema in another:

```
schema LoggedInUser
  User
  sessionToken : N
where
  sessionToken > 0
end
```

This brings all User components and constraints into LoggedInUser.

## Schema Composition

Combine schemas using operators:

**Conjunction:**
```
SchemaA and SchemaB
```

**Disjunction:**
```
SchemaA or SchemaB
```

**Sequential composition:**
```
SchemaA o9 SchemaB
```

## Zed Blocks

Group multiple definitions:

```
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

```
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

**Next:** [Tutorial: Advanced Features](docs/tutorials/10_advanced.md) or explore `complete_examples/`

---

**Practice:** Explore `examples/10_schemas/`
