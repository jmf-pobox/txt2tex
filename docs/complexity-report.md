# Complexity Report

_Generated 2026-05-25T08:52:21+00:00 at commit `6a31c21`._

This snapshot is produced by `make complexity-report` (see `scripts/complexity_report.py`).  It composes radon, lizard, pydeps, and wily into a point-in-time view of the codebase plus a trend window if a wily history exists.

## Maintainability Index (radon mi)

Lower = harder to maintain.  Grades: A >= 20, B 10-19, C < 10.

| File | MI | Grade |
|------|---:|:-----:|
| `src/txt2tex/lexer.py` | 0.00 | C |
| `src/txt2tex/parser_pkg/expressions.py` | 0.00 | C |
| `src/txt2tex/codegen/text_pipeline.py` | 11.90 | B |
| `src/txt2tex/codegen/expressions.py` | 22.11 | A |
| `src/txt2tex/codegen/proofs.py` | 27.89 | A |
| `src/txt2tex/ast_nodes.py` | 29.32 | A |
| `src/txt2tex/parser.py` | 33.93 | A |
| `src/txt2tex/latex_gen.py` | 38.89 | A |
| `src/txt2tex/parser_pkg/text_blocks.py` | 39.60 | A |
| `src/txt2tex/parser_pkg/paragraphs.py` | 40.65 | A |
| `src/txt2tex/parser_pkg/proofs.py` | 41.92 | A |
| `src/txt2tex/codegen/paragraphs.py` | 45.55 | A |
| `src/txt2tex/parser_pkg/schemas.py` | 45.91 | A |
| `src/txt2tex/codegen/text_blocks.py` | 47.11 | A |
| `src/txt2tex/cli.py` | 47.60 | A |
| `src/txt2tex/parser_pkg/algebra.py` | 51.04 | A |
| `src/txt2tex/free_vars.py` | 54.21 | A |
| `src/txt2tex/repl.py` | 56.62 | A |
| `src/txt2tex/codegen/schemas.py` | 57.64 | A |
| `src/txt2tex/compile.py` | 60.84 | A |
| `src/txt2tex/codegen/paren_policy.py` | 67.10 | A |
| `src/txt2tex/parser_pkg/lexer_state.py` | 68.07 | A |
| `src/txt2tex/errors.py` | 74.27 | A |
| `src/txt2tex/codegen/algebra.py` | 74.99 | A |
| `src/txt2tex/parser_pkg/types.py` | 77.76 | A |
| `src/txt2tex/codegen/overflow.py` | 78.70 | A |
| `src/txt2tex/codegen/types.py` | 82.20 | A |
| `src/txt2tex/codegen/fuzz_routing.py` | 91.61 | A |
| `src/txt2tex/codegen/bindings.py` | 92.32 | A |
| `src/txt2tex/parser_pkg/errors.py` | 93.86 | A |
| `src/txt2tex/constants.py` | 100.00 | A |
| `src/txt2tex/__init__.py` | 100.00 | A |
| `src/txt2tex/__version__.py` | 100.00 | A |
| `src/txt2tex/tokens.py` | 100.00 | A |
| `src/txt2tex/parser_pkg/_base.py` | 100.00 | A |
| `src/txt2tex/parser_pkg/__init__.py` | 100.00 | A |
| `src/txt2tex/codegen/__init__.py` | 100.00 | A |
| `src/txt2tex/codegen/_dispatch.py` | 100.00 | A |
| `src/txt2tex/codegen/_smoke.py` | 100.00 | A |

## Cyclomatic Complexity ≥ D (radon cc)

Functions / methods with cyclomatic complexity grade D or worse.

