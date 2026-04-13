# Tutorial 5: Z Notation Definitions

<!-- markdownlint-disable-next-line MD036 -->
**Lecture 5: Z Notation Basics**

Learn Z notation definition forms: given types, free types, abbreviations, axiomatic definitions, and schemas.

**Prerequisites:** Tutorials 1-4  
**Examples:** `examples/06_definitions/`

---

## Introduction to Z Notation

Z notation is a formal specification language for describing systems precisely. It combines:

- Set theory and logic
- Schema notation for state and operations
- Type system for rigor

## Given Types

Declare basic types without defining their structure:

```text
given Person, Department, Account
```

These are primitive types—we don't specify what they contain, just that they exist.

## Free Types

Define algebraic data types with constructors:

```text
Color ::= red | green | blue
Status ::= pending | approved | rejected
```

**With parameters:**

```text
Tree ::= leaf | node⟨N × Tree × Tree⟩
Maybe ::= nothing | just⟨N⟩
```

**See:** `examples/06_definitions/free_types_demo.txt`, `examples/06_definitions/free_types_proper.txt`

## Abbreviations

Define constants and type synonyms:

```text
MAX == 100
IntSet == P Z
Coordinate == N cross N
```

**Syntax:** `name == expression`

**See:** `examples/06_definitions/abbrev_demo.txt`

## Axiomatic Definitions

Define global constants and functions with constraints:

```text
axdef
  maxSize : N
  minSize : N
where
  minSize = 0
  maxSize = 1000
  minSize < maxSize
end
```

**Function definition:**

```text
axdef
  square : N -> N
where
  forall n : N | square(n) = n * n
end
```

**See:** `examples/06_definitions/axdef_demo.txt`, `examples/08_functions/function_definitions_simple.txt`

## Schema Definitions

Group related variables with constraints:

```text
schema BankAccount
  accountNumber : N
  balance : Z
where
  balance >= 0
  accountNumber > 0
end
```

**Anonymous schema:**

```text
schema
  count : N
  limit : N
where
  count <= limit
end
```

**See:** `examples/06_definitions/schema_demo.txt`, `examples/06_definitions/anonymous_schema.txt`

## Generic Definitions

Polymorphic definitions with type parameters:

```text
gendef [X]
  identity : X -> X
where
  forall x : X | identity(x) = x
end
```

**Multiple parameters:**

```text
gendef [X, Y]
  fst : X cross Y -> X
  snd : X cross Y -> Y
where
  forall x : X; y : Y | fst(x, y) = x land snd(x, y) = y
end
```

**See:** `examples/06_definitions/gendef_basic.txt`, `examples/06_definitions/gendef_advanced.txt`

## Complete Example

```text
=== Library System Specification ===

given Book, Member

Status ::= available | borrowed | reserved

axdef
  maxLoans : N
where
  maxLoans = 5
end

schema Library
  books : P Book
  members : P Member
  loans : Member +-> P Book
where
  dom loans subseteq members
  forall m : Member | # (loans m) <= maxLoans
end
```

## Summary

You've learned:

- ✅ given types for primitives
- ✅ Free types for algebraic data
- ✅ Abbreviations for constants
- ✅ axdef for global definitions
- ✅ schema for grouping related data
- ✅ gendef for polymorphic definitions

**Next Tutorial:** [Tutorial 6: Relations](docs/tutorials/06_relations.md)

---

**Practice:** Explore `examples/06_definitions/`
