"""Tests for the NOFUZZ modifier: a one-line prefix marking the immediately
following box paragraph (axdef/schema/gendef/given type/free type/
abbreviation) as genuine Z that renders but is not fuzz-type-checked.

Covers lexing (mandatory reason, no slurped body), parsing (the marked
node's own grammar, unchanged, plus ``nofuzz_reason`` stamped on it via
``dataclasses.replace``), codegen (the ``*nofuzz`` twin per box kind,
reason escaping, zed consolidation-break), and the CLI reject-if-clean
lint (a NOFUZZ box that type-checks cleanly on its own is a mislabeled
waiver).
"""

from __future__ import annotations

import dataclasses
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from txt2tex.ast_nodes import (
    Abbreviation,
    AxDef,
    Document,
    FreeType,
    GenDef,
    GivenType,
    Schema,
)
from txt2tex.cli import lint_nofuzz_block, main
from txt2tex.codegen.paragraphs import (
    NoFuzzGenDefNotImplementedError,
    NoFuzzLintItem,
    NoFuzzUnsupportedError,
)
from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser, ParserError


def _fuzz_available() -> bool:
    """Return True when the fuzz binary is on PATH."""
    return shutil.which("fuzz") is not None


def _parse(source: str) -> Document:
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    assert isinstance(ast, Document)
    return ast


def _lex_and_parse(source: str) -> Document | object:
    """Lex and parse in one call, for use as pytest.raises' single statement."""
    return Parser(Lexer(source).tokenize()).parse()


def _parse_and_generate(source: str) -> str:
    ast = _parse(source)
    return LaTeXGenerator(use_fuzz=True).generate_document(ast)


# ---------------------------------------------------------------------------
# Lexer: mandatory reason, one-line modifier (no slurped body)
# ---------------------------------------------------------------------------


def test_missing_reason_raises_lexer_error():
    """A NOFUZZ: header with no reason is a lex error, not a silent no-op."""
    source = "NOFUZZ:\naxdef\n  n : N\nwhere\n  n = n\nend\n"
    with pytest.raises(LexerError) as exc_info:
        Lexer(source).tokenize()
    assert "reason" in str(exc_info.value)


def test_whitespace_only_reason_raises_lexer_error():
    """A reason of only whitespace is treated as no reason at all."""
    source = "NOFUZZ:   \naxdef\n  n : N\nwhere\n  n = n\nend\n"
    with pytest.raises(LexerError):
        Lexer(source).tokenize()


def test_reason_is_rest_of_header_line():
    """The reason is captured verbatim to end of line -- no END, no body slurp."""
    tokens = Lexer("NOFUZZ: fuzz reads ^ as relational iteration\ngiven A\n").tokenize()
    nofuzz_tokens = [t for t in tokens if t.type.name == "NOFUZZ"]
    assert len(nofuzz_tokens) == 1
    assert nofuzz_tokens[0].value == "fuzz reads ^ as relational iteration"


# ---------------------------------------------------------------------------
# Parser: NOFUZZ stamps nofuzz_reason via the box paragraph's normal grammar
# ---------------------------------------------------------------------------


def test_nofuzz_axdef_matches_locked_spec_example():
    """The exact example from the locked spec parses to a NOFUZZ-marked AxDef."""
    source = (
        "NOFUZZ: fuzz reads ^ as relational iteration, not exponentiation\n"
        "axdef\n"
        "  square : N -> N\n"
        "where\n"
        "  forall n : N | square(n) = n^2\n"
        "end\n"
    )
    doc = _parse(source)
    node = doc.items[0]
    assert isinstance(node, AxDef)
    assert node.nofuzz_reason == (
        "fuzz reads ^ as relational iteration, not exponentiation"
    )


def test_nofuzz_schema():
    source = "NOFUZZ: reason\nschema Foo\n  n : N\nwhere\n  n = n^2\nend\n"
    doc = _parse(source)
    node = doc.items[0]
    assert isinstance(node, Schema)
    assert node.name == "Foo"
    assert node.nofuzz_reason == "reason"


def test_nofuzz_gendef_parses_but_is_marked():
    """gendef NOFUZZ parses fine at the AST level; codegen rejects it later."""
    source = (
        "NOFUZZ: reason\ngendef [X]\n  f : X -> X\nwhere\n"
        "  forall x : X | f(x) = x\nend\n"
    )
    doc = _parse(source)
    node = doc.items[0]
    assert isinstance(node, GenDef)
    assert node.nofuzz_reason == "reason"