| File | Line | Name | CC | Grade |
|------|-----:|------|---:|:-----:|
| `src/txt2tex/lexer.py` | 339 | `Lexer._scan_token` | 192 | F |
| `src/txt2tex/lexer.py` | 1035 | `Lexer._scan_identifier` | 138 | F |
| `src/txt2tex/parser_pkg/expressions.py` | 2084 | `_ExpressionsParser._parse_postfix` | 43 | F |
| `src/txt2tex/codegen/proofs.py` | 308 | `_ProofsCodegen._generate_proof_node_infer` | 37 | E |
| `src/txt2tex/lexer.py` | 226 | `Lexer` | 31 | E |
| `src/txt2tex/parser_pkg/expressions.py` | 1812 | `_ExpressionsParser._parse_cross` | 31 | E |
| `src/txt2tex/parser_pkg/paragraphs.py` | 184 | `_ParagraphsParser._parse_syntax_block` | 30 | D |
| `src/txt2tex/parser_pkg/expressions.py` | 607 | `_ExpressionsParser._parse_quantifier` | 30 | D |
| `src/txt2tex/codegen/text_blocks.py` | 80 | `_TextBlocksCodegen._generate_part` | 29 | D |
| `src/txt2tex/codegen/proofs.py` | 563 | `_ProofsCodegen._generate_complex_assumption_scope` | 29 | D |
| `src/txt2tex/latex_gen.py` | 543 | `LaTeXGenerator._has_line_breaks_structural` | 28 | D |
| `src/txt2tex/parser.py` | 143 | `Parser.parse` | 26 | D |
| `src/txt2tex/parser.py` | 449 | `Parser._parse_document_item` | 26 | D |
| `src/txt2tex/free_vars.py` | 134 | `expr_free_vars` | 25 | D |
| `src/txt2tex/codegen/text_pipeline.py` | 697 | `_TextPipelineCodegen._convert_comparison_operators` | 25 | D |
| `src/txt2tex/parser_pkg/proofs.py` | 342 | `_ProofsParser._parse_proof_node` | 24 | D |
| `src/txt2tex/parser_pkg/expressions.py` | 1396 | `_ExpressionsParser._parse_set_comprehension_from_brace` | 23 | D |
| `src/txt2tex/codegen/schemas.py` | 161 | `_SchemasCodegen._generate_schema` | 23 | D |
| `src/txt2tex/parser.py` | 667 | `Parser._parse_declaration_or_inclusion` | 22 | D |
| `src/txt2tex/cli.py` | 161 | `main` | 22 | D |
| `src/txt2tex/latex_gen.py` | 374 | `LaTeXGenerator.generate_document` | 22 | D |
| `src/txt2tex/parser_pkg/expressions.py` | 2480 | `_ExpressionsParser._parse_atom` | 22 | D |
| `src/txt2tex/codegen/expressions.py` | 475 | `_ExpressionsCodegen._generate_logical_quantifier` | 22 | D |

## Lizard Warnings (CCN ≥ 20 or NLOC ≥ 100)

_26 function(s) exceed thresholds._

| File | Function | CCN | NLOC | Tokens | Params |
|------|----------|----:|-----:|-------:|-------:|
| `src/txt2tex/lexer.py` | `_scan_token` | 192 | 438 | 3373 | 1 |
| `src/txt2tex/lexer.py` | `_scan_identifier` | 138 | 398 | 2433 | 3 |
| `src/txt2tex/parser_pkg/expressions.py` | `_parse_postfix` | 43 | 190 | 949 | 2 |
| `src/txt2tex/codegen/proofs.py` | `_generate_proof_node_infer` | 37 | 100 | 616 | 2 |
| `src/txt2tex/parser_pkg/expressions.py` | `_parse_quantifier` | 32 | 169 | 971 | 1 |
| `src/txt2tex/parser_pkg/expressions.py` | `_parse_cross` | 32 | 162 | 858 | 1 |
| `src/txt2tex/parser_pkg/paragraphs.py` | `_parse_syntax_block` | 30 | 96 | 575 | 1 |
| `src/txt2tex/codegen/text_blocks.py` | `_generate_part` | 29 | 133 | 895 | 2 |
| `src/txt2tex/codegen/proofs.py` | `_generate_complex_assumption_scope` | 29 | 107 | 572 | 3 |
| `src/txt2tex/latex_gen.py` | `_has_line_breaks_structural` | 28 | 40 | 343 | 2 |
| `src/txt2tex/parser.py` | `parse` | 26 | 170 | 875 | 1 |
| `src/txt2tex/parser_pkg/expressions.py` | `_parse_set_comprehension_from_brace` | 26 | 106 | 636 | 1 |
| `src/txt2tex/parser.py` | `_parse_document_item` | 26 | 52 | 420 | 1 |
| `src/txt2tex/free_vars.py` | `expr_free_vars` | 25 | 67 | 529 | 1 |
| `src/txt2tex/codegen/text_pipeline.py` | `_convert_comparison_operators` | 25 | 49 | 348 | 2 |
| `src/txt2tex/codegen/schemas.py` | `_generate_schema` | 24 | 91 | 525 | 2 |
| `src/txt2tex/parser_pkg/proofs.py` | `_parse_proof_node` | 24 | 84 | 531 | 3 |
| `src/txt2tex/cli.py` | `main` | 22 | 159 | 702 | 0 |
| `src/txt2tex/parser_pkg/expressions.py` | `_parse_atom` | 22 | 130 | 709 | 1 |
| `src/txt2tex/parser.py` | `_parse_declaration_or_inclusion` | 22 | 120 | 644 | 1 |

_…6 more not shown._

## Module Structure (pydeps)

