"""Tests for relational algebra operators (Phase 2.2).

Covers the five AST nodes (Restrict, Project, RelationRename, NaturalJoin, Divide),
their token types, parser cases, and LaTeX generator output.  Negative cases
use the three-assertion pattern: message, line, column.

Acceptance probes at the end verify the canonical rendering for
relational algebra expressions.
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    Abbreviation,
    BinaryOp,
    Divide,
    Document,
    DocumentItem,
    Expr,
    Identifier,
    NaturalJoin,
    Project,
    RelationRename,
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

    def test_rho_is_identifier(self) -> None:
        """'rho' is no longer reserved — lexes as IDENTIFIER."""
        tokens = _lex("rho")
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "rho"

    def test_join_token(self) -> None:
        """'join' lexes to JOIN token."""
        tokens = _lex("join")
        assert tokens[0].type == TokenType.JOIN
        assert tokens[0].value == "join"

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
# Parser — RelationRename
# ---------------------------------------------------------------------------


class TestRelationRenameParser:
    """Parser produces RelationRename nodes for R[new/old] in relational context."""

    def test_rename_single_pair_in_pi(self) -> None:
        """R[b/a] inside pi[...](R[b/a]) produces RelationRename with one pair."""
        node = _expr("pi[b](R[b/a])")
        assert isinstance(node, Project)
        assert isinstance(node.relation, RelationRename)
        assert node.relation.pairs == [("b", "a")]
        assert isinstance(node.relation.relation, Identifier)
        assert node.relation.relation.name == "R"

    def test_rename_multiple_pairs_in_pi(self) -> None:
        """R[b/a, d/c] inside pi produces RelationRename with two pairs."""
        node = _expr("pi[b, d](R[b/a, d/c])")
        assert isinstance(node, Project)
        assert isinstance(node.relation, RelationRename)
        assert node.relation.pairs == [("b", "a"), ("d", "c")]

    def test_rename_in_sigma(self) -> None:
        """R[b/a] inside sigma[p](R[b/a]) produces RelationRename."""
        node = _expr("sigma[b != 0](R[b/a])")
        assert isinstance(node, Restrict)
        assert isinstance(node.relation, RelationRename)
        assert node.relation.pairs == [("b", "a")]

    def test_rename_right_of_join(self) -> None:
        """R[b/a] as right operand of join produces RelationRename."""
        # The right operand of join is parsed in relational context
        node = _expr("pi[b](S join R[b/a])")
        assert isinstance(node, Project)
        inner = node.relation
        assert isinstance(inner, NaturalJoin)
        assert isinstance(inner.right, RelationRename)
        assert inner.right.pairs == [("b", "a")]

    def test_rename_position(self) -> None:
        """RelationRename node carries position of opening bracket."""
        node = _expr("pi[b](R[b/a])")
        assert isinstance(node, Project)
        inner = node.relation
        assert isinstance(inner, RelationRename)
        assert inner.line >= 1
        assert inner.column >= 1

    def test_compound_base_rename(self) -> None:
        """(pi[x](R))[b/a] — compound base produces RelationRename."""
        node = _expr("pi[b](pi[x](R)[b/a])")
        assert isinstance(node, Project)
        inner = node.relation
        assert isinstance(inner, RelationRename)
        assert inner.pairs == [("b", "a")]
        assert isinstance(inner.relation, Project)

    def test_rename_pair_direction(self) -> None:
        """RelationRename pairs[0] is the new name, pairs[1] is the old name."""
        node = _expr("pi[ship](Ship[ship/name])")
        assert isinstance(node, Project)
        inner = node.relation
        assert isinstance(inner, RelationRename)
        assert inner.pairs[0] == ("ship", "name")  # new, old per Z RM §3.11

    def test_top_level_abbreviation_routes_to_relation_rename(self) -> None:
        """`B == R[a/b]` at top level — RHS routes via _in_relational_context."""
        ast = _parse("B == R[new/old]")
        item = ast.items[0]
        assert isinstance(item, Abbreviation)
        assert isinstance(item.expression, RelationRename)
        assert item.expression.pairs == [("new", "old")]

    def test_top_level_abbreviation_rename_emits_inline_math(self) -> None:
        """`B == R[a/b]` emits via `\\noindent $...$`, not inside a Z paragraph.

        Regression for the engine routing bug: SchemaRename inside `\\begin{zed}`
        contains an unescaped `/`, which fuzz rejects.  RelationRename routes
        through inline math (fuzz skips inline math content).
        """
        src = "TITLE: probe\n\ngiven Foo\nschema R\n  a : Foo\nend\n\nB == R[new/old]\n"
        ast_result = Parser(Lexer(src).tokenize()).parse()
        assert isinstance(ast_result, Document)
        latex = LaTeXGenerator().generate_document(ast_result)
        assert "\\noindent" in latex
        assert "$B == R[new/old]$" in latex
        # The abbreviation must NOT be inside a Z paragraph.
        assert "\\begin{zed}\nB ==" not in latex


# ---------------------------------------------------------------------------
# Parser — NaturalJoin (join)
# ---------------------------------------------------------------------------


class TestNaturalJoinParser:
    """Parser produces NaturalJoin nodes for R join S and R join [p] S."""

    def test_natural_join_no_subscript(self) -> None:
        """R join S → NaturalJoin with subscript=None."""
        node = _expr("R join S")
        assert isinstance(node, NaturalJoin)
        assert isinstance(node.left, Identifier)
        assert node.left.name == "R"
        assert isinstance(node.right, Identifier)
        assert node.right.name == "S"
        assert node.subscript is None

    def test_theta_join(self) -> None:
        """R join [p] S → NaturalJoin with subscript=p."""
        node = _expr("R join [p] S")
        assert isinstance(node, NaturalJoin)
        assert node.subscript is not None
        assert isinstance(node.subscript, Identifier)
        assert node.subscript.name == "p"

    def test_theta_join_equality_predicate(self) -> None:
        """R join [x = y] S → subscript is BinaryOp(=)."""
        node = _expr("R join [x = y] S")
        assert isinstance(node, NaturalJoin)
        assert isinstance(node.subscript, BinaryOp)
        assert node.subscript.operator == "="

    def test_natural_join_position(self) -> None:
        """NaturalJoin node carries position of join operator."""
        node = _expr("R join S")
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

    def test_nested_rename_in_sigma_in_pi(self) -> None:
        """pi[b](sigma[b=0](R[b/a])) — rename inside sigma inside pi."""
        node = _expr("pi[b](sigma[b = 0](R[b/a]))")
        assert isinstance(node, Project)
        assert isinstance(node.relation, Restrict)
        assert isinstance(node.relation.relation, RelationRename)

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
# Generator — RelationRename
# ---------------------------------------------------------------------------


class TestRelationRenameGenerator:
    """LaTeX generator emits R[new/old] pass-through for RelationRename nodes."""

    def test_rename_single_pair(self) -> None:
        """pi[b](R[b/a]) → R[b/a] literal emit (no mathrm)."""
        result = _expr_latex("pi[b](R[b/a])")
        assert "R[b/a]" in result
        assert r"\mathrm{Rename}" not in result

    def test_rename_multiple_pairs(self) -> None:
        """pi[b, d](R[b/a, d/c]) → R[b/a, d/c] literal emit."""
        result = _expr_latex("pi[b, d](R[b/a, d/c])")
        assert "R[b/a, d/c]" in result

    def test_rename_named_relation(self) -> None:
        """pi[ship](Ship[ship/name]) → Ship[ship/name] literal emit."""
        result = _expr_latex("pi[ship](Ship[ship/name])")
        assert "Ship[ship/name]" in result
        assert r"\mathrm{Rename}" not in result

    def test_rename_no_mathrm(self) -> None:
        """RelationRename never emits mathrm anywhere."""
        result = _expr_latex("pi[b](R[b/a])")
        assert r"\mathrm{Rename}" not in result
        assert r"\mathrm{rename}" not in result

    def test_compound_base_rename_emit(self) -> None:
        """(pi[x](R))[b/a] emits with parentheses around compound base."""
        result = _expr_latex("pi[b]((pi[x](R))[b/a])")
        assert "[b/a]" in result
        # Compound base is wrapped in parens
        assert "(" in result


# ---------------------------------------------------------------------------
# Generator — NaturalJoin
# ---------------------------------------------------------------------------


class TestNaturalJoinGenerator:
    r"""LaTeX generator: \mathrm{Join}(R, S) for both natural join and theta-join.

    Natural join (no subscript) emits \mathrm{Join}(R, S).
    Theta-join emits \mathrm{Join}_{p}(R, S).
    """

    def test_natural_join(self) -> None:
        r"""R join S → \mathrm{Join}(R, S)."""
        result = _expr_latex("R join S")
        assert result == r"\mathrm{Join}(R, S)"

    def test_theta_join(self) -> None:
        r"""R join [p] S → \mathrm{Join}_{p}(R, S) (function form)."""
        result = _expr_latex("R join [p] S")
        assert result == r"\mathrm{Join}_{p}(R, S)"

    def test_natural_join_named_relations(self) -> None:
        r"""Ship join Outcome → \mathrm{Join}(Ship, Outcome) (no relvar wrapping)."""
        result = _expr_latex("Ship join Outcome")
        assert result == r"\mathrm{Join}(Ship, Outcome)"


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

    def test_join_empty_subscript(self) -> None:
        """R join [] S — empty theta-join subscript."""
        with pytest.raises(ParserError) as exc_info:
            Parser(_lex("R join [] S")).parse()
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
        r"""Q1(b): Ship join Class — natural join.

        Expected: \mathrm{Join}(Ship, Class)
        """
        result = self._gen("Ship join Class")
        assert r"\mathrm{Join}(Ship, Class)" in result

    def test_q1c_rename_then_join(self) -> None:
        r"""Q1(c): pi[ship](Ship[ship/name]) join Class.

        Expected: Ship[ship/name] inside a \mathrm{Join}
        """
        result = self._gen("pi[ship, class, launched](Ship[ship/name] join Class)")
        assert "Ship[ship/name]" in result
        assert r"\mathrm{Join}(" in result


# ---------------------------------------------------------------------------
# Round-1 review fixes
# ---------------------------------------------------------------------------


class TestAttrNamePassthrough:
    """Attribute names in pi pass through as-is (no wrapping)."""

    def test_pi_decorated_attr(self) -> None:
        r"""pi[class'](R) — decorated attribute name passes through."""
        result = _expr_latex("pi[class'](R)")
        assert r"\mathrm{Project}_{class'}" in result

    def test_pi_plain_attr(self) -> None:
        r"""pi[name](R) → \mathrm{Project}_{name}(R)."""
        result = _expr_latex("pi[name](R)")
        assert result == r"\mathrm{Project}_{name}(R)"


class TestJoinPrecedence:
    """join binds tighter than union.

    R join S union T must parse as (R join S) union T, not
    R join (S union T).  Verified by inspecting the AST structure.
    """

    def test_join_binds_tighter_than_union(self) -> None:
        """R join S union T → BinaryOp('union', NaturalJoin(R, S), T)."""
        ast = _expr("R join S union T")
        assert isinstance(ast, BinaryOp)
        assert ast.operator == "union"
        assert isinstance(ast.left, NaturalJoin)
        assert isinstance(ast.left.left, Identifier)
        assert ast.left.left.name == "R"
        assert isinstance(ast.left.right, Identifier)
        assert ast.left.right.name == "S"
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "T"

    def test_intersect_binds_tighter_than_join(self) -> None:
        """R join S intersect T → NaturalJoin(R, intersect(S, T)).

        intersect is at _parse_intersect, which is called from _parse_cross
        to resolve operands.  intersect therefore binds tighter than join.
        """
        ast = _expr("R join S intersect T")
        assert isinstance(ast, NaturalJoin)
        assert isinstance(ast.left, Identifier)
        assert ast.left.name == "R"
        assert isinstance(ast.right, BinaryOp)
        assert ast.right.operator == "intersect"

    def test_pi_atom_feeds_join(self) -> None:
        """pi[a](R) join S → NaturalJoin(pi[a](R), S)."""
        ast = _expr("pi[a](R) join S")
        assert isinstance(ast, NaturalJoin)
        assert isinstance(ast.left, Project)
        assert isinstance(ast.right, Identifier)
        assert ast.right.name == "S"


# ---------------------------------------------------------------------------
# Regression: bowtie → join rename; \otimes → \mathrm{Join}
# ---------------------------------------------------------------------------


class TestJoinRenameRegression:
    r"""Regression: bowtie→join rename; \otimes→\mathrm{Join} emit.

    Added when the source keyword was renamed from ``bowtie`` to ``join``
    and the natural-join emission changed from ``R \otimes S`` to
    ``\mathrm{Join}(R, S)`` per the instructor's canonical vocabulary
    (slides/topic02.pdf page 45).
    """

    def test_natural_join_emits_mathrm_join(self) -> None:
        r"""R join S → \mathrm{Join}(R, S) (not \otimes)."""
        result = _expr_latex("R join S")
        assert result == r"\mathrm{Join}(R, S)"
        assert r"\otimes" not in result

    def test_theta_join_emits_mathrm_join_subscript(self) -> None:
        r"""R join [p] S → \mathrm{Join}_{p}(R, S)."""
        result = _expr_latex("R join [p] S")
        assert result == r"\mathrm{Join}_{p}(R, S)"

    def test_natural_join_three_way(self) -> None:
        r"""R join S join T is left-associative: Join(Join(R, S), T)."""
        result = _expr_latex("R join S join T")
        assert result == r"\mathrm{Join}(\mathrm{Join}(R, S), T)"

    def test_join_keyword_is_reserved(self) -> None:
        """'join' lexes to JOIN, not IDENTIFIER — it is reserved."""
        tokens = _lex("join")
        assert tokens[0].type == TokenType.JOIN
        assert tokens[0].value == "join"

    def test_bowtie_is_no_longer_a_keyword(self) -> None:
        """'bowtie' now lexes as IDENTIFIER (no longer reserved)."""
        tokens = _lex("bowtie")
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "bowtie"
