"""Codegen handlers for text and presentation constructs.

Covers: Section, Solution, Part, Paragraph (``TEXT:``), PureParagraph
(``PURETEXT:``), LatexBlock (``LATEX:``), RawLatexBlock, BMachine
(``B:``), LineBreak, PageBreak, Contents, PartsFormat, TruthTable.

This mixin is composed into :class:`LaTeXGenerator` via multiple
inheritance.  Methods are byte-identical to their counterparts in the
pre-refactor monolithic ``latex_gen.py``; only their file location has
changed.
"""

from __future__ import annotations

from txt2tex.ast_nodes import (
    BMachine,
    Contents,
    Expr,
    LatexBlock,
    LineBreak,
    PageBreak,
    Paragraph,
    Part,
    PartsFormat,
    ProofTree,
    PureParagraph,
    RawLatexBlock,
    Section,
    Solution,
    TruthTable,
)
from txt2tex.codegen._dispatch import CodegenDispatch, item_register
from txt2tex.codegen._toc import toc_depth_from_keyword


class _TextBlocksCodegen(CodegenDispatch):  # pyright: ignore[reportUnusedClass]
    """Mixin: handlers for text and presentation constructs."""

    @item_register.register(PageBreak)
    def _generate_pagebreak(self, node: PageBreak) -> list[str]:
        """Generate LaTeX for page break.

        PAGEBREAK: inserts a page break in PDF output.
        """
        return [r"\newpage", ""]

    @item_register.register(Section)
    def _generate_section(self, node: Section) -> list[str]:
        """Generate LaTeX for section."""
        lines: list[str] = []
        # Use _escape_latex_text: the raw title is already verbatim (captured
        # by the lexer without math-pipeline spacing).  Only LaTeX-unsafe
        # characters need escaping; punctuation like - ( ) : . is safe in text mode.
        title = self._escape_latex_text(node.title)
        lines.append(r"\section*{" + title + "}")
        if self._toc_depth >= 1:
            lines.append(r"\addcontentsline{toc}{section}{" + title + "}")
        lines.append("")

        for item in node.items:
            item_lines = self.generate_document_item(item)
            lines.extend(item_lines)

        return lines

    @item_register.register(Solution)
    def _generate_solution(self, node: Solution) -> list[str]:
        """Generate LaTeX for solution as unnumbered subsection."""
        lines: list[str] = []
        lines.append(r"\subsection*{" + node.number + "}")
        if self._toc_depth >= 2:
            lines.append(r"\addcontentsline{toc}{subsection}{" + node.number + "}")
        lines.append("")

        # Track first part in solution for indentation
        self._first_part_in_solution = True
        # Use consolidation logic for items within solution
        lines.extend(self._generate_document_items_with_consolidation(node.items))
        self._first_part_in_solution = False

        return lines

    @item_register.register(Part)
    def _generate_part(self, node: Part) -> list[str]:
        r"""Generate LaTeX for part label.

        If parts_format is "subsection": generates \subsection*{(a)} heading
        If parts_format is "inline": generates (a) followed by content inline
        """
        lines: list[str] = []
        part_label = "(" + node.label + ")"

        if self.parts_format == "inline":
            # Inline formatting: (a) content
            # All parts indented consistently using \noindent\hspace*{\parindent}
            # \noindent prevents LaTeX auto-indent, \hspace*{\parindent} adds our indent
            indent_prefix = r"\noindent\hspace*{\parindent}"
            # Add vertical spacing before parts that are not the first
            if not self._first_part_in_solution:
                lines.append(r"\medskip")
                lines.append("")
            # Reset flag after first part
            if self._first_part_in_solution:
                self._first_part_in_solution = False

            if len(node.items) == 1:
                # Single item - render inline
                item = node.items[0]
                if isinstance(item, Paragraph):
                    # Single paragraph: (a) text
                    # Process the text to convert operators and handle inline math
                    processed_text = self._process_paragraph_text(item.text)
                    lines.append(indent_prefix + part_label + " " + processed_text)
                    lines.append("")
                elif isinstance(item, Expr):
                    if self._has_line_breaks(item):
                        # Expression with line breaks: (a) on its own line
                        lines.append(indent_prefix + part_label)
                        lines.append("")
                        # Set \leftskip for content after label
                        lines.append(
                            r"\setlength{\leftskip}{\dimexpr\parindent+2em\relax}"
                        )
                        self._in_inline_part = True
                        item_lines = self.generate_document_item(item)
                        lines.extend(item_lines)
                        self._in_inline_part = False
                        # Reset \leftskip after part content
                        lines.append(r"\setlength{\leftskip}{0pt}")
                    else:
                        # Single-line expression: (a) $expr$
                        expr_latex = self.generate_expr(item)
                        lines.append(
                            indent_prefix + part_label + " $" + expr_latex + "$"
                        )
                        lines.append("")
                elif isinstance(item, TruthTable):
                    # Truth table: (a) on its own line, then centered table
                    lines.append(indent_prefix + part_label)
                    lines.append("")
                    # Set \leftskip for content after label
                    # Add extra space so content starts after the closing ) of label
                    lines.append(r"\setlength{\leftskip}{\dimexpr\parindent+2em\relax}")
                    self._in_inline_part = True
                    item_lines = self.generate_document_item(item)
                    lines.extend(item_lines)
                    self._in_inline_part = False
                    # Reset \leftskip after part content
                    lines.append(r"\setlength{\leftskip}{0pt}")
                elif isinstance(item, ProofTree):
                    # Proof tree: (a) on its own line, then proof on new line
                    lines.append(indent_prefix + part_label)
                    lines.append("")
                    item_lines = self.generate_document_item(item)
                    lines.extend(item_lines)
                else:
                    # Other single item types - render inline with space
                    item_lines = self.generate_document_item(item)
                    if item_lines:
                        # Remove leading bigskip/medskip from first item if present
                        first_line = item_lines[0]
                        if first_line.startswith(("\\bigskip", "\\medskip")):
                            item_lines = item_lines[1:]
                            first_line = item_lines[0] if item_lines else ""
                        # Remove \noindent from first line (we're indenting the part)
                        if first_line.startswith("\\noindent"):
                            # Remove \noindent and leading space
                            first_line = first_line[9:].lstrip()
                        lines.append(indent_prefix + part_label + " " + first_line)
                        lines.extend(item_lines[1:])
            # Multiple items: (a) first item inline, then remaining
            elif node.items:
                first_item = node.items[0]
                if isinstance(first_item, Paragraph):
                    # Paragraph: (a) on separate line to avoid line-wrap issues
                    lines.append(indent_prefix + part_label)
                    lines.append("")
                    # Set \leftskip for this paragraph (stays set for remaining)
                    lines.append(r"\setlength{\leftskip}{\dimexpr\parindent+2em\relax}")
                    self._in_inline_part = True
                    item_lines = self.generate_document_item(first_item)
                    lines.extend(item_lines)
                    self._in_inline_part = False
                    # Note: \leftskip stays set for remaining items
                elif isinstance(first_item, Expr):
                    if self._has_line_breaks(first_item):
                        # Expression with line breaks: (a) on its own line
                        lines.append(indent_prefix + part_label)
                        lines.append("")
                        # Set \leftskip for content after label
                        lines.append(
                            r"\setlength{\leftskip}{\dimexpr\parindent+2em\relax}"
                        )
                        self._in_inline_part = True
                        item_lines = self.generate_document_item(first_item)
                        lines.extend(item_lines)
                        self._in_inline_part = False
                        # Note: \leftskip reset after processing all items
                    else:
                        # Single-line expression: render inline
                        expr_latex = self.generate_expr(first_item)
                        lines.append(
                            indent_prefix + part_label + " $" + expr_latex + "$"
                        )
                elif isinstance(first_item, TruthTable):
                    # Truth table: (a) on its own line, then centered table
                    lines.append(indent_prefix + part_label)
                    lines.append("")
                    # Set \leftskip for content after label
                    # Add extra space so content starts after the closing ) of label
                    lines.append(r"\setlength{\leftskip}{\dimexpr\parindent+2em\relax}")
                    self._in_inline_part = True
                    item_lines = self.generate_document_item(first_item)
                    lines.extend(item_lines)
                    self._in_inline_part = False
                    # Note: \leftskip will be reset after all items are processed
                elif isinstance(first_item, ProofTree):
                    # Proof tree: (a) on its own line, then proof on new line
                    lines.append(indent_prefix + part_label)
                    lines.append("")
                    item_lines = self.generate_document_item(first_item)
                    lines.extend(item_lines)
                else:
                    item_lines = self.generate_document_item(first_item)
                    if item_lines:
                        first_line = item_lines[0]
                        if first_line.startswith(("\\bigskip", "\\medskip")):
                            item_lines = item_lines[1:]
                            first_line = item_lines[0] if item_lines else ""
                        # Remove \noindent (we're indenting the part)
                        if first_line.startswith("\\noindent"):
                            # Remove \noindent and leading space
                            first_line = first_line[9:].lstrip()
                        lines.append(indent_prefix + part_label + " " + first_line)
                        lines.extend(item_lines[1:])
                lines.append("")
                # Add spacing before remaining items for visual separation
                lines.append(r"\bigskip")
                lines.append("")
                # Remaining items - use \leftskip to create indented container
                # This allows paragraphs to justify properly while maintaining
                # indentation. Add extra space so paragraphs start after the
                # closing ) of the part label
                lines.append(r"\setlength{\leftskip}{\dimexpr\parindent+2em\relax}")
                self._in_inline_part = True
                for item in node.items[1:]:
                    item_lines = self.generate_document_item(item)
                    lines.extend(item_lines)
                self._in_inline_part = False
                # Reset \leftskip after part content
                lines.append(r"\setlength{\leftskip}{0pt}")
        else:
            # Subsection formatting (default)
            # Add vertical spacing before parts that are not the first
            if not self._first_part_in_solution:
                lines.append(r"\medskip")
                lines.append("")
            # Reset flag after first part
            if self._first_part_in_solution:
                self._first_part_in_solution = False
            lines.append(r"\subsubsection*{" + part_label + "}")
            # Add to table of contents: always at depth>=3, or when toc_parts override
            if self._toc_depth >= 3 or self.toc_parts:
                lines.append(
                    r"\addcontentsline{toc}{subsubsection}{" + part_label + "}"
                )
            lines.append("")

            for item in node.items:
                item_lines = self.generate_document_item(item)
                lines.extend(item_lines)

        return lines

    @item_register.register(Paragraph)
    def _generate_paragraph(self, node: Paragraph) -> list[str]:
        """Generate LaTeX for plain text paragraph.

        Converts symbolic operators like <=> and => to LaTeX math symbols.
        Supports inline math expressions like { x : N | x > 0 }.
        Does NOT convert words like 'and', 'or', 'not' - these are English prose.
        Paragraphs are justified with no first-line indentation.
        If inside an inline part, respects the part's indentation.
        """
        lines: list[str] = []

        # Process the paragraph text
        text = self._process_paragraph_text(node.text)

        # Prevent first-line indentation for all paragraphs
        # Paragraphs inside parts will be indented via \leftskip set at part level
        # \noindent prevents LaTeX's automatic first-line indentation
        # \leftskip handles the overall indentation of the paragraph block
        # Both work together: \noindent prevents extra indent,
        # \leftskip provides base indent
        lines.append(r"\noindent " + text)
        lines.append("")  # Blank line ends paragraph for proper justification
        # Add trailing space after paragraph for separation from following elements
        lines.append(r"\bigskip")
        lines.append("")
        return lines

    @item_register.register(PureParagraph)
    def _generate_pure_paragraph(self, node: PureParagraph) -> list[str]:
        """Generate LaTeX for pure text paragraph with NO processing.

        PURETEXT: blocks are output with:
        - NO formula detection
        - NO operator conversion
        - NO inline math processing
        - Only basic LaTeX character escaping
        """
        lines: list[str] = []
        lines.append(r"\bigskip")  # Leading vertical space
        lines.append("")

        # Only escape LaTeX special characters, no other processing
        text = self._escape_latex(node.text)

        lines.append(text)
        lines.append("")
        lines.append(r"\bigskip")  # Trailing vertical space
        lines.append("")
        return lines

    @item_register.register(LatexBlock)
    def _generate_latex_block(self, node: LatexBlock) -> list[str]:
        """Generate LaTeX for raw LaTeX passthrough block.

        LATEX: blocks output raw LaTeX with NO escaping.
        The LaTeX is passed directly through to the output.
        """
        lines: list[str] = []
        lines.append(node.latex)  # Raw LaTeX, no processing
        lines.append("")
        return lines

    @item_register.register(RawLatexBlock)
    def _generate_raw_latex_block(self, node: RawLatexBlock) -> list[str]:
        """Generate LaTeX for multi-line raw LaTeX passthrough block.

        Body is emitted verbatim with NO escaping and NO environment
        wrapper.  The user owns the raw LaTeX — indentation and blank
        lines are preserved exactly as written between LATEX: and END.
        """
        lines: list[str] = []
        if node.body:
            lines.append(node.body)
        lines.append("")
        return lines

    @item_register.register(BMachine)
    def _generate_b_machine(self, node: BMachine) -> list[str]:
        r"""Generate LaTeX for B-machine verbatim block.

        Wraps the body in \begin{verbatim}…\end{verbatim}.
        Body indentation and blank lines are preserved exactly.
        """
        lines: list[str] = []
        lines.append(r"\begin{verbatim}")
        lines.append(node.body)
        lines.append(r"\end{verbatim}")
        lines.append("")
        return lines

    @item_register.register(LineBreak)
    def _generate_linebreak(self, node: LineBreak) -> list[str]:
        r"""Generate LaTeX for line break.

        LINEBREAK: inserts a \medskip vertical space in PDF output.
        Useful for visual separation between logical groups of paragraphs
        when neither a paragraph boundary nor a full page break is right.
        """
        return [r"\medskip", ""]

    @item_register.register(Contents)
    def _generate_contents(self, node: Contents) -> list[str]:
        """Generate LaTeX for table of contents.

        Depth is determined by the keyword: "1" → 1; empty/"2"/unrecognised → 2;
        "3"/"full"/"all" → 3.  The counter tells LaTeX how many heading levels
        to render in the printed TOC; filtering of addcontentsline calls is
        handled by _toc_depth on the generator.
        """
        lines: list[str] = []
        depth = toc_depth_from_keyword(node.depth)
        lines.append(rf"\setcounter{{tocdepth}}{{{depth}}}")
        lines.append(r"\tableofcontents")
        lines.append("")
        return lines

    @item_register.register(PartsFormat)
    def _generate_parts_format(self, node: PartsFormat) -> list[str]:
        """Generate LaTeX for parts format directive.

        PartsFormat directive is already applied at document level during parsing,
        so we return empty list here (no LaTeX output needed).
        """
        return []

    @item_register.register(TruthTable)
    def _generate_truth_table(self, node: TruthTable) -> list[str]:
        """Generate LaTeX for truth table (centered, with auto-scaling if needed)."""
        lines: list[str] = []

        # Calculate available width and setup positioning
        if self._in_inline_part:
            # Inside part with leftskip: skip centering, align naturally
            lines.append(r"\savedleftskip=\leftskip")
            max_width = r"\dimexpr\textwidth-\savedleftskip\relax"
            # Just prevent extra indentation - leftskip handles positioning
            lines.append(r"\noindent")
        else:
            # Normal context: use centering
            max_width = r"\textwidth"
            lines.append(r"\begin{center}")

        # Wrap table in adjustbox to scale if wider than available width
        lines.append(r"\adjustbox{max width=" + max_width + r"}{%")

        # Start table environment with vertical bars between columns (not at edges)
        # Spacing is controlled by part labels
        num_cols = len(node.headers)
        col_spec = "|".join(["c"] * num_cols)
        lines.append(r"\begin{tabular}{" + col_spec + r"}")

        # Generate header row (last column in bold as it's the overall assessment)
        header_parts: list[str] = []
        for i, header in enumerate(node.headers):
            # Convert operators to LaTeX symbols
            header_latex = self._convert_operators_to_latex(header)
            # Last column in bold, all in math mode
            if i == len(node.headers) - 1:
                header_parts.append(r"$\mathbf{" + header_latex + r"}$")
            else:
                header_parts.append(f"${header_latex}$")
        lines.append(" & ".join(header_parts) + r" \\")
        lines.append(r"\hline")

        # Generate data rows (lowercase t/f in italic, last column in bold non-italic)
        for row in node.rows:
            row_parts: list[str] = []
            for i, val in enumerate(row):
                # Lowercase t/f for truth values
                cell = val.lower() if val in ("T", "F") else val
                # Last column in bold (no italic), others in italic
                if i == len(row) - 1:
                    row_parts.append(r"\textbf{" + cell + r"}")
                else:
                    row_parts.append(r"\textit{" + cell + r"}")
            lines.append(" & ".join(row_parts) + r" \\")

        lines.append(r"\end{tabular}%")
        # Close adjustbox wrapper
        lines.append(r"}")
        # Close center environment (only if we opened it)
        if not self._in_inline_part:
            lines.append(r"\end{center}")
        # Add trailing spacing for separation from following content
        lines.append(r"\bigskip")
        lines.append("")

        return lines
