# State-Based Modeling

The discipline of describing a software system as a state space, an
initial state, and operations that transform state while preserving an
invariant.

## Languages

- **Z** — typed set theory and predicate logic. Schemas as the unit of
  composition. The reference notation for txt2tex output. Standard:
  Spivey's *Z Reference Manual* 2nd ed.
- **B / Event-B** — abstract machines, refinement, proof obligations.
  Abrial's tradition. Companion to Z; B operations have a more
  imperative shape, refinement is more central.
- **VDM** — Vienna Development Method. Predates Z; similar
  state+invariant+operations split.
- **TLA+** — Lamport. Temporal logic over state predicates. Different
  flavor; relevant for distributed/reactive systems.

## Core constructs

- **Carrier sets and given types** — the universe the model is built
  in. `[NAME, ID]` in Z; `SETS` in B.
- **State schema / abstract machine** — declared variables and the
  invariant they jointly satisfy.
- **Initialization** — a state predicate establishing the invariant.
- **Operations** — schemas (Z) or events (B) that transform state and
  re-establish the invariant. Δ-schemas mark mutation; Ξ-schemas mark
  query.
- **Promotion** — composing local state operations into operations on a
  global state indexed by some key set.
- **Schema calculus** — composition (`;`), piping (`>>`), conjunction
  (`∧`), disjunction (`∨`), hiding (`\`), projection.
- **Refinement** — replacing an abstract model with a concrete one,
  with proof that observable behavior is preserved (forward simulation).

## Tools

- **fuzz** — Z type checker. Mike Spivey's tool, the project's primary
  validation gate. The `argue` environment for equational reasoning;
  the `axdef`, `schema`, `gendef`, `zed`, `syntax` environments.
- **ProB** — animation and model checking for Z and B. Bounded
  verification. Useful for finding small counterexamples to invariants.
- **Atelier B / Rodin** — proof environments for B and Event-B
  respectively. Discharge proof obligations interactively or via
  automated provers.
- **Lean 4** — when proof obligations need a richer logic; the
  `z-spec` plugin in this environment generates Lean obligations.

## Method

The Abrial discipline:

1. **Carrier sets first.** What objects exist? Name them.
2. **Constants and properties.** What is fixed? What relationships
   hold among the constants?
3. **State variables and invariant.** What changes over time? What
   property must always hold among the state variables?
4. **Initialization.** A state satisfying the invariant.
5. **Operations, one at a time.** Each operation must establish the
   invariant from any state where its precondition holds. State the
   precondition. State the effect. Discharge the obligation.
6. **Refinement only after the abstract model is settled.** Concrete
   data structures are projections of abstract sets and relations;
   they introduce new proof obligations (gluing invariant, simulation).

## Anti-patterns

- Mixing abstract and concrete state in the same machine. Refinement
  exists to keep them separate.
- Operations that modify state without restating the invariant they
  preserve. The whole point of the discipline is the invariant.
- Treating a Z document as documentation rather than a typed artefact.
  If it does not type-check with fuzz, it is not Z — it is prose
  decorated with mathematical symbols.
- Reaching for a temporal logic when a state-and-invariant model
  suffices. TLA+ pays for itself when behavior unfolds over time;
  for a sequential specification, Z or B is lighter.

## Relevance to txt2tex

txt2tex generates LaTeX that fuzz must accept. Every feature added to
the lexer, parser, or generator should be evaluated against:

- *Does this map to a defined Z construct in the standard?*
- *Will fuzz type-check the output?*
- *What is the smallest model that exercises the feature?*

When the answer to the first is no, the feature is a notational
convenience for Jim's whiteboard; document it as such and ensure the
LaTeX it emits is still well-typed Z.
