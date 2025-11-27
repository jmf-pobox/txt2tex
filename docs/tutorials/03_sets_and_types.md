# Tutorial 3: Sets and Types

**Lecture 3: Set Theory**

Learn set notation, set operations, power sets, Cartesian products, and tuples.

**Prerequisites:** Tutorial 2 (Predicate Logic)  
**Examples:** `examples/05_sets/`

---

## Set Basics

**Set:** Unordered collection of distinct elements

**Notation:**
```
{1, 2, 3}              (set literal)
{x : N | x < 5}        (set comprehension)
emptyset               (empty set)
```

### Set Membership

```
x elem S               (x is a member of S)
x notin S              (x is not a member of S)
```

### Set Comprehension

```
{ x : T | constraint }
{ x : T | constraint . term }
```

**Example:**
```
{ x : N | x < 10 }                  (numbers less than 10)
{ x : N | x < 5 . x * x }           (squares of numbers less than 5)
```

**See:** `examples/05_sets/set_basics.txt`, `examples/03_equality/bullet_separator.txt`

## Set Operations

### Union (union)

```
A union B              (elements in A or B or both)
```

### Intersection (intersect)

```
A intersect B          (elements in both A and B)
```

### Difference (\)

```
A \ B                  (elements in A but not in B)
```

### Subset Relations

```
A subset B             (A ⊆ B: every element of A is in B)
A subseteq B           (same as subset)
A psubset B            (A ⊂ B: A ⊆ B and A ≠ B)
```

**See:** `examples/05_sets/set_operations.txt`, `examples/05_sets/strict_subset.txt`

## Power Set

**Power set P(S):** Set of all subsets of S

```
P {1, 2} = {{}, {1}, {2}, {1, 2}}
```

**Type notation:**
```
s : P N                (s is a set of natural numbers)
S : P (P N)            (S is a set of sets of natural numbers)
```

## Cartesian Product

**Cartesian product A × B:** Set of all ordered pairs (a, b) where a ∈ A and b ∈ B

**Notation:**
```
A cross B
N cross N              (pairs of natural numbers)
```

**Example:**
```
{1, 2} cross {a, b} = {(1, a), (1, b), (2, a), (2, b)}
```

**See:** `examples/05_sets/cartesian_tuples.txt`

## Tuples

**Tuple:** Ordered collection (can have duplicates, order matters)

**Notation:**
```
(1, 2)                 (pair)
(a, b, c)              (triple)
```

**Tuple projection:**
```
p.1                    (first element of pair p)
p.2                    (second element)
(a, b, c).2 = b        (second element of triple)
```

**See:** `examples/05_sets/tuple_examples.txt`

## Set Cardinality

**Cardinality #S:** Number of elements in a finite set

```
# {1, 2, 3} = 3
# {} = 0
```

## Complete Example

```
=== Set Theory Examples ===

** Example 1: Set Literals **

{1, 2, 3, 4, 5}

** Example 2: Set Comprehension **

{ x : N | x < 10 land x mod 2 = 0 }

TEXT: This is the set {0, 2, 4, 6, 8}.

** Example 3: Set Operations **

given A, B : P N

axdef
  A_union_B : P N
  A_intersect_B : P N
  A_diff_B : P N
where
  A = {1, 2, 3}
  B = {2, 3, 4}
  A_union_B = A union B
  A_intersect_B = A intersect B
  A_diff_B = A \ B
end

TEXT: Results: A ∪ B = {1,2,3,4}, A ∩ B = {2,3}, A \ B = {1}

** Example 4: Cartesian Product **

{1, 2} cross {a, b}

TEXT: Result: {(1,a), (1,b), (2,a), (2,b)}
```

## Summary

You've learned:
- ✅ Set notation and set comprehension
- ✅ Set operations (union, intersect, difference, subset)
- ✅ Power sets
- ✅ Cartesian products
- ✅ Tuples and tuple projection
- ✅ Set cardinality

**Next Tutorial:** [Tutorial 4: Proof Trees](docs/tutorials/04_proof_trees.md)

---

**Practice:** Explore `examples/05_sets/`
