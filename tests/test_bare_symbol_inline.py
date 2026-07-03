r"""Phase 2a bare-symbol mode tests: lone whiteboard tokens inside $...$ spans.

A $...$ span whose stripped content is exactly one key from _BARE_SYMBOL emits
that symbol's LaTeX macro directly, bypassing the full expression parser.

Examples: $|->$ -> $\mapsto$, $forall$ -> $\forall$, $dom$ -> $\dom$.

These tests follow strict TDD sequence: written before the implementation,
confirmed failing, then confirmed passing after the change.
"""

from __future__ import annotations

import pytest

from txt2tex.codegen.text_pipeline import InlineMathError
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def _gen(source: str) -> str:
    """Parse source and return the generated LaTeX document body."""
    if not source.startswith("==="):
        source = "=== Test ===\n\n" + source
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    gen = LaTeXGenerator(use_fuzz=True)
    return gen.generate_document(doc)


class TestBareSymbolOperators:
    """Lone operator tokens emit their LaTeX macro, not the raw ASCII."""

    def test_maplet(self) -> None:
        r"""$|->$ emits $\mapsto$."""
        latex = _gen(r"TEXT: The maplet $|->$ symbol.")
        assert r"$\mapsto$" in latex

    def test_total_function(self) -> None:
        r"""$->$ emits $\fun$."""
        latex = _gen(r"TEXT: The function $->$ arrow.")
        assert r"$\fun$" in latex

    def test_relation(self) -> None:
        r"""$<->$ emits $\rel$ (not \leftrightarrow)."""
        latex = _gen(r"TEXT: The relation $<->$ type.")
        assert r"$\rel$" in latex
        assert r"\leftrightarrow" not in latex

    def test_semi(self) -> None:
        r"""$o9$ emits $\semi$ (not \comp)."""
        latex = _gen(r"TEXT: The composition $o9$ symbol.")
        assert r"$\semi$" in latex
        assert r"\comp" not in latex

    def test_iff(self) -> None:
        r"""$<=>$ emits $\Leftrightarrow$."""
        latex = _gen(r"TEXT: The biconditional $<=>$ symbol.")
        assert r"$\Leftrightarrow$" in latex

    def test_leq(self) -> None:
        r"""$<=$ emits $\leq$."""
        latex = _gen(r"TEXT: The ordering $<=$ symbol.")
        assert r"$\leq$" in latex

    def test_pfun(self) -> None:
        r"""$+->$ emits $\pfun$."""
        latex = _gen(r"TEXT: The partial function $+->$ symbol.")
        assert r"$\pfun$" in latex


class TestBareSymbolKeywords:
    """Lone keyword tokens emit their LaTeX macro."""

    def test_forall(self) -> None:
        r"""$forall$ emits $\forall$."""
        latex = _gen(r"TEXT: The quantifier $forall$ symbol.")
        assert r"$\forall$" in latex

    def test_exists1(self) -> None:
        r"""$exists1$ emits $\exists_1$."""
        latex = _gen(r"TEXT: The unique-existence $exists1$ symbol.")
        assert r"$\exists_1$" in latex

    def test_mu(self) -> None:
        r"""$mu$ emits $\mu$."""
        latex = _gen(r"TEXT: The definite description $mu$ symbol.")
        assert r"$\mu$" in latex

    def test_lambda(self) -> None:
        r"""$lambda$ emits $\lambda$."""
        latex = _gen(r"TEXT: The abstraction $lambda$ symbol.")
        assert r"$\lambda$" in latex

    def test_dom(self) -> None:
        r"""$dom$ emits $\dom$."""
        latex = _gen(r"TEXT: The domain $dom$ operator.")
        assert r"$\dom$" in latex

    def test_elem(self) -> None:
        r"""$elem$ emits $\in$."""
        latex = _gen(r"TEXT: The membership $elem$ symbol.")
        assert r"$\in$" in latex

    def test_emptyset(self) -> None:
        r"""$emptyset$ emits $\emptyset$."""
        latex = _gen(r"TEXT: The empty set $emptyset$ symbol.")
        assert r"$\emptyset$" in latex


class TestBareSymbolWhitespaceTolerance:
    """Interior whitespace is stripped before the table lookup."""

    def test_forall_with_spaces(self) -> None:
        r"""$ forall $ (interior spaces) emits $\forall$."""
        latex = _gen("TEXT: The quantifier $ forall $ symbol.")
        assert r"$\forall$" in latex

    def test_maplet_with_spaces(self) -> None:
        r"""$  |->  $ (interior spaces) emits $\mapsto$."""
        latex = _gen("TEXT: The maplet $  |->  $ symbol.")
        assert r"$\mapsto$" in latex


class TestBareSymbolSetminus:
    r"""A lone backslash inside $...$  emits $\setminus$."""

    def test_lone_backslash(self) -> None:
        r"""$\ $ (backslash + space) emits $\setminus$.

        Stripped inner content is a single backslash, which maps to \setminus.
        This short-circuits before the strict backslash check so there is no
        InlineMathError despite the backslash being present.
        """
        # r"TEXT: Set difference $\ $ here." — inner is "\ " (backslash+space),
        # stripped is a single backslash, which is the _BARE_SYMBOL key.
        latex = _gen(r"TEXT: Set difference $\ $ here.")
        assert r"$\setminus$" in latex


class TestBareSymbolNonInterference:
    """Bare-symbol mode is additive: full expressions still route through the parser."""

    def test_full_expression_nat_fun_nat(self) -> None:
        r"""$N -> N$ is a full expression; parser emits $\nat \fun \nat$."""
        latex = _gen("TEXT: The type $N -> N$.")
        assert r"\nat \fun \nat" in latex

    def test_full_expression_maplet_selection(self) -> None:
        r"""$p.a |-> p.b$ is a multi-token expression; parser emits p.a \mapsto p.b."""
        latex = _gen("TEXT: The pair $p.a |-> p.b$ is a maplet.")
        assert r"p.a \mapsto p.b" in latex

    def test_non_symbol_word_left_literal(self) -> None:
        r"""$hello$ is not in the bare-symbol table; parser emits it as a literal."""
        latex = _gen("TEXT: The word $hello$.")
        assert "$hello$" in latex

    def test_raw_latex_still_raises(self) -> None:
        r"""$\geq 0$ still raises InlineMathError: stripped content is not a table key.

        \geq 0 is not a single _BARE_SYMBOL key so execution falls through to
        the strict backslash check, which raises.
        """
        with pytest.raises(InlineMathError, match="whiteboard notation only"):
            _gen(r"TEXT: We need $\geq 0$ to hold.")

    def test_lone_raw_latex_command_still_raises(self) -> None:
        r"""$\forall$ (raw LaTeX) still raises; only "forall" (no backslash) maps."""
        with pytest.raises(InlineMathError, match="whiteboard notation only"):
            _gen(r"TEXT: A lone $\forall$ symbol appears.")
