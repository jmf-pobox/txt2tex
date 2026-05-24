"""Parser rules for text and presentation constructs.

Covers: Section, Solution, Part, Paragraph (TEXT:), PureParagraph
(PURETEXT:), LatexBlock (LATEX:), RawLatexBlock, BMachine (B:),
LineBreak, PageBreak, Contents, BibliographyMetadata, PartsFormat
(plus its directive parser), PartsDirective, and TruthTable.

This mixin is composed into :class:`Parser` via multiple inheritance.
Method bodies are byte-identical to their counterparts in the
pre-refactor monolithic ``parser.py``; only their file location has
changed.
"""

from __future__ import annotations

import re

from txt2tex.ast_nodes import (
    BibliographyMetadata,
    BMachine,
    Contents,
    DocumentItem,
    LatexBlock,
    LineBreak,
    PageBreak,
    Paragraph,
    Part,
    PartsFormat,
    PureParagraph,
    RawLatexBlock,
    Section,
    Solution,
    TruthTable,
)
from txt2tex.parser_pkg._base import ParserBase, ParserError
from txt2tex.tokens import TokenType


class _TextBlocksParser(ParserBase):  # pyright: ignore[reportUnusedClass]
    """Mixin: rules for text and presentation constructs."""

    def _parse_paragraph(self) -> Paragraph | Part:
        """Parse plain text paragraph from TEXT token.

        The TEXT token value contains the raw text content (no tokenization).
        If the text starts with a part label like "(a) content...",
        return a Part node containing a Paragraph instead.
        """
        text_token = self._advance()  # Consume TEXT token

        if text_token.type != TokenType.TEXT:
            raise ParserError("Expected TEXT token for paragraph", text_token)

        # The token value contains the raw text (already captured by lexer)
        text = text_token.value

        # Check if text starts with a structural part label at paragraph start.
        # Only short, recognised label forms are promoted to Part nodes:
        # single letter (a)-(z), single digit (1)-(9), or a short Roman numeral.
        # Longer words like (underlined) or (continued) stay as prose text.
        roman_numerals: frozenset[str] = frozenset(
            {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"}
        )
        part_match = re.match(r"^\(([a-z0-9]+)\)\s+(.+)", text, re.IGNORECASE)
        if part_match:
            label = part_match.group(1).lower()
            is_single_letter = len(label) == 1 and label.isalpha()
            is_single_digit = len(label) == 1 and label.isdigit()
            is_roman = label in roman_numerals
            if is_single_letter or is_single_digit or is_roman:
                content = part_match.group(2)
                paragraph = Paragraph(
                    text=content, line=text_token.line, column=text_token.column
                )
                return Part(
                    label=label,
                    items=[paragraph],
                    line=text_token.line,
                    column=text_token.column,
                )

        return Paragraph(text=text, line=text_token.line, column=text_token.column)

    def _parse_paragraph_coalesced(self) -> Paragraph | Part:
        """Parse one or more adjacent TEXT: directives as a single paragraph.

        Adjacent TEXT: lines (separated only by a single newline, no blank
        line between them) are joined into one paragraph separated by a
        single space.  A blank line (two successive NEWLINEs, or any
        non-TEXT structural token) breaks the paragraph.

        Delegates to _parse_paragraph for the first token so the
        part-label promotion rule still applies when the leading TEXT:
        line starts with a recognised structural label like ``(a)``.
        """
        # Parse the first TEXT token (may return a Part for labelled content).
        result = self._parse_paragraph()

        # If the first token produced a Part, do not attempt coalescing —
        # the content already belongs to the Part's item list.
        if isinstance(result, Part):
            return result

        # Coalesce following TEXT tokens that are adjacent (no blank line).
        # A blank line is signalled by two consecutive NEWLINEs or by any
        # token that is not NEWLINE + TEXT.
        accumulated: list[str] = [result.text]
        while True:
            # Peek: is the next token a NEWLINE followed directly by TEXT?
            if not self._match(TokenType.NEWLINE):
                break
            # Save position in case we need to back off.
            saved_pos = self.pos
            self._advance()  # consume the NEWLINE
            if not self._match(TokenType.TEXT):
                # Not followed by TEXT — restore to before the NEWLINE.
                self.pos = saved_pos
                break
            # Check it is not a blank line (another NEWLINE would appear before TEXT).
            # Since we consumed exactly one NEWLINE and the next token is TEXT,
            # this is a single-newline separation — coalesce it.
            text_token = self._advance()  # consume TEXT token
            text = text_token.value
            # Apply the same part-label guard: if this line starts with a
            # structural label, stop coalescing (it forms a new Part).
            roman_numerals: frozenset[str] = frozenset(
                {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"}
            )
            pm = re.match(r"^\(([a-z0-9]+)\)\s+(.+)", text, re.IGNORECASE)
            if pm:
                lbl = pm.group(1).lower()
                if (
                    (len(lbl) == 1 and lbl.isalpha())
                    or (len(lbl) == 1 and lbl.isdigit())
                    or lbl in roman_numerals
                ):
                    # Back off: put pos back before the TEXT token and stop.
                    self.pos = saved_pos
                    break
            accumulated.append(text)

        if len(accumulated) == 1:
            # No coalescing happened; return the already-parsed result.
            return result

        merged_text = " ".join(accumulated)
        return Paragraph(
            text=merged_text,
            line=result.line,
            column=result.column,
        )

    def _parse_pure_paragraph(self) -> PureParagraph:
        """Parse pure text paragraph from PURETEXT token.

        PURETEXT: blocks contain raw text with NO processing:
        - No formula detection
        - No operator conversion
        - Only basic LaTeX escaping applied during generation
        """
        text_token = self._advance()  # Consume PURETEXT token
        if text_token.type != TokenType.PURETEXT:
            raise ParserError("Expected PURETEXT token for pure paragraph", text_token)

        # The token value contains the raw text (already captured by lexer)
        text = text_token.value

        return PureParagraph(text=text, line=text_token.line, column=text_token.column)

    def _parse_latex_block(self) -> LatexBlock:
        """Parse raw LaTeX block from LATEX token.

        LATEX: blocks contain raw LaTeX with NO escaping.
        The LaTeX is passed directly through to the output.
        """
        latex_token = self._advance()  # Consume LATEX token
        if latex_token.type != TokenType.LATEX:
            raise ParserError("Expected LATEX token for LaTeX block", latex_token)

        # The token value contains the raw LaTeX (already captured by lexer)
        latex = latex_token.value

        return LatexBlock(latex=latex, line=latex_token.line, column=latex_token.column)

    def _parse_identifier_document_item(self) -> DocumentItem:
        """Parse document item starting with an IDENTIFIER token.

        Dispatches to free type, horizontal schema definition, or abbreviation
        based on the tokens that follow the identifier.
        Note: Partial support for compound identifiers like "R+ ==" (GitHub #3).
        """
        next_token = self._peek_ahead(1)
        if next_token.type == TokenType.FREE_TYPE:
            return self._parse_free_type()
        if next_token.type == TokenType.DEFS:
            return self._parse_horiz_def()
        has_generics = next_token.type == TokenType.LBRACKET
        if has_generics and self._scan_for_defs_after_brackets(offset=1):
            return self._parse_horiz_def()
        is_abbrev = next_token.type == TokenType.ABBREV
        if not is_abbrev and next_token.type in (
            TokenType.PLUS,
            TokenType.STAR,
            TokenType.TILDE,
        ):
            token_after_postfix = self._peek_ahead(2)
            is_abbrev = token_after_postfix.type == TokenType.ABBREV
        if is_abbrev:
            return self._parse_abbreviation()
        return self._parse_expr()

    def _parse_bracket_document_item(self) -> DocumentItem:
        """Parse document item starting with a left-bracket token.

        Distinguishes bag literals ([[...]]) from abbreviations with generic
        parameters ([X, Y] Name == expression).
        """
        next_token = self._peek_ahead(1)
        if next_token.type == TokenType.LBRACKET:
            return self._parse_expr()
        return self._parse_abbreviation()

    def _parse_parts_directive(self) -> PartsFormat:
        """Parse PARTS directive from PARTS token.

        PARTS directives parsed at document start are the authoritative source;
        one appearing later in content is parsed but has no effect.
        """
        parts_token = self._advance()
        return PartsFormat(
            style=parts_token.value.strip().lower(),
            line=parts_token.line,
            column=parts_token.column,
        )

    def _parse_b_block(self) -> BMachine:
        """Parse B-machine verbatim block from B_BLOCK token.

        The token value is the raw multi-line body (including the final END
        line) already captured by the lexer.  No Z-parser involvement.
        """
        b_token = self._advance()  # Consume B_BLOCK token
        if b_token.type != TokenType.B_BLOCK:
            raise ParserError("Expected B_BLOCK token for B-machine block", b_token)
        return BMachine(body=b_token.value, line=b_token.line, column=b_token.column)

    def _parse_raw_latex_block(self) -> RawLatexBlock:
        """Parse multi-line raw LaTeX block from RAW_LATEX_BLOCK token.

        The token value is the verbatim body already slurped by the lexer
        (body lines only — the END terminator is not included).  Emitted
        directly to .tex output with no escaping and no environment wrapper.
        """
        tok = self._advance()  # Consume RAW_LATEX_BLOCK token
        if tok.type != TokenType.RAW_LATEX_BLOCK:
            raise ParserError(
                "Expected RAW_LATEX_BLOCK token for multi-line LATEX block", tok
            )
        return RawLatexBlock(body=tok.value, line=tok.line, column=tok.column)

    def _parse_pagebreak(self) -> PageBreak:
        """Parse page break from PAGEBREAK token.

        PAGEBREAK: inserts a page break in the PDF output.
        """
        pagebreak_token = self._advance()  # Consume PAGEBREAK token
        if pagebreak_token.type != TokenType.PAGEBREAK:
            raise ParserError("Expected PAGEBREAK token", pagebreak_token)

        return PageBreak(line=pagebreak_token.line, column=pagebreak_token.column)

    def _parse_linebreak(self) -> LineBreak:
        r"""Parse line break (vertical \medskip) from LINEBREAK token.

        LINEBREAK: inserts a medium vertical space in the PDF output.
        """
        linebreak_token = self._advance()  # Consume LINEBREAK token
        if linebreak_token.type != TokenType.LINEBREAK:
            raise ParserError("Expected LINEBREAK token", linebreak_token)

        return LineBreak(line=linebreak_token.line, column=linebreak_token.column)

    def _parse_contents(self) -> Contents:
        """Parse table of contents directive from CONTENTS token.

        CONTENTS: generates table of contents (sections only)
        CONTENTS: full generates table of contents (sections + subsections)
        CONTENTS: 2 also generates table of contents (sections + subsections)
        """
        contents_token = self._advance()  # Consume CONTENTS token
        if contents_token.type != TokenType.CONTENTS:
            raise ParserError("Expected CONTENTS token", contents_token)

        depth = contents_token.value.strip()  # "full", "2", or empty
        return Contents(
            depth=depth, line=contents_token.line, column=contents_token.column
        )

    def _parse_bibliography_metadata(self) -> BibliographyMetadata:
        """Parse bibliography metadata directives.

        Parses BIBLIOGRAPHY: and BIBLIOGRAPHY_STYLE: directives.
        Returns BibliographyMetadata with file and style, or None values
        if not present.
        """
        file: str | None = None
        style: str | None = None

        # Parse BIBLIOGRAPHY: and BIBLIOGRAPHY_STYLE: tokens
        while not self._at_end():
            if self._match(TokenType.BIBLIOGRAPHY):
                token = self._advance()
                file = token.value.strip()
                self._skip_newlines()
            elif self._match(TokenType.BIBLIOGRAPHY_STYLE):
                token = self._advance()
                style = token.value.strip()
                self._skip_newlines()
            elif self._match(
                TokenType.TITLE,
                TokenType.SUBTITLE,
                TokenType.AUTHOR,
                TokenType.DATE,
                TokenType.INSTITUTION,
                TokenType.PARTS,
                TokenType.CONTENTS,
            ):
                # Other metadata directives - stop here, let them be parsed separately
                break
            else:
                # Not a metadata directive - stop parsing metadata
                break

        return BibliographyMetadata(
            file=file if file else None,
            style=style if style else None,
            line=self._current().line if not self._at_end() else 1,
            column=self._current().column if not self._at_end() else 1,
        )

    def _parse_parts_format(self) -> str:
        """Parse parts formatting style from PARTS token.

        PARTS: inline generates inline parts formatting
        PARTS: subsection generates subsection parts formatting (default)
        Returns the style string or "subsection" if not found.
        """
        if self._match(TokenType.PARTS):
            parts_token = self._advance()  # Consume PARTS token
            style = parts_token.value.strip().lower()
            # Validate style
            if style not in ("inline", "subsection"):
                raise ParserError(
                    f"Invalid parts format: {style}. Must be 'inline' or 'subsection'",
                    parts_token,
                )
            self._skip_newlines()  # Skip newlines after PARTS directive
            return style
        return "subsection"  # Default

    def _parse_section(self) -> Section:
        """Parse section: === Title ==="""
        start_token = self._advance()  # Consume first '==='

        # The lexer emits a TEXT token carrying the raw title text between the
        # two === markers (verbatim, stripped of surrounding whitespace).  Fall
        # back to collecting individual tokens for malformed inputs.
        if self._match(TokenType.TEXT):
            title = self._advance().value
            # Consume the closing ===
            if self._match(TokenType.SECTION_MARKER):
                self._advance()
        else:
            # Fallback: collect individual tokens until closing ===.
            title_parts: list[str] = []
            while not self._match(TokenType.SECTION_MARKER) and not self._at_end():
                if self._match(TokenType.NEWLINE):
                    break  # Section title on one line
                title_parts.append(self._current().value)
                self._advance()

            if not self._match(TokenType.SECTION_MARKER):
                raise ParserError("Expected closing '===' for section", self._current())

            self._advance()  # Consume closing '==='
            # Reconstruct title, joining contraction/possessive suffixes directly
            # (no space before tokens that start with apostrophe, e.g. "'s", "'t").
            title_words: list[str] = []
            for part in title_parts:
                if part.startswith("'") and title_words:
                    title_words[-1] += part
                else:
                    title_words.append(part)
            title = " ".join(title_words)

        self._skip_newlines()

        # Parse section content until next section or end
        items: list[DocumentItem] = []
        while not self._at_end() and not self._match(TokenType.SECTION_MARKER):
            items.append(self._parse_document_item())
            self._skip_newlines()

        return Section(
            title=title, items=items, line=start_token.line, column=start_token.column
        )

    def _parse_solution(self) -> Solution:
        """Parse solution: ** Solution N **"""
        start_token = self._advance()  # Consume first '**'

        # Collect solution number/text (all tokens until closing **)
        solution_parts: list[str] = []
        while not self._match(TokenType.SOLUTION_MARKER) and not self._at_end():
            if self._match(TokenType.NEWLINE):
                break  # Solution marker on one line
            solution_parts.append(self._current().value)
            self._advance()

        if not self._match(TokenType.SOLUTION_MARKER):
            raise ParserError("Expected closing '**' for solution", self._current())

        self._advance()  # Consume closing '**'
        # Reconstruct number, joining contraction/possessive suffixes directly.
        number_words: list[str] = []
        for part in solution_parts:
            if part.startswith("'") and number_words:
                number_words[-1] += part
            else:
                number_words.append(part)
        number = " ".join(number_words)
        self._skip_newlines()

        # Parse solution content until next solution/section or end
        items: list[DocumentItem] = []
        while not self._at_end() and not self._match(
            TokenType.SOLUTION_MARKER, TokenType.SECTION_MARKER
        ):
            items.append(self._parse_document_item())
            self._skip_newlines()

        return Solution(
            number=number, items=items, line=start_token.line, column=start_token.column
        )

    def _parse_part(self) -> Part:
        """Parse part: (a) content"""
        part_token = self._advance()  # Consume '(a)', '(b)', etc.

        # Extract label from token value: "(a)" -> "a"
        label = part_token.value[1:-1]
        self._skip_newlines()

        # Parse part content until next part/solution/section or end
        items: list[DocumentItem] = []
        while not self._at_end() and not self._match(
            TokenType.PART_LABEL,
            TokenType.SOLUTION_MARKER,
            TokenType.SECTION_MARKER,
        ):
            items.append(self._parse_document_item())
            self._skip_newlines()

        return Part(
            label=label, items=items, line=part_token.line, column=part_token.column
        )

    def _parse_truth_table(self) -> TruthTable:
        """Parse truth table: TRUTH TABLE: followed by table rows."""
        start_token = self._advance()  # Consume 'TRUTH TABLE:'
        self._skip_newlines()

        # Parse header row (columns separated by |)
        headers: list[str] = []
        if not self._match(TokenType.IDENTIFIER):
            raise ParserError("Expected truth table header row", self._current())

        # Collect columns (tokens between pipes)
        column_tokens: list[str] = []
        while not self._match(TokenType.NEWLINE) and not self._at_end():
            if self._match(TokenType.PIPE):
                # Save current column
                if column_tokens:
                    headers.append(" ".join(column_tokens))
                    column_tokens = []
                self._advance()  # Skip pipe
            elif self._match(
                TokenType.IDENTIFIER,
                TokenType.AND,
                TokenType.OR,
                TokenType.NOT,
                TokenType.IMPLIES,
                TokenType.IFF,
                TokenType.LPAREN,
                TokenType.RPAREN,
            ):
                column_tokens.append(self._current().value)
                self._advance()
            else:
                break

        # Add last column
        if column_tokens:
            headers.append(" ".join(column_tokens))

        if not headers:
            raise ParserError("Expected truth table headers", self._current())

        self._skip_newlines()

        # Parse data rows
        rows: list[list[str]] = []
        while not self._at_end() and not self._is_structural_token():
            row: list[str] = []

            # Check if line starts with T/t or F/f (truth values)
            # Note: F may be lexed as FINSET, P as POWER
            if not self._match(TokenType.IDENTIFIER, TokenType.FINSET, TokenType.POWER):
                break

            first_val = self._current().value
            if first_val.upper() not in ("T", "F", "P"):
                break  # Not a truth table row

            # Collect row values separated by pipes, normalizing to uppercase
            while not self._match(TokenType.NEWLINE) and not self._at_end():
                if self._match(TokenType.PIPE):
                    self._advance()  # Skip pipe
                elif self._match(
                    TokenType.IDENTIFIER, TokenType.FINSET, TokenType.POWER
                ):
                    val = self._current().value
                    # Normalize t/f to T/F
                    row.append(val.upper() if val.upper() in ("T", "F") else val)
                    self._advance()
                else:
                    break

            if row:
                rows.append(row)
            self._skip_newlines()

        return TruthTable(
            headers=headers,
            rows=rows,
            line=start_token.line,
            column=start_token.column,
        )
