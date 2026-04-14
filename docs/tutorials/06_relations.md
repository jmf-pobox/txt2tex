# Tutorial 6: Relations

<!-- markdownlint-disable-next-line MD036 -->
**Lecture 6: Relations**

Learn about binary relations, maplets, domain/range, and relational operators.

**Prerequisites:** Tutorial 5  
**Examples:** `examples/07_relations/`

---

## Binary Relations

**Relation:** Set of ordered pairs

**Notation:**

```text
R : X <-> Y        (relation from X to Y)
R : X ↔ Y          (Unicode alternative)
```

**Example:**

```text
parentOf : Person <-> Person
married : Person <-> Person
```

## Maplets

**Maplet notation:** `x |-> y` represents the ordered pair (x, y)

```text
{1 |-> 'a', 2 |-> 'b', 3 |-> 'c'}
```

**See:** `examples/07_relations/maplets.txt`

## Domain and Range

**Domain dom R:** Set of first components
**Range ran R:** Set of second components

```text
R = {1 |-> 'a', 2 |-> 'b', 3 |-> 'c'}
dom R = {1, 2, 3}
ran R = {'a', 'b', 'c'}
```

**See:** `examples/07_relations/domain_range.txt`, `examples/07_relations/range_examples.txt`

## Relation Operators

### Domain Restriction (|)

```text
S <| R        (restrict R to domain S)
```

**Example:**

```text
{1, 2} <| {1 |-> 'a', 2 |-> 'b', 3 |-> 'c'} = {1 |-> 'a', 2 |-> 'b'}
```

### Domain Subtraction

```text
S <-| R       (remove domain S from R)
```

### Range Restriction (|>)

```text
R |> T        (restrict R to range T)
```

### Range Subtraction

```text
R |>- T       (remove range T from R)
```

**See:** `examples/07_relations/restrictions.txt`

## Relational Composition

**Forward composition R o9 S:** Apply R then S

```text
R = {1 |-> 10, 2 |-> 20}
S = {10 |-> 100, 20 |-> 200}
R o9 S = {1 |-> 100, 2 |-> 200}
```

**Backward composition R o S:** Apply S then R (traditional math notation)

**See:** `examples/07_relations/relational_composition.txt`

## Relational Inverse

**R~ (R inverse):** Swap pairs

```text
R = {1 |-> 'a', 2 |-> 'b'}
R~ = {'a' |-> 1, 'b' |-> 2}
```

## Relational Image

**R(| S |):** Image of set S under relation R

```text
R = {1 |-> 'a', 2 |-> 'b', 3 |-> 'c'}
R(| {1, 2} |) = {'a', 'b'}
```

**See:** `examples/07_relations/relational_image.txt`

## Complete Example

```text
=== Relations Example ===

given Person

axdef
  parentOf : Person <-> Person
  grandparentOf : Person <-> Person
  siblings : Person <-> Person
where
  grandparentOf = parentOf o9 parentOf
  forall p, q : Person | (p, q) elem siblings <=>
    (exists parent : Person | (p, parent) elem parentOf land (q, parent) elem parentOf land p /= q)
end
```

## Summary

You've learned:

- ✅ Binary relations (X <-> Y)
- ✅ Maplet notation (|->)
- ✅ Domain and range (dom, ran)
- ✅ Restrictions (<|, <-|, |>, |>-)
- ✅ Composition (o9, o)
- ✅ Inverse (~)
- ✅ Relational image

**Next Tutorial:** [Tutorial 7: Functions](07_functions.md)

---

**Practice:** Explore `examples/07_relations/`
