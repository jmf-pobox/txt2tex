# 17_state_machines

State machine specifications using the canonical Z four-piece layout.

## What this directory shows

Every Z state machine follows the same four-piece structure. Once you
know the pattern, you can read (or write) any state machine specification
immediately.

| Piece | Role | Z keyword |
|---|---|---|
| State schema | variables + invariant | `schema S` |
| Init schema | initial configuration | bare `S'` inclusion |
| Delta operations | state-changing ops | `Delta S` |
| Xi queries | read-only observers | `Xi S` |

## Examples

### `turnstile.txt` — Turnstile

A gate that alternates between `locked` and `unlocked`.

**Carrier type** — `Gate ::= locked | unlocked`

**State schema** (`TurnstileState`) — two variables: `gate : Gate` and
`passed : N`. The invariant asserts `passed >= 0`.

**Init schema** (`TurnstileInit`) — bare inclusion of `TurnstileState'`
(the after-state signature) with predicates `gate' = locked` and
`passed' = 0`.

**Delta operations**:

- `Coin` — coin accepted when locked; gate transitions to unlocked.
  Passage count unchanged.
- `Push` — bar pushed when unlocked; gate relocks, `passed` increments,
  output `result!` carries the new count.

**Xi query** (`IsLocked`) — returns `status! : Gate` equal to the current
`gate` value. `Xi TurnstileState` guarantees no state mutation.

### Features exercised

- `Delta S` / `Xi S` schema inclusion
- `'` (prime) after-state decoration on variables and schema names
- `?` input and `!` output identifier decoration
- `theta`-style Init (bare `State'` inclusion with predicates)
- Free type with named constructors

## Build

```bash
# From project root
uv run txt2tex examples/17_state_machines/turnstile.txt
```

Or from the examples directory:

```bash
cd examples
make 17_state_machines/turnstile.pdf
```
