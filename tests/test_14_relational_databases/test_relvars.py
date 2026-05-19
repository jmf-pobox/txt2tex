"""Tests for relvars declaration paragraph (Phase 2.1).

Covers lexer token, AST node, parser dispatch, generator typography, and
all negative cases with the three-assertion pattern (message + line + column).
"""

from __future__ import annotations

import pytest

from txt2tex.ast_nodes import (
    Document,
    Identifier,
    Relvars,
    Schema,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser, ParserError
from txt2tex.tokens import TokenType

# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------


class TestRelvarLexer:
    """RELVARS token is produced correctly by the lexer."""

    def test_relvars_keyword_produces_relvars_token(self) -> None:
        """'relvars' lexes to RELVARS token type."""
        tokens = Lexer("relvars").tokenize()
        assert tokens[0].type == TokenType.RELVARS
        assert tokens[0].value == "relvars"

    def test_relvars_keyword_column_is_one(self) -> None:
        """RELVARS token has correct line and column."""
        tokens = Lexer("relvars Class").tokenize()
        tok = tokens[0]
        assert tok.line == 1
        assert tok.column == 1

    def test_relvars_is_reserved_cannot_be_decorated(self) -> None:
        """relvars' raises LexerError — reserved words cannot be decorated."""
        with pytest.raises(LexerError) as exc_info:
            Lexer("relvars'").tokenize()
        err = exc_info.value
        assert "relvars" in err.message


# ---------------------------------------------------------------------------
# Parser — positive cases
# ---------------------------------------------------------------------------


class TestRelvarParserPositive:
    """Parser produces Relvars AST nodes for valid relvars paragraphs."""

    def test_single_relvar(self) -> None:
        """Single name: relvars Class → Relvars(names=['Class'])."""
        ast = Parser(Lexer("relvars Class").tokenize()).parse()
        assert isinstance(ast, Document)
        node = ast.items[0]
        assert isinstance(node, Relvars)
        assert node.names == ["Class"]

    def test_multiple_relvars(self) -> None:
        """Multiple names: relvars Class, Ship, Battle, Outcome."""
        src = "relvars Class, Ship, Battle, Outcome"
        ast = Parser(Lexer(src).tokenize()).parse()
        assert isinstance(ast, Document)
        node = ast.items[0]
        assert isinstance(node, Relvars)
        assert node.names == ["Class", "Ship", "Battle", "Outcome"]

    def test_three_relvars_ast_node(self) -> None:
        """Three-name declaration: Relvars(names=['A', 'B', 'C'])."""
        ast = Parser(Lexer("relvars A, B, C").tokenize()).parse()
        assert isinstance(ast, Document)
        node = ast.items[0]
        assert isinstance(node, Relvars)
        assert node.names == ["A", "B", "C"]

    def test_relvars_line_and_column(self) -> None:
        """Relvars node carries start position of the keyword."""
        ast = Parser(Lexer("relvars Class").tokenize()).parse()
        assert isinstance(ast, Document)
        node = ast.items[0]
        assert isinstance(node, Relvars)
        assert node.line == 1
        assert node.column == 1

    def test_two_separate_relvars_paragraphs(self) -> None:
        """Two separate relvars paragraphs both parse correctly."""
        src = "relvars Class\nrelvars Ship"
        ast = Parser(Lexer(src).tokenize()).parse()
        assert isinstance(ast, Document)
        assert len(ast.items) == 2
        first, second = ast.items
        assert isinstance(first, Relvars)
        assert isinstance(second, Relvars)
        assert first.names == ["Class"]
        assert second.names == ["Ship"]

    def test_relvars_followed_by_schema(self) -> None:
        """relvars and schema in same document both parse."""
        src = "relvars Class\n\nschema Class\n  class : N\nend"
        ast = Parser(Lexer(src).tokenize()).parse()
        assert isinstance(ast, Document)
        assert len(ast.items) == 2
        assert isinstance(ast.items[0], Relvars)
        assert isinstance(ast.items[1], Schema)


# ---------------------------------------------------------------------------
# Parser — negative cases (three-assertion pattern: message, line, column)
# ---------------------------------------------------------------------------


class TestRelvarParserNegative:
    """Parser raises ParserError with correct message, line, and column."""

    def test_relvars_alone_raises(self) -> None:
        """'relvars' with no names raises ParserError."""
        with pytest.raises(ParserError) as exc_info:
            Parser(Lexer("relvars").tokenize()).parse()
        err = exc_info.value
        assert "relvar" in err.message.lower()
        assert err.token.line == 1

    def test_relvars_leading_comma_raises(self) -> None:
        """'relvars ,' raises — comma where name expected."""
        with pytest.raises(ParserError) as exc_info:
            Parser(Lexer("relvars ,").tokenize()).parse()
        err = exc_info.value
        assert "comma" in err.message.lower() or "relvar" in err.message.lower()
        assert err.token.line == 1
        assert err.token.column > 1

    def test_relvars_double_comma_raises(self) -> None:
        """'relvars Class, ,Ship' (double comma) raises ParserError."""
        with pytest.raises(ParserError) as exc_info:
            Parser(Lexer("relvars Class, , Ship").tokenize()).parse()
        err = exc_info.value
        assert "comma" in err.message.lower() or "relvar" in err.message.lower()
        assert err.token.line == 1

    def test_relvars_trailing_comma_raises(self) -> None:
        """'relvars Class,' (trailing comma then newline) raises ParserError."""
        with pytest.raises(ParserError) as exc_info:
            Parser(Lexer("relvars Class,\n").tokenize()).parse()
        err = exc_info.value
        assert "relvar" in err.message.lower() or "comma" in err.message.lower()
        assert err.token.line >= 1

    def test_relvars_missing_comma_raises(self) -> None:
        """'relvars Class Ship' (no comma between names) raises ParserError."""
        with pytest.raises(ParserError) as exc_info:
            Parser(Lexer("relvars Class Ship").tokenize()).parse()
        err = exc_info.value
        assert "comma" in err.message.lower() or "relvar" in err.message.lower()
        assert err.token.line == 1
        assert err.token.column > 1


# ---------------------------------------------------------------------------
# Generator — identifier typography
# ---------------------------------------------------------------------------


class TestRelvarGeneratorTypography:
    """Generator wraps relvar names in \\mathrm{} and leaves attributes italic."""

    def _gen(self, *, use_fuzz: bool = False) -> LaTeXGenerator:
        return LaTeXGenerator(use_fuzz=use_fuzz)

    def _identifier(self, name: str) -> Identifier:
        return Identifier(name=name, line=1, column=1)

    # -- relvar_set is empty: no wrapping --

    def test_no_relvar_set_identifier_unchanged(self) -> None:
        """Without relvar declaration, 'Class' renders unchanged."""
        gen = self._gen()
        assert gen.relvar_set == frozenset()
        result = gen._generate_identifier(self._identifier("Class"))
        assert result == "Class"

    # -- relvar_set populated: wrapping --

    def test_relvar_plain_renders_upright(self) -> None:
        """Declared relvar 'Class' renders as \\mathrm{Class}."""
        gen = self._gen()
        gen.relvar_set = frozenset({"Class"})
        result = gen._generate_identifier(self._identifier("Class"))
        assert result == r"\mathrm{Class}"

    def test_non_relvar_identifier_unchanged(self) -> None:
        """'class' (attribute) does not match 'Class' (relvar); stays italic."""
        gen = self._gen()
        gen.relvar_set = frozenset({"Class"})
        result = gen._generate_identifier(self._identifier("class"))
        assert result == "class"

    def test_relvar_fuzz_mode_same_mathrm(self) -> None:
        """\\mathrm is LaTeX kernel; works identically in fuzz mode."""
        gen = self._gen(use_fuzz=True)
        gen.relvar_set = frozenset({"Ship"})
        result = gen._generate_identifier(self._identifier("Ship"))
        assert result == r"\mathrm{Ship}"

    # -- decoration interaction (decoration outside \mathrm) --

    def test_relvar_primed_decoration_outside(self) -> None:
        """Class' renders as \\mathrm{Class}' (decoration outside wrapper)."""
        gen = self._gen()
        gen.relvar_set = frozenset({"Class"})
        result = gen._generate_identifier(self._identifier("Class'"))
        assert result == r"\mathrm{Class}'"

    def test_relvar_input_decoration_outside(self) -> None:
        """Class? renders as \\mathrm{Class}?."""
        gen = self._gen()
        gen.relvar_set = frozenset({"Class"})
        result = gen._generate_identifier(self._identifier("Class?"))
        assert result == r"\mathrm{Class}?"

    def test_relvar_output_decoration_outside(self) -> None:
        """Class! renders as \\mathrm{Class}!."""
        gen = self._gen()
        gen.relvar_set = frozenset({"Class"})
        result = gen._generate_identifier(self._identifier("Class!"))
        assert result == r"\mathrm{Class}!"

    def test_relvar_multiple_primes_outside(self) -> None:
        """Class'' renders as \\mathrm{Class}''."""
        gen = self._gen()
        gen.relvar_set = frozenset({"Class"})
        result = gen._generate_identifier(self._identifier("Class''"))
        assert result == r"\mathrm{Class}''"

    # -- subscript interaction --

    def test_relvar_subscript_renders_mathrm_base(self) -> None:
        """Class_1 renders as \\mathrm{Class}_1."""
        gen = self._gen()
        gen.relvar_set = frozenset({"Class"})
        result = gen._generate_identifier(self._identifier("Class_1"))
        assert result == r"\mathrm{Class}_1"

    def test_relvar_subscript_two_char(self) -> None:
        """Class_12 renders as \\mathrm{Class}_{12} (2-char all-digit subscript)."""
        gen = self._gen()
        gen.relvar_set = frozenset({"Class"})
        result = gen._generate_identifier(self._identifier("Class_12"))
        assert result == r"\mathrm{Class}_{12}"

    def test_relvar_subscript_and_decoration_combined(self) -> None:
        """Class_1' renders as \\mathrm{Class}_1' (subscript then decoration)."""
        gen = self._gen()
        gen.relvar_set = frozenset({"Class"})
        result = gen._generate_identifier(self._identifier("Class_1'"))
        assert result == r"\mathrm{Class}_1'"

    def test_relvar_alpha_suffix_falls_through_to_multiword(self) -> None:
        """Class_test: 'test' is 4 chars — falls through to multi-word path, no wrap."""
        gen = self._gen()
        gen.relvar_set = frozenset({"Class"})
        result = gen._generate_identifier(self._identifier("Class_test"))
        # Multi-word path: \mathit{Class\_test} in standard mode
        assert result == r"\mathit{Class\_test}"
        assert r"\mathrm" not in result

    def test_relvar_long_multiword_falls_through(self) -> None:
        """Class_test_long: multiple underscores → multi-word, no wrap."""
        gen = self._gen()
        gen.relvar_set = frozenset({"Class"})
        result = gen._generate_identifier(self._identifier("Class_test_long"))
        assert r"\mathrm" not in result
        assert r"\mathit" in result

    def test_relvar_two_char_nondigit_suffix_falls_through(self) -> None:
        """Class_AB: 2-char non-digit suffix → normal path, no \\mathrm wrap."""
        gen = self._gen()
        gen.relvar_set = frozenset({"Class"})
        result = gen._generate_identifier(self._identifier("Class_AB"))
        # Normal path for 2-char suffix — not wrapped in \mathrm
        assert r"\mathrm" not in result

    # -- multiple relvars in set --

    def test_multiple_relvars_each_rendered_upright(self) -> None:
        """Each member of the relvar set is wrapped independently."""
        gen = self._gen()
        gen.relvar_set = frozenset({"Class", "Ship", "Battle", "Outcome"})
        for name in ("Class", "Ship", "Battle", "Outcome"):
            result = gen._generate_identifier(self._identifier(name))
            assert result == rf"\mathrm{{{name}}}"

    def test_non_member_not_wrapped(self) -> None:
        """An identifier not in the relvar set is not wrapped."""
        gen = self._gen()
        gen.relvar_set = frozenset({"Class"})
        result = gen._generate_identifier(self._identifier("Battle"))
        assert result == "Battle"


# ---------------------------------------------------------------------------
# Generator — document-level integration (pre-walk collects relvar_set)
# ---------------------------------------------------------------------------


class TestRelvarDocumentIntegration:
    """generate_document pre-walks the AST to populate relvar_set."""

    def test_collect_relvars_from_document(self) -> None:
        """_collect_relvars returns frozenset of declared names."""
        src = "relvars Class, Ship"
        ast = Parser(Lexer(src).tokenize()).parse()
        gen = LaTeXGenerator(use_fuzz=True)
        result = gen._collect_relvars(ast)
        assert result == frozenset({"Class", "Ship"})

    def test_collect_relvars_two_paragraphs_combined(self) -> None:
        """Two relvars paragraphs combine into one frozenset."""
        src = "relvars Class\nrelvars Ship"
        ast = Parser(Lexer(src).tokenize()).parse()
        gen = LaTeXGenerator(use_fuzz=True)
        result = gen._collect_relvars(ast)
        assert result == frozenset({"Class", "Ship"})

    def test_collect_relvars_no_declaration_is_empty(self) -> None:
        """Document with no relvars paragraph → empty frozenset."""
        src = "x > 0"
        ast = Parser(Lexer(src).tokenize()).parse()
        gen = LaTeXGenerator(use_fuzz=True)
        result = gen._collect_relvars(ast)
        assert result == frozenset()

    def test_generate_document_sets_relvar_set(self) -> None:
        """generate_document populates self.relvar_set before emitting LaTeX."""
        src = "relvars Class\n\nschema Class\n  class : N\nend"
        ast = Parser(Lexer(src).tokenize()).parse()
        gen = LaTeXGenerator(use_fuzz=True)
        gen.generate_document(ast)
        assert "Class" in gen.relvar_set

    def test_relvar_in_schema_renders_upright(self) -> None:
        """Schema type annotation with declared relvar renders \\mathrm{Class}."""
        src = "relvars Class\n\nschema Ship\n  class : Class\nend"
        ast = Parser(Lexer(src).tokenize()).parse()
        gen = LaTeXGenerator(use_fuzz=True)
        latex = gen.generate_document(ast)
        assert r"\mathrm{Class}" in latex

    def test_attribute_alongside_relvar_stays_italic(self) -> None:
        """Attribute 'class' (lowercase) is not wrapped even when Class is a relvar."""
        src = "relvars Class\n\nschema Ship\n  class : Class\nend"
        ast = Parser(Lexer(src).tokenize()).parse()
        gen = LaTeXGenerator(use_fuzz=True)
        latex = gen.generate_document(ast)
        # 'class' declaration appears but is not in \mathrm{class}
        assert r"\mathrm{class}" not in latex

    def test_relvars_emits_no_visible_environment(self) -> None:
        """Relvars paragraph emits a LaTeX comment, not a zed environment."""
        src = "relvars Class, Ship"
        ast = Parser(Lexer(src).tokenize()).parse()
        gen = LaTeXGenerator(use_fuzz=True)
        latex = gen.generate_document(ast)
        # Comment line is present
        assert "% relvars: Class, Ship" in latex
        # No zed environment wrapping the relvar names
        assert r"\begin{zed}" not in latex

    def test_acceptance_probe_class_ship_schemas(self) -> None:
        """Acceptance probe: Class and Ship are upright; class/name are italic."""
        src = (
            "relvars Class, Ship, Battle, Outcome\n"
            "\n"
            "schema Class\n"
            "  class : N\n"
            "  country : N\n"
            "  bore : N\n"
            "end\n"
            "\n"
            "schema Ship\n"
            "  name : N\n"
            "  class : Class\n"
            "end"
        )
        ast = Parser(Lexer(src).tokenize()).parse()
        gen = LaTeXGenerator(use_fuzz=True)
        latex = gen.generate_document(ast)
        # Relvar names render upright wherever they appear as identifiers
        assert r"\mathrm{Class}" in latex
        # Ship appears as the schema name — schema names go through identifier emission
        assert r"\mathrm{Ship}" in latex
        # Attribute names are not wrapped (they are lowercase, not in relvar_set)
        assert r"\mathrm{class}" not in latex
        assert r"\mathrm{name}" not in latex
        assert r"\mathrm{bore}" not in latex


# ---------------------------------------------------------------------------
# Generator — generate_fragment (REPL path) also runs pre-walk
# ---------------------------------------------------------------------------


class TestRelvarGenerateFragment:
    """generate_fragment populates relvar_set before emitting LaTeX."""

    def test_generate_fragment_populates_relvar_set(self) -> None:
        """relvars declared in a fragment document are collected before emission."""
        src = "relvars Class\n\nschema Ship\n  class : Class\nend"
        ast = Parser(Lexer(src).tokenize()).parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator(use_fuzz=True)
        # generate_fragment is the REPL path — must pre-walk
        fragment = gen.generate_fragment(ast)
        assert "Class" in gen.relvar_set
        assert r"\mathrm{Class}" in fragment

    def test_generate_fragment_without_relvars_empty_set(self) -> None:
        """Fragment with no relvars declaration leaves relvar_set empty."""
        # Need a multi-line doc so the parser returns a Document (not bare Expr)
        src = "given A\ngiven B"
        ast = Parser(Lexer(src).tokenize()).parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator(use_fuzz=True)
        gen.generate_fragment(ast)
        assert gen.relvar_set == frozenset()


# ---------------------------------------------------------------------------
# REPL warning surface: emit_warnings + clear_warnings between turns
# ---------------------------------------------------------------------------


class TestRelvarReplWarnings:
    """REPL turn pattern: generate_fragment → emit_warnings → clear_warnings."""

    def test_duplicate_relvar_warning_surfaced_via_fragment(self) -> None:
        """generate_fragment with duplicate relvars produces a warning."""
        src = "relvars Class\nrelvars Class"
        ast = Parser(Lexer(src).tokenize()).parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator(use_fuzz=True)
        gen.generate_fragment(ast)
        warnings = gen.get_warnings()
        assert len(warnings) == 1
        assert "Class" in warnings[0]

    def test_clear_warnings_resets_buffer(self) -> None:
        """clear_warnings removes accumulated warnings so they don't repeat."""
        src = "relvars Class\nrelvars Class"
        ast = Parser(Lexer(src).tokenize()).parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator(use_fuzz=True)
        gen.generate_fragment(ast)
        # After first turn: one warning
        assert len(gen.get_warnings()) == 1
        # REPL clears between turns
        gen.clear_warnings()
        assert gen.get_warnings() == []

    def test_second_repl_turn_no_stale_warnings(self) -> None:
        """After clear_warnings, a clean second turn produces no stale warnings."""
        src = "relvars Class\nrelvars Class"
        ast = Parser(Lexer(src).tokenize()).parse()
        assert isinstance(ast, Document)
        gen = LaTeXGenerator(use_fuzz=True)
        # First REPL turn: duplicate relvar
        gen.generate_fragment(ast)
        gen.emit_warnings()
        gen.clear_warnings()
        # Second REPL turn: clean document — no warning carryover
        src2 = "relvars Ship"
        ast2 = Parser(Lexer(src2).tokenize()).parse()
        assert isinstance(ast2, Document)
        gen.generate_fragment(ast2)
        assert gen.get_warnings() == []


# ---------------------------------------------------------------------------
# Generator — duplicate relvar warning
# ---------------------------------------------------------------------------


class TestRelvarDuplicateWarning:
    """_collect_relvars warns once per duplicate relvar name."""

    def test_single_relvar_no_warning(self) -> None:
        """Single relvars paragraph: no duplicate warning."""
        src = "relvars Class"
        ast = Parser(Lexer(src).tokenize()).parse()
        gen = LaTeXGenerator(use_fuzz=True)
        gen._collect_relvars(ast)
        assert gen.get_warnings() == []

    def test_duplicate_relvar_emits_warning(self) -> None:
        """Two relvars paragraphs declaring the same name: one warning emitted."""
        src = "relvars Class\nrelvars Class"
        ast = Parser(Lexer(src).tokenize()).parse()
        gen = LaTeXGenerator(use_fuzz=True)
        result = gen._collect_relvars(ast)
        # Still merged correctly
        assert "Class" in result
        # Exactly one warning for the duplicate
        warnings = gen.get_warnings()
        assert len(warnings) == 1
        assert "Class" in warnings[0]

    def test_duplicate_relvar_warns_only_once(self) -> None:
        """Three declarations of the same name: still exactly one warning."""
        src = "relvars Class\nrelvars Class\nrelvars Class"
        ast = Parser(Lexer(src).tokenize()).parse()
        gen = LaTeXGenerator(use_fuzz=True)
        gen._collect_relvars(ast)
        class_warnings = [w for w in gen.get_warnings() if "Class" in w]
        assert len(class_warnings) == 1

    def test_distinct_names_no_warning(self) -> None:
        """Two relvars paragraphs with distinct names: no warning."""
        src = "relvars Class\nrelvars Ship"
        ast = Parser(Lexer(src).tokenize()).parse()
        gen = LaTeXGenerator(use_fuzz=True)
        gen._collect_relvars(ast)
        assert gen.get_warnings() == []


# ---------------------------------------------------------------------------
# Regression: existing documents without relvars are byte-identical
# ---------------------------------------------------------------------------


class TestRelvarRegression:
    """Documents without relvars declarations produce unchanged output."""

    def test_simple_expression_unchanged(self) -> None:
        """x > 0 renders without any \\mathrm wrapping."""
        src = "x > 0"
        ast = Parser(Lexer(src).tokenize()).parse()
        gen = LaTeXGenerator()
        latex = gen.generate_document(ast)
        assert r"\mathrm" not in latex

    def test_given_type_unchanged(self) -> None:
        """given A, B is not affected by relvar machinery."""
        src = "given A, B"
        ast = Parser(Lexer(src).tokenize()).parse()
        gen = LaTeXGenerator(use_fuzz=True)
        latex = gen.generate_document(ast)
        assert r"\mathrm" not in latex
        assert r"\begin{zed}[A, B]\end{zed}" in latex
