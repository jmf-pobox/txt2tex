# Lecture 6: Definitions

This directory contains examples for Lecture 6, covering different ways to define types and values in Z notation.

## Topics Covered

- Given types (basic type declarations)
- Abbreviations (type aliases)
- Free types (algebraic data types)
- Generic definitions (`gendef`)
- Axiomatic definitions (`axdef`)

## Definition Types

### Given Types
```
given Person, Company
```
Declares basic types without internal structure.

### Abbreviations
```
Pairs == N cross N
[X, Y] Product == X cross Y
```
Create type aliases with optional generic parameters.

### Free Types
```
Status ::= active | inactive | pending
Tree ::= stalk | leaf<N> | branch<Tree × Tree>
```
Define algebraic data types with constructors.

### Generic Definitions
```
gendef [X, Y]
  fst : X cross Y -> X
where
  forall x : X; y : Y | fst(x, y) = x
end
```
Define polymorphic functions with type parameters.

### Axiomatic Definitions
```
axdef
  population : N
where
  population > 0
end
```
Define global constants with constraints.

## Examples in This Directory

Browse the `.txt` files to see:
- Basic and generic given types
- Simple and recursive free types
- Generic function definitions
- Axiomatic definitions with constraints

## See Also

- **docs/guides/USER_GUIDE.md** - Section "Definitions"
- **docs/tutorials/06_relations.md** - Detailed tutorial for Lecture 6
- **Previous**: 05_sets/
- **Next**: 07_relations/
