"""Regression tests for bug 4: PROOF rule-label typography inconsistency.

Bug: Rule labels without a discharge number (no "from N" or "[N]") fell through
to the fallback path, which wrapped each word in ``\\mbox{}`` and left literal
hyphens between them.  In math mode a bare ``-`` renders as a spaced binary
minus, producing "false - intro" instead of "false\\textrm{-intro}".

Fix: Pattern 3 in ``_format_justification_label`` catches un-discharged labels
of the form ``<op>[\\s-]+(intro|elim)`` and emits the same tight
``{op_latex}\\textrm{-{rule_name}}`` form used by patterns 1 and 2.

Reference: tests/bugs/bug4_proof_label_typography.txt
Mission: m-2026-05-21-010
"""

from __future__ import annotations

import pytest

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def _gen(source: str) -> str:
    """Parse *source* and return the full generated LaTeX document."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    doc = parser.parse()
    gen = LaTeXGenerator(use_fuzz=True)
    return gen.generate_document(doc)


def _label(just: str) -> str:
    """Call ``_format_justification_label`` directly for unit assertions."""
    gen = LaTeXGenerator(use_fuzz=True)
    return gen._format_justification_label(just)


# ---------------------------------------------------------------------------
# Unit tests — _format_justification_label in isolation
# ---------------------------------------------------------------------------


class TestPlainRuleLabelUnit:
    """Pattern 3: plain rule labels without discharge number or subscript."""

    def test_false_intro_hyphen_separator(self) -> None:
        """[false-intro] must produce false\\textrm{-intro}, not two \\mbox{} boxes."""
        result = _label("false-intro")
        assert result == r"false\textrm{-intro}"

    def test_arrow_elim_space_separator(self) -> None:
        """[=> elim] must produce tight \\Rightarrow\\textrm{-elim} form."""
        result = _label("=> elim")
        assert result == r"\Rightarrow\textrm{-elim}"

    def test_and_intro_space_separator(self) -> None:
        """[and intro] must produce \\land\\textrm{-intro}."""
        result = _label("and intro")
        assert result == r"\land\textrm{-intro}"

    def test_lnot_elim_space_separator(self) -> None:
        """[lnot elim] must produce \\lnot\\textrm{-elim}."""
        result = _label("lnot elim")
        assert result == r"\lnot\textrm{-elim}"

    def test_lor_intro(self) -> None:
        """[lor intro] must produce \\lor\\textrm{-intro}."""
        result = _label("lor intro")
        assert result == r"\lor\textrm{-intro}"

    def test_land_elim(self) -> None:
        """[land elim] — land keyword form, not and."""
        result = _label("land elim")
        assert result == r"\land\textrm{-elim}"

    def test_false_elim_hyphen(self) -> None:
        """[false-elim] with hyphen separator."""
        result = _label("false-elim")
        assert result == r"false\textrm{-elim}"


class TestExistingPatternsUnchanged:
    """Patterns 1 and 2 must not regress."""

    def test_discharge_pattern_arrow_intro_from(self) -> None:
        """Pattern 1: [=> intro from 1] remains tight with discharge superscript."""
        result = _label("=> intro from 1")
        assert result == r"\Rightarrow\textrm{-intro}^{[1]}"

    def test_discharge_pattern_false_elim_from(self) -> None:
        """Pattern 1: [false elim from 2] remains tight with discharge superscript."""
        result = _label("false elim from 2")
        assert result == r"false\textrm{-elim}^{[2]}"

    def test_subscript_pattern_land_elim_1(self) -> None:
        """Pattern 2: [land elim 1] remains tight with subscript."""
        result = _label("land elim 1")
        assert result == r"\land\textrm{-elim-1}"

    def test_subscript_pattern_land_elim_2(self) -> None:
        """Pattern 2: [land elim 2] remains tight with subscript."""
        result = _label("land elim 2")
        assert result == r"\land\textrm{-elim-2}"

    def test_subscript_pattern_lor_intro_1(self) -> None:
        """Pattern 2: [lor intro 1] remains tight with subscript."""
        result = _label("lor intro 1")
        assert result == r"\lor\textrm{-intro-1}"


class TestBugSymptomAbsent:
    """Verify the concrete bug symptom is gone: no bare hyphen between mbox boxes."""

    def test_false_intro_no_bare_hyphen_between_mboxes(self) -> None:
        """`false-intro` must not produce \\mbox{false}-\\mbox{intro}."""
        result = _label("false-intro")
        assert r"\mbox{false}-\mbox{intro}" not in result
        assert "-\\mbox" not in result

    def test_arrow_elim_no_trailing_space_mbox(self) -> None:
        """`=> elim` must not produce \\Rightarrow \\mbox{elim} (space + mbox)."""
        result = _label("=> elim")
        assert r"\Rightarrow \mbox{elim}" not in result
        assert r" \mbox{elim}" not in result


# ---------------------------------------------------------------------------
# Integration tests — full PROOF: block round-trip
# ---------------------------------------------------------------------------

_BUG4_SOURCE = """\
PROOF:
((p => q) land lnot q) => lnot p [=> intro from 1]
  [1] (p => q) land lnot q [assumption]
  :: lnot p [false elim from 2]
    [2] p [assumption]
    :: false [false-intro]
      :: q [=> elim]
        :: p => q [land elim 1]
          (p => q) land lnot q [from 1]
        :: p [from 2]
      :: lnot q [land elim 2]
        (p => q) land lnot q [from 1]
"""


class TestBug4RoundTrip:
    """End-to-end: the repro from tests/bugs/bug4_proof_label_typography.txt."""

    def test_generates_without_error(self) -> None:
        """The repro input must parse and generate without raising."""
        latex = _gen(_BUG4_SOURCE)
        assert "\\infer" in latex

    def test_false_intro_tight_in_output(self) -> None:
        """[false-intro] must appear as false\\textrm{-intro} in the document."""
        latex = _gen(_BUG4_SOURCE)
        assert r"false\textrm{-intro}" in latex

    def test_arrow_elim_tight_in_output(self) -> None:
        """[=> elim] must appear as \\Rightarrow\\textrm{-elim} in the document."""
        latex = _gen(_BUG4_SOURCE)
        assert r"\Rightarrow\textrm{-elim}" in latex

    def test_no_bare_hyphen_between_mboxes_in_output(self) -> None:
        """The spaced hyphen artefact must be absent from the generated document."""
        latex = _gen(_BUG4_SOURCE)
        assert r"\mbox{false}-\mbox{intro}" not in latex

    def test_discharge_labels_still_correct(self) -> None:
        """Patterns 1 and 2 must produce correct output in the same document."""
        latex = _gen(_BUG4_SOURCE)
        # Pattern 1: discharge with from N
        assert r"\Rightarrow\textrm{-intro}^{[1]}" in latex
        assert r"false\textrm{-elim}^{[2]}" in latex
        # Pattern 2: subscript
        assert r"\land\textrm{-elim-1}" in latex
        assert r"\land\textrm{-elim-2}" in latex


# ---------------------------------------------------------------------------
# Parametrized round-trip coverage for the four repro cases from the bug file
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("just", "expected"),
    [
        ("false-intro", r"false\textrm{-intro}"),
        ("=> elim", r"\Rightarrow\textrm{-elim}"),
        ("and intro", r"\land\textrm{-intro}"),
        ("lnot elim", r"\lnot\textrm{-elim}"),
    ],
    ids=["false-intro", "arrow-elim", "and-intro", "lnot-elim"],
)
def test_plain_rule_label_parametrized(just: str, expected: str) -> None:
    """All four bug-repro labels produce tight output."""
    assert _label(just) == expected