def test_nofuzz_given_type():
    doc = _parse("NOFUZZ: reason\ngiven A, B\n")
    node = doc.items[0]
    assert isinstance(node, GivenType)
    assert node.names == ["A", "B"]
    assert node.nofuzz_reason == "reason"


def test_nofuzz_free_type():
    doc = _parse("NOFUZZ: reason\nStatus ::= active | inactive\n")
    node = doc.items[0]
    assert isinstance(node, FreeType)
    assert node.name == "Status"
    assert node.nofuzz_reason == "reason"


def test_nofuzz_abbreviation():
    doc = _parse("NOFUZZ: reason\nSq == n^2\n")
    node = doc.items[0]
    assert isinstance(node, Abbreviation)
    assert node.name == "Sq"
    assert node.nofuzz_reason == "reason"


def test_reason_with_colon_preserved():
    """A reason containing its own colon is captured in full (rest of line)."""
    doc = _parse("NOFUZZ: see RM 3.4: fuzz misreads ^\ngiven A\n")
    node = doc.items[0]
    assert isinstance(node, GivenType)
    assert node.nofuzz_reason == "see RM 3.4: fuzz misreads ^"


def test_nofuzz_not_followed_by_box_paragraph_raises_parser_error():
    """NOFUZZ before prose (not a box paragraph) is a ParserError, not silent."""
    source = "NOFUZZ: reason\nTEXT: hello\n"
    with pytest.raises(ParserError) as exc_info:
        _lex_and_parse(source)
    assert "axdef, schema, gendef, given type, free type, or abbreviation" in str(
        exc_info.value
    )
    assert "Paragraph" in str(exc_info.value)


def test_nofuzz_at_end_of_input_raises_parser_error():
    """NOFUZZ with nothing following it at all is a ParserError."""
    source = "NOFUZZ: reason\n"
    with pytest.raises(ParserError) as exc_info:
        _lex_and_parse(source)
    assert "axdef, schema, gendef, given type, free type, or abbreviation" in str(
        exc_info.value
    )


# ---------------------------------------------------------------------------
# Codegen: each box kind emits its correct twin
# ---------------------------------------------------------------------------


def test_axdef_emits_axdefnofuzz_twin_with_reason_and_body():
    """axdef NOFUZZ emits axdefnofuzz{reason}, never axdef, same body."""
    source = (
        "NOFUZZ: fuzz reads ^ as relational iteration, not exponentiation\n"
        "axdef\n"
        "  square : N -> N\n"
        "where\n"
        "  forall n : N | square(n) = n^2\n"
        "end\n"
    )
    latex = _parse_and_generate(source)
    assert (
        r"\begin{axdefnofuzz}{fuzz reads \textasciicircum{} as relational "
        r"iteration, not exponentiation}" in latex
    )
    assert r"\end{axdefnofuzz}" in latex
    assert r"\begin{axdef}" not in latex
    assert r"\end{axdef}" not in latex
    assert r"square : \nat \fun \nat" in latex
    assert r"\forall n : \nat @ square(n) = n \bsup 2 \esup" in latex


def test_given_type_emits_zednofuzz_twin():
    latex = _parse_and_generate("NOFUZZ: reason\ngiven A, B\n")
    assert r"\begin{zednofuzz}{reason}[A, B]\end{zednofuzz}" in latex
    assert r"\begin{zed}" not in latex


def test_free_type_emits_zednofuzz_twin():
    latex = _parse_and_generate("NOFUZZ: reason\nStatus ::= active | inactive\n")
    assert (
        r"\begin{zednofuzz}{reason}Status ::= active | inactive\end{zednofuzz}" in latex
    )
    assert r"\begin{zed}" not in latex


def test_abbreviation_emits_zednofuzz_twin():
    latex = _parse_and_generate("NOFUZZ: reason\nSq == n^2\n")
    assert r"\begin{zednofuzz}{reason}" in latex
    assert r"Sq == n \bsup 2 \esup" in latex
    assert r"\end{zednofuzz}" in latex
    assert r"\begin{zed}" not in latex


def test_schema_emits_two_arg_schemanofuzz_twin():
    """schema NOFUZZ emits schemanofuzz{name}{reason} -- TWO args, name first."""
    source = "NOFUZZ: schema reason\nschema Foo\n  n : N\nwhere\n  n = n^2\nend\n"
    latex = _parse_and_generate(source)
    assert r"\begin{schemanofuzz}{Foo}{schema reason}" in latex
    assert r"\end{schemanofuzz}" in latex
    assert r"\begin{schema}" not in latex
    assert r"n = n \bsup 2 \esup" in latex


