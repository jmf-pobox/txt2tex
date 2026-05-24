# Schema Calculus Examples

Z RM §3.11 schema-calculus operators: composition, piping, hiding, and
projection.

## Files

- `composition.txt` — sequential schema composition with `;`
- `piping_hiding.txt` — schema piping with `>>` and hiding with `hide`

## Operators

| Source notation     | LaTeX         | Meaning                          |
|---------------------|---------------|----------------------------------|
| `S ; T`             | `S \semi T`   | Compose: chain S output to T     |
| `S >> T`            | `S \pipe T`   | Pipe: connect S output channel to T input |
| `S hide (x, y)`     | `S \hide (x, y)` | Hide components x and y       |
| `S project T`       | `S \project T` | Project S onto T's signature    |

## Precedence (tightest to loosest)

1. `hide` and `project`
2. `;` (composition)
3. `>>` (piping)

Example: `S hide (x) ; T >> U` = `((S hide (x)) ; T) >> U`