| Module | Fan-in | Fan-out |
|--------|-------:|--------:|
| `txt2tex` | 34 | 2 |
| `txt2tex.__version__` | 4 | 0 |
| `txt2tex.ast_nodes` | 25 | 0 |
| `txt2tex.cli` | 1 | 8 |
| `txt2tex.codegen` | 16 | 15 |
| `txt2tex.codegen._dispatch` | 15 | 2 |
| `txt2tex.codegen._smoke` | 3 | 3 |
| `txt2tex.codegen.algebra` | 3 | 4 |
| `txt2tex.codegen.bindings` | 3 | 4 |
| `txt2tex.codegen.expressions` | 3 | 5 |
| `txt2tex.codegen.fuzz_routing` | 3 | 4 |
| `txt2tex.codegen.overflow` | 3 | 3 |
| `txt2tex.codegen.paragraphs` | 3 | 4 |
| `txt2tex.codegen.paren_policy` | 3 | 4 |
| `txt2tex.codegen.proofs` | 3 | 4 |
| `txt2tex.codegen.schemas` | 3 | 4 |
| `txt2tex.codegen.text_blocks` | 3 | 4 |
| `txt2tex.codegen.text_pipeline` | 3 | 7 |
| `txt2tex.codegen.types` | 3 | 4 |
| `txt2tex.compile` | 3 | 0 |
| `txt2tex.constants` | 3 | 0 |
| `txt2tex.errors` | 3 | 0 |
| `txt2tex.free_vars` | 2 | 2 |
| `txt2tex.latex_gen` | 3 | 18 |
| `txt2tex.lexer` | 4 | 2 |
| `txt2tex.parser` | 4 | 14 |
| `txt2tex.parser_pkg` | 12 | 11 |
| `txt2tex.parser_pkg._base` | 11 | 3 |
| `txt2tex.parser_pkg.algebra` | 3 | 5 |
| `txt2tex.parser_pkg.errors` | 3 | 4 |
| `txt2tex.parser_pkg.expressions` | 3 | 6 |
| `txt2tex.parser_pkg.lexer_state` | 3 | 4 |
| `txt2tex.parser_pkg.paragraphs` | 3 | 5 |
| `txt2tex.parser_pkg.proofs` | 3 | 5 |
| `txt2tex.parser_pkg.schemas` | 3 | 5 |
| `txt2tex.parser_pkg.text_blocks` | 3 | 5 |
| `txt2tex.parser_pkg.types` | 3 | 5 |
| `txt2tex.repl` | 2 | 7 |
| `txt2tex.tokens` | 13 | 0 |

## Recent Trend (wily)

LoC and cyclomatic complexity at the **oldest** and **newest** revisions in the wily window.  Files with zero net change in both metrics are omitted.

| File | Oldest commit | Oldest LoC | Oldest CC | Newest commit | Newest LoC | Newest CC | LoC d | CC d |
|------|--------------|-----------:|----------:|---------------|-----------:|----------:|------:|-----:|
| `src/txt2tex/latex_gen.py` | `0606052` (2026-05-19) | 5802 | 771 | `3b80a19` (2026-05-22) | 6815 | 868 | +1013 | +97 |
| `src/txt2tex/parser.py` | `c62874b` (2026-05-19) | 5425 | 794 | `17e0be0` (2026-05-22) | 6280 | 912 | +855 | +118 |
| `src/txt2tex/ast_nodes.py` | `c62874b` (2026-05-19) | 1230 | 69 | `3b80a19` (2026-05-22) | 1427 | 80 | +197 | +11 |
| `src/txt2tex/lexer.py` | `c62874b` (2026-05-19) | 1441 | 346 | `772861d` (2026-05-22) | 1635 | 394 | +194 | +48 |
| `src/txt2tex/tokens.py` | `c62874b` (2026-05-19) | 222 | 4 | `3b80a19` (2026-05-22) | 239 | 4 | +17 | +0 |
| `src/txt2tex/free_vars.py` | `92823b7` (2026-05-20) | 212 | 42 | `17e0be0` (2026-05-22) | 214 | 41 | +2 | -1 |

## Delta vs Prior Snapshot

Prior snapshot: 2026-05-23T09:54:44+00:00 @ `5ef7054`

**MI shifts (Δ ≥ 0.5):**
  src/txt2tex/ast_nodes.py: MI 30.57 -> 29.32 (↓1.25)
  src/txt2tex/parser.py: MI 0.00 -> 33.93 (↑33.93)
  src/txt2tex/latex_gen.py: MI 0.00 -> 38.89 (↑38.89)
  src/txt2tex/free_vars.py: MI 53.22 -> 54.21 (↑0.99)

  D-or-worse functions: 23 → 23
  Lizard warnings: 26 → 26

---

_Generated by `scripts/complexity_report.py`.  Both `docs/complexity-report.md` and `docs/complexity-report.json` are committed so future runs can show deltas._