def test_gendef_nofuzz_raises_not_implemented_error():
    """No gendefnofuzz environment exists yet -- codegen rejects, doesn't emit it."""
    source = (
        "NOFUZZ: reason\ngendef [X]\n  f : X -> X\nwhere\n"
        "  forall x : X | f(x) = x\nend\n"
    )
    doc = _parse(source)
    with pytest.raises(NoFuzzGenDefNotImplementedError) as exc_info:
        LaTeXGenerator(use_fuzz=True).generate_document(doc)
    assert "gendefnofuzz not yet implemented" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Codegen: reason escaping (CRITICAL -- ^ and _ are common in real reasons)
# ---------------------------------------------------------------------------


def test_reason_escapes_caret():
    latex = _parse_and_generate("NOFUZZ: fuzz reads ^ as iteration\ngiven A\n")
    assert r"\textasciicircum{}" in latex
    assert "reads ^ as" not in latex


def test_reason_escapes_underscore():
    latex = _parse_and_generate("NOFUZZ: fuzz misreads relation_iteration\ngiven A\n")
    assert r"relation\_iteration" in latex
    assert "relation_iteration" not in latex


def test_reason_escapes_caret_and_underscore_together():
    """The exact combination the locked spec calls out as CRITICAL."""
    latex = _parse_and_generate(
        "NOFUZZ: fuzz reads n^2 as iter_2 not exponentiation\ngiven A\n"
    )
    assert r"n\textasciicircum{}2" in latex
    assert r"iter\_2" in latex


# ---------------------------------------------------------------------------
# Codegen: zed consolidation-break
# ---------------------------------------------------------------------------


def test_nofuzz_zed_item_breaks_consolidation():
    """A NOFUZZ-marked item never joins a consolidated zed run.

    A checked run before it and a checked run after it still consolidate
    normally; the NOFUZZ item renders alone in its own zednofuzz box.
    """
    source = "given A\ngiven B\nNOFUZZ: mid reason\ngiven C\ngiven D\ngiven E\n"
    latex = _parse_and_generate(source)
    # Checked run before: A and B consolidated into one zed with \also.
    assert r"\begin{zed}" in latex
    assert "[A]" in latex
    assert "[B]" in latex
    assert r"\also" in latex
    # NOFUZZ item alone in its own box.
    assert r"\begin{zednofuzz}{mid reason}[C]\end{zednofuzz}" in latex
    # Checked run after: D and E consolidated into their own zed with \also.
    zed_envs = latex.count(r"\begin{zed}")
    assert zed_envs == 2  # [A, B] run and [D, E] run, each its own box
    assert "[D]" in latex
    assert "[E]" in latex


def test_nofuzz_lint_items_staged_per_box_kind():
    """Each nofuzz_reason box stages a probe_snippet wrapped in its own kind."""
    source = (
        "NOFUZZ: axdef reason\naxdef\n  n : N\nwhere\n  n = n^2\nend\n"
        "\n"
        "NOFUZZ: given reason\ngiven A\n"
    )
    doc = _parse(source)
    generator = LaTeXGenerator(use_fuzz=True)
    generator.generate_document(doc)
    assert len(generator.nofuzz_lint_items) == 2
    axdef_item, given_item = generator.nofuzz_lint_items
    assert axdef_item.reason == "axdef reason"
    assert axdef_item.probe_snippet.startswith(r"\begin{axdef}")
    assert axdef_item.probe_snippet.endswith(r"\end{axdef}")
    assert given_item.reason == "given reason"
    assert given_item.probe_snippet == r"\begin{zed}[A]\end{zed}"


# ---------------------------------------------------------------------------
# CLI lint: reject-if-clean (unit level, real fuzz)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not installed")
def test_lint_rejects_clean_typechecking_content():
    """fuzz accepting a NOFUZZ probe cleanly means the waiver is a lie -- reject."""
    item = NoFuzzLintItem(
        line=3, reason="reason", probe_snippet=r"\begin{zed}[A, B]\end{zed}"
    )
    assert lint_nofuzz_block(item) is False


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not installed")
def test_lint_accepts_genuinely_unparseable_content():
    """fuzz genuinely rejecting the probe (the ^ misparse) justifies the waiver."""
    item = NoFuzzLintItem(
        line=3,
        reason="reason",
        probe_snippet=(
            r"\begin{axdef}"
            "\n"
            r"square : \nat \fun \nat"
            "\n"
            r"\where"
            "\n"
            r"\forall n : \nat @ square(n) = n \bsup 2 \esup"
            "\n"
            r"\end{axdef}"
        ),
    )
    assert lint_nofuzz_block(item) is True


