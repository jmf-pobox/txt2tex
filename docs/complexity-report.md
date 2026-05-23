# Complexity Report

_Generated 2026-05-23T09:43:45+00:00 at commit `eb7e1b2`._

This snapshot is produced by `make complexity-report` (see `scripts/complexity_report.py`).  It composes radon, lizard, pydeps, and wily into a point-in-time view of the codebase plus a trend window if a wily history exists.

## Maintainability Index (radon mi)

Lower = harder to maintain.  Grades: A ≥ 20, B 10–19, C < 10.

| File | MI | Grade |
|------|---:|:-----:|
| `src/txt2tex/parser.py` | 0.00 | C |
| `src/txt2tex/latex_gen.py` | 0.00 | C |
| `src/txt2tex/lexer.py` | 0.00 | C |
| `src/txt2tex/ast_nodes.py` | 30.57 | A |
| `src/txt2tex/cli.py` | 47.91 | A |
| `src/txt2tex/free_vars.py` | 53.22 | A |
| `src/txt2tex/repl.py` | 56.62 | A |
| `src/txt2tex/compile.py` | 60.84 | A |
| `src/txt2tex/errors.py` | 74.27 | A |
| `src/txt2tex/constants.py` | 100.00 | A |
| `src/txt2tex/__init__.py` | 100.00 | A |
| `src/txt2tex/__version__.py` | 100.00 | A |
| `src/txt2tex/tokens.py` | 100.00 | A |

## Cyclomatic Complexity ≥ D (radon cc)

Functions / methods with cyclomatic complexity grade D or worse.

| File | Line | Name | CC | Grade |
|------|-----:|------|---:|:-----:|
| `src/txt2tex/lexer.py` | 341 | `Lexer._scan_token` | 192 | F |
| `src/txt2tex/lexer.py` | 1037 | `Lexer._scan_identifier` | 138 | F |
| `src/txt2tex/latex_gen.py` | 5922 | `LaTeXGenerator._generate_proof_node_infer` | 37 | E |
| `src/txt2tex/parser.py` | 4093 | `Parser._parse_postfix` | 35 | E |
| `src/txt2tex/parser.py` | 3653 | `Parser._parse_cross` | 31 | E |
| `src/txt2tex/lexer.py` | 228 | `Lexer` | 31 | E |
| `src/txt2tex/parser.py` | 2413 | `Parser._parse_quantifier` | 30 | D |
| `src/txt2tex/parser.py` | 5044 | `Parser._parse_syntax_block` | 30 | D |
| `src/txt2tex/latex_gen.py` | 2715 | `LaTeXGenerator._generate_part` | 29 | D |
| `src/txt2tex/latex_gen.py` | 6177 | `LaTeXGenerator._generate_complex_assumption_scope` | 29 | D |
| `src/txt2tex/latex_gen.py` | 848 | `LaTeXGenerator._has_line_breaks_structural` | 28 | D |
| `src/txt2tex/parser.py` | 189 | `Parser.parse` | 26 | D |
| `src/txt2tex/parser.py` | 814 | `Parser._parse_document_item` | 26 | D |
| `src/txt2tex/free_vars.py` | 127 | `expr_free_vars` | 25 | D |
| `src/txt2tex/latex_gen.py` | 3698 | `LaTeXGenerator._convert_comparison_operators` | 25 | D |
| `src/txt2tex/parser.py` | 6098 | `Parser._parse_proof_node` | 24 | D |
| `src/txt2tex/parser.py` | 3202 | `Parser._parse_set_comprehension_from_brace` | 23 | D |
| `src/txt2tex/parser.py` | 4606 | `Parser._parse_atom` | 23 | D |
| `src/txt2tex/latex_gen.py` | 5621 | `LaTeXGenerator._generate_schema` | 23 | D |
| `src/txt2tex/parser.py` | 1291 | `Parser._parse_declaration_or_inclusion` | 22 | D |
| `src/txt2tex/cli.py` | 160 | `main` | 22 | D |
| `src/txt2tex/latex_gen.py` | 638 | `LaTeXGenerator.generate_document` | 22 | D |
| `src/txt2tex/latex_gen.py` | 1511 | `LaTeXGenerator._generate_logical_quantifier` | 22 | D |

