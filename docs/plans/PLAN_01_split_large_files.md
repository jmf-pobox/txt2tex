## Plan 01: Split Large Files into Cohesive Modules (Behavior-Preserving)

### Objective
Reduce file size and improve maintainability by extracting cohesive modules from `parser.py` and `latex_gen.py` without changing behavior. All steps are formal refactorings: structure-only, identical observable behavior, tests remain green after each step.

### Target Structure

- `src/txt2tex/parser/`
  - `__init__.py` (re-exports public API)
  - `expressions.py` (core expression grammar, precedence)
  - `documents.py` (sections, solutions, parts, truth tables, paragraphs)
  - `quantifiers.py` (forall/exists/exists1/mu, continuations)
  - `postfix.py` (subscript, superscript, postfix ops)
  - `relations.py` (relations, sets, function types, images, projections)

- `src/txt2tex/latex_gen/`
  - `__init__.py` (re-exports public API)
  - `documents.py` (section/solution/part/proof/zed/schema/axdef/gendef)
  - `expressions.py` (identifiers, numbers, unary/binary, quantifiers, lambda)
  - `operators.py` (operator maps, fuzz-aware helpers)
  - `zed.py` (Zed-specific generation glue)

### Guardrails

- No signature changes; public classes/functions remain import-compatible
- Add thin forwarding wrappers as needed; remove only after stability
- Run `hatch run check` after each step; commit small, reversible edits

### Phased Steps

1) Introduce Packages (no code movement)
- Add empty packages with `__init__.py` that import nothing yet
- Add TODO-free comments indicating intent and linkage to this plan
- Verify `hatch run check` remains green

2) Extract Smallest, Self-Contained Generator Helpers
- Move `_generate_tuple`, `_generate_sequence_literal`, `_generate_range`, `_generate_tuple_projection`, `_generate_bag_literal` into `latex_gen/expressions.py`
- Keep `LaTeXGenerator` class in place; import moved helpers and call them
- Ensure identical rendering; run tests

3) Extract Document Generators
- Move `_generate_schema`, `_generate_axdef`, `_generate_gendef`, `_generate_zed`, `_generate_proof_tree` into `latex_gen/documents.py`
- Wire through the existing `LaTeXGenerator` methods by delegation
- Tests must remain identical (consider golden tests to guard whitespace)

4) Centralize Operator Maps and Fuzz Helpers
- Move operator dictionaries and fuzz-aware helpers into `latex_gen/operators.py`
- Replace scattered literals with imports from `operators`
- No logic change; verify both standard and fuzz paths remain identical

5) Parser: Extract Postfix/Relations
- Move postfix parsing cluster (`_parse_postfix`, subscript/superscript, images) to `parser/postfix.py`
- Move relation/set/function-type parsing cluster to `parser/relations.py`
- Keep method names; forward from original class methods to extracted functions

6) Parser: Extract Quantifiers and Documents
- Move quantifier parsing (`_parse_quantifier`, continuation helpers) to `parser/quantifiers.py`
- Move document and paragraph parsing to `parser/documents.py`
- Keep constructor and public `parse()` in `parser.py` for now

7) Parser: Extract Core Expressions
- Move precedence ladder (`_parse_iff`, `_parse_implies`, `_parse_and`, etc.) to `parser/expressions.py`
- Ensure shared utilities (lookahead, token matching) stay accessible

8) Stabilize Public API
- Create re-exports in `parser/__init__.py` and `latex_gen/__init__.py` so existing imports (`from txt2tex.parser import Parser`) continue to work
- Remove temporary forwarding wrappers only after a green burn-in

### Risk Mitigations
- Keep changes small and category-based; avoid interleaving parser and generator moves in a single commit
- Use ruff format before commits to minimize diff noise
- If a refactor causes subtle whitespace regressions, snapshot and compare outputs before proceeding

### Completion Criteria
- `parser.py` and `latex_gen.py` reduced to thin orchestration and class shells
- New packages own cohesive functionality
- All tests and coverage remain at prior levels; no behavior changes


