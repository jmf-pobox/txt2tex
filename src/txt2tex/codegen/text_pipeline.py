"""Plain-text to LaTeX conversion pipeline.

This module owns the escape-and-parse subsystem that converts user ASCII
text inside ``Paragraph`` (``TEXT:``), ``PureParagraph`` (``PURETEXT:``),
``LatexBlock`` (``LATEX:``), and the inline-text portions of
``_generate_part`` into LaTeX.  The pipeline is leaf-cohesive: every
helper either calls its peers or delegates to ``re``/``str`` primitives;
it never reaches back into the rest of :class:`LaTeXGenerator`.

The entry point is :meth:`_process_paragraph_text`; the other public
helpers (``_escape_latex``, ``_escape_latex_text``) are consumed
elsewhere in the codegen package.

Inline math is opt-in: wrap expressions in ``$whiteboard-expr$`` to
render them as LaTeX math.  Bare prose words pass through with only
LaTeX character escaping applied.
"""

from __future__ import annotations

import re
from typing import Final

from txt2tex.ast_nodes import Expr
from txt2tex.codegen._dispatch import CodegenDispatch
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser, ParserError

# Bare-symbol lookup table (jms-confirmed against bundled fuzz.sty).
# A $...$ span whose stripped content matches exactly one key here is emitted
# as the corresponding LaTeX macro, bypassing the full expression parser.
# Keys are the raw ASCII whiteboard tokens; values are ready-to-use LaTeX.
# Ordered by descending key length to aid readability; lookup is by dict key.
_BARE_SYMBOL: Final[dict[str, str]] = {
    # Arrow / relation / operator family
    "77->": r"\ffun",
    ">->>": r"\bij",
    "+->>": r"\psurj",
    "-->>": r"\surj",
    "|>>": r"\nrres",
    "<<|": r"\ndres",
    "|->": r"\mapsto",
    "<->": r"\rel",
    "-|>": r"\pinj",
    ">+>": r"\pinj",
    ">->": r"\inj",
    "+->": r"\pfun",
    "<|": r"\dres",
    "|>": r"\rres",
    "->": r"\fun",
    "++": r"\oplus",
    "o9": r"\semi",
    "<=>": r"\Leftrightarrow",
    "=>": r"\Rightarrow",
    "<=": r"\leq",
    ">=": r"\geq",
    "/=": r"\neq",
    "\\": r"\setminus",
    "cat": r"\cat",
    "filter": r"\filter",
    # Quantifiers / binders / logical / membership / sets
    "forall": r"\forall",
    "exists": r"\exists",
    "exists1": r"\exists_1",
    "lambda": r"\lambda",
    "mu": r"\mu",
    "land": r"\land",
    "lor": r"\lor",
    "lnot": r"\lnot",
    "elem": r"\in",
    "notin": r"\notin",
    "union": r"\cup",
    "inter": r"\cap",
    "cross": r"\cross",
    "power": r"\power",
    "nat": r"\nat",
    "num": r"\num",
    "emptyset": r"\emptyset",
    "dom": r"\dom",
    "ran": r"\ran",
    # Unicode math symbols (lone references in prose)
    "∈": r"\in",
    "∉": r"\notin",
    "⊆": r"\subseteq",
    "⊂": r"\subset",
    "⊇": r"\supseteq",
    "⊃": r"\supset",
    "∪": r"\cup",  # noqa: RUF001
    "∩": r"\cap",
    "≤": r"\leq",
    "≥": r"\geq",
    "≠": r"\neq",
    "→": r"\rightarrow",
    "←": r"\leftarrow",
    "↔": r"\leftrightarrow",
    "↾": r"\filter",
    "⊎": r"\uplus",
    "⌢": r"\cat",
    "ℕ": r"\nat",  # noqa: RUF001
    "ℤ": r"\num",  # noqa: RUF001
    "×": r"\cross",  # noqa: RUF001
    "∀": r"\forall",
    "∃": r"\exists",
    "∅": r"\emptyset",
    "μ": r"\mu",
    "λ": r"\lambda",
    "∧": r"\land",
    "∨": r"\lor",  # noqa: RUF001
    "¬": r"\lnot",
    "⇒": r"\Rightarrow",
    "⇔": r"\Leftrightarrow",
    "⊢": r"\vdash",
}