## Lizard Warnings (CCN ≥ 20 or NLOC ≥ 100)

_340 function(s) exceed thresholds._

| File | Function | CCN | NLOC | Tokens | Params |
|------|----------|----:|-----:|-------:|-------:|
| `src/txt2tex/lexer.py` | `_scan_token` | 192 | 438 | 3373 | 1 |
| `src/txt2tex/lexer.py` | `_scan_token` | 192 | 438 | 3373 | 1 |
| `src/txt2tex/lexer.py` | `_scan_identifier` | 138 | 398 | 2433 | 3 |
| `src/txt2tex/lexer.py` | `_scan_identifier` | 138 | 398 | 2433 | 3 |
| `src/txt2tex/latex_gen.py` | `_generate_proof_node_infer` | 37 | 100 | 616 | 2 |
| `src/txt2tex/latex_gen.py` | `_generate_proof_node_infer` | 37 | 100 | 616 | 2 |
| `src/txt2tex/parser.py` | `_parse_postfix` | 35 | 178 | 862 | 2 |
| `src/txt2tex/parser.py` | `_parse_postfix` | 35 | 178 | 862 | 2 |
| `src/txt2tex/parser.py` | `_parse_quantifier` | 32 | 169 | 971 | 1 |
| `src/txt2tex/parser.py` | `_parse_quantifier` | 32 | 169 | 971 | 1 |
| `src/txt2tex/parser.py` | `_parse_cross` | 30 | 152 | 820 | 1 |
| `src/txt2tex/parser.py` | `_parse_cross` | 30 | 152 | 820 | 1 |
| `src/txt2tex/parser.py` | `_parse_syntax_block` | 30 | 96 | 575 | 1 |
| `src/txt2tex/parser.py` | `_parse_syntax_block` | 30 | 96 | 575 | 1 |
| `src/txt2tex/latex_gen.py` | `_generate_part` | 29 | 133 | 895 | 2 |
| `src/txt2tex/latex_gen.py` | `_generate_part` | 29 | 133 | 895 | 2 |
| `src/txt2tex/latex_gen.py` | `_generate_complex_assumption_scope` | 29 | 107 | 572 | 3 |
| `src/txt2tex/latex_gen.py` | `_generate_complex_assumption_scope` | 29 | 107 | 572 | 3 |
| `src/txt2tex/latex_gen.py` | `_has_line_breaks_structural` | 28 | 40 | 343 | 2 |
| `src/txt2tex/latex_gen.py` | `_has_line_breaks_structural` | 28 | 40 | 343 | 2 |

_…320 more not shown._

## Module Structure (pydeps)

| Module | Fan-in | Fan-out |
|--------|-------:|--------:|
| `txt2tex` | 8 | 2 |
| `txt2tex.__version__` | 3 | 0 |
| `txt2tex.ast_nodes` | 5 | 0 |
| `txt2tex.cli` | 1 | 7 |
| `txt2tex.compile` | 3 | 0 |
| `txt2tex.constants` | 3 | 0 |
| `txt2tex.errors` | 3 | 0 |
| `txt2tex.free_vars` | 2 | 2 |
| `txt2tex.latex_gen` | 3 | 7 |
| `txt2tex.lexer` | 4 | 2 |
| `txt2tex.parser` | 4 | 4 |
| `txt2tex.repl` | 2 | 7 |
| `txt2tex.tokens` | 3 | 0 |

## Recent Trend (wily)

_No wily history available.  Run `uv run wily build src/txt2tex --max-revisions 50` to seed the cache, then re-run this report._

---

_Generated by `scripts/complexity_report.py`.  Both `docs/complexity-report.md` and `docs/complexity-report.json` are committed so future runs can show deltas._
