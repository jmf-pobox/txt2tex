"""Tests for relational algebra operators (Phase 2.2).

Covers the six new AST nodes (Restrict, Project, Rename, NaturalJoin,
Divide, Assignment), their token types, parser cases, and LaTeX generator
output.  Negative cases use the three-assertion pattern: message, line,
column.

Q1(a)-(d) acceptance probes at the end verify the canonical rendering
that exercises1.tex from the Oxford DAT course expects.
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    Assignment,
    BinaryOp,
    Divide,
    Document,
    DocumentItem,
    Expr,
    Identifier,
    NaturalJoin,
    Project,
    Relvars,
    Rename,
    Restrict,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser, ParserError
from txt2tex.tokens import Token, TokenType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lex(src: str) -> list[Token]:
    """Tokenize src."""
    return Lexer(src).tokenize()


def _parse(src: str) -> Document:
    """Parse src into a Document, wrapping bare Expr results in a Document."""
    result = Parser(_lex(src)).parse()
    if isinstance(result, Document):
        return result
    # Bare expression returned by parse() in single-expression mode
    return Document(items=[result], line=1, column=1)


def _expr(src: str) -> DocumentItem:
    """Parse a single-line algebra expression and return the first document item."""
    return _parse(src).items[0]


def _latex(src: str, *, relvars: frozenset[str] = frozenset()) -> str:
    """Generate LaTeX from source, optionally with relvar declarations."""
    gen = LaTeXGenerator(use_fuzz=True)
    gen.relvar_set = relvars
    ast = Parser(_lex(src)).parse()
    doc = ast if isinstance(ast, Document) else Document(items=[ast], line=1, column=1)
    lines: list[str] = []
    for item in doc.items:
        lines.extend(gen.generate_document_item(item))
    return "\n".join(lines)


def _expr_latex(src: str, *, relvars: frozenset[str] = frozenset()) -> str:
    """Generate LaTeX for an expression (math content without wrapper)."""
    gen = LaTeXGenerator(use_fuzz=True)
    gen.relvar_set = relvars
    ast = Parser(_lex(src)).parse()
    item: Expr = ast.items[0] if isinstance(ast, Document) else ast  # type: ignore[assignment]
    return gen.generate_expr(item)


# ---------------------------------------------------------------------------
# Lexer: token types for new keywords
# ---------------------------------------------------------------------------


class TestAlgebraLexer:
    """New token types tokenize correctly."""

    def test_sigma_token(self) -> None:
        """'sigma' lexes to SIGMA token."""
        tokens = _lex("sigma")
        assert tokens[0].type == TokenType.SIGMA
        assert tokens[0].value == "sigma"

    def test_pi_token(self) -> None:
        """'pi' lexes to PI token."""
        tokens = _lex("pi")
        assert tokens[0].type == TokenType.PI
        assert tokens[0].value == "pi"

    def test_rho_token(self) -> None:
        """'rho' lexes to RHO token."""
        tokens = _lex("rho")
        assert tokens[0].type == TokenType.RHO
        assert tokens[0].value == "rho"

    def test_bowtie_token(self) -> None:
        """'bowtie' lexes to BOWTIE token."""
        tokens = _lex("bowtie")
        assert tokens[0].type == TokenType.BOWTIE
        assert tokens[0].value == "bowtie"

    def test_div_token(self) -> None:
        """'div' lexes to DIV token."""
        tokens = _lex("div")
        assert tokens[0].type == TokenType.DIV
        assert tokens[0].value == "div"

    def test_assign_token(self) -> None:
        """':=' lexes to ASSIGN token."""
        tokens = _lex(":=")
        assert tokens[0].type == TokenType.ASSIGN
        assert tokens[0].value == ":="

    def test_assign_does_not_conflict_with_free_type(self) -> None:
        """':=' is distinct from '::='."""
        tokens = _lex("::=")
        assert tokens[0].type == TokenType.FREE_TYPE
        tokens2 = _lex(":=")
        assert tokens2[0].type == TokenType.ASSIGN

    def test_assign_column_position(self) -> None:
        """':=' token reports correct column."""
        tokens = _lex("R :=")
        # R at col 1, space skipped, := at col 3
        assign_tok = next(t for t in tokens if t.type == TokenType.ASSIGN)
        assert assign_tok.column == 3


# ---------------------------------------------------------------------------
# Parser — Restrict (sigma)
# ---------------------------------------------------------------------------


class TestRestrictParser:
    """Parser produces Restrict nodes for sigma[pred](R)."""

    def test_restrict_simple(self) -> None:
        """sigma[p](R) produces Restrict with predicate and relation."""
        node = _expr("sigma[p](R)")
        assert isinstance(node, Restrict)
        assert isinstance(node.predicate, Identifier)
        assert node.predicate.name == "p"
        assert isinstance(node.relation, Identifier)
        assert node.relation.name == "R"

    def test_restrict_comparison_predicate(self) -> None:
        """sigma[bore >= 16](Class) — predicate is BinaryOp."""
        node = _expr("sigma[bore >= 16](Class)")
        assert isinstance(node, Restrict)
        assert isinstance(node.predicate, BinaryOp)
        assert node.predicate.operator == ">="

    def test_restrict_position(self) -> None:
        """Restrict node carries start position of sigma keyword."""
        node = _expr("sigma[p](R)")
        assert node.line == 1
        assert node.column == 1

    def test_restrict_nested_relation(self) -> None:
        """sigma can wrap another algebra expression as relation."""
        node = _expr("sigma[p](sigma[q](R))")
        assert isinstance(node, Restrict)
        assert isinstance(node.relation, Restrict)


# ---------------------------------------------------------------------------
# Parser — Project (pi)
# ---------------------------------------------------------------------------


class TestProjectParser:
    """Parser produces Project nodes for pi[A, B](R)."""

    def test_project_single_attr(self) -> None:
        """pi[a](R) produces Project with one attribute."""
        node = _expr("pi[a](R)")
        assert isinstance(node, Project)
        assert node.attrs == ["a"]

    def test_project_multiple_attrs(self) -> None:
        """pi[class, country](Class) produces Project with two attributes."""
        node = _expr("pi[class, country](Class)")
        assert isinstance(node, Project)
        assert node.attrs == ["class", "country"]

    def test_project_position(self) -> None:
        """Project node carries start position of pi keyword."""
        node = _expr("pi[a](R)")
        assert node.line == 1
        assert node.column == 1

    def test_project_relation_is_identifier(self) -> None:
        """Project relation is an Identifier."""
        node = _expr("pi[a](R)")
        assert isinstance(node, Project)
        assert isinstance(node.relation, Identifier)
        assert node.relation.name == "R"


# ---------------------------------------------------------------------------
# Parser — Rename (rho)
# ---------------------------------------------------------------------------


class TestRenameParser:
    """Parser produces Rename nodes for rho[A as B, ...](R)."""

    def test_rename_single_pair(self) -> None:
        """rho[ship as name](Outcome) produces Rename with one pair."""
        node = _expr("rho[ship as name](Outcome)")
        assert isinstance(node, Rename)
        assert node.pairs == [("ship", "name")]
        assert isinstance(node.relation, Identifier)
        assert node.relation.name == "Outcome"

    def test_rename_multiple_pairs(self) -> None:
        """rho[A as B, C as D](R) produces Rename with two pairs."""
        node = _expr("rho[A as B, C as D](R)")
        assert isinstance(node, Rename)
        assert node.pairs == [("A", "B"), ("C", "D")]

    def test_rename_position(self) -> None:
        """Rename node carries start position of rho keyword."""
        node = _expr("rho[x as y](R)")
        assert node.line == 1
        assert node.column == 1


# ---------------------------------------------------------------------------
# Parser — NaturalJoin (bowtie)
# ---------------------------------------------------------------------------


class TestNaturalJoinParser:
    """Parser produces NaturalJoin nodes for R bowtie S and R bowtie [p] S."""

    def test_natural_join_no_subscript(self) -> None:
        """R bowtie S → NaturalJoin with subscript=None."""
        node = _expr("R bowtie S")
        assert isinstance(node, NaturalJoin)
        assert isinstance(node.left, Identifier)
        assert node.left.name == "R"
        assert isinstance(node.right, Identifier)
        assert node.right.name == "S"
        assert node.subscript is None

    def test_theta_join(self) -> None:
        """R bowtie [p] S → NaturalJoin with subscript=p."""
        node = _expr("R bowtie [p] S")
        assert isinstance(node, NaturalJoin)
        assert node.subscript is not None
        assert isinstance(node.subscript, Identifier)
        assert node.subscript.name == "p"

    def test_theta_join_equality_predicate(self) -> None:
        """R bowtie [x = y] S → subscript is BinaryOp(=)."""
        node = _expr("R bowtie [x = y] S")
        assert isinstance(node, NaturalJoin)
        assert isinstance(node.subscript, BinaryOp)
        assert node.subscript.operator == "="

    def test_natural_join_position(self) -> None:
        """NaturalJoin node carries position of bowtie operator."""
        node = _expr("R bowtie S")
        assert node.line == 1


# ---------------------------------------------------------------------------
# Parser — Divide (div)
# ---------------------------------------------------------------------------


class TestDivideParser:
    """Parser produces Divide nodes for R div S."""

    def test_divide_simple(self) -> None:
        """R div S → Divide with left=R, right=S."""
        node = _expr("R div S")
        assert isinstance(node, Divide)
        assert isinstance(node.left, Identifier)
        assert node.left.name == "R"
        assert isinstance(node.right, Identifier)
        assert node.right.name == "S"

    def test_divide_position(self) -> None:
        """Divide node carries position of div operator."""
        node = _expr("R div S")
        assert node.line == 1


# ---------------------------------------------------------------------------
# Parser — Assignment
# ---------------------------------------------------------------------------


class TestAssignmentParser:
    """Parser produces Assignment nodes for T := expression."""

    def test_assignment_simple_identifier(self) -> None:
        """T := R → Assignment with target=T, expression=R."""
        node = _expr("T := R")
        assert isinstance(node, Assignment)
        assert isinstance(node.target, Identifier)
        assert node.target.name == "T"
        assert isinstance(node.expression, Identifier)
        assert node.expression.name == "R"

    def test_assignment_with_algebra_expression(self) -> None:
        """T := pi[a](R) → Assignment with expression=Project."""
        node = _expr("T := pi[a](R)")
        assert isinstance(node, Assignment)
        assert isinstance(node.expression, Project)

    def test_assignment_position(self) -> None:
        """Assignment node carries position of target identifier."""
        node = _expr("T := R")
        assert node.line == 1
        assert node.column == 1

    def test_assignment_multiple_items(self) -> None:
        """Multiple assignments in a document parse correctly."""
        doc = _parse("A := R\nB := S")
        assert len(doc.items) == 2
        assert isinstance(doc.items[0], Assignment)
        assert isinstance(doc.items[1], Assignment)


# ---------------------------------------------------------------------------
# Parser — Composition and nesting
# ---------------------------------------------------------------------------


class TestAlgebraComposition:
    """Algebra operators compose and nest correctly."""

    def test_nested_sigma_in_pi(self) -> None:
        """pi[a](sigma[p](R)) — project of restrict."""
        node = _expr("pi[a](sigma[p](R))")
        assert isinstance(node, Project)
        assert isinstance(node.relation, Restrict)

    def test_nested_sigma_in_pi_in_rho(self) -> None:
        """pi[A](sigma[p](rho[B as C](R))) — triple nesting."""
        node = _expr("pi[A](sigma[p](rho[B as C](R)))")
        assert isinstance(node, Project)
        assert isinstance(node.relation, Restrict)
        assert isinstance(node.relation.relation, Rename)

    def test_algebra_with_set_union(self) -> None:
        """pi[a](R union S) — project of union."""
        node = _expr("pi[a](R union S)")
        assert isinstance(node, Project)
        assert isinstance(node.relation, BinaryOp)
        assert node.relation.operator == "union"

    def test_algebra_with_set_difference(self) -> None:
        """pi[a](R - S) — project of set difference."""
        node = _expr("pi[a](R - S)")
        assert isinstance(node, Project)
        assert isinstance(node.relation, BinaryOp)
        assert node.relation.operator == "-"

    def test_relvars_then_algebra(self) -> None:
        """relvars + algebra expression in same document."""
        doc = _parse("relvars R, S\npi[a](R)")
        assert isinstance(doc.items[0], Relvars)
        assert isinstance(doc.items[1], Project)

    def test_assignment_with_nested_algebra(self) -> None:
        """T := pi[a](sigma[p](R)) — assignment with nested expression."""
        node = _expr("T := pi[a](sigma[p](R))")
        assert isinstance(node, Assignment)
        assert isinstance(node.expression, Project)


# ---------------------------------------------------------------------------
# Generator — Restrict
# ---------------------------------------------------------------------------


class TestRestrictGenerator:
    r"""LaTeX generator emits \sigma_{pred}(rel) for Restrict nodes."""

    def test_restrict_simple(self) -> None:
        r"""sigma[p](R) → \sigma_{p}(R)."""
        result = _expr_latex("sigma[p](R)")
        assert result == r"\sigma_{p}(R)"

    def test_restrict_comparison(self) -> None:
        r"""sigma[bore >= 16](R) → \sigma_{bore \geq 16}(R)."""
        result = _expr_latex("sigma[bore >= 16](R)")
        assert r"\sigma_{" in result
        assert r"\geq" in result
        assert r"16" in result

    def test_restrict_relvar_wrapping(self) -> None:
        r"""sigma[p](Class) with Class as relvar → \sigma_{p}(\mathrm{Class})."""
        result = _expr_latex("sigma[p](Class)", relvars=frozenset({"Class"}))
        assert result == r"\sigma_{p}(\mathrm{Class})"

    def test_restrict_attribute_not_wrapped(self) -> None:
        r"""sigma[bore >= 16](Class) — bore stays italic, not \mathrm."""
        result = _expr_latex("sigma[bore >= 16](Class)", relvars=frozenset({"Class"}))
        assert r"\mathrm{bore}" not in result
        assert r"\mathrm{Class}" in result


# ---------------------------------------------------------------------------
# Generator — Project
# ---------------------------------------------------------------------------


class TestProjectGenerator:
    r"""LaTeX generator emits \pi_{attrs}(rel) for Project nodes."""

    def test_project_single_attr(self) -> None:
        r"""pi[a](R) → \pi_{a}(R)."""
        result = _expr_latex("pi[a](R)")
        assert result == r"\pi_{a}(R)"

    def test_project_multiple_attrs(self) -> None:
        r"""pi[class, country](R) → \pi_{class, country}(R)."""
        result = _expr_latex("pi[class, country](R)")
        assert result == r"\pi_{class, country}(R)"

    def test_project_relvar_relation(self) -> None:
        r"""pi[class, country](Class) with relvar wraps Class in \mathrm."""
        result = _expr_latex("pi[class, country](Class)", relvars=frozenset({"Class"}))
        assert result == r"\pi_{class, country}(\mathrm{Class})"

    def test_project_attr_is_relvar_gets_mathrm(self) -> None:
        r"""pi[Class](R) where Class is a relvar — Class in subscript gets \mathrm."""
        result = _expr_latex("pi[Class](R)", relvars=frozenset({"Class"}))
        assert r"\mathrm{Class}" in result


# ---------------------------------------------------------------------------
# Generator — Rename
# ---------------------------------------------------------------------------


class TestRenameGenerator:
    r"""LaTeX generator emits \rho_{A \to B}(rel) for Rename nodes."""

    def test_rename_single_pair(self) -> None:
        r"""rho[ship as name](R) → \rho_{ship \to name}(R)."""
        result = _expr_latex("rho[ship as name](R)")
        assert result == r"\rho_{ship \to name}(R)"

    def test_rename_multiple_pairs(self) -> None:
        r"""rho[A as B, C as D](R) → \rho_{A \to B, C \to D}(R)."""
        result = _expr_latex("rho[A as B, C as D](R)")
        assert result == r"\rho_{A \to B, C \to D}(R)"

    def test_rename_relvar_relation(self) -> None:
        r"""rho[ship as name](Outcome) with relvar wraps Outcome in \mathrm."""
        result = _expr_latex(
            "rho[ship as name](Outcome)", relvars=frozenset({"Outcome"})
        )
        assert result == r"\rho_{ship \to name}(\mathrm{Outcome})"


# ---------------------------------------------------------------------------
# Generator — NaturalJoin
# ---------------------------------------------------------------------------


class TestNaturalJoinGenerator:
    r"""LaTeX generator emits \bowtie for NaturalJoin nodes."""

    def test_natural_join(self) -> None:
        r"""R bowtie S → R \bowtie S."""
        result = _expr_latex("R bowtie S")
        assert result == r"R \bowtie S"

    def test_theta_join(self) -> None:
        r"""R bowtie [p] S → R \bowtie_{p} S."""
        result = _expr_latex("R bowtie [p] S")
        assert result == r"R \bowtie_{p} S"

    def test_natural_join_with_relvars(self) -> None:
        r"""Ship bowtie Outcome with relvars wraps both in \mathrm."""
        result = _expr_latex(
            "Ship bowtie Outcome", relvars=frozenset({"Ship", "Outcome"})
        )
        assert result == r"\mathrm{Ship} \bowtie \mathrm{Outcome}"


# ---------------------------------------------------------------------------
# Generator — Divide
# ---------------------------------------------------------------------------


class TestDivideGenerator:
    r"""LaTeX generator emits \div for Divide nodes."""

    def test_divide(self) -> None:
        r"""R div S → R \div S."""
        result = _expr_latex("R div S")
        assert result == r"R \div S"

    def test_divide_with_relvars(self) -> None:
        r"""R div S with relvars → \mathrm{R} \div \mathrm{S}."""
        result = _expr_latex("R div S", relvars=frozenset({"R", "S"}))
        assert result == r"\mathrm{R} \div \mathrm{S}"


# ---------------------------------------------------------------------------
# Generator — Assignment
# ---------------------------------------------------------------------------


class TestAssignmentGenerator:
    r"""LaTeX generator emits \begin{zed}T := expr\end{zed} for Assignment."""

    def test_assignment_simple(self) -> None:
        """T := R emits a zed block containing 'T := R'."""
        result = _latex("T := R")
        assert r"\begin{zed}" in result
        assert "T := R" in result
        assert r"\end{zed}" in result

    def test_assignment_with_project(self) -> None:
        r"""T := pi[a](R) — zed block with \pi in expression."""
        result = _latex("T := pi[a](R)")
        assert r"\begin{zed}" in result
        assert r"\pi_{a}(R)" in result

    def test_assignment_with_relvar(self) -> None:
        r"""T := Class with Class as relvar — assignment renders \mathrm."""
        full_src = "relvars Class\nT := Class"
        gen = LaTeXGenerator(use_fuzz=True)
        ast = Parser(_lex(full_src)).parse()
        assert isinstance(ast, Document)
        result = gen.generate_document(ast)
        assert r"\mathrm{Class}" in result


# ---------------------------------------------------------------------------
# Negative cases — malformed inputs
# ---------------------------------------------------------------------------


class TestAlgebraNegative:
    """Malformed algebra expressions raise ParserError with correct position."""

    def test_sigma_missing_bracket(self) -> None:
        """sigma(R) — missing '[' after sigma."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("sigma(R)")).parse()
        err = exc_info.value
        assert "Expected '[' after sigma" in err.message
        assert err.token.line == 1
        assert err.token.column >= 1

    def test_sigma_empty_bracket(self) -> None:
        """sigma[](R) — empty predicate bracket."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("sigma[](R)")).parse()
        err = exc_info.value
        assert "predicate" in err.message.lower()
        assert err.token.line == 1

    def test_sigma_unclosed_bracket(self) -> None:
        """sigma[p(R) — unclosed predicate bracket."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("sigma[p(R)")).parse()
        err = exc_info.value
        assert err.token.line == 1

    def test_sigma_missing_paren(self) -> None:
        """sigma[p] R — missing '(' after sigma[...]."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("sigma[p] R")).parse()
        err = exc_info.value
        assert "Expected '(' after sigma" in err.message
        assert err.token.line == 1

    def test_pi_empty_attr_list(self) -> None:
        """pi[](R) — empty attribute list."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("pi[](R)")).parse()
        err = exc_info.value
        assert "attribute" in err.message.lower()
        assert err.token.line == 1

    def test_pi_non_identifier_attr(self) -> None:
        """pi[1](R) — numeric literal in attribute list is rejected."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("pi[1](R)")).parse()
        err = exc_info.value
        assert "attribute" in err.message.lower()
        assert err.token.line == 1

    def test_rho_missing_as(self) -> None:
        """rho[A B](R) — missing 'as' between attribute names."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("rho[A B](R)")).parse()
        err = exc_info.value
        assert "'as'" in err.message
        assert err.token.line == 1

    def test_rho_empty_bracket(self) -> None:
        """rho[](R) — empty rename list."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("rho[](R)")).parse()
        err = exc_info.value
        assert "rename pair" in err.message.lower()
        assert err.token.line == 1

    def test_rho_missing_target(self) -> None:
        """rho[A as](R) — missing target after 'as'."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("rho[A as](R)")).parse()
        err = exc_info.value
        assert "target attribute" in err.message.lower()
        assert err.token.line == 1

    def test_bowtie_empty_subscript(self) -> None:
        """R bowtie [] S — empty theta-join subscript."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("R bowtie [] S")).parse()
        err = exc_info.value
        assert "predicate" in err.message.lower()
        assert err.token.line == 1

    def test_assignment_missing_expression(self) -> None:
        """T := — missing expression after ':='."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("T :=\n")).parse()
        err = exc_info.value
        assert err.token.line == 1


# ---------------------------------------------------------------------------
# Acceptance probes -- Q1(a)-(d) from exercises1.tex
# ---------------------------------------------------------------------------


class TestQ1AcceptanceProbes:
    """Exercise 1 from the Oxford DAT course, rendered via txt2tex.

    These probes verify the canonical rendering that the course expects.
    Each probe declares the relvars used in the query, then writes the
    algebra expression, and checks the LaTeX output.
    """

    _RELVARS = frozenset({"Class", "Ship", "Outcome", "Battle"})

    def _gen(self, src: str) -> str:
        """Generate LaTeX for src with the standard warships relvars."""
        full_src = f"relvars Class, Ship, Battle, Outcome\n{src}"
        gen = LaTeXGenerator(use_fuzz=True)
        ast = Parser(_lex(full_src)).parse()
        assert isinstance(ast, Document)
        return gen.generate_document(ast)

    def test_q1a_project_restrict(self) -> None:
        r"""Q1(a): pi[class, country](sigma[bore >= 16](Class)).

        Expected: \pi_{class, country}(\sigma_{bore \geq 16}(\mathrm{Class}))
        """
        result = self._gen("pi[class, country](sigma[bore >= 16](Class))")
        assert r"\pi_{class, country}" in result
        assert r"\sigma_{bore \geq 16}" in result
        assert r"\mathrm{Class}" in result

    def test_q1b_natural_join(self) -> None:
        r"""Q1(b): Ship bowtie Class — natural join of two relvars.

        Expected: \mathrm{Ship} \bowtie \mathrm{Class}
        """
        result = self._gen("Ship bowtie Class")
        assert r"\mathrm{Ship} \bowtie \mathrm{Class}" in result

    def test_q1c_rename_then_join(self) -> None:
        r"""Q1(c): rho[ship as name](Outcome) bowtie Ship.

        Expected: \rho_{ship \to name}(\mathrm{Outcome}) \bowtie \mathrm{Ship}
        """
        result = self._gen("rho[ship as name](Outcome) bowtie Ship")
        assert r"\rho_{ship \to name}(\mathrm{Outcome})" in result
        assert r"\bowtie \mathrm{Ship}" in result

    def test_q1d_assignment(self) -> None:
        r"""Q1(d): Result := pi[class, country](sigma[bore >= 16](Class)).

        Expected: Result := \pi_{class, country}(\sigma_{bore \geq 16}(\mathrm{Class}))
        """
        result = self._gen("Result := pi[class, country](sigma[bore >= 16](Class))")
        assert r"\begin{zed}" in result
        assert r"\pi_{class, country}" in result
        assert r"\sigma_{bore \geq 16}" in result
        assert r"\mathrm{Class}" in result


# ---------------------------------------------------------------------------
# Round-1 review fixes
# ---------------------------------------------------------------------------


class TestFix1DecorationAwareAttrName:
    r"""FIX 1: _emit_attr_name strips trailing decoration before relvar lookup.

    pi[class'](R) and rho[class' as name](R) must emit \mathrm{class}'
    when 'class' is a declared relvar.
    """

    _RELVARS = frozenset({"class", "Class"})

    def test_pi_decorated_attr_relvar(self) -> None:
        r"""pi[class'](R) with 'class' as relvar: class' → \mathrm{class}'."""
        result = _expr_latex("pi[class'](R)", relvars=self._RELVARS)
        assert r"\mathrm{class}'" in result

    def test_pi_non_relvar_attr_unchanged(self) -> None:
        """pi[name'](R) with 'name' not in relvar_set: name' stays italic."""
        result = _expr_latex("pi[name'](R)", relvars=self._RELVARS)
        assert r"\mathrm{name}" not in result
        assert "name'" in result

    def test_rho_decorated_src_relvar(self) -> None:
        r"""rho[class' as id](R) with 'class' as relvar: class' → \mathrm{class}'."""
        result = _expr_latex("rho[class' as id](R)", relvars=self._RELVARS)
        assert r"\mathrm{class}'" in result

    def test_rho_decorated_dst_relvar(self) -> None:
        r"""rho[name as class'](R) with 'class' as relvar: class' → \mathrm{class}'."""
        result = _expr_latex("rho[name as class'](R)", relvars=self._RELVARS)
        assert r"\mathrm{class}'" in result

    def test_pi_question_mark_decoration(self) -> None:
        r"""pi[class?](R) with 'class' as relvar: class? → \mathrm{class}?."""
        result = _expr_latex("pi[class?](R)", relvars=self._RELVARS)
        assert r"\mathrm{class}?" in result

    def test_pi_exclamation_decoration(self) -> None:
        r"""pi[class!](R) with 'class' as relvar: class! → \mathrm{class}!."""
        result = _expr_latex("pi[class!](R)", relvars=self._RELVARS)
        assert r"\mathrm{class}!" in result


class TestFix2ChainedAssignment:
    """FIX 2: T := R := S raises a clear parser error."""

    def test_chained_assignment_rejected(self) -> None:
        """T := R := S must raise ParserError mentioning 'chained'."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("T := R := S")).parse()
        err = exc_info.value
        assert "chained assignment" in err.message.lower()
        assert err.token.line == 1

    def test_chained_assignment_error_column(self) -> None:
        """Error token for T := R := S points at the offending second ':='."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("T := R := S")).parse()
        err = exc_info.value
        # Error points at the *second* := which is the offending token, not the first.
        # "T := R := S" — column 1=T, 2=space, 3=:=, 5=space, 6=R, 7=space, 8=:=
        assert err.token.column == 8


class TestFix3AssignmentNoLHS:
    """FIX 3: := R (no LHS) raises a clear parser error at the := token."""

    def test_assign_no_lhs_clear_error(self) -> None:
        """':= R' must raise ParserError mentioning target name on the left."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex(":= R")).parse()
        err = exc_info.value
        assert "target" in err.message.lower()
        assert "left" in err.message.lower()
        assert err.token.line == 1
        assert err.token.column == 1


class TestFix4BowtiePrecedence:
    """FIX 4: bowtie binds tighter than union.

    R bowtie S union T must parse as (R bowtie S) union T, not
    R bowtie (S union T).  Verified by inspecting the AST structure.
    """

    def test_bowtie_binds_tighter_than_union(self) -> None:
        """R bowtie S union T → BinaryOp('union', NaturalJoin(R, S), T)."""
        ast = _expr("R bowtie S union T")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "union"
        assert isinstance(ast.left, NaturalJoin)
        assert isinstance(ast.left.left, Identifier)
        assert ast.left.left.name == "R"
        assert isinstance(ast.left.right, Identifier)
        assert ast.left.right.name == "S"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "T"

    def test_intersect_binds_tighter_than_bowtie(self) -> None:
        """R bowtie S intersect T → NaturalJoin(R, intersect(S, T)).

        intersect is at _parse_intersect, which is called from _parse_cross
        to resolve operands.  intersect therefore binds tighter than bowtie.
        """
        ast = _expr("R bowtie S intersect T")
        assert isinstance(ast, NaturalJoin)
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "R"
        assert isinstance(ast.right, BinaryOp)
        assert ast.right.operator == "intersect"

    def test_pi_atom_feeds_bowtie(self) -> None:
        """pi[a](R) bowtie S → NaturalJoin(pi[a](R), S)."""
        ast = _expr("pi[a](R) bowtie S")
        assert isinstance(ast, NaturalJoin)
        assert isinstance(ast.left, Project)
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "S"
