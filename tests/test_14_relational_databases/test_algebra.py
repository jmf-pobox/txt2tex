"""Tests for relational algebra operators (Phase 2.2).

Covers the five AST nodes (Restrict, Project, Rename, NaturalJoin, Divide),
their token types, parser cases, and LaTeX generator output.  Negative cases
use the three-assertion pattern: message, line, column.

Acceptance probes at the end verify the canonical rendering for
relational algebra expressions.
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    BinaryOp,
    Divide,
    Document,
    DocumentItem,
    Expr,
    Identifier,
    NaturalJoin,
    Project,
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


def _expr_latex(src: str) -> str:
    """Generate LaTeX for an expression (math content without wrapper)."""
    gen = LaTeXGenerator(use_fuzz=True)
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


# ---------------------------------------------------------------------------
# Generator — Restrict
# ---------------------------------------------------------------------------


class TestRestrictGenerator:
    r"""LaTeX generator emits \mathrm{Restrict}_{pred}(rel) for Restrict nodes."""

    def test_restrict_simple(self) -> None:
        r"""sigma[p](R) → \mathrm{Restrict}_{p}(R)."""
        result = _expr_latex("sigma[p](R)")
        assert result == r"\mathrm{Restrict}_{p}(R)"

    def test_restrict_comparison(self) -> None:
        r"""sigma[bore >= 16](R) → \mathrm{Restrict}_{bore \geq 16}(R)."""
        result = _expr_latex("sigma[bore >= 16](R)")
        assert r"\mathrm{Restrict}_{" in result
        assert r"\geq" in result
        assert r"16" in result

    def test_restrict_with_named_relation(self) -> None:
        r"""sigma[p](Class) → \mathrm{Restrict}_{p}(Class) (no relvar wrapping)."""
        result = _expr_latex("sigma[p](Class)")
        assert result == r"\mathrm{Restrict}_{p}(Class)"

    def test_restrict_bore_attribute_italic(self) -> None:
        r"""sigma[bore >= 16](Class) — bore and Class both render italic."""
        result = _expr_latex("sigma[bore >= 16](Class)")
        assert r"\mathrm{bore}" not in result
        assert r"\mathrm{Class}" not in result
        assert "Class" in result


# ---------------------------------------------------------------------------
# Generator — Project
# ---------------------------------------------------------------------------


class TestProjectGenerator:
    r"""LaTeX generator emits \mathrm{Project}_{attrs}(rel) for Project nodes."""

    def test_project_subscript_form(self) -> None:
        r"""pi[a](R) → \mathrm{Project}_{a}(R) (subscript, not braces)."""
        result = _expr_latex("pi[a](R)")
        assert result == r"\mathrm{Project}_{a}(R)"

    def test_project_single_attr(self) -> None:
        r"""pi[a](R) → \mathrm{Project}_{a}(R)."""
        result = _expr_latex("pi[a](R)")
        assert result == r"\mathrm{Project}_{a}(R)"

    def test_project_multiple_attrs(self) -> None:
        r"""pi[class, country](R) → \mathrm{Project}_{class, country}(R)."""
        result = _expr_latex("pi[class, country](R)")
        assert result == r"\mathrm{Project}_{class, country}(R)"

    def test_project_named_relation(self) -> None:
        r"""pi[class, country](Class) → \mathrm{Project}_{class, country}(Class)."""
        result = _expr_latex("pi[class, country](Class)")
        assert result == r"\mathrm{Project}_{class, country}(Class)"

    def test_project_attr_in_subscript(self) -> None:
        r"""pi[Class](R) — Class in subscript."""
        result = _expr_latex("pi[Class](R)")
        assert result == r"\mathrm{Project}_{Class}(R)"


# ---------------------------------------------------------------------------
# Generator — Rename
# ---------------------------------------------------------------------------


class TestRenameGenerator:
    r"""LaTeX generator emits \mathrm{Rename}_{A \to B}(rel) for Rename nodes."""

    def test_rename_single_pair(self) -> None:
        r"""rho[ship as name](R) → \mathrm{Rename}_{ship \to name}(R)."""
        result = _expr_latex("rho[ship as name](R)")
        assert result == r"\mathrm{Rename}_{ship \to name}(R)"

    def test_rename_multiple_pairs(self) -> None:
        r"""rho[A as B, C as D](R) → \mathrm{Rename}_{A \to B, C \to D}(R)."""
        result = _expr_latex("rho[A as B, C as D](R)")
        assert result == r"\mathrm{Rename}_{A \to B, C \to D}(R)"

    def test_rename_named_relation(self) -> None:
        r"""rho[ship as name](Outcome) → \mathrm{Rename}_{ship \to name}(Outcome)."""
        result = _expr_latex("rho[ship as name](Outcome)")
        assert result == r"\mathrm{Rename}_{ship \to name}(Outcome)"


# ---------------------------------------------------------------------------
# Generator — NaturalJoin
# ---------------------------------------------------------------------------


class TestNaturalJoinGenerator:
    r"""LaTeX generator: \otimes (natural join) or \mathrm{Join} (theta-join).

    Natural join (no subscript) stays infix; theta-join becomes function form.
    """

    def test_natural_join(self) -> None:
        r"""R bowtie S → R \otimes S (unchanged)."""
        result = _expr_latex("R bowtie S")
        assert result == r"R \otimes S"

    def test_theta_join(self) -> None:
        r"""R bowtie [p] S → \mathrm{Join}_{p}(R, S) (function form)."""
        result = _expr_latex("R bowtie [p] S")
        assert result == r"\mathrm{Join}_{p}(R, S)"

    def test_natural_join_named_relations(self) -> None:
        r"""Ship bowtie Outcome → Ship \otimes Outcome (no relvar wrapping)."""
        result = _expr_latex("Ship bowtie Outcome")
        assert result == r"Ship \otimes Outcome"


# ---------------------------------------------------------------------------
# Generator — Divide
# ---------------------------------------------------------------------------


class TestDivideGenerator:
    r"""LaTeX generator emits \div for Divide nodes."""

    def test_divide(self) -> None:
        r"""R div S → R~\div~S."""
        result = _expr_latex("R div S")
        assert result == r"R~\div~S"

    def test_divide_named_relations(self) -> None:
        r"""R div S → R~\div~S (no relvar wrapping)."""
        result = _expr_latex("R div S")
        assert result == r"R~\div~S"


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


# ---------------------------------------------------------------------------
# Acceptance probes -- Q1(a)-(d) from exercises1.tex
# ---------------------------------------------------------------------------


class TestQ1AcceptanceProbes:
    """Acceptance probes for relational algebra rendering.

    These probes verify the canonical keyword-algebra rendering.
    Relation names render italic (default fuzz output).
    """

    def _gen(self, src: str) -> str:
        """Generate LaTeX for src."""
        gen = LaTeXGenerator(use_fuzz=True)
        ast = Parser(_lex(src)).parse()
        if isinstance(ast, Document):
            return gen.generate_document(ast)
        return gen.generate_expr(ast)

    def test_q1a_project_restrict(self) -> None:
        r"""Q1(a): pi[class, country](sigma[bore >= 16](Class)).

        Expected:
            \mathrm{Project}_{class, country}(\mathrm{Restrict}_{bore \geq 16}(Class))
        """
        result = self._gen("pi[class, country](sigma[bore >= 16](Class))")
        assert r"\mathrm{Project}_{class, country}" in result
        assert r"\mathrm{Restrict}_{bore \geq 16}" in result
        assert "Class" in result

    def test_q1b_natural_join(self) -> None:
        r"""Q1(b): Ship bowtie Class — natural join.

        Expected: Ship \otimes Class (⊗ notation, natural join)
        """
        result = self._gen("Ship bowtie Class")
        assert r"Ship \otimes Class" in result

    def test_q1c_rename_then_join(self) -> None:
        r"""Q1(c): rho[ship as name](Outcome) bowtie Ship.

        Expected: \mathrm{Rename}_{ship \to name}(Outcome) \otimes Ship
        """
        result = self._gen("rho[ship as name](Outcome) bowtie Ship")
        assert r"\mathrm{Rename}_{ship \to name}(Outcome)" in result
        assert r"\otimes Ship" in result


# ---------------------------------------------------------------------------
# Round-1 review fixes
# ---------------------------------------------------------------------------


class TestAttrNamePassthrough:
    """Attribute names in pi/rho pass through as-is (no wrapping)."""

    def test_pi_decorated_attr(self) -> None:
        r"""pi[class'](R) — decorated attribute name passes through."""
        result = _expr_latex("pi[class'](R)")
        assert r"\mathrm{Project}_{class'}" in result

    def test_pi_plain_attr(self) -> None:
        r"""pi[name](R) → \mathrm{Project}_{name}(R)."""
        result = _expr_latex("pi[name](R)")
        assert result == r"\mathrm{Project}_{name}(R)"

    def test_rho_decorated_src(self) -> None:
        r"""rho[class' as id](R) → \mathrm{Rename}_{class' \to id}(R)."""
        result = _expr_latex("rho[class' as id](R)")
        assert r"\mathrm{Rename}_{class' \to id}(R)" in result

    def test_rho_decorated_dst(self) -> None:
        r"""rho[name as class'](R) → \mathrm{Rename}_{name \to class'}(R)."""
        result = _expr_latex("rho[name as class'](R)")
        assert r"name \to class'" in result


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