def test_lint_skips_when_fuzz_absent():
    """No fuzz binary on PATH -> lint is skipped (None), never a hard failure."""
    item = NoFuzzLintItem(
        line=3, reason="reason", probe_snippet=r"\begin{zed}[A, B]\end{zed}"
    )
    with patch("shutil.which", return_value=None):
        assert lint_nofuzz_block(item) is None


# ---------------------------------------------------------------------------
# CLI end-to-end: build fails/succeeds based on the lint outcome
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not installed")
def test_cli_build_fails_when_nofuzz_content_is_clean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A NOFUZZ box wrapping trivially-clean content fails the build."""
    input_file = tmp_path / "clean_nofuzz.txt"
    input_file.write_text("NOFUZZ: should have been a plain given\ngiven A, B\n")
    with patch.object(sys, "argv", ["txt2tex", str(input_file), "--tex-only"]):
        result = main()
    assert result == 1
    captured = capsys.readouterr()
    assert "type-checks cleanly under fuzz" in captured.err
    assert "use a plain box instead" in captured.err


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not installed")
def test_cli_build_succeeds_when_nofuzz_content_genuinely_fails(
    tmp_path: Path,
) -> None:
    """A NOFUZZ axdef wrapping genuinely-unparseable content passes the build."""
    input_file = tmp_path / "genuine_nofuzz.txt"
    input_file.write_text(
        "NOFUZZ: fuzz reads ^ as relational iteration, not exponentiation\n"
        "axdef\n"
        "  square : N -> N\n"
        "where\n"
        "  forall n : N | square(n) = n^2\n"
        "end\n"
    )
    with patch.object(sys, "argv", ["txt2tex", str(input_file), "--tex-only"]):
        result = main()
    assert result == 0
    output_file = input_file.with_suffix(".tex")
    latex = output_file.read_text()
    assert r"\begin{axdefnofuzz}" in latex


@pytest.mark.skipif(not _fuzz_available(), reason="fuzz binary not installed")
def test_cli_document_with_axdef_and_nofuzz_axdef_still_typechecks(
    tmp_path: Path,
) -> None:
    """fuzz skips axdefnofuzz structurally: a real axdef alongside NOFUZZ
    still gets type-checked, and the whole build succeeds."""
    input_file = tmp_path / "mixed.txt"
    input_file.write_text(
        "axdef\n"
        "  population : N\n"
        "where\n"
        "  population > 0\n"
        "end\n"
        "\n"
        "NOFUZZ: fuzz reads ^ as relational iteration, not exponentiation\n"
        "axdef\n"
        "  square : N -> N\n"
        "where\n"
        "  forall n : N | square(n) = n^2\n"
        "end\n"
    )
    with patch.object(sys, "argv", ["txt2tex", str(input_file), "--tex-only"]):
        result = main()
    assert result == 0


def test_cli_gendef_nofuzz_error_surfaces_cleanly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """NoFuzzGenDefNotImplementedError is caught -- one clean error, no traceback."""
    input_file = tmp_path / "gendef_nofuzz.txt"
    input_file.write_text(
        "NOFUZZ: reason\ngendef [X]\n  f : X -> X\nwhere\n"
        "  forall x : X | f(x) = x\nend\n"
    )
    with patch.object(sys, "argv", ["txt2tex", str(input_file), "--tex-only"]):
        result = main()
    assert result == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "gendefnofuzz not yet implemented" in captured.err
    assert "Traceback" not in captured.err


def test_cli_nofuzz_lint_skipped_when_fuzz_not_installed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """No fuzz on PATH: the NOFUZZ lint degrades gracefully, build still succeeds."""
    input_file = tmp_path / "clean_nofuzz.txt"
    input_file.write_text("NOFUZZ: should have been a plain given\ngiven A, B\n")
    with (
        patch.object(sys, "argv", ["txt2tex", str(input_file), "--tex-only"]),
        patch("shutil.which", return_value=None),
    ):
        result = main()
    assert result == 0
    captured = capsys.readouterr()
    assert "Skipping NOFUZZ lint" in captured.err


# ---------------------------------------------------------------------------
# Rejections: unsupported NOFUZZ targets (generics, --zed, stacked modifiers)
# ---------------------------------------------------------------------------


def test_nofuzz_schema_with_generics_raises() -> None:
    """A generic schema cannot be a NOFUZZ twin -- the env takes no generics."""
    doc = _parse("NOFUZZ: r\nschema S[X]\n  x : X\nwhere\n  x = x\nend\n")
    with pytest.raises(NoFuzzUnsupportedError) as exc_info:
        LaTeXGenerator(use_fuzz=True).generate_document(doc)
    assert "generic parameters" in str(exc_info.value)


def test_nofuzz_axdef_with_generics_raises() -> None:
    """A generic axdef cannot be a NOFUZZ twin -- the env takes no generics."""
    doc = _parse("NOFUZZ: r\naxdef\n  n : N\nwhere\n  n = n\nend\n")
    axdef = doc.items[0]
    assert isinstance(axdef, AxDef)
    doc.items[0] = dataclasses.replace(axdef, generic_params=["X"])
    with pytest.raises(NoFuzzUnsupportedError) as exc_info:
        LaTeXGenerator(use_fuzz=True).generate_document(doc)
    assert "generic parameters" in str(exc_info.value)


def test_nofuzz_in_zed_mode_raises() -> None:
    """NOFUZZ has no meaning and no defined env in zed-cm (--zed) mode."""
    doc = _parse("NOFUZZ: fuzz reads ^ as iteration\ngiven A\n")
    with pytest.raises(NoFuzzUnsupportedError) as exc_info:
        LaTeXGenerator(use_fuzz=False).generate_document(doc)
    assert "--zed" in str(exc_info.value)


def test_cli_nofuzz_zed_mode_error_surfaces_cleanly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--zed + NOFUZZ is one clean error, not an undefined-env LaTeX crash."""
    input_file = tmp_path / "zed_nofuzz.txt"
    input_file.write_text("NOFUZZ: fuzz reads ^ as iteration\ngiven A\n")
    with patch.object(sys, "argv", ["txt2tex", str(input_file), "--zed", "--tex-only"]):
        result = main()
    assert result == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "--zed" in captured.err
    assert "Traceback" not in captured.err


