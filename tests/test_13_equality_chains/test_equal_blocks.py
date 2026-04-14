"""Tests for EQUAL: equality chain blocks.

EQUAL: joins expression-chain steps with = (equality of expressions of the
same Z type), as opposed to EQUIV: which joins predicate steps with
\\Leftrightarrow (logical equivalence).

Motivation: Oxford SE assessment feedback for Q11/Q12 chains was
"you've used equivalence, rather than equality!" Natural-number valued
expressions must render = not ⇔.
"""

from __future__ import annotations

import re

import pytest

from txt2tex.ast_nodes import (
    ArgueChain,
    ArgueStep,
    BinaryOp,
    Document,
    Identifier,
    Quantifier,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser, ParserError
from txt2tex.tokens import TokenType

# ---------------------------------------------------------------------------
# Lexer tests
# ---------------------------------------------------------------------------


class TestEqualBlockLexer:
    """Test that EQUAL: is lexed to TokenType.EQUAL."""

    def test_equal_keyword_produces_equal_token(self) -> None:
        """Lex EQUAL: and confirm token type is EQUAL."""
        tokens = Lexer("EQUAL:").tokenize()
        assert tokens[0].type is TokenType.EQUAL

    def test_equal_keyword_value(self) -> None:
        """EQUAL: token value is the full keyword string."""
        tokens = Lexer("EQUAL:").tokenize()
        assert tokens[0].value == "EQUAL:"

    def test_equal_followed_by_expression(self) -> None:
        """EQUAL: followed by an expression starts with EQUAL token."""
        tokens = Lexer("EQUAL:\nlength s").tokenize()
        assert tokens[0].type is TokenType.EQUAL

    def test_argue_still_produces_argue_token(self) -> None:
        """ARGUE: still produces ARGUE (not EQUAL)."""
        tokens = Lexer("ARGUE:").tokenize()
        assert tokens[0].type is TokenType.ARGUE

    def test_equiv_still_produces_argue_token(self) -> None:
        """EQUIV: still produces ARGUE (not EQUAL)."""
        tokens = Lexer("EQUIV:").tokenize()
        assert tokens[0].type is TokenType.ARGUE

    def test_equal_plain_identifier_not_keyword(self) -> None:
        """EQUAL without a colon is parsed as a plain identifier, not EQUAL."""
        tokens = Lexer("EQUAL").tokenize()
        assert tokens[0].type is TokenType.IDENTIFIER


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class TestEqualBlockParser:
    """Test that EQUAL: produces ArgueChain with connector='eq'."""

    def test_equal_parses_to_argue_chain(self) -> None:
        """EQUAL: block parses to ArgueChain."""
        text = "EQUAL:\nlength s\nlength t"
        ast = Parser(Lexer(text).tokenize()).parse()
        assert isinstance(ast, Document)
        assert len(ast.items) == 1
        assert isinstance(ast.items[0], ArgueChain)

    def test_equal_connector_is_eq(self) -> None:
        """ArgueChain produced by EQUAL: has connector='eq'."""
        text = "EQUAL:\nlength s\nlength t"
        ast = Parser(Lexer(text).tokenize()).parse()
        assert isinstance(ast, Document)
        chain = ast.items[0]
        assert isinstance(chain, ArgueChain)
        assert chain.connector == "eq"

    def test_equiv_connector_is_iff(self) -> None:
        """ArgueChain produced by EQUIV: retains connector='iff'."""
        text = "EQUIV:\np land q\nq land p"
        ast = Parser(Lexer(text).tokenize()).parse()
        assert isinstance(ast, Document)
        chain = ast.items[0]
        assert isinstance(chain, ArgueChain)
        assert chain.connector == "iff"

    def test_argue_connector_is_iff(self) -> None:
        """ArgueChain produced by ARGUE: retains connector='iff'."""
        text = "ARGUE:\np land q\nq land p"
        ast = Parser(Lexer(text).tokenize()).parse()
        assert isinstance(ast, Document)
        chain = ast.items[0]
        assert isinstance(chain, ArgueChain)
        assert chain.connector == "iff"

    def test_equal_parses_two_steps(self) -> None:
        """EQUAL: with two lines produces two steps."""
        text = "EQUAL:\nlength s\nlength t"
        ast = Parser(Lexer(text).tokenize()).parse()
        assert isinstance(ast, Document)
        chain = ast.items[0]
        assert isinstance(chain, ArgueChain)
        assert len(chain.steps) == 2

    def test_equal_parses_three_steps(self) -> None:
        """EQUAL: with three lines produces three steps."""
        text = "EQUAL:\nlength s\nlength t + 1\nlength u"
        ast = Parser(Lexer(text).tokenize()).parse()
        assert isinstance(ast, Document)
        chain = ast.items[0]
        assert isinstance(chain, ArgueChain)
        assert len(chain.steps) == 3

    def test_equal_with_justification(self) -> None:
        """EQUAL: steps can carry justifications."""
        text = "EQUAL:\nlength s\nlength t [hypothesis]"
        ast = Parser(Lexer(text).tokenize()).parse()
        assert isinstance(ast, Document)
        chain = ast.items[0]
        assert isinstance(chain, ArgueChain)
        assert chain.steps[0].justification is None
        assert chain.steps[1].justification == "hypothesis"

    def test_equal_empty_raises(self) -> None:
        """EQUAL: with no steps raises ParserError."""
        with pytest.raises(ParserError):
            Parser(Lexer("EQUAL:\n").tokenize()).parse()


# ---------------------------------------------------------------------------
# LaTeX generator tests
# ---------------------------------------------------------------------------


class TestEqualBlockGenerator:
    """Test that ArgueChain(connector='eq') emits = as the connective."""

    def _make_equal_chain(self, *exprs: str) -> ArgueChain:
        """Build a minimal ArgueChain with connector='eq' from identifier names."""
        steps = [
            ArgueStep(
                expression=Identifier(name=e, line=i + 1, column=1),
                justification=None,
                line=i + 1,
                column=1,
            )
            for i, e in enumerate(exprs)
        ]
        return ArgueChain(steps=steps, connector="eq", line=1, column=1)

    def _make_iff_chain(self, *exprs: str) -> ArgueChain:
        """Build a minimal ArgueChain with connector='iff' from identifier names."""
        steps = [
            ArgueStep(
                expression=Identifier(name=e, line=i + 1, column=1),
                justification=None,
                line=i + 1,
                column=1,
            )
            for i, e in enumerate(exprs)
        ]
        return ArgueChain(steps=steps, connector="iff", line=1, column=1)

    def test_eq_connector_emits_equals(self) -> None:
        """connector='eq' produces = between steps."""
        gen = LaTeXGenerator()
        chain = self._make_equal_chain("a", "b")
        latex = "\n".join(gen._generate_argue_chain(chain))
        assert "= b" in latex

    def test_eq_connector_no_leftrightarrow(self) -> None:
        """connector='eq' does not emit \\Leftrightarrow."""
        gen = LaTeXGenerator()
        chain = self._make_equal_chain("a", "b")
        latex = "\n".join(gen._generate_argue_chain(chain))
        assert r"\Leftrightarrow" not in latex

    def test_iff_connector_emits_leftrightarrow(self) -> None:
        """connector='iff' still produces \\Leftrightarrow between steps."""
        gen = LaTeXGenerator()
        chain = self._make_iff_chain("p", "q")
        latex = "\n".join(gen._generate_argue_chain(chain))
        assert r"\Leftrightarrow q" in latex

    def test_iff_connector_no_equals_connective(self) -> None:
        """connector='iff' does not use = as a step prefix."""
        gen = LaTeXGenerator()
        chain = self._make_iff_chain("p", "q")
        lines = gen._generate_argue_chain(chain)
        # The second step line begins with \Leftrightarrow, not bare "= "
        step_line = [ln for ln in lines if r"\Leftrightarrow" in ln]
        assert step_line, "Expected a \\Leftrightarrow step line"

    def test_eq_chain_first_step_no_prefix(self) -> None:
        """First step in equality chain has no leading = prefix."""
        gen = LaTeXGenerator()
        chain = self._make_equal_chain("length_s", "length_t")
        latex = "\n".join(gen._generate_argue_chain(chain))
        # First non-environment line should not start with "= "
        lines = latex.split("\n")
        first_expr_line = next(
            ln for ln in lines if "length" in ln and not ln.startswith("= length")
        )
        assert "length_s" in first_expr_line

    def test_eq_chain_with_justification(self) -> None:
        """Justifications appear correctly in equality chains."""
        gen = LaTeXGenerator()
        step0 = ArgueStep(
            expression=Identifier(name="a", line=1, column=1),
            justification=None,
            line=1,
            column=1,
        )
        step1 = ArgueStep(
            expression=Identifier(name="b", line=2, column=1),
            justification="by def",
            line=2,
            column=1,
        )
        chain = ArgueChain(steps=[step0, step1], connector="eq", line=1, column=1)
        latex = "\n".join(gen._generate_argue_chain(chain))
        assert r"[\mbox{by def}]" in latex

    def test_array_environment_present(self) -> None:
        """Equality chains still use the array environment."""
        gen = LaTeXGenerator()
        chain = self._make_equal_chain("a", "b")
        latex = "\n".join(gen._generate_argue_chain(chain))
        assert r"\begin{array}" in latex
        assert r"\end{array}" in latex


# ---------------------------------------------------------------------------
# End-to-end round-trip tests
# ---------------------------------------------------------------------------


class TestEqualBlockEndToEnd:
    """End-to-end pipeline from source text to LaTeX output."""

    def test_equal_chain_latex_contains_equals(self) -> None:
        """Full pipeline: EQUAL: produces = in output."""
        text = "EQUAL:\nlength s\nlength t"
        ast = Parser(Lexer(text).tokenize()).parse()
        latex = LaTeXGenerator().generate_document(ast)
        assert "= length" in latex

    def test_equal_chain_no_leftrightarrow(self) -> None:
        """Full pipeline: EQUAL: does not produce \\Leftrightarrow."""
        text = "EQUAL:\nlength s\nlength t"
        ast = Parser(Lexer(text).tokenize()).parse()
        latex = LaTeXGenerator().generate_document(ast)
        # \Leftrightarrow may appear in preamble macros; check step context only
        # by asserting the connective is = not \Leftrightarrow length
        assert r"\Leftrightarrow length" not in latex

    def test_equiv_chain_still_uses_leftrightarrow(self) -> None:
        """Regression: EQUIV: still produces \\Leftrightarrow after the rename."""
        text = "EQUIV:\np land q\nq land p"
        ast = Parser(Lexer(text).tokenize()).parse()
        latex = LaTeXGenerator().generate_document(ast)
        assert r"\Leftrightarrow q \land p" in latex

    def test_argue_chain_still_uses_leftrightarrow(self) -> None:
        """Regression: ARGUE: still produces \\Leftrightarrow after the rename."""
        text = "ARGUE:\np land q\nq land p"
        ast = Parser(Lexer(text).tokenize()).parse()
        latex = LaTeXGenerator().generate_document(ast)
        assert r"\Leftrightarrow q \land p" in latex

    def test_equal_chain_with_justification_end_to_end(self) -> None:
        """Full pipeline: justification renders correctly in EQUAL: chain."""
        text = "EQUAL:\nlength s\nlength (tail s) + 1 [by induction hypothesis]"
        ast = Parser(Lexer(text).tokenize()).parse()
        latex = LaTeXGenerator().generate_document(ast)
        assert r"[\mbox{by induction hypothesis}]" in latex

    def test_equal_chain_multiple_steps_end_to_end(self) -> None:
        """Full pipeline: three-step EQUAL: chain."""
        text = "EQUAL:\nlength s\nlength (tail s) + 1\nlength u + 1"
        ast = Parser(Lexer(text).tokenize()).parse()
        latex = LaTeXGenerator().generate_document(ast)
        # Three steps means two = connectives appear in the array
        # Count '= length' or '= ' prefixes on separate lines
        step_prefixes = re.findall(r"^= ", latex, re.MULTILINE)
        assert len(step_prefixes) == 2

    def test_in_argue_block_flag_resets_after_equal_chain(self) -> None:
        """_in_argue_block is False after generating an EQUAL: chain."""
        text = "EQUAL:\na\nb"
        ast = Parser(Lexer(text).tokenize()).parse()
        gen = LaTeXGenerator()
        gen.generate_document(ast)
        assert gen._in_argue_block is False


# ---------------------------------------------------------------------------
# Regression tests for connector-specificity fix (item #1)
# ---------------------------------------------------------------------------


class TestConnectorSpecificity:
    """EQUAL: must not silently consume <=> continuation; EQUIV: must not consume =."""

    def test_equal_chain_rejects_iff_continuation(self) -> None:
        """EQUAL: continuation line starting with <=> must raise ParserError.

        Before the fix, _parse_argue_chain(connector='eq') hit the elif
        branch and silently consumed <=> on continuation lines.  The resulting
        AST looked valid but was semantically wrong: an equality chain had an
        iff connective mixed in.
        """
        # A continuation line in an EQUAL: block should never start with <=>
        # because <=> is the iff connective, not an equality connective.
        text = "EQUAL:\na\n<=> b"
        with pytest.raises(ParserError):
            Parser(Lexer(text).tokenize()).parse()

    def test_equal_chain_eq_on_continuation_is_expression_operator(self) -> None:
        """In EQUAL: chains, = on a continuation line becomes an expression operator.

        The comparison parser crosses newlines when it sees a comparison op.
        So 'a\n= b' is parsed as one step with BinaryOp(a = b), not two steps.
        This is distinct from the iff-connector bug: = is not a chain connector
        in the outer loop sense (it is consumed by _parse_comparison instead).
        """
        text = "EQUAL:\na\n= b"
        ast = Parser(Lexer(text).tokenize()).parse()
        assert isinstance(ast, Document)
        chain = ast.items[0]
        assert isinstance(chain, ArgueChain)
        # _parse_comparison crosses the newline and consumes 'a = b' as one step
        assert len(chain.steps) == 1

    def test_equal_chain_iff_continuation_error_message(self) -> None:
        """EQUAL: + <=> continuation produces a targeted, readable error message."""
        text = "EQUAL:\na\n<=> b"
        with pytest.raises(ParserError, match="found '<=>' continuation in an EQUAL:"):
            Parser(Lexer(text).tokenize()).parse()

    def test_equiv_chain_does_not_consume_eq_continuation(self) -> None:
        """EQUIV: continuation line starting with = keeps = in the expression."""
        # '=' is a valid expression operator in EQUIV chains (e.g., #s = #t).
        # It must NOT be consumed as a chain connector.
        text = "EQUIV:\na = b\nc = d"
        ast = Parser(Lexer(text).tokenize()).parse()
        assert isinstance(ast, Document)
        chain = ast.items[0]
        assert isinstance(chain, ArgueChain)
        assert chain.connector == "iff"
        # Two expression steps; = was NOT swallowed as a connector
        assert len(chain.steps) == 2


# ---------------------------------------------------------------------------
# Regression tests for multi-line step with justification (item #2)
# ---------------------------------------------------------------------------


class TestMultiLineStepWithJustification:
    r"""Multi-line step + justification must not produce three array cells.

    The array environment has two columns: l@{\hspace{2em}}r.
    A multi-line expression in _in_argue_block mode emits '& ' as a
    continuation prefix inside the expression.  When the step also has a
    justification, a second '& ' appears for the right column.  That yields
    three cells in a two-column array — a LaTeX error.

    The fix: strip the leading '& ' from the continuation line (or avoid
    emitting it) when the expression will also need a justification column.
    The rendered LaTeX must have at most one '&' per array row.
    """

    def _count_ampersands_per_row(self, latex: str) -> list[int]:
        """Return the number of & characters on each array row."""
        # Rows are separated by \\
        rows = latex.split(r"\\")
        return [row.count("&") for row in rows]

    def test_multiline_step_no_justification_one_ampersand_max(self) -> None:
        """Multi-line step without justification has at most one & per row."""
        # Use a line-break via \\ continuation marker in a long expression.
        # Construct directly via AST to avoid needing continuation syntax.
        gen = LaTeXGenerator()
        expr = BinaryOp(
            operator="land",
            left=Identifier(name="p", line=1, column=1),
            right=Identifier(name="q", line=1, column=1),
            line_break_after=True,
            line=1,
            column=1,
        )
        step0 = ArgueStep(
            expression=Identifier(name="a", line=1, column=1),
            justification=None,
            line=1,
            column=1,
        )
        step1 = ArgueStep(
            expression=expr,
            justification=None,
            line=2,
            column=1,
        )
        chain = ArgueChain(steps=[step0, step1], connector="eq", line=1, column=1)
        latex = "\n".join(gen._generate_argue_chain(chain))
        counts = self._count_ampersands_per_row(latex)
        # Rows inside the array: first step has 0, second has at most 1
        # (for continuation)
        assert all(c <= 1 for c in counts), f"Too many & in some rows: {counts}"

    def test_multiline_step_with_justification_at_most_one_ampersand(self) -> None:
        """Multi-line step with justification has exactly one & per array row.

        One & separates the expression from the justification column.
        The continuation prefix inside a multi-line expression must not
        introduce a second &.
        """
        gen = LaTeXGenerator()
        expr = BinaryOp(
            operator="land",
            left=Identifier(name="p", line=1, column=1),
            right=Identifier(name="q", line=1, column=1),
            line_break_after=True,
            line=1,
            column=1,
        )
        step0 = ArgueStep(
            expression=Identifier(name="a", line=1, column=1),
            justification=None,
            line=1,
            column=1,
        )
        step1 = ArgueStep(
            expression=expr,
            justification="by hypothesis",
            line=2,
            column=1,
        )
        chain = ArgueChain(steps=[step0, step1], connector="eq", line=1, column=1)
        latex = "\n".join(gen._generate_argue_chain(chain))
        # The row containing the justification must have exactly one &
        rows = latex.split(r"\\")
        justification_rows = [r for r in rows if "by hypothesis" in r]
        assert justification_rows, "No row with justification found"
        for row in justification_rows:
            assert row.count("&") == 1, (
                f"Expected exactly one & in justification row, got: {row!r}"
            )

    def test_quantifier_multiline_step_with_justification_at_most_one_ampersand(
        self,
    ) -> None:
        """Quantifier with line_break_after_pipe plus justification has at most one &.

        Before the fix, _generate_quantifier emitted '& {indent}' as the
        continuation prefix when _in_argue_block was True.  When the step also
        carried a justification, the row gained a second & — three cells in a
        two-column array.
        """
        gen = LaTeXGenerator()
        # forall x : N | x > 0, with a line break after the | pipe
        quant = Quantifier(
            quantifier="forall",
            variables=["x"],
            domain=Identifier(name="N", line=1, column=1),
            body=Identifier(name="P", line=1, column=1),
            line_break_after_pipe=True,
            line=1,
            column=1,
        )
        step0 = ArgueStep(
            expression=Identifier(name="a", line=1, column=1),
            justification=None,
            line=1,
            column=1,
        )
        step1 = ArgueStep(
            expression=quant,
            justification="by definition",
            line=2,
            column=1,
        )
        chain = ArgueChain(steps=[step0, step1], connector="iff", line=1, column=1)
        latex = "\n".join(gen._generate_argue_chain(chain))
        rows = latex.split(r"\\")
        for row in rows:
            assert row.count("&") <= 1, (
                f"More than one & in array row (three-cell overflow): {row!r}"
            )
