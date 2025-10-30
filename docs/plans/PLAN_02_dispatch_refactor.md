## Plan 02: Replace isinstance Chains with Dispatch (Behavior-Preserving)

### Objective
Refactor expression generation to use a dispatch mechanism instead of long `isinstance` chains, preserving output exactly. Begin with `LaTeXGenerator.generate_expr` and reuse existing `_generate_*` methods.

### Approach
Prefer an internal registry-based dispatch to avoid decorator overhead and to keep method bindings explicit. Optionally evaluate `functools.singledispatch` later.

### Guardrails
- No change to LaTeX output strings (including whitespace)
- Keep all `_generate_*` methods intact; only change how they are selected
- Add tests for unknown-node error messages (exhaustiveness)

### Phased Steps

1) Introduce Internal Registry (No Behavior Change)
- Add `_expr_handlers: dict[type, callable]` as a private attribute in `LaTeXGenerator`
- Populate it in `__init__` mapping concrete AST types (e.g., `Identifier: _generate_identifier`)
- Keep the existing `if isinstance` chain intact and used

2) Add Lookup Helper
- Implement `_dispatch_expr(self, expr: Expr, parent: Expr | None) -> str` that resolves `type(expr)` in `_expr_handlers`, else raises the existing `TypeError`
- Add a temporary feature flag (`_use_dispatch = False`) to toggle dispatch

3) Shadow the Chain (Burn-in)
- In `generate_expr`, call the dispatch path first and assert it equals the chain result on a small random subset (only in tests if practical)
- Keep default path as the original chain for one commit

4) Switch Default to Dispatch
- Replace the chain body with a single call to `_dispatch_expr`
- Remove the feature flag; keep the chain code commented out for one commit window only if necessary, then delete

5) Extendability Hooks
- Add a public `register_expr_handler(self, node_type: type[Expr], handler: callable) -> None` primarily for tests/extensibility
- Document invariants (handler must be pure w.r.t. generator state except formatting flags)

6) Tests
- Add tests that ensure every known AST node type is registered (coverage-based or explicit list)
- Add tests that an unknown node type raises the same `TypeError` as before with unchanged message text
- Add golden-output tests for a representative set of documents to catch formatting regressions

### Optional: singledispatch Variant
- If desired later, implement `@singledispatchmethod` (Python 3.8+ via backport) or emulate via classmethod + registry to avoid decorator complexity
- Keep one approach (registry) to reduce surface area during this refactor

### Completion Criteria
- `generate_expr` uses dispatch
- All existing behavior and outputs identical (golden tests green)
- New handlers can be added without modifying `generate_expr`