def _sanitise_span_for_error(inner: str) -> str:
    """Return *inner* with non-printable characters removed.

    Applied to the raw content of a $...$ span before interpolating it into
    an InlineMathError message, so that control bytes (ESC, BEL, NUL, …) can
    never reach stderr.  Printable ASCII and printable Unicode pass through
    unchanged; Python's ``str.isprintable()`` is the gate.
    """
    return "".join(ch for ch in inner if ch.isprintable())


class InlineMathError(Exception):
    """Raised when a $...$ span in TEXT: prose contains invalid content.

    Two cases trigger this error:

    - A raw LaTeX command inside $...$: any ``\\cmd`` pattern (backslash
      immediately before a letter) must go through a ``LATEX:`` block.
      The whiteboard set-difference operator ``A \\ B`` (backslash + space)
      is allowed.  Use ``$p <=> q$``, ``$forall x : N | P$`` etc. instead.
    - A Z paragraph construct (schema, axdef, gendef, given, ``::=``, ``==``)
      written inline: these are block-level constructs, not expressions.
    """


class _TextPipelineCodegen(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Mixin: plain-text to LaTeX conversion pipeline."""

    def _escape_underscores_outside_math(self, text: str) -> str:
        r"""Escape underscores only when NOT inside $...$ math mode or citations.

        Prevents LaTeX errors when identifiers like count_N appear in prose.
        Math mode already handles underscores as subscripts, so only escape
        underscores in text mode. Also skip underscores in citation keys like
        \citep{author_name_2025}.
        """
        result: list[str] = []
        in_math = False
        in_citation = False
        i = 0

        while i < len(text):
            # Check for $ to toggle math mode
            if text[i] == "$":
                in_math = not in_math
                result.append("$")
                i += 1
            # Check for \citep{ or \cite{ to enter citation mode
            elif not in_math and not in_citation and text[i : i + 7] == r"\citep{":
                in_citation = True
                result.append(r"\citep{")
                i += 7
            elif not in_math and not in_citation and text[i : i + 6] == r"\cite{":
                in_citation = True
                result.append(r"\cite{")
                i += 6
            # Check for } to exit citation mode
            elif in_citation and text[i] == "}":
                in_citation = False
                result.append("}")
                i += 1
            # Escape underscore only outside math mode and citations
            # Skip if already escaped (preceded by backslash)
            elif not in_math and not in_citation and text[i] == "_":
                # Check if underscore is already escaped
                if i > 0 and text[i - 1] == "\\":
                    # Already escaped, just append as-is
                    result.append("_")
                else:
                    # Not escaped, escape it
                    result.append(r"\_")
                i += 1
            else:
                result.append(text[i])
                i += 1

        return "".join(result)

    def _pre_sanitise_dollars(self, text: str) -> str:
        r"""Sanitise dollar signs in TEXT prose before any math parsing.

        Two unsafe patterns are handled:

        1. **``$$``**: display-math delimiters have no meaning in TEXT prose and
           interact badly with the ``$...$`` span splitter.  Every ``$$..$$``
           span (and bare ``$$`` without a matching pair) is replaced with an
           opaque placeholder whose expansion (``\$\$ escaped_content \$\$``)
           is stored in ``_dollar_sanitise_registry``.  The placeholder contains
           no ``$`` or ``\`` so every downstream step ignores it.

        2. **Unbalanced ``$``**: a line with an odd number of ``$`` characters
           would leave a stray ``$`` that silently opens math mode, potentially
           swallowing subsequent prose until the next ``$`` elsewhere in the
           document.  When the count is odd every ``$`` on the line is escaped
           to ``\$``.

        This method must be called *before* ``_process_explicit_dollar_math``
        so that ``$$`` sequences and unbalanced singles never reach the span
        matcher.  Call ``_restore_dollar_sanitise`` at the end of the pipeline
        to expand the placeholders to their final escaped forms.
        """
        self._dollar_sanitise_registry = {}

        def _make_placeholder(escaped_form: str) -> str:
            idx = len(self._dollar_sanitise_registry)
            key = f"\x00DS{idx}\x00"
            self._dollar_sanitise_registry[key] = escaped_form
            return key

        # Pass 1: replace $$...$$ spans with opaque placeholders whose escaped
        # expansion is stored in the registry.  The content between $$ markers
        # is also escaped with \textbackslash{} so no TeX command survives.
        def _escape_dbl_span(m: re.Match[str]) -> str:
            inner = m.group(1) if m.lastindex else ""
            safe_inner = inner.replace("\\", r"\textbackslash{}")
            return _make_placeholder(r"\$\$" + safe_inner + r"\$\$")

        # Match $$...$$ (non-newline content) or bare $$ (empty)
        sanitised = re.sub(r"\$\$([^$\n]*)\$\$", _escape_dbl_span, text)
        # Also escape any remaining bare $$ (e.g. $$\n, or $$ at end of line)
        sanitised = re.sub(r"\$\$", lambda _: _make_placeholder(r"\$\$"), sanitised)

        # Pass 2: count remaining *real* $ characters — those not already
        # escaped as \$.  Mask the user-written \$ first so they do not skew
        # the odd-parity guard: a literal \$ on the line must not cancel out
        # or create an apparent imbalance among the real $...$  spans.
        bs_dollar_mask = "\x00BSDOLLAR\x00"
        masked = sanitised.replace(r"\$", bs_dollar_mask)
        if masked.count("$") % 2 == 1:
            # Odd real $: escape every real $ to \$, then restore masked ones.
            sanitised = masked.replace("$", r"\$").replace(bs_dollar_mask, r"\$")
        else:
            # Even real $: just restore already-escaped ones unchanged.
            sanitised = masked.replace(bs_dollar_mask, r"\$")

        # Pass 3: any $-escaped singles (from Pass 2) also get opaque placeholders
        # so downstream pipeline steps do not see their $ character.
        # Replace \$ (but not already-placeholder content) with a per-instance
        # placeholder so math-tracking loops don't count them.
        return re.sub(
            r"\\\$",
            lambda _m: _make_placeholder(r"\$"),
            sanitised,
        )

    def _restore_dollar_sanitise(self, text: str) -> str:
        """Expand all dollar-sanitise placeholders to their escaped LaTeX forms.

        Must be called at the very end of _process_paragraph_text, after all
        pipeline steps that interpret $ as a math delimiter have finished.
        """
        for key, value in self._dollar_sanitise_registry.items():
            text = text.replace(key, value)
        return text

    def _process_explicit_dollar_math(self, text: str, base_line: int = 1) -> str:
        r"""Parse explicit $...$ inline-math spans through the whiteboard parser.

        Called before any character-escaping so that ^ and other special chars
        inside $...$ are handled by the math parser, not by the prose escaper.

        $...$ is strictly whiteboard notation — the same engine as zed/axdef/schema
        blocks.  Two error conditions are raised:

        1. **Raw LaTeX command in $...$**: raw LaTeX must go through ``LATEX:``
           blocks.  Any ``\\cmd`` pattern (backslash immediately before a letter)
           raises ``InlineMathError``.  The whiteboard set-difference operator
           ``A \\ B`` is allowed because its backslash is followed by a space.
           Write ``$p <=> q$`` (whiteboard) not ``$p \\Leftrightarrow q$``.

        2. **Paragraph construct in $...$**: ``Parser.parse()`` returns a
           ``Document`` when the content is a Z paragraph (schema, axdef, gendef,
           given, ``::=``, ``==``).  These cannot be written inline; raise
           ``InlineMathError``.

        Whiteboard expressions (``Parser.parse()`` returns ``Expr``): rendered via
        ``generate_expr`` with ``_in_z_paragraph=False`` so ``o9`` → ``\semi``.
        If parsing fails (``LexerError``/``ParserError``) the span is left unchanged.

        Stray $$ sequences and unbalanced $ delimiters are handled by
        ``_pre_sanitise_dollars`` before this method is called.
        """
        result = text
        # Match balanced $...$ (non-nested, no newlines inside)
        dollar_pattern = re.compile(r"\$([^$\n]+)\$")
        matches = list(dollar_pattern.finditer(result))

        for match in reversed(matches):
            start = match.start()
            end = match.end()
            inner = match.group(1)

            # Skip if already inside a math span (odd $ count before this match)
            before = result[:start]
            if before.count("$") % 2 == 1:
                continue

            # Source line of this span: base_line plus the number of newlines in
            # the block text before the match.  TEXT: values are single-line
            # captures so before.count("\n") is usually 0; for text with embedded
            # newlines (e.g. constructed in tests) it gives the correct offset.
            actual_line = base_line + before.count("\n")
            span = f"${_sanitise_span_for_error(inner)}$"

            # Bare-symbol fast path: a span containing exactly one known
            # whiteboard token is emitted directly without parsing.
            # This runs BEFORE the strict backslash check so that the lone
            # set-difference backslash ("\\") maps to \setminus cleanly.
            stripped = inner.strip()
            if stripped in _BARE_SYMBOL:
                result = result[:start] + f"${_BARE_SYMBOL[stripped]}$" + result[end:]
                continue

            # Strict: a raw LaTeX command (backslash + letter, e.g. \geq,
            # \forall, \input) in $...$ is an error.  This runs BEFORE parsing so
            # that a raw comparison like "$n \geq 0$" gives a clear error, rather
            # than silently parsing as "n \setminus geq(0)".  Trade-off: the
            # whiteboard set-difference operator must be written with a space
            # ("A \ B"); compact "A\B" is indistinguishable from a raw command
            # here, so it is rejected — the message says how to write it.
            # Control symbols (\%, \_, \\, ...) do not match and are inert in
            # math mode (Phase 1 security review).
            if re.search(r"\\[A-Za-z]", inner):
                msg = (
                    f"line {actual_line}: {span} — "
                    "$...$ takes whiteboard notation only "
                    r"(e.g. $n >= 0$, $forall x : N | P$); "
                    r"raw LaTeX (\geq, \Leftrightarrow) belongs in a LATEX: block. "
                    r"For set difference write $A \ B$ (with a space)."
                )
                raise InlineMathError(msg)

            # Parse as whiteboard math.
            try:
                lexer = Lexer(inner)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()
            except (LexerError, ParserError):
                # Not valid whiteboard math — leave the span unchanged.
                continue

            if isinstance(ast, Expr):
                # Generate with _in_z_paragraph=False (inline context → \semi)
                prev_z = self._in_z_paragraph
                self._in_z_paragraph = False
                try:
                    math_latex = self.generate_expr(ast)
                finally:
                    self._in_z_paragraph = prev_z
                result = result[:start] + f"${math_latex}$" + result[end:]
            elif not ast.items:
                # Empty/whitespace/comment-only span (parse produced a Document
                # with no items) — not a paragraph construct; leave it unchanged,
                # like a parse failure.
                continue
            else:
                # Parser returned a non-empty Document — user wrote a Z paragraph
                # construct inline (schema, axdef, gendef, given, ::=, ==).
                msg = (
                    f"line {actual_line}: {span} — "
                    "$...$ takes an inline Z expression or predicate; "
                    "schema/axdef/gendef/given/::=/== is a block-level Z construct "
                    "— use a schema/axdef/zed block, not inline."
                )
                raise InlineMathError(msg)

        return result

    def _escape_special_chars_outside_math(self, text: str) -> str:
        r"""Escape LaTeX-special characters that appear outside $...$ spans.

        Handles ``\ { } % & # ~ ^`` in each prose segment (outside ``$...$``).
        Leaves characters inside existing ``$...$`` spans untouched.

        Processing order within each prose segment:

        1. Replace ``\``, ``~``, ``^`` with NUL-byte placeholders.  These
           characters expand to LaTeX commands containing ``{}``, so they must
           be shielded before the brace-escaping step (step 4) to prevent
           double-escaping the braces in ``\textbackslash{}``,
           ``\textasciitilde{}``, and ``\textasciicircum{}``.
        2. Escape ``%``, ``&``, ``#`` — none of these expand to ``{}``.
        3. Escape ``{`` → ``\{`` and ``}`` → ``\}``.
        4. Restore placeholders to their final LaTeX forms.

        Note: ``_`` (underscore) is handled separately by
        ``_escape_underscores_outside_math`` at the end of the pipeline,
        because that function also skips underscores inside ``\citep{}`` keys.
        """
        bsl = "\x00BSL\x00"  # placeholder for backslash
        tld = "\x00TLD\x00"  # placeholder for tilde
        crt = "\x00CRT\x00"  # placeholder for caret

        parts: list[str] = []
        # Split on $...$ boundaries; alternate: prose, math, prose, math, ...
        segments = re.split(r"(\$[^$\n]*\$)", text)
        for i, seg in enumerate(segments):
            if i % 2 == 0:
                # Prose segment — use placeholders to shield the braces in the
                # final LaTeX expansions of \, ~, ^ from the {} escaping step.
                seg = seg.replace("\\", bsl)
                seg = seg.replace("~", tld)
                seg = seg.replace("^", crt)
                # Escape characters that expand to safe forms (no braces).
                seg = seg.replace("%", r"\%")
                seg = seg.replace("&", r"\&")
                seg = seg.replace("#", r"\#")
                # Escape braces (safe now: \ ~ ^ placeholders contain no braces).
                seg = seg.replace("{", r"\{")
                seg = seg.replace("}", r"\}")
                # Restore placeholders to their final LaTeX forms.
                seg = seg.replace(bsl, r"\textbackslash{}")
                seg = seg.replace(tld, r"\textasciitilde{}")
                seg = seg.replace(crt, r"\textasciicircum{}")
            parts.append(seg)
        return "".join(parts)

    def _process_paragraph_text(self, text: str, base_line: int = 1) -> str:
        """Process paragraph text through the escape-only pipeline.

        Inline math is opt-in: wrap expressions in ``$...$`` to render them
        as whiteboard math.  Bare prose passes through with only LaTeX
        character escaping applied.

        Pipeline (in order):

        1. ``_pre_sanitise_dollars`` — reject ``$$`` and escape unbalanced
           ``$`` before any span matching.
        2. ``_process_explicit_dollar_math`` — parse ``$...$`` spans through
           the whiteboard math engine.
        3. ``_escape_special_chars_outside_math`` — escape ``\\ { } % & # ~ ^``
           in all prose segments (closes issue #79).
        4. ``_process_citations`` — convert ``[cite key]`` to ``\\citep{key}``.
        5. ``_process_manual_markup`` — convert bracketed operators
           (``[and]``, ``[or]``, ``[not]``) to their LaTeX symbols.
        6. ``_escape_underscores_outside_math`` — escape ``_`` in prose,
           preserving underscores inside ``$...$`` and ``\\citep{}`` keys.
        7. ``_restore_dollar_sanitise`` — expand sanitised-dollar placeholders.

        ``base_line`` is the 1-indexed source line of the enclosing paragraph
        node, threaded into ``_process_explicit_dollar_math`` for error messages.
        """
        text = self._pre_sanitise_dollars(text)
        text = self._process_explicit_dollar_math(text, base_line)
        text = self._escape_special_chars_outside_math(text)
        text = self._process_citations(text)
        text = self._process_manual_markup(text)
        text = self._escape_underscores_outside_math(text)
        return self._restore_dollar_sanitise(text)

    def _process_citations(self, text: str) -> str:
        """Process citation markup in text.

        Converts [cite key] to \\citep{key} for Harvard-style parenthetical citations.
        Supports optional page/slide numbers.

        Examples:
            "[cite spivey92]" → "\\citep{spivey92}"
            "[cite spivey92 p. 42]" → "\\citep[p. 42]{spivey92}"
            "[cite spivey92 p. 42]" → "\\citep[p. 42]{spivey92}"
            "[cite woodcock96 pp. 10-15]" → "\\citep[pp. 10-15]{woodcock96}"

        The citation key can contain letters, numbers, hyphens, and underscores.
        The locator (page/slide) can contain any text after the key.
        """
        # Pattern: [cite key optional-locator]
        # Capture key (alphanumeric with hyphens/underscores) and optional locator text
        # Example: [cite spivey92 p. 42] → \citep[p. 42]{spivey92}
        pattern = r"\[cite\s+([a-zA-Z0-9_-]+)(?:\s+([^\]]+))?\]"

        def replace_citation(match: re.Match[str]) -> str:
            key = match.group(1)
            locator = match.group(2)
            if locator:
                # Strip leading/trailing whitespace from locator
                locator = locator.strip()
                return f"\\citep[{locator}]{{{key}}}"
            return f"\\citep{{{key}}}"

        return re.sub(pattern, replace_citation, text)

    def _process_manual_markup(self, text: str) -> str:
        """Convert bracketed operator markup to LaTeX symbols.

        Converts explicit markup like [and], [or], [not] to LaTeX symbols.
        This is explicit opt-in notation, not auto-detection.

        Example: "([not], [and], [or])" becomes "($\\lnot$, $\\land$, $\\lor$)"
        """
        result = text
        markup_operators = {
            r"\[not\]": r"$\\lnot$",
            r"\[and\]": r"$\\land$",
            r"\[or\]": r"$\\lor$",
            r"\[=>\]": r"$\\Rightarrow$",
            r"\[<=>\]": r"$\\Leftrightarrow$",
            r"\[forall\]": r"$\\forall$",
            r"\[exists\]": r"$\\exists$",
            r"\[exists1\]": r"$\\exists_1$",
        }

        for pattern, replacement in markup_operators.items():
            result = re.sub(pattern, replacement, result)

        return result

    def _convert_operators_to_latex(self, text: str) -> str:
        """Convert operator keywords to LaTeX symbols in text.

        Used by truth-table header processing in text_blocks.py.  Headers
        are already inside ``$...$`` math mode when this is called, so no
        math-mode wrapping is added here.
        """
        # Replace operators with LaTeX commands using word boundaries
        # Order matters: replace longer operators first
        result = text.replace("<=>", r"\Leftrightarrow")
        result = result.replace("=>", r"\Rightarrow")
        # Only LaTeX-style keywords supported: land, lor, lnot, elem
        result = re.sub(r"\bland\b", r"\\land", result)
        result = re.sub(r"\blor\b", r"\\lor", result)
        result = re.sub(r"\blnot\b", r"\\lnot", result)
        return re.sub(r"\belem\b", r"\\in", result)

    def _escape_latex(self, text: str) -> str:
        """Escape LaTeX special characters.

        Escapes: & % $ # _ { } ~ ^ \
        Does NOT convert operators or detect formulas.
        """
        # Escape backslash first to avoid double-escaping
        result = text.replace("\\", r"\textbackslash{}")
        # Escape other special characters
        result = result.replace("&", r"\&")
        result = result.replace("%", r"\%")
        result = result.replace("$", r"\$")
        result = result.replace("#", r"\#")
        result = result.replace("_", r"\_")
        result = result.replace("{", r"\{")
        result = result.replace("}", r"\}")
        result = result.replace("~", r"\textasciitilde{}")
        return result.replace("^", r"\textasciicircum{}")

    def _escape_latex_text(self, text: str) -> str:
        """Escape LaTeX-unsafe characters for verbatim heading text.

        Used for section and subsection headings where the text should pass
        through verbatim.  Only characters that are structurally significant
        to LaTeX are escaped; punctuation like ``-``, ``(``, ``)``, ``:`` and
        ``.`` is left untouched.

        Escaped: \\ → \\textbackslash{}, & → \\&, % → \\%,
                 $ → \\$, # → \\#, _ → \\_, { → \\{, } → \\},
                 ~ → \\textasciitilde{}, ^ → \\textasciicircum{}.
        NOT escaped: ( ) : . - (safe in LaTeX text mode).
        """
        # Escape backslash first to avoid double-escaping later replacements.
        result = text.replace("\\", r"\textbackslash{}")
        result = result.replace("&", r"\&")
        result = result.replace("%", r"\%")
        result = result.replace("$", r"\$")
        result = result.replace("#", r"\#")
        result = result.replace("_", r"\_")
        result = result.replace("{", r"\{")
        result = result.replace("}", r"\}")
        result = result.replace("~", r"\textasciitilde{}")
        return result.replace("^", r"\textasciicircum{}")