def test_consecutive_nofuzz_raises_parser_error() -> None:
    """Stacking NOFUZZ: on NOFUZZ: is rejected, not silently collapsed."""
    source = "NOFUZZ: a\nNOFUZZ: b\naxdef\n  n : N\nwhere\n  n = n\nend\n"
    with pytest.raises(ParserError) as exc_info:
        _lex_and_parse(source)
    assert "twice" in str(exc_info.value)


def test_nofuzz_on_relational_algebra_abbreviation_raises() -> None:
    """RA abbreviations render as display math outside any box; fuzz never
    checks them, so a NOFUZZ waiver has nothing to waive -- reject rather
    than silently drop the note (the RA branch used to ignore the modifier)."""
    doc = _parse("NOFUZZ: fuzz reads ^ as iteration\nR == S join T\n")
    with pytest.raises(NoFuzzUnsupportedError) as exc_info:
        LaTeXGenerator(use_fuzz=True).generate_document(doc)
    assert "relational-algebra" in str(exc_info.value)


def test_nofuzz_declared_names_are_not_fuzz_visible() -> None:
    """A name declared in a NOFUZZ box must not enter _fuzz_declared_names.

    The *nofuzz environment is skipped by fuzz's scanner, so its declared
    names are invisible to the type-checker; treating them as fuzz-declared
    would wrongly un-taint later RA references or make a checked box look as
    if fuzz had seen the declaration. The identical checked axdef DOES declare
    the name -- the contrast is the whole point.
    """
    nofuzz_src = (
        "NOFUZZ: fuzz reads ^ as iteration\n"
        "axdef\n  square : N -> N\nwhere\n  forall n : N | square(n) = n^2\nend\n"
    )
    gen = LaTeXGenerator(use_fuzz=True)
    gen.generate_document(_parse(nofuzz_src))
    assert "square" not in gen._fuzz_declared_names

    checked_src = "axdef\n  square : N -> N\nwhere\n  square(0) = 0\nend\n"
    checked_gen = LaTeXGenerator(use_fuzz=True)
    checked_gen.generate_document(_parse(checked_src))
    assert "square" in checked_gen._fuzz_declared_names
