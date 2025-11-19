# Lecture 7: Relations

This directory contains examples for Lecture 7, covering binary relations and their operations.

## Topics Covered

- Maplets (`|->`) - ordered pair constructor
- Relation types (`<->`)
- Domain and range (`dom`, `ran`)
- Domain and range restriction (`<|`, `|>`)
- Domain and range corestriction (`<<|`, `|>>`)
- Relational inverse (`~`, `inv`)
- Relational image (`(| ... |)`)
- Relational composition (`o9`, `comp`)
- Transitive and reflexive-transitive closures (`+`, `*`)

## Key Operators

```
x |-> y          →  x ↦ y       [maplet]
X <-> Y          →  X ↔ Y       [relation type]
dom R            →  dom R       [domain]
ran R            →  ran R       [range]
S <| R           →  S ◁ R       [domain restriction]
R |> T           →  R ▷ T       [range restriction]
S <<| R          →  S ⩤ R       [domain corestriction]
R |>> T          →  R ⩥ T       [range corestriction]
R~               →  R⁻¹         [inverse]
R(| S |)         →  R(⦇ S ⦈)    [relational image]
R o9 S           →  R ∘ S       [composition]
R+               →  R⁺          [transitive closure]
R*               →  R*          [reflexive-transitive closure]
```

## Important Notes

- Semicolon (`;`) is NOT used for composition - use `o9` or `comp`
- Composition `R o9 S` means "R then S": `(R o9 S)(x) = S(R(x))`
- Closure operators (`+`, `*`) are postfix operators

## Examples in This Directory

Browse the `.txt` files to see:
- Basic relation construction with maplets
- Domain and range operations
- Restriction and corestriction patterns
- Composition and closure usage
- Relational image applications

## See Also

- **docs/USER_GUIDE.md** - Section "Relations"
- **docs/TUTORIAL_07.md** - Detailed tutorial for Lecture 7
- **Previous**: 06_definitions/
- **Next**: 08_functions/
