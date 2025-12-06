"""KaTeX HTML generator for txt2tex - converts AST to HTML with KaTeX math."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from functools import singledispatchmethod
from pathlib import Path
from typing import ClassVar, cast

from txt2tex.__version__ import __version__
from txt2tex.ast_nodes import (
    Abbreviation,
    ArgueChain,
    AxDef,
    BagLiteral,
    BinaryOp,
    CaseAnalysis,
    Conditional,
    Contents,
    Declaration,
    Document,
    DocumentItem,
    Expr,
    FreeType,
    FunctionApp,
    FunctionType,
    GenDef,
    GenericInstantiation,
    GivenType,
    GuardedBranch,
    GuardedCases,
    Identifier,
    InfruleBlock,
    Lambda,
    LatexBlock,
    Number,
    PageBreak,
    Paragraph,
    Part,
    PartsFormat,
    ProofNode,
    ProofTree,
    PureParagraph,
    Quantifier,
    Range,
    RelationalImage,
    Schema,
    Section,
    SequenceLiteral,
    SetComprehension,
    SetLiteral,
    Solution,
    Subscript,
    Superscript,
    SyntaxBlock,
    TitleMetadata,
    TruthTable,
    Tuple,
    TupleProjection,
    UnaryOp,
    Zed,
)
from txt2tex.bib_parser import BibEntry, BibParser
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser, ParserError


@dataclass
class TocEntry:
    """A table of contents entry."""

    title: str
    anchor_id: str
    level: int  # 1 = section, 2 = solution


def _empty_toc_entries() -> list[TocEntry]:
    """Factory for empty TOC entries list."""
    return []


def _empty_citations() -> list[str]:
    """Factory for empty citations list."""
    return []


def _empty_citation_map() -> dict[str, int]:
    """Factory for empty citation map."""
    return {}


def _empty_bib_entries() -> dict[str, BibEntry]:
    """Factory for empty bib entries dict."""
    return {}


@dataclass
class DocumentStructure:
    """Collected document structure for two-pass generation."""

    toc_entries: list[TocEntry] = field(default_factory=_empty_toc_entries)
    citations_used: list[str] = field(default_factory=_empty_citations)
    citation_to_number: dict[str, int] = field(default_factory=_empty_citation_map)
    bib_entries: dict[str, BibEntry] = field(default_factory=_empty_bib_entries)


class KaTeXGenerator:
    """Converts txt2tex AST to HTML with KaTeX math rendering.

    Generates self-contained HTML documents that use KaTeX for math rendering.
    Z notation environments (schemas, axdefs) are rendered as styled HTML boxes.
    """

    # Binary operator mappings to KaTeX-compatible LaTeX
    BINARY_OPS: ClassVar[dict[str, str]] = {
        # Propositional logic
        "land": r"\land",
        "lor": r"\lor",
        "=>": r"\Rightarrow",
        "implies": r"\Rightarrow",
        "<=>": r"\Leftrightarrow",
        # Comparison operators
        "<": r"<",
        ">": r">",
        "<=": r"\leq",
        ">=": r"\geq",
        "=": r"=",
        "!=": r"\neq",
        "/=": r"\neq",
        # Sequent judgment
        "shows": r"\vdash",
        # Set operators
        "elem": r"\in",
        "notin": r"\notin",
        "/in": r"\notin",
        "subset": r"\subseteq",
        "subseteq": r"\subseteq",
        "psubset": r"\subset",
        "union": r"\cup",
        "intersect": r"\cap",
        "cross": r"\times",
        "×": r"\times",  # noqa: RUF001
        "\\": r"\setminus",
        "++": r"\oplus",
        # Relation operators
        "<->": r"\leftrightarrow",
        "|->": r"\mapsto",
        "<|": r"\triangleleft",
        "|>": r"\triangleright",
        "comp": r"\circ",
        ";": r"\mathbin{;}",
        # Extended relation operators
        "<<|": r"\mathbin{\lhd\kern-0.4em-}",
        "|>>": r"\mathbin{-\kern-0.4em\rhd}",
        "o9": r"\circ",
        # Function type operators
        "->": r"\rightarrow",
        "+->": r"\rightharpoonup",
        ">->": r"\rightarrowtail",
        ">+>": r"\rightarrowtail\kern-0.5em\rightharpoonup",
        "-->>": r"\twoheadrightarrow",
        "+->>": r"\rightharpoonup\kern-1em\twoheadrightarrow",
        ">->>": r"\rightarrowtail\kern-0.5em\twoheadrightarrow",
        "77->": r"\rightharpoonup",
        # Arithmetic operators
        "+": r"+",
        "-": r"-",
        "*": r"\cdot",
        "mod": r"\bmod",
        # Sequence operators
        "⌢": r"\frown",
        "^": r"\frown",
        "↾": r"\upharpoonright",
        "filter": r"\upharpoonright",
        # Bag operators
        "⊎": r"\uplus",
        "bag_union": r"\uplus",
    }

    # Unary operator mappings
    UNARY_OPS: ClassVar[dict[str, str]] = {
        "lnot": r"\lnot",
        "-": r"-",
        "#": r"\#",
        "dom": r"\textrm{dom}",
        "ran": r"\textrm{ran}",
        "inv": r"{}^{-1}",
        "id": r"\textrm{id}",
        "P": r"\mathcal{P}",
        "P1": r"\mathcal{P}_1",
        "F": r"\mathbb{F}",
        "F1": r"\mathbb{F}_1",
        "bigcup": r"\bigcup",
        "bigcap": r"\bigcap",
        "~": r"^{-1}",
        "+": r"^{+}",
        "*": r"^{*}",
    }

    # Quantifier mappings
    QUANTIFIERS: ClassVar[dict[str, str]] = {
        "forall": r"\forall",
        "exists": r"\exists",
        "exists1": r"\exists_1",
        "mu": r"\mu",
    }

    # Operator precedence (lower number = lower precedence)
    PRECEDENCE: ClassVar[dict[str, int]] = {
        "<=>": 1,
        "=>": 2,
        "implies": 2,
        "lor": 3,
        "land": 4,
        "<": 5,
        ">": 5,
        "<=": 5,
        ">=": 5,
        "=": 5,
        "!=": 5,
        "<->": 6,
        "|->": 6,
        "<|": 6,
        "|>": 6,
        "<<|": 6,
        "|>>": 6,
        "o9": 6,
        "comp": 6,
        ";": 6,
        "->": 6,
        "+->": 6,
        ">->": 6,
        ">+>": 6,
        "-->>": 6,
        "+->>": 6,
        ">->>": 6,
        "77->": 6,
        "elem": 7,
        "notin": 7,
        "subset": 7,
        "subseteq": 7,
        "psubset": 7,
        "union": 8,
        "cross": 8,
        "×": 8,  # noqa: RUF001
        "intersect": 9,
        "\\": 9,
    }

    # Right-associative operators
    RIGHT_ASSOCIATIVE: ClassVar[set[str]] = {"=>", "<=>"}

    # Type names mapping
    TYPE_MAP: ClassVar[dict[str, str]] = {
        "Z": r"\mathbb{Z}",
        "N": r"\mathbb{N}",
        "N1": r"\mathbb{N}_1",
    }

    # Special function mappings for generic types
    SPECIAL_TYPES: ClassVar[dict[str, str]] = {
        "seq": r"\textrm{seq}",
        "seq1": r"\textrm{seq}_1",
        "iseq": r"\textrm{iseq}",
        "bag": r"\textrm{bag}",
        "P": r"\mathcal{P}",
        "F": r"\mathbb{F}",
    }

    def __init__(self, source_dir: Path | None = None) -> None:
        """Initialize the KaTeX generator.

        Args:
            source_dir: Directory containing source file (for resolving bib paths).
        """
        self._in_math_mode = False
        self._source_dir = source_dir or Path.cwd()
        self._structure = DocumentStructure()
        self._section_counter = 0
        self._solution_counter = 0
        self._bib_parser = BibParser()

    def _collect_document_structure(self, ast: Document) -> None:
        """First pass: collect TOC entries and citations from document.

        Populates self._structure with TOC entries and citation mappings.
        """
        self._structure = DocumentStructure()
        self._section_counter = 0
        self._solution_counter = 0

        # Load bibliography if specified
        if ast.bibliography_metadata and ast.bibliography_metadata.file:
            bib_file = ast.bibliography_metadata.file
            bib_path = self._source_dir / bib_file
            self._structure.bib_entries = self._bib_parser.parse(bib_path)

        # Collect TOC entries and citations from items
        for item in ast.items:
            self._collect_from_item(item)

    def _collect_from_item(self, item: DocumentItem) -> None:
        """Recursively collect TOC entries and citations from a document item."""
        if isinstance(item, Section):
            self._section_counter += 1
            anchor_id = f"section-{self._section_counter}"
            self._structure.toc_entries.append(
                TocEntry(title=item.title, anchor_id=anchor_id, level=1)
            )
            for sub_item in item.items:
                self._collect_from_item(sub_item)

        elif isinstance(item, Solution):
            self._solution_counter += 1
            anchor_id = f"solution-{item.number}"
            self._structure.toc_entries.append(
                TocEntry(title=f"Solution {item.number}", anchor_id=anchor_id, level=2)
            )
            for sub_item in item.items:
                self._collect_from_item(sub_item)

        elif isinstance(item, Part):
            for sub_item in item.items:
                self._collect_from_item(sub_item)

        elif isinstance(item, Paragraph):
            # Extract citations from paragraph text
            self._collect_citations_from_text(item.text)

    def _collect_citations_from_text(self, text: str) -> None:
        """Extract [cite key] citations from text and track them."""
        # Pattern: [cite key optional-locator]
        pattern = r"\[cite\s+([a-zA-Z0-9_-]+)(?:\s+[^\]]+)?\]"

        for match in re.finditer(pattern, text):
            key = match.group(1)
            if key not in self._structure.citation_to_number:
                # Assign next citation number
                num = len(self._structure.citations_used) + 1
                self._structure.citations_used.append(key)
                self._structure.citation_to_number[key] = num

    def generate_document(self, ast: Document | Expr) -> str:
        """Generate complete HTML document with KaTeX.

        Uses two-pass generation:
        1. First pass: Collect TOC entries and citations
        2. Second pass: Generate HTML with TOC and numbered citations

        Args:
            ast: The AST root node.

        Returns:
            Complete HTML document string.
        """
        # First pass: collect document structure (for Document only)
        if isinstance(ast, Document):
            self._collect_document_structure(ast)
            # Reset counters for second pass
            self._section_counter = 0
            self._solution_counter = 0

        lines: list[str] = []

        # HTML preamble
        lines.append("<!DOCTYPE html>")
        lines.append('<html lang="en">')
        lines.append("<head>")
        lines.append('  <meta charset="UTF-8">')
        lines.append(
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0">'
        )
        lines.append(f'  <meta name="generator" content="txt2tex {__version__}">')

        # Title
        if isinstance(ast, Document) and ast.title_metadata:
            title = ast.title_metadata.title or "txt2tex Document"
            lines.append(f"  <title>{html.escape(title)}</title>")
        else:
            lines.append("  <title>txt2tex Document</title>")

        # KaTeX CSS and JS from CDN (version 0.16.11)
        lines.append(
            '  <link rel="stylesheet" '
            'href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">'
        )
        lines.append(
            "  <script defer "
            'src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js">'
            "</script>"
        )
        lines.append(
            "  <script defer "
            'src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/'
            'contrib/auto-render.min.js"></script>'
        )

        # Custom styles for Z notation
        lines.append("  <style>")
        lines.append(self._get_css_styles())
        lines.append("  </style>")

        lines.append("</head>")
        lines.append("<body>")

        # Auto-render script with Z notation macros
        lines.append("<script>")
        lines.append('  document.addEventListener("DOMContentLoaded", function() {')
        lines.append("    renderMathInElement(document.body, {")
        lines.append("      delimiters: [")
        lines.append('        {left: "$$", right: "$$", display: true},')
        lines.append('        {left: "$", right: "$", display: false}')
        lines.append("      ],")
        lines.append("      macros: {")
        # Add proper indentation to first macro line
        macros_str = self._get_katex_macros()
        lines.append("        " + macros_str)
        lines.append("      },")
        lines.append("      throwOnError: false")
        lines.append("    });")
        lines.append("  });")
        lines.append("</script>")

        # Document content
        lines.append('<div class="document">')

        # Title block
        if isinstance(ast, Document) and ast.title_metadata:
            lines.extend(self._generate_title_block(ast.title_metadata))

        # Table of Contents (if there are TOC entries)
        if isinstance(ast, Document) and self._structure.toc_entries:
            lines.extend(self._generate_toc())

        # Body content
        if isinstance(ast, Document):
            for item in ast.items:
                lines.extend(self._generate_document_item(item))

            # Bibliography (if citations were used)
            if self._structure.citations_used:
                lines.extend(self._generate_bibliography())
        else:
            # Single expression
            math = self.generate_expr(ast)
            lines.append(f"<p>$${math}$$</p>")

        lines.append("</div>")
        lines.append("</body>")
        lines.append("</html>")

        return "\n".join(lines)

    def _generate_toc(self) -> list[str]:
        """Generate table of contents HTML."""
        lines: list[str] = ['<div class="toc">']
        lines.append("  <h2>Contents</h2>")
        lines.append("  <ul>")

        for entry in self._structure.toc_entries:
            indent = "    " if entry.level == 1 else "      "
            css_class = "toc-section" if entry.level == 1 else "toc-solution"
            lines.append(
                f'{indent}<li class="{css_class}">'
                f'<a href="#{entry.anchor_id}">{html.escape(entry.title)}</a></li>'
            )

        lines.append("  </ul>")
        lines.append("</div>")
        return lines

    def _generate_bibliography(self) -> list[str]:
        """Generate bibliography/references section HTML."""
        lines: list[str] = ['<div class="bibliography">']
        lines.append('  <h2 id="references">References</h2>')
        lines.append("  <ol>")

        for key in self._structure.citations_used:
            entry = self._structure.bib_entries.get(key)
            if entry:
                citation_html = self._format_bib_entry(entry)
                lines.append(f'    <li id="ref-{key}">{citation_html}</li>')
            else:
                # Unknown citation key
                lines.append(
                    f'    <li id="ref-{key}">'
                    f"<em>[Unknown reference: {html.escape(key)}]</em></li>"
                )

        lines.append("  </ol>")
        lines.append("</div>")
        return lines

    def _format_bib_entry(self, entry: BibEntry) -> str:
        """Format a bibliography entry for display."""
        parts: list[str] = []

        # Author
        if entry.author:
            parts.append(html.escape(entry.author))

        # Year
        if entry.year:
            parts.append(f"({html.escape(entry.year)})")

        # Title (in italics for books, quotes for articles)
        if entry.title:
            if entry.entry_type == "book":
                parts.append(f"<em>{html.escape(entry.title)}</em>")
            else:
                parts.append(f'"{html.escape(entry.title)}"')

        # Publisher and address for books
        if entry.entry_type == "book":
            if entry.publisher:
                pub_str = html.escape(entry.publisher)
                if entry.address:
                    pub_str = f"{html.escape(entry.address)}: {pub_str}"
                parts.append(pub_str)

        # Howpublished for misc entries
        elif entry.entry_type == "misc" and entry.howpublished:
            parts.append(html.escape(entry.howpublished))

        # Note for unpublished
        elif entry.entry_type == "unpublished" and entry.note:
            parts.append(html.escape(entry.note))

        return ". ".join(parts) + "."

    def _get_css_styles(self) -> str:
        """Return CSS styles for Z notation and document structure."""
        return """
    body {
      font-family: 'Computer Modern Serif', 'Latin Modern Roman', Georgia, serif;
      max-width: 800px;
      margin: 0 auto;
      padding: 2em;
      line-height: 1.6;
      color: #333;
    }
    .document { }
    .title-block {
      text-align: center;
      margin-bottom: 2em;
    }
    .title-block h1 { margin-bottom: 0.25em; }
    .title-block .subtitle { font-size: 1.2em; color: #666; }
    .title-block .author { margin-top: 1em; }
    .title-block .date { color: #666; }
    h1, h2, h3 { margin-top: 1.5em; }
    .section { margin-bottom: 2em; }
    .solution { margin: 1.5em 0; }
    .solution-header { font-weight: bold; margin-bottom: 0.5em; }
    .part { margin: 1em 0 1em 1.5em; }
    .part-label { font-weight: bold; }
    /* Z notation boxes */
    .z-box {
      border: 1px solid #333;
      margin: 1em 0;
      padding: 0;
      display: inline-block;
      min-width: 300px;
    }
    .z-schema { }
    .z-axdef { }
    .z-gendef { }
    .z-header {
      padding: 0.3em 0.5em;
      border-bottom: 1px solid #333;
      font-style: italic;
    }
    .z-generic-params {
      font-style: normal;
    }
    .z-decl {
      padding: 0.5em;
    }
    .z-divider {
      border: none;
      border-top: 1px solid #333;
      margin: 0;
    }
    .z-pred {
      padding: 0.5em;
    }
    .z-zed {
      margin: 1em 0;
      padding: 0.5em;
    }
    /* Truth table - compact like LaTeX */
    .truth-table {
      border-collapse: collapse;
      margin: 1em auto;
      font-size: 0.85em;
    }
    .truth-table th, .truth-table td {
      border: 1px solid #333;
      padding: 0.15em 0.5em;
      text-align: center;
    }
    .truth-table th {
      background: #f5f5f5;
      font-weight: bold;
      white-space: nowrap;
    }
    .truth-table td {
      font-style: italic;
    }
    /* Equivalence chain - compact two-column layout like LaTeX */
    .argue-chain {
      margin: 1em 0;
      width: 100%;
    }
    .argue-step {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin: 0;
      padding: 0;
      line-height: 1.8;
    }
    .argue-expr {
      text-align: left;
      padding-left: 3em;
    }
    .argue-expr .katex-display {
      margin: 0.1em 0 !important;
      padding: 0;
    }
    .argue-just {
      color: #555;
      text-align: right;
      flex-shrink: 0;
      padding-left: 1.5em;
      font-size: 0.95em;
    }
    /* Proof tree - Fitch-style nested boxes */
    .proof-tree {
      margin: 1em 0;
      font-size: 0.95em;
    }
    .proof-node {
      margin: 0.2em 0 0.2em 1.5em;
      padding-left: 0.5em;
      border-left: 1px solid #ccc;
    }
    .proof-node:first-child {
      border-left: none;
      margin-left: 0;
      padding-left: 0;
    }
    .proof-line {
      margin: 0.3em 0;
      line-height: 1.8;
    }
    .proof-assumption {
      border: 1px solid #666;
      padding: 0.1em 0.4em;
      background: #f9f9f9;
      display: inline-block;
    }
    .proof-label {
      color: #666;
      font-size: 0.85em;
      margin-left: 0.3em;
    }
    .proof-case {
      margin: 0.5em 0 0.5em 1em;
      padding-left: 0.5em;
      border-left: 2px solid #999;
    }
    .proof-case-header {
      font-weight: bold;
      margin-bottom: 0.3em;
    }
    /* Inference rule */
    .infrule {
      display: inline-block;
      text-align: center;
      margin: 1em 0;
    }
    .infrule-premises {
      margin-bottom: 0.2em;
    }
    .infrule-line {
      border-top: 1px solid #333;
      margin: 0.2em 0;
    }
    .infrule-conclusion {
      margin-top: 0.2em;
    }
    /* Page break (for print) */
    .page-break {
      page-break-after: always;
      break-after: page;
    }
    /* Table of Contents */
    .toc {
      margin: 2em 0;
      padding: 1em;
      background: #f9f9f9;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    .toc h2 {
      margin-top: 0;
      font-size: 1.3em;
    }
    .toc ul {
      list-style: none;
      padding-left: 0;
      margin: 0;
    }
    .toc li {
      margin: 0.3em 0;
    }
    .toc .toc-section {
      font-weight: bold;
    }
    .toc .toc-solution {
      padding-left: 1.5em;
    }
    .toc a {
      color: #0066cc;
      text-decoration: none;
    }
    .toc a:hover {
      text-decoration: underline;
    }
    /* Bibliography */
    .bibliography {
      margin-top: 3em;
      padding-top: 1em;
      border-top: 2px solid #333;
    }
    .bibliography h2 {
      margin-top: 0;
    }
    .bibliography ol {
      padding-left: 2em;
    }
    .bibliography li {
      margin: 0.8em 0;
      line-height: 1.5;
    }
    /* Citation links */
    .citation {
      color: #0066cc;
      text-decoration: none;
    }
    .citation:hover {
      text-decoration: underline;
    }
    @media print {
      body { max-width: none; }
      .toc { background: #fff; }
    }
"""

    def _get_katex_macros(self) -> str:
        """Return KaTeX macro definitions for Z notation.

        Only defines macros for commands that KaTeX doesn't support natively.
        KaTeX already supports: \\land, \\lor, \\lnot, \\mu, etc.
        """
        macros = [
            # Type symbols
            '"\\\\nat": "\\\\mathbb{N}"',
            '"\\\\num": "\\\\mathbb{Z}"',
            '"\\\\bool": "\\\\mathbb{B}"',
            '"\\\\real": "\\\\mathbb{R}"',
            # Set operators
            '"\\\\power": "\\\\mathcal{P}"',
            '"\\\\finset": "\\\\mathbb{F}"',
            '"\\\\cross": "\\\\times"',
            # Relation operators
            '"\\\\rel": "\\\\leftrightarrow"',
            '"\\\\fun": "\\\\rightarrow"',
            '"\\\\pfun": "\\\\rightharpoonup"',
            '"\\\\inj": "\\\\rightarrowtail"',
            '"\\\\pinj": "\\\\rightarrowtail\\\\!\\\\rightharpoonup"',
            '"\\\\surj": "\\\\twoheadrightarrow"',
            '"\\\\psurj": "\\\\rightharpoonup\\\\!\\\\!\\\\twoheadrightarrow"',
            '"\\\\bij": "\\\\rightarrowtail\\\\!\\\\twoheadrightarrow"',
            '"\\\\ffun": "\\\\rightharpoonup"',
            # Domain/range operators
            '"\\\\dom": "\\\\textrm{dom}"',
            '"\\\\ran": "\\\\textrm{ran}"',
            '"\\\\dres": "\\\\triangleleft"',
            '"\\\\rres": "\\\\triangleright"',
            # Anti-restriction (use triangles with line)
            '"\\\\ndres": "\\\\mathbin{\\\\triangleleft\\\\!\\\\!-}"',
            '"\\\\nrres": "\\\\mathbin{-\\\\!\\\\!\\\\triangleright}"',
            '"\\\\comp": "\\\\circ"',
            '"\\\\semi": "\\\\mathbin{;}"',
            # Sequence operators
            '"\\\\seq": "\\\\textrm{seq}"',
            '"\\\\cat": "\\\\frown"',
            '"\\\\filter": "\\\\upharpoonright"',
            # Bag operators
            '"\\\\bag": "\\\\textrm{bag}"',
            # Relational image (use proper delimiters)
            '"\\\\limg": "\\\\langle\\\\!|"',
            '"\\\\rimg": "|\\\\!\\\\rangle"',
            # Override
            '"\\\\oplus": "\\\\oplus"',
            # Range
            '"\\\\upto": "\\\\ldots"',
            # Closure operators
            '"\\\\plus": "^{+}"',
            '"\\\\star": "^{*}"',
            '"\\\\inv": "^{-1}"',
            # Turnstile
            '"\\\\shows": "\\\\vdash"',
            # Implication/equivalence shortcuts
            '"\\\\implies": "\\\\Rightarrow"',
            '"\\\\iff": "\\\\Leftrightarrow"',
            # Unique existence
            '"\\\\exists_1": "\\\\exists_1"',
        ]
        return ",\n        ".join(macros)

    def _generate_title_block(self, meta: TitleMetadata) -> list[str]:
        """Generate HTML for title metadata."""
        lines: list[str] = ['<div class="title-block">']
        if meta.title:
            lines.append(f"  <h1>{html.escape(meta.title)}</h1>")
        if meta.subtitle:
            lines.append(f'  <div class="subtitle">{html.escape(meta.subtitle)}</div>')
        if meta.author:
            lines.append(f'  <div class="author">{html.escape(meta.author)}</div>')
        if meta.institution:
            lines.append(
                f'  <div class="institution">{html.escape(meta.institution)}</div>'
            )
        if meta.date:
            lines.append(f'  <div class="date">{html.escape(meta.date)}</div>')
        lines.append("</div>")
        return lines

    def _generate_document_item(self, item: DocumentItem) -> list[str]:
        """Generate HTML for a document item."""
        if isinstance(item, Section):
            return self._generate_section(item)
        if isinstance(item, Solution):
            return self._generate_solution(item)
        if isinstance(item, Part):
            return self._generate_part(item)
        if isinstance(item, TruthTable):
            return self._generate_truth_table(item)
        if isinstance(item, ArgueChain):
            return self._generate_argue_chain(item)
        if isinstance(item, InfruleBlock):
            return self._generate_infrule(item)
        if isinstance(item, Schema):
            return self._generate_schema(item)
        if isinstance(item, AxDef):
            return self._generate_axdef(item)
        if isinstance(item, GenDef):
            return self._generate_gendef(item)
        if isinstance(item, GivenType):
            return self._generate_given_type(item)
        if isinstance(item, FreeType):
            return self._generate_free_type(item)
        if isinstance(item, Abbreviation):
            return self._generate_abbreviation(item)
        if isinstance(item, Zed):
            return self._generate_zed(item)
        if isinstance(item, SyntaxBlock):
            return self._generate_syntax_block(item)
        if isinstance(item, ProofTree):
            return self._generate_proof_tree(item)
        if isinstance(item, Paragraph):
            return self._generate_paragraph(item)
        if isinstance(item, PureParagraph):
            return self._generate_pure_paragraph(item)
        if isinstance(item, LatexBlock):
            return self._generate_latex_block(item)
        if isinstance(item, PageBreak):
            return ['<div class="page-break"></div>']
        if isinstance(item, Contents):
            # TOC is already generated at document start via two-pass generation
            return []
        if isinstance(item, PartsFormat):
            return []  # Style directive, no output

        # Expression item - render as math
        math = self.generate_expr(item)
        return [f"<p>$${math}$$</p>"]

    def _generate_section(self, section: Section) -> list[str]:
        """Generate HTML for a section."""
        self._section_counter += 1
        anchor_id = f"section-{self._section_counter}"
        lines: list[str] = [f'<div class="section" id="{anchor_id}">']
        lines.append(f"  <h2>{html.escape(section.title)}</h2>")
        for item in section.items:
            lines.extend(self._generate_document_item(item))
        lines.append("</div>")
        return lines

    def _generate_solution(self, solution: Solution) -> list[str]:
        """Generate HTML for a solution block."""
        self._solution_counter += 1
        anchor_id = f"solution-{solution.number}"
        lines: list[str] = [f'<div class="solution" id="{anchor_id}">']
        lines.append(
            f'  <div class="solution-header">Solution {html.escape(solution.number)}'
            "</div>"
        )
        for item in solution.items:
            lines.extend(self._generate_document_item(item))
        lines.append("</div>")
        return lines

    def _generate_part(self, part: Part) -> list[str]:
        """Generate HTML for a part label."""
        lines: list[str] = ['<div class="part">']
        lines.append(f'  <span class="part-label">({html.escape(part.label)})</span> ')
        for item in part.items:
            item_lines = self._generate_document_item(item)
            lines.extend(item_lines)
        lines.append("</div>")
        return lines

    def _generate_truth_table(self, table: TruthTable) -> list[str]:
        """Generate HTML for a truth table."""
        lines: list[str] = ['<table class="truth-table">']

        # Headers
        lines.append("  <thead><tr>")
        for header in table.headers:
            # Parse header as expression
            header_math = self._parse_and_generate(header)
            lines.append(f"    <th>${header_math}$</th>")
        lines.append("  </tr></thead>")

        # Rows
        lines.append("  <tbody>")
        for row in table.rows:
            lines.append("    <tr>")
            for cell in row:
                # Convert T/F to lowercase t/f for LaTeX-style appearance
                cell_display = cell.lower() if cell in ("T", "F") else html.escape(cell)
                lines.append(f"      <td>{cell_display}</td>")
            lines.append("    </tr>")
        lines.append("  </tbody>")
        lines.append("</table>")
        return lines

    def _generate_argue_chain(self, chain: ArgueChain) -> list[str]:
        """Generate HTML for an equivalence/argue chain.

        Uses table layout for proper two-column alignment:
        - Left column: expressions (left-aligned)
        - Right column: justifications (right-aligned)
        """
        lines: list[str] = ['<div class="argue-chain">']

        for i, step in enumerate(chain.steps):
            expr_math = self.generate_expr(step.expression)
            # Use ⇔ prefix for subsequent steps
            prefix = r"\Leftrightarrow \;" if i > 0 else ""

            lines.append('  <div class="argue-step">')
            # Use display math but in table cell
            lines.append(f'    <span class="argue-expr">$${prefix}{expr_math}$$</span>')
            # Justification column (may be empty)
            if step.justification:
                just_escaped = html.escape(step.justification)
                lines.append(f'    <span class="argue-just">[{just_escaped}]</span>')
            else:
                lines.append('    <span class="argue-just"></span>')
            lines.append("  </div>")

        lines.append("</div>")
        return lines

    def _generate_infrule(self, rule: InfruleBlock) -> list[str]:
        """Generate HTML for an inference rule."""
        lines: list[str] = ['<div class="infrule">']

        # Premises
        lines.append('  <div class="infrule-premises">')
        premise_parts: list[str] = []
        for premise, label in rule.premises:
            prem_math = self.generate_expr(premise)
            if label:
                premise_parts.append(f"${prem_math}$ [{html.escape(label)}]")
            else:
                premise_parts.append(f"${prem_math}$")
        lines.append("    " + " &nbsp;&nbsp; ".join(premise_parts))
        lines.append("  </div>")

        # Line
        lines.append('  <div class="infrule-line"></div>')

        # Conclusion
        concl_expr, concl_label = rule.conclusion
        concl_math = self.generate_expr(concl_expr)
        lines.append('  <div class="infrule-conclusion">')
        if concl_label:
            lines.append(f"    ${concl_math}$ [{html.escape(concl_label)}]")
        else:
            lines.append(f"    ${concl_math}$")
        lines.append("  </div>")

        lines.append("</div>")
        return lines

    def _generate_schema(self, schema: Schema) -> list[str]:
        """Generate HTML for a schema box."""
        lines: list[str] = ['<div class="z-box z-schema">']

        # Header with name (if named)
        if schema.name:
            header = html.escape(schema.name)
            if schema.generic_params:
                params = ", ".join(schema.generic_params)
                escaped_params = html.escape(params)
                header += f' <span class="z-generic-params">[{escaped_params}]</span>'
            lines.append(f'  <div class="z-header">{header}</div>')

        # Declarations
        if schema.declarations:
            lines.append('  <div class="z-decl">')
            for decl in schema.declarations:
                decl_math = self._generate_declaration(decl)
                lines.append(f"    <div>${decl_math}$</div>")
            lines.append("  </div>")

        # Divider (if there are predicates)
        if schema.predicates and any(schema.predicates):
            lines.append('  <hr class="z-divider">')

        # Predicates
        if schema.predicates:
            lines.append('  <div class="z-pred">')
            for group in schema.predicates:
                for pred in group:
                    pred_math = self.generate_expr(pred)
                    lines.append(f"    <div>${pred_math}$</div>")
            lines.append("  </div>")

        lines.append("</div>")
        return lines

    def _generate_axdef(self, axdef: AxDef) -> list[str]:
        """Generate HTML for an axiomatic definition box."""
        lines: list[str] = ['<div class="z-box z-axdef">']

        # Header with generic params (if any)
        if axdef.generic_params:
            params = ", ".join(axdef.generic_params)
            lines.append(
                f'  <div class="z-header">'
                f'<span class="z-generic-params">[{html.escape(params)}]</span></div>'
            )

        # Declarations
        if axdef.declarations:
            lines.append('  <div class="z-decl">')
            for decl in axdef.declarations:
                decl_math = self._generate_declaration(decl)
                lines.append(f"    <div>${decl_math}$</div>")
            lines.append("  </div>")

        # Divider (if there are predicates)
        if axdef.predicates and any(axdef.predicates):
            lines.append('  <hr class="z-divider">')

        # Predicates
        if axdef.predicates:
            lines.append('  <div class="z-pred">')
            for group in axdef.predicates:
                for pred in group:
                    pred_math = self.generate_expr(pred)
                    lines.append(f"    <div>${pred_math}$</div>")
            lines.append("  </div>")

        lines.append("</div>")
        return lines

    def _generate_gendef(self, gendef: GenDef) -> list[str]:
        """Generate HTML for a generic definition box."""
        lines: list[str] = ['<div class="z-box z-gendef">']

        # Header with generic params
        params = ", ".join(gendef.generic_params)
        lines.append(
            f'  <div class="z-header">'
            f'<span class="z-generic-params">[{html.escape(params)}]</span></div>'
        )

        # Declarations
        if gendef.declarations:
            lines.append('  <div class="z-decl">')
            for decl in gendef.declarations:
                decl_math = self._generate_declaration(decl)
                lines.append(f"    <div>${decl_math}$</div>")
            lines.append("  </div>")

        # Divider (if there are predicates)
        if gendef.predicates and any(gendef.predicates):
            lines.append('  <hr class="z-divider">')

        # Predicates
        if gendef.predicates:
            lines.append('  <div class="z-pred">')
            for group in gendef.predicates:
                for pred in group:
                    pred_math = self.generate_expr(pred)
                    lines.append(f"    <div>${pred_math}$</div>")
            lines.append("  </div>")

        lines.append("</div>")
        return lines

    def _generate_given_type(self, given: GivenType) -> list[str]:
        """Generate HTML for given type declaration."""
        names = ", ".join(given.names)
        return [f'<div class="z-zed">$$[{html.escape(names)}]$$</div>']

    def _generate_free_type(self, ftype: FreeType) -> list[str]:
        """Generate HTML for free type definition."""
        branches_parts: list[str] = []
        for branch in ftype.branches:
            if branch.parameters:
                param_math = self.generate_expr(branch.parameters)
                branches_parts.append(
                    f"{html.escape(branch.name)} \\langle {param_math} \\rangle"
                )
            else:
                branches_parts.append(html.escape(branch.name))

        branches_str = " \\mid ".join(branches_parts)
        return [
            f'<div class="z-zed">$${html.escape(ftype.name)} ::= {branches_str}$$</div>'
        ]

    def _generate_abbreviation(self, abbrev: Abbreviation) -> list[str]:
        """Generate HTML for abbreviation definition."""
        expr_math = self.generate_expr(abbrev.expression)
        name = html.escape(abbrev.name)

        if abbrev.generic_params:
            params = ", ".join(abbrev.generic_params)
            return [
                f'<div class="z-zed">$$[{params}] \\; {name} == {expr_math}$$</div>'
            ]

        return [f'<div class="z-zed">$${name} == {expr_math}$$</div>']

    def _generate_zed(self, zed: Zed) -> list[str]:
        """Generate HTML for a zed block."""
        if isinstance(zed.content, Document):
            lines: list[str] = []
            for item in zed.content.items:
                lines.extend(self._generate_document_item(item))
            return lines

        # Single expression
        math = self.generate_expr(zed.content)
        return [f'<div class="z-zed">$${math}$$</div>']

    def _generate_syntax_block(self, block: SyntaxBlock) -> list[str]:
        """Generate HTML for a syntax block."""
        lines: list[str] = ['<div class="z-zed">']

        for group in block.groups:
            for defn in group:
                branches_parts: list[str] = []
                for branch in defn.branches:
                    if branch.parameters:
                        param_math = self.generate_expr(branch.parameters)
                        branches_parts.append(
                            f"{html.escape(branch.name)} \\langle {param_math} \\rangle"
                        )
                    else:
                        branches_parts.append(html.escape(branch.name))

                branches_str = " \\mid ".join(branches_parts)
                lines.append(
                    f"  <div>$${html.escape(defn.name)} ::= {branches_str}$$</div>"
                )

        lines.append("</div>")
        return lines

    def _generate_proof_tree(self, tree: ProofTree) -> list[str]:
        """Generate HTML for a proof tree (Fitch-style nested boxes)."""
        lines: list[str] = ['<div class="proof-tree">']
        lines.extend(self._generate_proof_node(tree.conclusion, 0))
        lines.append("</div>")
        return lines

    def _generate_proof_node(self, node: ProofNode, depth: int) -> list[str]:
        """Generate HTML for a proof node."""
        lines: list[str] = []
        indent = "  " * (depth + 1)

        expr_math = self.generate_expr(node.expression)

        # Build the formula line
        formula_parts: list[str] = []
        if node.is_assumption:
            formula_parts.append(f'<span class="proof-assumption">${expr_math}$</span>')
        else:
            formula_parts.append(f"${expr_math}$")

        # Add labels
        if node.label is not None:
            formula_parts.append(f'<span class="proof-label">[{node.label}]</span>')

        if node.justification:
            formula_parts.append(
                f'<span class="proof-label">[{html.escape(node.justification)}]</span>'
            )

        # Start node container
        lines.append(f'{indent}<div class="proof-node">')
        formula_html = "".join(formula_parts)
        lines.append(f'{indent}  <div class="proof-line">{formula_html}</div>')

        # Children (premises that lead to this conclusion)
        for child in node.children:
            if isinstance(child, CaseAnalysis):
                lines.append(f'{indent}  <div class="proof-case">')
                lines.append(
                    f'{indent}    <div class="proof-case-header">'
                    f"Case {html.escape(child.case_name)}:</div>"
                )
                for step in child.steps:
                    lines.extend(self._generate_proof_node(step, depth + 2))
                lines.append(f"{indent}  </div>")
            else:
                lines.extend(self._generate_proof_node(child, depth + 1))

        lines.append(f"{indent}</div>")
        return lines

    def _generate_paragraph(self, para: Paragraph) -> list[str]:
        """Generate HTML for a paragraph with formula detection."""
        # Process text for inline math
        text = self._process_text_for_math(para.text)
        return [f"<p>{text}</p>"]

    def _generate_pure_paragraph(self, para: PureParagraph) -> list[str]:
        """Generate HTML for a pure paragraph (no processing)."""
        return [f"<p>{html.escape(para.text)}</p>"]

    def _generate_latex_block(self, block: LatexBlock) -> list[str]:
        """Generate HTML for a LaTeX block (pass through as math).

        Handles raw LaTeX that may contain:
        - Already-delimited math ($..$ or $$..$$)
        - LaTeX commands not supported by KaTeX (e.g., \\hspace*)
        """
        latex = block.latex

        # Convert LaTeX-only commands to KaTeX equivalents
        latex = latex.replace(r"\hspace*", r"\hspace")

        # If content already has math delimiters, output as-is in a div
        if "$" in latex:
            return [f"<div>{latex}</div>"]

        # Otherwise wrap in display math
        return [f"<div>$${latex}$$</div>"]

    def _generate_declaration(self, decl: Declaration) -> str:
        """Generate KaTeX for a declaration (var : Type)."""
        var = self._format_identifier(decl.variable)
        type_math = self.generate_expr(decl.type_expr)
        return f"{var} : {type_math}"

    def _process_text_for_math(self, text: str) -> str:
        """Process text: convert operators to math symbols, citations, escape HTML."""
        # Convert operators to KaTeX math (longest patterns first)
        # 3-character operators
        text = self._replace_outside_math(text, "<=>", r"\Leftrightarrow")
        text = self._replace_outside_math(text, "|->", r"\mapsto")
        text = self._replace_outside_math(text, "<->", r"\leftrightarrow")

        # 2-character operators
        text = self._replace_outside_math(text, "=>", r"\Rightarrow")
        text = self._replace_outside_math(text, "->", r"\rightarrow")
        text = self._replace_outside_math(text, "+->", r"\rightharpoonup")

        # Keywords that should become math symbols
        text = self._replace_outside_math(text, " land ", r" \land ")
        text = self._replace_outside_math(text, " lor ", r" \lor ")
        text = self._replace_outside_math(text, " lnot ", r" \lnot ")
        text = self._replace_outside_math(text, "(lnot ", r"(\lnot ")
        text = self._replace_outside_math(text, " elem ", r" \in ")
        text = self._replace_outside_math(text, " forall ", r" \forall ")
        text = self._replace_outside_math(text, " exists ", r" \exists ")

        # Escape HTML special characters in non-math parts
        text = self._escape_html_outside_math(text)

        # Process citations AFTER HTML escaping: [cite key] → numbered link [1]
        # (citations need to output HTML tags that shouldn't be escaped)
        return self._process_citations_for_html(text)

    def _process_citations_for_html(self, text: str) -> str:
        """Convert [cite key locator] to numbered HTML links.

        Examples:
            "[cite spivey92]" → '<a href="#ref-..." class="citation">[1]</a>'
            "[cite key p. 42]" → '<a href="#ref-..." class="citation">[1, p. 42]</a>'
        """
        # Pattern: [cite key optional-locator]
        pattern = r"\[cite\s+([a-zA-Z0-9_-]+)(?:\s+([^\]]+))?\]"

        def replace_citation(match: re.Match[str]) -> str:
            key = match.group(1)
            locator = match.group(2)

            # Get citation number (should already exist from first pass)
            num = self._structure.citation_to_number.get(key, "?")

            if locator:
                locator = locator.strip()
                return f'<a href="#ref-{key}" class="citation">[{num}, {locator}]</a>'
            return f'<a href="#ref-{key}" class="citation">[{num}]</a>'

        return re.sub(pattern, replace_citation, text)

    def _replace_outside_math(self, text: str, pattern: str, replacement: str) -> str:
        """Replace pattern with math symbol only when NOT inside $...$ math mode."""
        result: list[str] = []
        in_math = False
        i = 0

        while i < len(text):
            if text[i] == "$":
                in_math = not in_math
                result.append("$")
                i += 1
            elif not in_math and text[i : i + len(pattern)] == pattern:
                result.append(f"${replacement}$")
                i += len(pattern)
            else:
                result.append(text[i])
                i += 1

        return "".join(result)

    def _escape_html_outside_math(self, text: str) -> str:
        """Escape HTML special characters only outside math delimiters."""
        result: list[str] = []
        in_math = False
        i = 0

        while i < len(text):
            if text[i] == "$":
                in_math = not in_math
                result.append("$")
                i += 1
            elif not in_math:
                if text[i] == "<":
                    result.append("&lt;")
                elif text[i] == ">":
                    result.append("&gt;")
                elif text[i] == "&":
                    result.append("&amp;")
                else:
                    result.append(text[i])
                i += 1
            else:
                result.append(text[i])
                i += 1

        return "".join(result)

    def _parse_and_generate(self, text: str) -> str:
        """Parse text as expression and generate KaTeX.

        Used internally to parse truth table headers and similar short expressions.
        Falls back to HTML-escaped text if parsing fails.
        """
        try:
            lexer = Lexer(text)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            result = parser.parse()
            # Result is Document | Expr
            if isinstance(result, Document):
                if result.items:
                    first_item = result.items[0]
                    # DocumentItem includes Expr types - try to generate
                    # If it's not an Expr, generate_expr will raise TypeError
                    # which is caught below
                    return self.generate_expr(cast("Expr", first_item))
                return html.escape(text)
            return self.generate_expr(result)
        except (LexerError, ParserError, TypeError):
            # Fallback: escape and return as-is
            return html.escape(text)

    def _format_identifier(self, name: str) -> str:
        """Format an identifier for KaTeX."""
        # Check for type names
        if name in self.TYPE_MAP:
            return self.TYPE_MAP[name]

        # Handle underscores for multi-word identifiers
        if "_" in name:
            parts = name.split("_")
            return r"\mathit{" + r"\_".join(parts) + "}"

        # Single letter identifiers
        if len(name) == 1:
            return name

        # Multi-letter identifiers get mathit
        return r"\mathit{" + name + "}"

    # =========================================================================
    # Expression generation using singledispatch
    # =========================================================================

    @singledispatchmethod
    def generate_expr(self, expr: Expr, _parent: Expr | None = None) -> str:
        """Generate KaTeX for an expression.

        Uses singledispatch to select the appropriate generator.

        Args:
            expr: The expression AST node.
            _parent: Parent expression for precedence handling (unused in base).

        Returns:
            KaTeX math string.

        Raises:
            TypeError: If expression type has no registered handler.
        """
        raise TypeError(f"Unknown expression type: {type(expr).__name__}")

    @generate_expr.register(Identifier)
    def _generate_identifier(
        self, node: Identifier, _parent: Expr | None = None
    ) -> str:
        """Generate KaTeX for identifier."""
        return self._format_identifier(node.name)

    @generate_expr.register(Number)
    def _generate_number(self, node: Number, _parent: Expr | None = None) -> str:
        """Generate KaTeX for number."""
        return node.value

    @generate_expr.register(BinaryOp)
    def _generate_binary_op(self, node: BinaryOp, parent: Expr | None = None) -> str:
        """Generate KaTeX for binary operation."""
        left = self.generate_expr(node.left, node)
        right = self.generate_expr(node.right, node)

        op_latex = self.BINARY_OPS.get(node.operator, node.operator)

        result = f"{left} {op_latex} {right}"

        # Add parentheses if needed
        if self._needs_parens(node, parent) or node.explicit_parens:
            result = f"({result})"

        return result

    @generate_expr.register(UnaryOp)
    def _generate_unary_op(self, node: UnaryOp, _parent: Expr | None = None) -> str:
        """Generate KaTeX for unary operation."""
        operand = self.generate_expr(node.operand, node)

        # Handle postfix operators
        if node.operator in ("~", "+", "*"):
            return f"{operand}{self.UNARY_OPS[node.operator]}"

        # Handle prefix operators
        op_latex = self.UNARY_OPS.get(node.operator, node.operator)

        # Special cases for functions that take arguments
        if node.operator in ("dom", "ran", "id", "P", "P1", "F", "F1"):
            return f"{op_latex} \\, {operand}"

        if node.operator == "#":
            return f"\\# {operand}"

        return f"{op_latex} {operand}"

    @generate_expr.register(Quantifier)
    def _generate_quantifier(
        self, node: Quantifier, _parent: Expr | None = None
    ) -> str:
        """Generate KaTeX for quantifier."""
        quant_latex = self.QUANTIFIERS.get(node.quantifier, node.quantifier)

        # Build variable part
        if node.tuple_pattern:
            vars_part = self.generate_expr(node.tuple_pattern)
        else:
            vars_part = ", ".join(node.variables)

        parts = [quant_latex, vars_part]

        # Add domain
        if node.domain:
            domain_latex = self.generate_expr(node.domain)
            parts.append(":")
            parts.append(domain_latex)

        # Add bullet and body
        parts.append(r"\bullet")
        body_latex = self.generate_expr(node.body)
        parts.append(body_latex)

        # Add expression part (for mu or constraints)
        if node.expression:
            expr_latex = self.generate_expr(node.expression)
            parts.append(r"\bullet")
            parts.append(expr_latex)

        return " ".join(parts)

    @generate_expr.register(Subscript)
    def _generate_subscript(self, node: Subscript, _parent: Expr | None = None) -> str:
        """Generate KaTeX for subscript."""
        base = self.generate_expr(node.base, node)
        index = self.generate_expr(node.index, node)
        return f"{base}_{{{index}}}"

    @generate_expr.register(Superscript)
    def _generate_superscript(
        self, node: Superscript, _parent: Expr | None = None
    ) -> str:
        """Generate KaTeX for superscript."""
        base = self.generate_expr(node.base, node)
        exp = self.generate_expr(node.exponent, node)
        return f"{base}^{{{exp}}}"

    @generate_expr.register(SetComprehension)
    def _generate_set_comprehension(
        self, node: SetComprehension, _parent: Expr | None = None
    ) -> str:
        """Generate KaTeX for set comprehension."""
        vars_str = ", ".join(node.variables)
        parts = [r"\{", vars_str]

        if node.domain:
            domain_latex = self.generate_expr(node.domain)
            parts.append(":")
            parts.append(domain_latex)

        if node.predicate:
            pred_latex = self.generate_expr(node.predicate)
            parts.append(r"\mid")
            parts.append(pred_latex)

        if node.expression:
            expr_latex = self.generate_expr(node.expression)
            parts.append(r"\bullet")
            parts.append(expr_latex)

        parts.append(r"\}")
        return " ".join(parts)

    @generate_expr.register(SetLiteral)
    def _generate_set_literal(
        self, node: SetLiteral, _parent: Expr | None = None
    ) -> str:
        """Generate KaTeX for set literal."""
        if not node.elements:
            return r"\emptyset"

        elements = [self.generate_expr(e) for e in node.elements]
        return r"\{" + ", ".join(elements) + r"\}"

    @generate_expr.register(FunctionApp)
    def _generate_function_app(
        self, node: FunctionApp, _parent: Expr | None = None
    ) -> str:
        """Generate KaTeX for function application."""
        func = self.generate_expr(node.function, node)
        args = [self.generate_expr(a) for a in node.args]

        if not args:
            return f"{func}()"

        # Handle single arg without parens for standard notation
        if len(args) == 1:
            return f"{func}({args[0]})"

        return f"{func}({', '.join(args)})"

    @generate_expr.register(FunctionType)
    def _generate_function_type(
        self, node: FunctionType, _parent: Expr | None = None
    ) -> str:
        """Generate KaTeX for function type."""
        domain = self.generate_expr(node.domain, node)
        range_type = self.generate_expr(node.range, node)
        arrow = self.BINARY_OPS.get(node.arrow, r"\rightarrow")
        return f"{domain} {arrow} {range_type}"

    @generate_expr.register(Lambda)
    def _generate_lambda(self, node: Lambda, _parent: Expr | None = None) -> str:
        """Generate KaTeX for lambda expression."""
        vars_str = ", ".join(node.variables)
        domain = self.generate_expr(node.domain)
        body = self.generate_expr(node.body)
        return rf"\lambda {vars_str} : {domain} \bullet {body}"

    @generate_expr.register(Tuple)
    def _generate_tuple(self, node: Tuple, _parent: Expr | None = None) -> str:
        """Generate KaTeX for tuple."""
        elements = [self.generate_expr(e) for e in node.elements]
        return "(" + ", ".join(elements) + ")"

    @generate_expr.register(RelationalImage)
    def _generate_relational_image(
        self, node: RelationalImage, _parent: Expr | None = None
    ) -> str:
        """Generate KaTeX for relational image."""
        rel = self.generate_expr(node.relation, node)
        set_expr = self.generate_expr(node.set, node)
        return rf"{rel}(| {set_expr} |)"

    @generate_expr.register(GenericInstantiation)
    def _generate_generic_instantiation(
        self, node: GenericInstantiation, _parent: Expr | None = None
    ) -> str:
        """Generate KaTeX for generic instantiation."""
        base = self.generate_expr(node.base, node)

        # Handle special types with single param
        if (
            isinstance(node.base, Identifier)
            and node.base.name in self.SPECIAL_TYPES
            and len(node.type_params) == 1
        ):
            type_latex = self.SPECIAL_TYPES[node.base.name]
            param = self.generate_expr(node.type_params[0])
            return f"{type_latex} \\, {param}"

        params = [self.generate_expr(p) for p in node.type_params]
        return f"{base}[{', '.join(params)}]"

    @generate_expr.register(Range)
    def _generate_range(self, node: Range, _parent: Expr | None = None) -> str:
        """Generate KaTeX for range expression."""
        start = self.generate_expr(node.start, node)
        end = self.generate_expr(node.end, node)
        return rf"{start} \ldots {end}"

    @generate_expr.register(SequenceLiteral)
    def _generate_sequence_literal(
        self, node: SequenceLiteral, _parent: Expr | None = None
    ) -> str:
        """Generate KaTeX for sequence literal."""
        if not node.elements:
            return r"\langle \rangle"

        elements = [self.generate_expr(e) for e in node.elements]
        return r"\langle " + ", ".join(elements) + r" \rangle"

    @generate_expr.register(TupleProjection)
    def _generate_tuple_projection(
        self, node: TupleProjection, _parent: Expr | None = None
    ) -> str:
        """Generate KaTeX for tuple projection."""
        base = self.generate_expr(node.base, node)
        if isinstance(node.index, int):
            return f"{base}.{node.index}"
        return f"{base}.{node.index}"

    @generate_expr.register(BagLiteral)
    def _generate_bag_literal(
        self, node: BagLiteral, _parent: Expr | None = None
    ) -> str:
        """Generate KaTeX for bag literal."""
        elements = [self.generate_expr(e) for e in node.elements]
        return r"\lbag " + ", ".join(elements) + r" \rbag"

    @generate_expr.register(Conditional)
    def _generate_conditional(
        self, node: Conditional, _parent: Expr | None = None
    ) -> str:
        """Generate KaTeX for conditional expression."""
        cond = self.generate_expr(node.condition)
        then_expr = self.generate_expr(node.then_expr)
        else_expr = self.generate_expr(node.else_expr)
        return (
            rf"\text{{if }} {cond} \text{{ then }} {then_expr} "
            rf"\text{{ else }} {else_expr}"
        )

    @generate_expr.register(GuardedBranch)
    def _generate_guarded_branch(
        self, node: GuardedBranch, _parent: Expr | None = None
    ) -> str:
        """Generate KaTeX for a guarded branch."""
        expr = self.generate_expr(node.expression)
        guard = self.generate_expr(node.guard)
        return rf"{expr} \text{{ if }} {guard}"

    @generate_expr.register(GuardedCases)
    def _generate_guarded_cases(
        self, node: GuardedCases, _parent: Expr | None = None
    ) -> str:
        """Generate KaTeX for guarded cases."""
        branches = [self.generate_expr(b) for b in node.branches]
        return r" \\ ".join(branches)

    # =========================================================================
    # Helper methods
    # =========================================================================

    def _needs_parens(self, node: BinaryOp, parent: Expr | None) -> bool:
        """Check if parentheses are needed based on precedence."""
        if parent is None:
            return False

        if not isinstance(parent, BinaryOp):
            return False

        node_prec = self.PRECEDENCE.get(node.operator, 10)
        parent_prec = self.PRECEDENCE.get(parent.operator, 10)

        # Lower precedence needs parens
        if node_prec < parent_prec:
            return True

        # Same precedence: check associativity
        if node_prec == parent_prec:
            # Right child of left-associative op needs parens
            if parent.operator not in self.RIGHT_ASSOCIATIVE:
                if node is parent.right:
                    return True
            # Left child of right-associative op needs parens
            else:
                if node is parent.left:
                    return True

        return False
