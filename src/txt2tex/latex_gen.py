"""LaTeX generator for txt2tex - converts AST to LaTeX."""

from __future__ import annotations

import re
import sys
from functools import singledispatchmethod
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
    SyntaxDefinition,
    TruthTable,
    Tuple,
    TupleProjection,
    UnaryOp,
    Zed,
)
from txt2tex.constants import PROSE_WORDS
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser, ParserError


class LaTeXGenerator:
    """Converts txt2tex AST to LaTeX source code.

    Supports propositional/predicate logic, Z notation (schemas, axdefs, free types),
    sets, relations, functions, sequences, bags, proof trees, and text blocks.
    """

    # Operator mappings
    BINARY_OPS: ClassVar[dict[str, str]] = {
        # Propositional logic - Only LaTeX-style keywords
        "land": r"\land",
        "lor": r"\lor",
        "=>": r"\Rightarrow",
        "implies": r"\Rightarrow",  # Internal operator for filter semantics
        "<=>": r"\Leftrightarrow",
        # Comparison operators
        "<": r"<",
        ">": r">",
        "<=": r"\leq",
        ">=": r"\geq",
        "=": r"=",
        "!=": r"\neq",
        "/=": r"\neq",  # Z notation slash negation
        # Sequent judgment
        "shows": r"\shows",  # Turnstile (⊢)
        # Set operators
        "elem": r"\in",  # Set membership
        "notin": r"\notin",
        "/in": r"\notin",  # Z notation slash negation
        "subset": r"\subseteq",
        "subseteq": r"\subseteq",  # Alternative notation for subset
        "psubset": r"\subset",  # Strict/proper subset
        "union": r"\cup",
        "intersect": r"\cap",
        "cross": r"\cross",  # Cartesian product
        "×": r"\cross",  # Cartesian product (Unicode)  # noqa: RUF001
        "\\": r"\setminus",  # Set difference
        "++": r"\oplus",  # Override
        # Relation operators
        "<->": r"\rel",  # Relation type
        "|->": r"\mapsto",  # Maplet constructor
        "<|": r"\dres",  # Domain restriction
        "|>": r"\rres",  # Range restriction
        "comp": r"\comp",  # Relational composition
        ";": r"\semi",  # Relational composition (semicolon)
        # Extended relation operators
        "<<|": r"\ndres",  # Domain subtraction (anti-restriction)
        "|>>": r"\nrres",  # Range subtraction (anti-restriction)
        "o9": r"\circ",  # Forward/backward composition
        # Function type operators
        "->": r"\fun",  # Total function
        "+->": r"\pfun",  # Partial function
        ">->": r"\inj",  # Total injection
        ">+>": r"\pinj",  # Partial injection
        "-|>": r"\pinj",  # Partial injection (alternative notation)
        "-->>": r"\surj",  # Total surjection
        "+->>": r"\psurj",  # Partial surjection
        ">->>": r"\bij",  # Bijection
        "77->": r"\ffun",  # Finite partial function
        # Arithmetic operators
        "+": r"+",  # Addition (also postfix in relational context)
        "-": r"-",  # Subtraction
        "*": r"*",  # Multiplication (also postfix in relational context)
        "mod": r"\mod",  # Modulo (use \mod not \bmod for fuzz compatibility)
        # Sequence operators
        "⌢": r"\cat",  # Sequence concatenation (Unicode)
        "^": r"\cat",  # Sequence concatenation (ASCII alternative)
        "↾": r"\filter",  # Sequence filter (Unicode)
        "filter": r"\filter",  # Sequence filter (ASCII alternative)
        # Bag operators
        "⊎": r"\uplus",  # Bag union (Unicode)
        "bag_union": r"\uplus",  # Bag union (ASCII alternative)
    }

    UNARY_OPS: ClassVar[dict[str, str]] = {
        "lnot": r"\lnot",  # Only LaTeX-style keyword
        "-": r"-",  # Unary negation
        "#": r"\#",  # Cardinality
        # Relation functions
        "dom": r"\dom",  # Domain of relation
        "ran": r"\ran",  # Range of relation
        # Extended relation functions
        "inv": r"\inv",  # Inverse function
        "id": r"\id",  # Identity relation
        # Set functions
        "P": r"\power",  # Power set
        "P1": r"\power_1",  # Non-empty power set
        "F": r"\finset",  # Finite set
        "F1": r"\finset_1",  # Non-empty finite set
        "bigcup": r"\bigcup",  # Distributed union
        "bigcap": r"\bigcap",  # Distributed intersection
        # Postfix operators - special handling needed
        "~": r"^{-1}",  # Relational inverse (superscript -1)
        "+": r"^{+}",  # Transitive closure (superscript +)
        "*": r"^{*}",  # Reflexive-transitive closure (superscript *)
    }

    # Quantifier mappings
    QUANTIFIERS: ClassVar[dict[str, str]] = {
        "forall": r"\forall",
        "exists": r"\exists",
        "exists1": r"\exists_1",  # Unique existence quantifier
        "mu": r"\mu",  # Definite description (mu-operator)
    }

    # Operator precedence (lower number = lower precedence)
    # Only LaTeX-style keywords supported: land, lor
    PRECEDENCE: ClassVar[dict[str, int]] = {
        "<=>": 1,  # Lowest precedence
        "=>": 2,
        "implies": 2,  # Internal operator for filter semantics
        "lor": 3,
        "land": 4,
        # Comparison operators
        "<": 5,
        ">": 5,
        "<=": 5,
        ">=": 5,
        "=": 5,
        "!=": 5,
        # Relation operators - between comparison and set ops
        "<->": 6,
        "|->": 6,
        "<|": 6,
        "|>": 6,
        "<<|": 6,  # Domain subtraction
        "|>>": 6,  # Range subtraction
        "o9": 6,  # Composition
        "comp": 6,
        ";": 6,
        # Function type operators - same precedence as relations
        "->": 6,
        "+->": 6,
        ">->": 6,
        ">+>": 6,
        "-->>": 6,
        "+->>": 6,
        ">->>": 6,
        "77->": 6,  # Finite partial function
        # Set operators - highest precedence
        "elem": 7,  # Set membership (replaces "in" after migration)
        "notin": 7,
        "subset": 7,
        "subseteq": 7,  # Alternative notation for subset
        "psubset": 7,  # Strict/proper subset
        "union": 8,
        "cross": 8,  # Cartesian product - same as union
        "×": 8,  # Cartesian product (Unicode) - same as union  # noqa: RUF001
        "intersect": 9,
        "\\": 9,  # Set difference - same as intersect
    }

    # Right-associative operators (need parens on left when same operator)
    # Implication and equivalence are right-associative
    RIGHT_ASSOCIATIVE: ClassVar[set[str]] = {"=>", "<=>"}

    # Instance variable type annotations
    use_fuzz: bool
    toc_parts: bool
    parts_format: str
    _in_equiv_block: bool
    _first_part_in_solution: bool
    _in_inline_part: bool
    _quantifier_depth: int
    _warn_overflow: bool
    _overflow_threshold: int
    _overflow_warnings: list[str]

    # Default threshold for overflow warnings (LaTeX characters)
    # ~140 LaTeX chars ≈ text width at 10pt with 1in margins in fuzz mode
    # Empirically calibrated: 136 chars fits, 150+ chars likely overflows
    DEFAULT_OVERFLOW_THRESHOLD: ClassVar[int] = 140

    def __init__(
        self,
        *,
        use_fuzz: bool = False,
        toc_parts: bool = False,
        warn_overflow: bool = True,
        overflow_threshold: int | None = None,
    ) -> None:
        """Initialize generator with package choice and TOC options.

        Args:
            use_fuzz: Use fuzz package instead of zed-* packages.
            toc_parts: Include parts (a, b, c) in table of contents.
            warn_overflow: Emit warnings for lines that may overflow page margins.
            overflow_threshold: LaTeX character threshold for overflow warnings.
                Defaults to DEFAULT_OVERFLOW_THRESHOLD (~100 chars).
        """
        self.use_fuzz = use_fuzz
        self.toc_parts = toc_parts
        self.parts_format = "subsection"  # Document-level parts format
        self._in_equiv_block = False  # Track context for line break formatting
        self._first_part_in_solution = False  # Track if we're generating first part
        self._in_inline_part = False  # Track if we're inside an inline part
        self._quantifier_depth = 0  # Track nesting for \t1, \t2 indentation
        self._warn_overflow = warn_overflow
        self._overflow_threshold = (
            overflow_threshold
            if overflow_threshold is not None
            else self.DEFAULT_OVERFLOW_THRESHOLD
        )
        self._overflow_warnings = []  # Collected warnings to emit

    # -------------------------------------------------------------------------
    # Overflow warning helpers
    # -------------------------------------------------------------------------

    def _check_overflow(
        self,
        latex: str,
        source_line: int,
        context: str,
        content_preview: str | None = None,
    ) -> None:
        """Check if generated LaTeX may overflow page margins.

        Args:
            latex: The generated LaTeX string to check.
            source_line: Source file line number for the warning.
            context: Description of where overflow occurs (e.g., "axdef where").
            content_preview: Optional preview of source content for warning.
        """
        if not self._warn_overflow:
            return

        # Split on LaTeX line breaks (\\) and check each line individually
        # This respects user-inserted line breaks via \ continuation
        lines = latex.split("\\\\")

        # Find the longest line (strip leading whitespace like \t1)
        max_line_len = 0
        for line in lines:
            # Strip common indentation markers
            stripped = line.lstrip()
            if stripped.startswith("\\t1 "):
                stripped = stripped[4:]
            max_line_len = max(max_line_len, len(stripped))

        if max_line_len <= self._overflow_threshold:
            return

        # Build warning message
        preview = content_preview or latex[:50] + "..." if len(latex) > 50 else latex
        warning = (
            f"Warning: Line {source_line} may overflow page margin "
            f"(~{max_line_len} chars)\n"
            f"  In: {context}\n"
            f"  Content: {preview}\n"
            f"  Suggestion: Break long expressions using indentation continuation"
        )
        self._overflow_warnings.append(warning)

    def emit_warnings(self) -> None:
        """Emit all collected overflow warnings to stderr."""
        for warning in self._overflow_warnings:
            print(warning, file=sys.stderr)  # noqa: T201 - intentional user warning

    def get_warnings(self) -> list[str]:
        """Return collected overflow warnings (for testing)."""
        return self._overflow_warnings.copy()

    # -------------------------------------------------------------------------
    # Fuzz/Standard LaTeX mode helpers
    # -------------------------------------------------------------------------

    def _get_bullet_separator(self) -> str:
        """Return bullet separator: @ for fuzz, \\bullet for standard LaTeX."""
        return "@" if self.use_fuzz else r"\bullet"

    def _get_colon_separator(self) -> str:
        """Return colon separator: : for fuzz, \\colon for standard LaTeX."""
        return ":" if self.use_fuzz else r"\colon"

    def _get_mid_separator(self) -> str:
        """Return mid separator: | for fuzz, \\mid for standard LaTeX."""
        return "|" if self.use_fuzz else r"\mid"

    def _get_type_latex(self, name: str) -> str | None:
        """Return LaTeX for mathematical type names (N, Z, N1).

        Returns None if name is not a known type name.
        """
        type_map_fuzz = {"Z": r"\num", "N": r"\nat", "N1": r"\nat_1"}
        type_map_std = {"Z": r"\mathbb{Z}", "N": r"\mathbb{N}", "N1": r"\mathbb{N}_1"}
        if name in type_map_fuzz:
            return type_map_fuzz[name] if self.use_fuzz else type_map_std[name]
        return None

    def _get_closure_operator_latex(self, operator: str, operand: str) -> str:
        """Return LaTeX for closure/inverse operators (+, *, ~).

        Args:
            operator: One of '+', '*', '~'
            operand: The operand LaTeX string

        Returns:
            Formatted LaTeX with appropriate operator for fuzz/standard mode.
        """
        if self.use_fuzz:
            if operator == "+":
                return rf"{operand} \plus"
            if operator == "*":
                return rf"{operand} \star"
            # ~ inverse uses \inv in fuzz mode (fuzz.sty defines \inv as ^\sim)
            return rf"{operand} \inv"
        # Standard LaTeX: superscript notation
        op_superscript = {"+": "^{+}", "*": "^{*}", "~": "^{-1}"}
        return f"{operand}{op_superscript[operator]}"

    def _format_multiword_identifier(self, name: str) -> str:
        """Format a multi-word identifier with underscores.

        For fuzz: just escape underscores (name\\_with\\_underscores)
        For standard LaTeX: escape and wrap in \\mathit{...}
        """
        escaped = name.replace("_", r"\_")
        if self.use_fuzz:
            return escaped
        return rf"\mathit{{{escaped}}}"

    def _map_binary_operator(self, operator: str, base_latex: str) -> str:
        """Map binary operator to appropriate LaTeX for fuzz/standard mode.

        Fuzz-specific mappings:
        - => / implies → \\implies (instead of \\Rightarrow)
        - <=> → \\iff (outside EQUIV blocks) or \\Leftrightarrow (in EQUIV)
        """
        if not self.use_fuzz:
            return base_latex
        if operator in ("=>", "implies"):
            return r"\implies"
        # In EQUIV blocks, use \Leftrightarrow; otherwise use \iff
        if operator == "<=>" and not self._in_equiv_block:
            return r"\iff"
        return base_latex

    def _generate_document_items_with_consolidation(
        self, items: list[DocumentItem]
    ) -> list[str]:
        """Generate document items with zed environment consolidation.

        Groups consecutive GivenType, FreeType, and Abbreviation items
        into a single zed environment with \\also between them.
        """
        lines: list[str] = []
        i = 0
        while i < len(items):
            item = items[i]
            # Check if this is a zed-generating item
            if isinstance(item, (GivenType, FreeType, Abbreviation)):
                # Collect consecutive zed items
                zed_items: list[GivenType | FreeType | Abbreviation] = [item]
                j = i + 1
                while j < len(items):
                    next_item = items[j]
                    if not isinstance(next_item, (GivenType, FreeType, Abbreviation)):
                        break
                    zed_items.append(next_item)
                    j += 1

                # Generate consolidated zed environment
                if len(zed_items) == 1:
                    # Single item: generate normally
                    item_lines = self.generate_document_item(item)
                    lines.extend(item_lines)
                else:
                    # Multiple consecutive items: consolidate
                    lines.append(r"\begin{zed}")
                    for idx, zed_item in enumerate(zed_items):
                        if idx > 0:
                            lines.append(r"\also")
                        # Generate content without wrapping zed environment
                        content = self._generate_zed_content(zed_item)
                        lines.append(content)
                    lines.append(r"\end{zed}")
                    lines.append("")

                # Skip processed items
                i = j
            else:
                # Not a zed item: generate normally
                item_lines = self.generate_document_item(item)
                lines.extend(item_lines)
                i += 1

        return lines

    def _generate_zed_content(self, item: GivenType | FreeType | Abbreviation) -> str:
        """Generate the content of a zed item without the environment wrapper."""
        if isinstance(item, GivenType):
            names_str = ", ".join(item.names)
            return f"[{names_str}]"
        if isinstance(item, FreeType):
            # Generate branches
            branch_strs: list[str] = []
            for branch in item.branches:
                if branch.parameters is None:
                    branch_strs.append(branch.name)
                else:
                    if isinstance(branch.parameters, SequenceLiteral):
                        if branch.parameters.elements:
                            params_latex = self.generate_expr(
                                branch.parameters.elements[0]
                            )
                        else:
                            params_latex = ""
                    else:
                        params_latex = self.generate_expr(branch.parameters)
                    branch_strs.append(f"{branch.name} \\ldata {params_latex} \\rdata")
            branches_str = " | ".join(branch_strs)
            return f"{item.name} ::= {branches_str}"
        # Abbreviation
        expr_latex = self.generate_expr(item.expression)
        name_latex = self._generate_identifier(
            Identifier(line=0, column=0, name=item.name)
        )
        if item.generic_params:
            params_str = ", ".join(item.generic_params)
            return f"{name_latex}[{params_str}] == {expr_latex}"
        return f"{name_latex} == {expr_latex}"

    def generate_fragment(self, ast: Document) -> str:
        """Generate LaTeX content without document wrapper.

        Useful for interactive mode and previews where the content
        will be wrapped in a minimal document separately.

        Args:
            ast: The Document AST to generate content for.

        Returns:
            LaTeX content (body only, no preamble/postamble).
        """
        # Store document-level parts format
        self.parts_format = ast.parts_format

        # Generate all document items
        lines = self._generate_document_items_with_consolidation(ast.items)

        return "\n".join(lines)

    def generate_document(self, ast: Document | Expr) -> str:
        """Generate complete LaTeX document with preamble and postamble.

        Produces a full LaTeX document including documentclass, packages,
        title/author metadata, bibliography, and document body.

        Args:
            ast: The AST root node, either a Document with structural elements
                or a single Expr for backward compatibility.

        Returns:
            Complete LaTeX source code ready for compilation.
        """
        lines: list[str] = []

        # Preamble
        # Use fleqn option to left-align all equations (no centering)
        # a4paper for A4 page size, 10pt font
        lines.append(r"\documentclass[a4paper,10pt,fleqn]{article}")
        # Standard 1 inch margins on all sides
        lines.append(r"\usepackage[margin=1in]{geometry}")
        # Load amssymb for \mathbb{N} and \mathbb{Z} blackboard bold
        # Note: amsmath removed - using array{lll} instead of align* for EQUIV
        lines.append(r"\usepackage{amssymb}")  # For \mathbb{N} and \mathbb{Z}
        # Load adjustbox for scaling wide elements to fit page width
        lines.append(r"\usepackage{adjustbox}")
        # Load natbib for author-year citations (Harvard style)
        lines.append(r"\usepackage{natbib}")
        # Load hyperref BEFORE fuzz to avoid conflict with fuzz's \t command
        # hyperref redefines \t, but fuzz needs to override it for indentation
        lines.append(
            r"\usepackage[colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue]{hyperref}"
        )
        if self.use_fuzz:
            lines.append(r"\usepackage{fuzz}")  # Replaces zed-cm (fonts/styling)
        else:
            lines.append(r"\usepackage{zed-cm}")  # Computer Modern fonts/styling
        # These packages work with both fuzz and zed-cm
        lines.append(r"\usepackage{zed-maths}")  # Mathematical operators
        lines.append(r"\usepackage{zed-proof}")  # Proof tree macros (\infer)

        # Declare dimension register for saving \leftskip before \begin{center}
        # The center environment resets \leftskip, but we need it for width calc
        lines.append(r"\newdimen\savedleftskip")

        # Title metadata (if present)
        if isinstance(ast, Document) and ast.title_metadata:
            meta = ast.title_metadata
            if meta.title:
                lines.append(r"\title{" + meta.title + "}")
            # Generate author field with optional subtitle/institution footnotes
            # Even without author name, generate \author{} if they're present
            if meta.author or meta.subtitle or meta.institution:
                author_parts: list[str] = []
                if meta.author:
                    author_parts.append(meta.author)
                if meta.subtitle:
                    author_parts.append(r"\thanks{" + meta.subtitle + "}")
                if meta.institution:
                    author_parts.append(r"\thanks{" + meta.institution + "}")
                lines.append(r"\author{" + " ".join(author_parts) + "}")
            if meta.date:
                lines.append(r"\date{" + meta.date + "}")

            # PDF metadata via hyperref (already loaded above)
            hypersetup_opts: list[str] = []
            if meta.title:
                hypersetup_opts.append(f"pdftitle={{{meta.title}}}")
            if meta.author:
                hypersetup_opts.append(f"pdfauthor={{{meta.author}}}")
            if meta.subtitle:
                hypersetup_opts.append(f"pdfsubject={{{meta.subtitle}}}")
            hypersetup_opts.append(f"pdfcreator={{txt2tex v{__version__}}}")
            lines.append(r"\hypersetup{" + ",".join(hypersetup_opts) + "}")

        lines.append(r"\begin{document}")
        lines.append("")

        # Generate title page if metadata present
        if isinstance(ast, Document) and ast.title_metadata:
            lines.append(r"\maketitle")
            lines.append("")

        # Content - handle both Document and single Expr
        if isinstance(ast, Document):
            # Store document-level parts format
            self.parts_format = ast.parts_format
            # Multi-line document: generate each item
            # Consolidate consecutive zed environments
            lines.extend(self._generate_document_items_with_consolidation(ast.items))

            # Generate bibliography if bibliography file is specified
            if ast.bibliography_metadata and ast.bibliography_metadata.file:
                # Reset indentation before bibliography
                lines.append(r"\setlength{\leftskip}{0pt}")
                lines.append("")
                # Generate bibliography style (default to "plainnat" if not specified)
                # plainnat works with natbib package and provides author-year citations
                style = ast.bibliography_metadata.style or "plainnat"
                lines.append(r"\bibliographystyle{" + style + "}")
                lines.append("")
                # Generate bibliography command (remove .bib extension if present)
                bib_file = ast.bibliography_metadata.file
                if bib_file.endswith(".bib"):
                    bib_file = bib_file[:-4]
                lines.append(r"\bibliography{" + bib_file + "}")
                lines.append("")
        else:
            # Single expression (backward compatibility)
            latex_expr = self.generate_expr(ast)
            lines.append(f"${latex_expr}$")
            lines.append("")

        # Postamble
        lines.append(r"\end{document}")

        return "\n".join(lines)

    @singledispatchmethod
    def generate_document_item(self, item: DocumentItem) -> list[str]:
        """Generate LaTeX lines for a document item.

        Uses singledispatch to select the appropriate generator based on
        the item type. This fallback handles bare Expr nodes that appear
        as document items.

        Args:
            item: The document item node to generate. Can be Section,
                Solution, TruthTable, EquivChain, Schema, AxDef, or Expr.

        Returns:
            List of LaTeX lines (without newline characters).
        """
        # Fallback only reached for Expr types (all document types are registered)
        expr = cast("Expr", item)
        latex_expr = self.generate_expr(expr)

        if self._has_line_breaks(expr):
            # Multi-line expression: use display math with array
            # Respect inline part context for proper positioning
            lines: list[str] = []

            if self._in_inline_part:
                # Inside part with leftskip: position naturally with leftskip
                lines.append(r"\savedleftskip=\leftskip")
                lines.append(r"\noindent")
            else:
                # Normal context: just prevent paragraph indentation
                lines.append(r"\noindent")

            lines.append(r"$\displaystyle")
            lines.append(r"\begin{array}{l}")  # Left-aligned single column
            lines.append(latex_expr)
            lines.append(r"\end{array}$")
            lines.append("")
            # Add trailing spacing for separation from following content
            lines.append(r"\bigskip")
            lines.append("")
            return lines
        # Single-line expression: use inline math (original behavior)
        return [r"\noindent", f"${latex_expr}$", "", ""]

    def _has_line_breaks(self, expr: Expr) -> bool:
        """Recursively check if expression contains any line breaks.

        Args:
            expr: The expression to check

        Returns:
            True if expr or any sub-expression has line breaks
        """
        if isinstance(expr, BinaryOp):
            if expr.line_break_after:
                return True
            return self._has_line_breaks(expr.left) or self._has_line_breaks(expr.right)
        if isinstance(expr, UnaryOp):
            return self._has_line_breaks(expr.operand)
        if isinstance(expr, Quantifier):
            if expr.line_break_after_pipe:
                return True
            if expr.domain and self._has_line_breaks(expr.domain):
                return True
            return self._has_line_breaks(expr.body)
        if isinstance(expr, Lambda):
            return self._has_line_breaks(expr.body)
        if isinstance(expr, Subscript):
            return self._has_line_breaks(expr.base) or self._has_line_breaks(expr.index)
        if isinstance(expr, Superscript):
            return self._has_line_breaks(expr.base) or self._has_line_breaks(
                expr.exponent
            )
        if isinstance(expr, SetComprehension):
            # Check all parts of set comprehension
            if expr.domain and self._has_line_breaks(expr.domain):
                return True
            if expr.predicate and self._has_line_breaks(expr.predicate):
                return True
            return bool(expr.expression and self._has_line_breaks(expr.expression))
        if isinstance(expr, SetLiteral):
            return any(self._has_line_breaks(elem) for elem in expr.elements)
        if isinstance(expr, FunctionApp):
            if self._has_line_breaks(expr.function):
                return True
            return any(self._has_line_breaks(arg) for arg in expr.args)
        if isinstance(expr, Tuple):
            return any(self._has_line_breaks(elem) for elem in expr.elements)
        if isinstance(expr, RelationalImage):
            return self._has_line_breaks(expr.relation) or self._has_line_breaks(
                expr.set
            )
        if isinstance(expr, GenericInstantiation):
            if self._has_line_breaks(expr.base):
                return True
            return any(self._has_line_breaks(param) for param in expr.type_params)
        if isinstance(expr, SequenceLiteral):
            return any(self._has_line_breaks(elem) for elem in expr.elements)
        if isinstance(expr, Conditional):
            return (
                self._has_line_breaks(expr.condition)
                or self._has_line_breaks(expr.then_expr)
                or self._has_line_breaks(expr.else_expr)
            )
        # Base cases: Identifier, Number, etc. - no line breaks
        return False

    @singledispatchmethod
    def generate_expr(self, expr: Expr, parent: Expr | None = None) -> str:
        """Generate LaTeX for expression (without wrapping in math mode).

        Uses singledispatch to select the appropriate generator based on
        the expression type. Each registered handler generates LaTeX for
        its specific node type, with precedence-aware parenthesization.

        Args:
            expr: The expression AST node to generate LaTeX for.
            parent: The parent expression context for precedence handling
                (None if top-level).

        Returns:
            LaTeX math-mode source code (caller wraps in $...$ or environments).

        Raises:
            TypeError: If expression type has no registered handler.
        """
        raise TypeError(f"Unknown expression type: {type(expr).__name__}")

    @generate_expr.register(Identifier)
    def _generate_identifier(self, node: Identifier, parent: Expr | None = None) -> str:
        """Generate LaTeX for identifier with smart underscore handling.

        Handles three cases:
        1. No underscore: return as-is (e.g., 'x' → 'x')
        2. Simple subscript: return as-is (e.g., 'a_i' → 'a_i', 'x_0' → 'x_0')
        3. Multi-char subscript: add braces (e.g., 'a_max' → 'a_{max}')
        4. Multi-word identifier: escape/mathit (e.g., 'cumulative_total')

        Special keywords (Issue #3 from QA):
        - emptyset → \\emptyset (empty set symbol)
        """
        name = node.name

        # Special keywords (Issue #2 and #3 from QA)
        special_keywords = {
            "emptyset": r"\emptyset",
            "forall": r"\forall",
            "exists": r"\exists",
        }
        if name in special_keywords:
            return special_keywords[name]

        # Handle compound identifiers with postfix closure operators (R+, R*, R~, Rr)
        # Appears in abbreviation and schema names
        # (partial support, GitHub #3 still open)
        if name.endswith("+"):
            base = name[:-1]
            # Render as R^+ (transitive closure)
            base_id = Identifier(line=0, column=0, name=base)
            return f"{self._generate_identifier(base_id)}^+"
        if name.endswith("*"):
            base = name[:-1]
            # Render as R^* (reflexive-transitive closure)
            base_id = Identifier(line=0, column=0, name=base)
            return f"{self._generate_identifier(base_id)}^*"
        if name.endswith("~"):
            base = name[:-1]
            # Render as R^{-1} (standard) or R^{\sim} (fuzz)
            base_id = Identifier(line=0, column=0, name=base)
            base_latex = self._generate_identifier(base_id)
            return self._get_closure_operator_latex("~", base_latex)

        # Check if this is an operator/function from UNARY_OPS dictionary
        # This handles operators like id, inv, dom, ran when used as identifiers
        # (e.g., in generic instantiations like id[Person])
        # Skip postfix operators (~, +, *) which have special handling
        if name in self.UNARY_OPS and name not in ["~", "+", "*"]:
            return self.UNARY_OPS[name]

        # Mathematical type names: use blackboard bold (or fuzz built-in types)
        # N = naturals, Z = integers, N1 = positive integers (≥ 1)
        # Only convert N and Z, not Q/R/C which are commonly used as variables
        type_latex = self._get_type_latex(name)
        if type_latex is not None:
            return type_latex

        # No underscore: return as-is
        if "_" not in name:
            return name

        # Check for multi-word identifier pattern
        # Heuristic: subscripts only for 1-2 char suffixes (e.g., z_1, x_10)
        # Anything 3+ chars is a multi-word identifier (e.g., cumulative_total)
        parts = name.split("_")

        # Multiple underscores → multi-word identifier
        if len(parts) > 2:
            return self._format_multiword_identifier(name)

        # Single underscore: prioritize suffix length for subscript detection
        if len(parts) == 2:
            prefix, suffix = parts
            # Priority 1: Single-char suffix → subscript (e.g., x_1, count_N)
            if len(suffix) == 1:
                if self.use_fuzz:
                    # Fuzz: numeric subscripts are decorations (bare _)
                    # Letter suffixes are identifier parts (escaped \_)
                    if suffix.isdigit():
                        return f"{prefix}_{suffix}"  # z_1 (decoration)
                    return f"{prefix}\\_{suffix}"  # length\_L (identifier)
                # Standard LaTeX: bare underscore for subscript
                return f"{prefix}_{suffix}"
            # Priority 2: Two-char suffix → subscript with braces (e.g., x_10)
            if len(suffix) == 2:
                if self.use_fuzz:
                    # Fuzz: all-numeric subscripts are decorations (bare _)
                    # Mixed/letter suffixes are identifier parts (escaped \_)
                    if suffix.isdigit():
                        return f"{prefix}_{{{suffix}}}"  # z_10 (decoration)
                    return f"{prefix}\\_{{{suffix}}}"  # state\_AB (identifier)
                # Standard LaTeX: bare underscore
                return f"{prefix}_{{{suffix}}}"
            # Priority 3: Long suffix → multi-word identifier (e.g., cumulative_total)
            # len(suffix) >= 3  # noqa: ERA001
            return self._format_multiword_identifier(name)

        # Fallback: multi-word identifier
        return self._format_multiword_identifier(name)

    @generate_expr.register(Number)
    def _generate_number(self, node: Number, parent: Expr | None = None) -> str:
        """Generate LaTeX for number."""
        return node.value

    @generate_expr.register(UnaryOp)
    def _generate_unary_op(self, node: UnaryOp, parent: Expr | None = None) -> str:
        """Generate LaTeX for unary operation.

        Unary operators have higher precedence than all binary operators,
        so parentheses are added around binary operator operands.

        Postfix operators (~, +, *, rcl) are rendered as superscripts
        on the operand, not as prefix operators.
        """
        op_latex = self.UNARY_OPS.get(node.operator)
        if op_latex is None:
            raise ValueError(f"Unknown unary operator: {node.operator}")

        operand = self.generate_expr(node.operand)

        # Add parentheses if operand is a binary operator
        # (unary has higher precedence than all binary operators)
        # Skip if operand has explicit_parens (it will add its own)
        if isinstance(node.operand, BinaryOp) and not node.operand.explicit_parens:
            operand = f"({operand})"

        # Add parentheses for function application with fuzz mode
        # Fuzz has different precedence: # binds less tightly than application
        # So # s(i) means (# s)(i), but we want # (s(i))  # noqa: ERA001
        if self.use_fuzz and isinstance(node.operand, FunctionApp):
            operand = f"({operand})"

        # Add parentheses when # is applied to function-like unary operators
        # in fuzz mode (e.g., # dom R needs to be # (dom R))
        # Otherwise fuzz parses it as (# dom) R
        function_like_ops = {
            "dom",
            "ran",
            "inv",
            "id",
            "P",
            "P1",
            "F",
            "F1",
            "bigcup",
            "bigcap",
        }
        if (
            self.use_fuzz
            and node.operator == "#"
            and isinstance(node.operand, UnaryOp)
            and node.operand.operator in function_like_ops
        ):
            operand = f"({operand})"

        # bigcup/bigcap need parentheses around function-like operands
        # E.g., bigcup (ran docs) must generate \bigcup (\ran docs)
        # Otherwise fuzz parses \bigcup \ran docs as (\bigcup \ran) docs
        if (
            self.use_fuzz
            and node.operator in {"bigcup", "bigcap"}
            and isinstance(node.operand, UnaryOp)
            and node.operand.operator in function_like_ops
        ):
            operand = f"({operand})"

        # Check if this is a postfix operator (rendered as superscript)
        if node.operator in {"~", "+", "*"}:
            return self._get_closure_operator_latex(node.operator, operand)
        # Generic instantiation operators (P, P1, F, F1)
        # Per fuzz manual p.23: prefix generic symbols are operator symbols,
        # LaTeX inserts thin space automatically - NO TILDE needed
        if node.operator in {"P", "P1", "F", "F1"}:
            # Generic instantiation: \power X or \finset X (no tilde)
            return f"{op_latex} {operand}"
        # Prefix: operator operand
        # Special case: no space for unary minus
        if node.operator == "-":
            return f"{op_latex}{operand}"
        return f"{op_latex} {operand}"

    def _needs_parens(
        self, child: Expr, parent: BinaryOp, *, is_left_child: bool
    ) -> bool:
        """Check if child expression needs parentheses in parent context.

        Args:
            child: The child expression to check
            parent: The parent BinaryOp node
            is_left_child: True if this is the left child, False if right

        Returns:
            True if parentheses are needed
        """
        parent_op = parent.operator
        # Quantifiers and lambdas have lowest precedence (bind most loosely)
        # Per Woodcock: "quantifiers bind very loosely, scope extends to next bracket"
        # Need parens when used as operands of binary operators
        # In fuzz mode, _quantifier_needs_parens handles this separately
        # In non-fuzz mode, we handle it here
        if isinstance(child, (Quantifier, Lambda)) and not self.use_fuzz:
            return True

        # FunctionType needs parentheses when used as operand in cross/other ops
        # E.g., (X -> Y) cross Z, not X -> Y cross Z which would be X -> (Y cross Z)
        if isinstance(child, FunctionType):
            return True

        # Only binary ops need precedence checking
        if not isinstance(child, BinaryOp):
            return False

        # If child has explicit parentheses from source, don't add
        # precedence-based parentheses. The child will add its own parens
        # when generated. Prevents double parenthesization ((A \land B))
        if child.explicit_parens:
            return False

        child_prec = self.PRECEDENCE.get(child.operator, 999)
        parent_prec = self.PRECEDENCE.get(parent_op, 999)

        # Need parens if child has lower precedence than parent
        if child_prec < parent_prec:
            return True

        # If same precedence, check associativity
        if child_prec == parent_prec and child.operator == parent_op:
            # For clarity in proofs, always add parentheses for nested
            # implications or equivalences (even if technically not required
            # by associativity)
            if parent_op in {"=>", "<=>"}:
                return True

            # Note: Cross product does NOT automatically get nested parens.
            # Fuzz distinguishes between:
            # - A x B x C (flat 3-tuple, no parens)
            # - (A x B) x C (nested pairs, with parens)
            # Only add parens where user explicitly wrote them in source.
            # Removed automatic parenthesization that was breaking fuzz 3-tuples.

            # For left-associative operators, right child needs parens
            # E.g., R o9 (S o9 T) requires parens on right
            # but (R o9 S) o9 T doesn't need parens on left
            # All operators except => and <=> are left-associative
            if not is_left_child:
                return True

        return False

    def _quantifier_needs_parens(self, node: Quantifier, parent: Expr | None) -> bool:
        """Check if quantifier needs parentheses in fuzz mode.

        In fuzz, quantifiers need parens when nested in expressions,
        but not when they're:
        - Top-level predicates (parent=None)
        - Bodies of other quantifiers (separated by @ or bullet)
        - Bodies of lambda expressions (separated by bullet)

        Args:
            node: The quantifier node
            parent: The parent expression (None if top-level)

        Returns:
            True if parentheses are needed in fuzz mode
        """
        if not self.use_fuzz:
            return False

        # Top-level: no parens needed
        if parent is None:
            return False

        # Body of quantifier/lambda: no parens (separated by @ or bullet)
        # Otherwise, nested in expression: needs parens
        return not isinstance(parent, (Quantifier, Lambda))

    @generate_expr.register(BinaryOp)
    def _generate_binary_op(self, node: BinaryOp, parent: Expr | None = None) -> str:
        """Generate LaTeX for binary operation.

        Supports line breaks with \\\\ for long expressions.
        """
        op_latex = self.BINARY_OPS.get(node.operator)
        if op_latex is None:
            raise ValueError(f"Unknown binary operator: {node.operator}")

        # Apply fuzz-specific operator mappings
        op_latex = self._map_binary_operator(node.operator, op_latex)

        # Pass this node as parent to children
        left = self.generate_expr(node.left, parent=node)
        right = self.generate_expr(node.right, parent=node)

        # Add parentheses if needed for precedence and associativity
        if self._needs_parens(node.left, node, is_left_child=True):
            left = f"({left})"
        if self._needs_parens(node.right, node, is_left_child=False):
            right = f"({right})"

        # Check for line break after operator
        if node.line_break_after:
            # Multi-line expression: insert \\ and indent continuation
            # EQUIV blocks use array format and need & prefix for column alignment
            # Schemas and proofs use plain \\ without & prefix
            indent = self._get_indentation()
            if self._in_equiv_block:
                result = f"{left} {op_latex} \\\\\n& {indent} {right}"
            else:
                result = f"{left} {op_latex} \\\\\n{indent} {right}"
        else:
            # Single-line expression
            result = f"{left} {op_latex} {right}"

        # Honor explicit parentheses from source
        # If the user explicitly wrote (expr), preserve those parentheses
        # regardless of precedence rules. This maintains semantic grouping clarity.
        if node.explicit_parens:
            result = f"({result})"

        return result

    def _get_indentation(self) -> str:
        """Get indentation command based on current quantifier depth.

        Returns:
            \\t1, \\t2, etc. for nested indentation, or \\quad for depth 0
        """
        # Use depth-based \t commands for nested quantifiers
        # \t1 = 1 * 2em, \t2 = 2 * 2em, etc.
        if self._quantifier_depth == 0:
            return r"\quad"  # Fallback for non-quantifier contexts
        return f"\\t{self._quantifier_depth}"

    @generate_expr.register(Quantifier)
    def _generate_quantifier(self, node: Quantifier, parent: Expr | None = None) -> str:
        """Generate LaTeX for quantifier (forall, exists, exists1, mu).

        Supports multiple variables, tuple patterns, and expression parts.

        Args:
            node: The quantifier node to generate.
            parent: The parent expression context (None if top-level).

        Returns:
            LaTeX string for the quantifier expression.

        Examples:
            forall x : N | pred -> \\forall x \\colon N \\bullet pred
            forall x, y : N | pred -> \\forall x, y \\colon N \\bullet pred
            forall (x, y) : T | pred -> \\forall (x, y) \\colon T \\bullet pred
            mu x : N | pred . expr -> \\mu x \\colon N \\mid pred \\bullet expr
        """
        quant_latex = self.QUANTIFIERS.get(node.quantifier)
        if quant_latex is None:
            raise ValueError(f"Unknown quantifier: {node.quantifier}")

        # Generate variables (tuple pattern or comma-separated list)
        if node.tuple_pattern:
            # Tuple pattern: forall (x, y) : T | P
            variables_str = self.generate_expr(node.tuple_pattern, parent=node)
        else:
            # Simple variables: forall x, y : T | P
            variables_str = ", ".join(node.variables)
        parts = [quant_latex, variables_str]

        if node.domain:
            domain_latex = self.generate_expr(node.domain, parent=node)
            parts.append(self._get_colon_separator())
            parts.append(domain_latex)

        # Special handling for mu operator in fuzz mode
        # Fuzz requires: (\mu decl | pred) with parentheses around ENTIRE mu expression
        if node.quantifier == "mu" and self.use_fuzz:
            mu_parts = [quant_latex, variables_str]
            if node.domain:
                domain_latex = self.generate_expr(node.domain, parent=node)
                mu_parts.append(f": {domain_latex}")
            # Always use | for predicate separator in mu

            # Increment depth for nested quantifiers
            self._quantifier_depth += 1
            # Get indentation at this depth (for line breaks)
            indent = self._get_indentation()
            body_latex = self.generate_expr(node.body, parent=node)
            self._quantifier_depth -= 1

            # Check for line break after pipe (|)
            if node.line_break_after_pipe:
                # Note: Fuzz mu is parenthesized, doesn't use array format
                # LaTeX source: \\ at end of line, then newline, then \t command
                mu_parts.append(f"| \\\\\n{indent} {body_latex}")
            else:
                mu_parts.append("|")
                mu_parts.append(body_latex)

            # If there's an expression part, add @ separator and expression
            if node.expression:
                mu_parts.append("@")
                expr_latex = self.generate_expr(node.expression, parent=node)
                mu_parts.append(expr_latex)

            # Wrap ENTIRE mu expression in parentheses
            return f"({' '.join(mu_parts)})"

        # Check if quantifier has expression part (bullet separator)
        if node.expression:
            # Use | or \mid for predicate separator
            pipe_sep = self._get_mid_separator()

            # Increment depth for nested quantifiers
            self._quantifier_depth += 1
            # Get indentation at this depth (for line breaks)
            indent = self._get_indentation()
            body_latex = self.generate_expr(node.body, parent=node)
            self._quantifier_depth -= 1

            # Check for line break after pipe (|)
            if node.line_break_after_pipe:
                # LaTeX source: \\ at end of line, then newline, then \t command
                if self._in_equiv_block:
                    parts.append(f"{pipe_sep} \\\\\n& {indent} {body_latex}")
                else:
                    parts.append(f"{pipe_sep} \\\\\n{indent} {body_latex}")
            else:
                parts.append(pipe_sep)
                parts.append(body_latex)

            # Add @ or bullet separator and expression
            bullet_sep = self._get_bullet_separator()
            expr_latex = self.generate_expr(node.expression, parent=node)

            # Check for line break after bullet (.)
            if node.line_break_after_bullet:
                # Get indentation for expression after bullet
                expr_indent = self._get_indentation()
                if self._in_equiv_block:
                    parts.append(f"{bullet_sep} \\\\\n& {expr_indent} {expr_latex}")
                else:
                    parts.append(f"{bullet_sep} \\\\\n{expr_indent} {expr_latex}")
            else:
                parts.append(bullet_sep)
                parts.append(expr_latex)
        else:
            # Standard quantifier: @ or bullet separator and body
            separator = self._get_bullet_separator()

            # Increment depth for nested quantifiers
            self._quantifier_depth += 1
            # Get indentation at this depth (for line breaks)
            indent = self._get_indentation()
            body_latex = self.generate_expr(node.body, parent=node)
            self._quantifier_depth -= 1

            # Check for line break after pipe (|)
            if node.line_break_after_pipe:
                # Multi-line quantifier: insert \\ and indent body
                # LaTeX source: \\ at end of line, then newline, then \t command
                # EQUIV blocks use array format and need & prefix
                # Schemas and proofs use plain \\ without &
                if self._in_equiv_block:
                    parts.append(f"{separator} \\\\\n& {indent} {body_latex}")
                else:
                    parts.append(f"{separator} \\\\\n{indent} {body_latex}")
            else:
                # Single-line quantifier
                parts.append(separator)
                parts.append(body_latex)

        result = " ".join(parts)

        # Smart parenthesization for fuzz mode (non-mu quantifiers only)
        # Mu expressions have special handling above (lines 593-610)
        if node.quantifier != "mu" and self._quantifier_needs_parens(node, parent):
            return f"({result})"

        return result

    @generate_expr.register(Lambda)
    def _generate_lambda(self, node: Lambda, parent: Expr | None = None) -> str:
        """Generate LaTeX for lambda expression.

        Examples:
        - lambda x : N . x^2 -> (\\lambda x : \\nat @ x^{2}) in fuzz mode
        - lambda x, y : N . x + y -> (\\lambda x, y : \\nat @ x + y) in fuzz mode
        - lambda f : X -> Y . f(x) -> (\\lambda f : X \\fun Y @ f(x)) in fuzz mode

        Note: Uses : (colon) for lambda binding, not \\colon.
        Fuzz requires @ separator and parentheses around lambdas in expressions.
        """
        # Generate variables (comma-separated for multi-variable)
        variables_str = ", ".join(node.variables)
        parts = [r"\lambda", variables_str, ":"]

        # Generate domain (required for lambda)
        domain_latex = self.generate_expr(node.domain)
        parts.append(domain_latex)

        # Add bullet/@ separator
        parts.append(self._get_bullet_separator())
        body_latex = self.generate_expr(node.body)
        parts.append(body_latex)

        result = " ".join(parts)

        # Fuzz requires lambdas to be parenthesized when appearing in expressions
        if self.use_fuzz and parent is not None:
            result = f"({result})"

        return result

    @generate_expr.register(SetComprehension)
    def _generate_set_comprehension(
        self, node: SetComprehension, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for set comprehension.

        Supports three forms:
        - Set by predicate: { x : X | predicate }
          -> \\{ x \\colon X \\mid predicate \\}
        - Set by expression with predicate: { x : X | pred . expr }
          -> \\{ x \\colon X \\mid pred \\bullet expr \\}
        - Set by expression only: { x : X . expr }
          -> \\{ x \\colon X \\bullet expr \\}

        Examples:
        - { x : N | x > 0 }
          -> \\{ x \\colon \\mathbb{N} \\mid x > 0 \\}
        - { x : N | x > 0 . x^2 }
          -> \\{ x \\colon \\mathbb{N} \\mid x > 0 \\bullet x^{2} \\}
        - { x : N . x^2 }
          -> \\{ x \\colon \\mathbb{N} \\bullet x^{2} \\}
        """
        # Generate variables (comma-separated for multi-variable)
        variables_str = ", ".join(node.variables)
        # Both fuzz and LaTeX use \{ \} for set braces
        # Add ~ spacing hints after { and before }
        parts = [r"\{~", variables_str]

        if node.domain:
            domain_latex = self.generate_expr(node.domain)
            parts.append(self._get_colon_separator())
            parts.append(domain_latex)

        # Handle case with no predicate
        if node.predicate is None:
            # No predicate: { x : X . expr } -> use bullet/@ directly
            if node.expression:
                parts.append(self._get_bullet_separator())
                expression_latex = self.generate_expr(node.expression)
                parts.append(expression_latex)
            # else: {x : T} with no predicate or expression - just the binding
        else:
            # Has predicate: add mid/pipe separator
            parts.append(self._get_mid_separator())

            # Generate predicate
            predicate_latex = self.generate_expr(node.predicate)
            parts.append(predicate_latex)

            # If expression is present, add bullet/@ and expression
            if node.expression:
                parts.append(self._get_bullet_separator())
                expression_latex = self.generate_expr(node.expression)
                parts.append(expression_latex)

        # Close set
        # Add ~ spacing hint before closing brace
        parts.append(r"~\}")

        return " ".join(parts)

    @generate_expr.register(SetLiteral)
    def _generate_set_literal(
        self, node: SetLiteral, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for set literal.

        Examples:
        - {1, 2, 3} -> \\{1, 2, 3\\}
        - {a, b} -> \\{a, b\\}
        - {} -> \\{\\} (empty set)
        """
        if not node.elements:
            # Empty set - render as \{\}
            return r"\{\}"

        # Generate comma-separated elements
        elements_latex = ", ".join(self.generate_expr(elem) for elem in node.elements)
        return f"\\{{{elements_latex}\\}}"

    @generate_expr.register(Subscript)
    def _generate_subscript(self, node: Subscript, parent: Expr | None = None) -> str:
        """Generate LaTeX for subscript (a_1, x_i)."""
        base = self.generate_expr(node.base)
        index = self.generate_expr(node.index)

        # Wrap index in braces if it's more than one character
        if len(index) > 1:
            return f"{base}_{{{index}}}"
        return f"{base}_{index}"

    @generate_expr.register(Superscript)
    def _generate_superscript(
        self, node: Superscript, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for superscript using \\bsup...\\esup (fuzz-compatible)."""
        base = self.generate_expr(node.base)
        exponent = self.generate_expr(node.exponent)

        # Use \bsup...\esup for fuzz compatibility
        # Standard ^{n} doesn't work in fuzz mode
        # This syntax works in both fuzz and zed modes

        # If base is itself a superscript, wrap in braces to avoid double superscript
        if isinstance(node.base, Superscript):
            base = f"{{{base}}}"

        return f"{base} \\bsup {exponent} \\esup"

    @generate_expr.register(FunctionApp)
    def _generate_function_app(
        self, node: FunctionApp, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for function application.

        Supports applying any expression, not just identifiers.

        Examples:
        - f(x) → f(x)
        - g(x, y, z) → g(x, y, z)
        - seq(N) → \\seq~N
        - seq seq N → \\seq \\seq N (nested special functions)
        - seq1 seq X → \\seq_1 \\seq X (nested special functions)
        - ⟨a, b, c⟩(2) → \\langle a, b, c \\rangle(2)
        - (f ++ g)(x) → (f \\oplus g)(x)
        """
        # Special Z notation functions with LaTeX commands
        special_functions = {
            "seq": r"\seq",
            "seq1": r"\seq_1",  # Non-empty sequences
            "iseq": r"\iseq",
            "bag": r"\bag",
            "P": r"\power",  # Power set
            "F": r"\finset",  # Finite set
        }

        # Check if function is a simple identifier with special handling
        if isinstance(node.function, Identifier):
            func_name = node.function.name
            if func_name in special_functions and len(node.args) == 1:
                # Generic instantiation: \seq N (no tilde)
                # Per fuzz manual p.23: prefix generic symbols are operator symbols,
                # LaTeX inserts thin space automatically
                func_latex = special_functions[func_name]
                arg = node.args[0]
                arg_latex = self.generate_expr(arg)
                # Add parentheses for nested applications
                # Critical for fuzz: P (P Z) → \power (\power Z) not \power \power Z
                # FunctionApp: P (P Z), seq (seq X)
                # BinaryOp: seq (X cross Y), P (A union B)
                # GenericInstantiation: seq (P[X])  # noqa: ERA001
                if isinstance(arg, (FunctionApp, BinaryOp, GenericInstantiation)):
                    arg_latex = f"({arg_latex})"
                # Add ~ spacing hint between function and argument
                return f"{func_latex}~{arg_latex}"

            # Standard function application with identifier: f(x, y, z)
            # Process identifier through _generate_identifier for underscore handling
            func_latex = self._generate_identifier(node.function)
            args_latex = ", ".join(self.generate_expr(arg) for arg in node.args)
            return f"{func_latex}({args_latex})"

        # Check for nested special functions: seq seq X or seq1 seq X
        # Parser treats "seq seq X" as ((seq seq) X) due to left-associativity
        # We need to recognize this pattern and generate \seq (\seq X) with parens
        if isinstance(node.function, FunctionApp):
            inner_func = node.function.function
            # Check if inner function is special and has one special function arg
            if (
                isinstance(inner_func, Identifier)
                and inner_func.name in special_functions
                and len(node.function.args) == 1
                and isinstance(node.function.args[0], Identifier)
                and node.function.args[0].name in special_functions
            ):
                # Pattern: (special_fn1(special_fn2))(args)  # noqa: ERA001
                # Generate: special_fn1~(special_fn2~args) with parens and tildes
                outer_latex = special_functions[inner_func.name]
                inner_latex = special_functions[node.function.args[0].name]
                args_latex = " ".join(self.generate_expr(arg) for arg in node.args)
                # Add ~ spacing hints
                return f"{outer_latex}~({inner_latex}~{args_latex})"

        # General function application: expr(args)
        func_latex = self.generate_expr(node.function)

        # Add parentheses around function if it's a binary operator
        if isinstance(node.function, BinaryOp):
            func_latex = f"({func_latex})"

        args_latex = ", ".join(self.generate_expr(arg) for arg in node.args)
        return f"{func_latex}({args_latex})"

    @generate_expr.register(FunctionType)
    def _generate_function_type(
        self, node: FunctionType, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for function type arrows.

        Examples:
        - X -> Y → X \\fun Y
        - X +-> Y → X \\pfun Y
        - X >-> Y → X \\inj Y
        - N +-> N → N \\pfun N
        - A -> B -> C → A \\fun (B \\fun C) [right-associative]
        """
        arrow_latex = self.BINARY_OPS.get(node.arrow)
        if arrow_latex is None:
            raise ValueError(f"Unknown function arrow: {node.arrow}")

        domain_latex = self.generate_expr(node.domain)
        range_latex = self.generate_expr(node.range)

        # Add parentheses to domain if it's a function type
        # (N1 +-> X) -> seq X should generate as (\nat_1 \pfun X) \fun \seq X
        if isinstance(node.domain, FunctionType):
            domain_latex = f"({domain_latex})"

        # Add parentheses to range if it's also a function type (for clarity)
        # Function types are right-associative: A -> B -> C means A -> (B -> C)
        if isinstance(node.range, FunctionType):
            range_latex = f"({range_latex})"

        return f"{domain_latex} {arrow_latex} {range_latex}"

    @generate_expr.register(Tuple)
    def _generate_tuple(self, node: Tuple, parent: Expr | None = None) -> str:
        """Generate LaTeX for tuple expression.

        Examples:
        - (1, 2) -> (1, 2)
        - (x, y, z) -> (x, y, z)
        - (a, b+1, f(c)) -> (a, b+1, f(c))

        Tuples are rendered as comma-separated expressions in parentheses.
        """
        elements_latex = ", ".join(self.generate_expr(elem) for elem in node.elements)
        return f"({elements_latex})"

    @generate_expr.register(RelationalImage)
    def _generate_relational_image(
        self, node: RelationalImage, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for relational image.

        The relational image R(| S |) gives the image of set S under relation R.

        Examples:
        - R(| {1, 2} |) -> (R \\limg \\{1, 2\\} \\rimg)
        - parentOf(| {john} |) -> (parentOf \\limg \\{john\\} \\rimg)
        - (R o9 S)(| A |) -> ((R \\circ S) \\limg A \\rimg)

        LaTeX rendering uses \\limg and \\rimg delimiters with spaces.
        Note: fuzz requires the entire expression wrapped in parentheses with
        spaces around \\limg/\\rimg, not function application syntax.
        """
        relation_latex = self.generate_expr(node.relation)
        set_latex = self.generate_expr(node.set)
        return f"({relation_latex} \\limg {set_latex} \\rimg)"

    @generate_expr.register(GenericInstantiation)
    def _generate_generic_instantiation(
        self, node: GenericInstantiation, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for generic type instantiation.

        Generic types can be instantiated with specific type parameters using
        bracket notation. Special Z notation types use special LaTeX commands.

        Examples:
        - ∅[N] -> \\emptyset[N] or special empty set notation
        - seq[N] -> \\seq N (special handling for single param)
        - P[X] -> \\power X (special handling for single param)
        - Type[A, B] -> Type[A, B]
        - ∅[N cross N] -> \\emptyset[N \\cross N]

        Strategy: Check if base is a special Z notation identifier with single
        type parameter, use LaTeX command notation. Otherwise use bracket notation.
        """
        # Special Z notation types with LaTeX commands
        special_types = {
            "seq": r"\seq",
            "seq1": r"\seq_1",
            "iseq": r"\iseq",
            "bag": r"\bag",
            "P": r"\power",
            "F": r"\finset",
        }

        # Check if base is a simple identifier with special handling
        if isinstance(node.base, Identifier):
            base_name = node.base.name
            if base_name in special_types and len(node.type_params) == 1:
                # Generic instantiation with single param: \seq N (no brackets)
                # Per fuzz manual: prefix generic symbols are operator symbols
                type_latex = special_types[base_name]
                param = node.type_params[0]
                param_latex = self.generate_expr(param)
                # Add parentheses for complex param expressions
                if isinstance(
                    param,
                    (
                        FunctionApp,
                        BinaryOp,
                        GenericInstantiation,
                        UnaryOp,
                        FunctionType,
                    ),
                ):
                    param_latex = f"({param_latex})"
                return f"{type_latex} {param_latex}"

        # Standard generic instantiation: Type[A, B, ...]
        base_latex = self.generate_expr(node.base)
        type_params_latex = ", ".join(
            self.generate_expr(param) for param in node.type_params
        )
        return f"{base_latex}[{type_params_latex}]"

    @generate_expr.register(Range)
    def _generate_range(self, node: Range, parent: Expr | None = None) -> str:
        """Generate LaTeX for range expression (m..n).

        Represents integer range expressions: m..n represents {m, m+1, ..., n}

        Examples:
        - 1..10 -> 1 \\upto 10
        - 1993..current -> 1993 \\upto current
        - x.2..x.3 -> x.2 \\upto x.3

        LaTeX rendering uses \\upto command.
        """
        start_latex = self.generate_expr(node.start)
        end_latex = self.generate_expr(node.end)
        return f"{start_latex} \\upto {end_latex}"

    @generate_expr.register(SequenceLiteral)
    def _generate_sequence_literal(
        self, node: SequenceLiteral, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for sequence literal.

        Examples:
        - ⟨⟩ -> \\langle \\rangle (empty sequence)
        - ⟨a⟩ -> \\langle a \\rangle
        - ⟨1, 2, 3⟩ -> \\langle 1, 2, 3 \\rangle
        """
        if not node.elements:
            # Empty sequence
            return r"\langle \rangle"

        # Generate comma-separated elements
        elements_latex = ", ".join(self.generate_expr(elem) for elem in node.elements)
        return f"\\langle {elements_latex} \\rangle"

    @generate_expr.register(TupleProjection)
    def _generate_tuple_projection(
        self, node: TupleProjection, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for tuple projection.

        Supports both numeric projection and named field projection.

        Examples (numeric):
        - x.1 -> x.1
        - (a, b).2 -> (a, b).2
        - f(x).3 -> f(x).3

        Examples (named fields):
        - e.name -> e.name
        - record.status -> record.status
        - person.age -> person.age

        Note: Fuzz only supports named field projection (identifiers).
        Numeric projections (.1, .2) violate fuzz grammar
        (requires Var-Name, not Number).
        """
        base_latex = self.generate_expr(node.base)

        # Add parentheses if base is a binary operator
        if isinstance(node.base, BinaryOp):
            base_latex = f"({base_latex})"

        # Generate projection suffix (works for both int and str)
        return f"{base_latex}.{node.index}"

    @generate_expr.register(BagLiteral)
    def _generate_bag_literal(
        self, node: BagLiteral, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for bag literal.

        Examples:
        - [[x]] -> \\lbag x \\rbag
        - [[1, 2, 2, 3]] -> \\lbag 1, 2, 2, 3 \\rbag

        Bags are multisets where elements can appear multiple times.
        """
        # Generate comma-separated elements
        elements_latex = ", ".join(self.generate_expr(elem) for elem in node.elements)
        return f"\\lbag {elements_latex} \\rbag"

    @generate_expr.register(Conditional)
    def _generate_conditional(
        self, node: Conditional, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for conditional expression (if/then/else).

        Examples:
        - if x > 0 then x else -x
        - if s = <> then 0 else head s

        Supports line breaks with \\\\ continuation:
        - if x > 0 \\\\
            then x \\\\
            else -x

        Fuzz mode: \\IF condition \\THEN expr1 \\ELSE expr2
        Standard LaTeX: (\\mbox{if } ... \\mbox{ then } ... \\mbox{ else } ...)
        """
        condition_latex = self.generate_expr(node.condition)
        then_latex = self.generate_expr(node.then_expr)
        else_latex = self.generate_expr(node.else_expr)

        # Build line break markers
        break_after_cond = " \\\\\n\\t1 " if node.line_break_after_condition else " "
        break_after_then = " \\\\\n\\t1 " if node.line_break_after_then else " "

        # Fuzz uses \IF \THEN \ELSE keywords
        if self.use_fuzz:
            return (
                f"\\IF {condition_latex}{break_after_cond}"
                f"\\THEN {then_latex}{break_after_then}"
                f"\\ELSE {else_latex}"
            )

        # Standard LaTeX uses mbox keywords
        return (
            f"(\\mbox{{if }} {condition_latex}{break_after_cond}"
            f"\\mbox{{ then }} {then_latex}{break_after_then}"
            f"\\mbox{{ else }} {else_latex})"
        )

    @generate_expr.register(GuardedCases)
    def _generate_guarded_cases(
        self, node: GuardedCases, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for guarded cases expression.

        Examples:
        premium_plays(<x> ^ s) =
          <x> ^ (premium_plays s) if user_status(x.2) = premium
          premium_plays s if user_status(x.2) = standard

        Rendered as multi-line with alignment and \\mbox{if} guards:
          <x> ^ (premium_plays~s) \\\\
          \\mbox{if } user_status(x.2) = premium \\\\
          premium_plays~s \\\\
          \\mbox{if } user_status(x.2) = standard
        """
        lines: list[str] = []
        for branch in node.branches:
            expr_latex = self.generate_expr(branch.expression)
            guard_latex = self.generate_expr(branch.guard)
            lines.append(f"{expr_latex} \\\\")
            lines.append(f"\\mbox{{if }} {guard_latex}")
            if branch != node.branches[-1]:  # Add line break between branches
                lines.append("\\\\")

        return "\n".join(lines)

    @generate_expr.register(GuardedBranch)
    def _generate_guarded_branch(
        self, node: GuardedBranch, parent: Expr | None = None
    ) -> str:
        """Generate LaTeX for single guarded branch.

        This is typically not called directly; GuardedCases handles the rendering.
        """
        expr_latex = self.generate_expr(node.expression)
        guard_latex = self.generate_expr(node.guard)
        return f"{expr_latex} \\mbox{{if }} {guard_latex}"

    @generate_document_item.register(Section)
    def _generate_section(self, node: Section) -> list[str]:
        """Generate LaTeX for section."""
        lines: list[str] = []
        title = self._convert_unicode_symbols(node.title)
        lines.append(r"\section*{" + title + "}")
        lines.append("")

        for item in node.items:
            item_lines = self.generate_document_item(item)
            lines.extend(item_lines)

        return lines

    @generate_document_item.register(Solution)
    def _generate_solution(self, node: Solution) -> list[str]:
        """Generate LaTeX for solution as unnumbered section."""
        lines: list[str] = []
        lines.append(r"\section*{" + node.number + "}")
        lines.append(r"\addcontentsline{toc}{section}{" + node.number + "}")
        lines.append("")

        # Track first part in solution for indentation
        self._first_part_in_solution = True
        # Use consolidation logic for items within solution
        lines.extend(self._generate_document_items_with_consolidation(node.items))
        self._first_part_in_solution = False

        return lines

    @generate_document_item.register(Part)
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
            lines.append(r"\subsection*{" + part_label + "}")
            # Add to table of contents with hyperlink (if enabled)
            if self.toc_parts:
                lines.append(r"\addcontentsline{toc}{subsection}{" + part_label + "}")
            lines.append("")

            for item in node.items:
                item_lines = self.generate_document_item(item)
                lines.extend(item_lines)

        return lines

    def _replace_outside_math(self, text: str, pattern: str, replacement: str) -> str:
        """Replace pattern with LaTeX command only when NOT inside $...$ math mode."""
        result: list[str] = []
        in_math = False
        i = 0

        while i < len(text):
            # Check for $ to toggle math mode
            if text[i] == "$":
                in_math = not in_math
                result.append("$")
                i += 1
            # Check for pattern match
            elif not in_math and text[i : i + len(pattern)] == pattern:
                result.append(f"${replacement}$")
                i += len(pattern)
            else:
                result.append(text[i])
                i += 1

        return "".join(result)

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

    def _convert_operators_bare(self, text: str) -> str:
        r"""Convert Z operators to LaTeX commands without wrapping in $...$.

        Used when content will be wrapped in math mode externally.
        Converts operators like |-> to \mapsto, <-> to \rel, etc.

        CRITICAL: Operators are processed by length (longest first) to avoid
        partial matches. For example, +-> must be replaced before ->.
        """
        # Order matters: longer operators first to avoid partial matches
        replacements = [
            # 5-character operators (process first)
            ("77->", r"\ffun"),  # Finite partial function
            # 4-character operators
            (">->>", r"\bij"),  # Bijection
            ("+->>", r"\psurj"),  # Partial surjection
            ("-->>", r"\surj"),  # Total surjection
            # 3-character operators
            ("<=>", r"\Leftrightarrow"),
            ("|>>", r"\nrres"),
            ("<<|", r"\ndres"),
            ("|->", r"\mapsto"),  # Maplet (before ->)
            ("<->", r"\rel"),
            ("-|>", r"\pinj"),
            (">+>", r"\pinj"),  # Partial injection (alt)
            (">->", r"\inj"),
            ("+->", r"\pfun"),  # Partial function (before ->)
            # 2-character operators
            ("=>", r"\Rightarrow"),
            ("<|", r"\dres"),
            ("|>", r"\rres"),
            ("->", r"\fun"),  # After +-> and |->
            ("++", r"\oplus"),
            ("o9", r"\circ"),
            ("⌢", r"\cat"),
            ("↾", r"\filter"),  # Sequence filter (Unicode)
            ("filter", r"\filter"),  # Sequence filter (ASCII)
            ("⊎", r"\uplus"),  # Bag union (Unicode)
            ("bag_union", r"\uplus"),  # Bag union (ASCII)
        ]

        result = text
        for pattern, replacement in replacements:
            result = result.replace(pattern, f" {replacement} ")

        return result

    def _convert_unicode_symbols(self, text: str) -> str:
        """Convert Unicode symbols to LaTeX equivalents.

        Used for section titles and other contexts where Unicode may appear
        but needs to be rendered as LaTeX math.
        """
        # Map of Unicode symbols to LaTeX (wrapped in $...$)
        replacements = [
            ("∈", r"$\in$"),
            ("∉", r"$\notin$"),
            ("⊂", r"$\subset$"),
            ("⊆", r"$\subseteq$"),
            ("⊃", r"$\supset$"),
            ("⊇", r"$\supseteq$"),
            ("∪", r"$\cup$"),  # noqa: RUF001
            ("∩", r"$\cap$"),
            ("∅", r"$\emptyset$"),
            ("∀", r"$\forall$"),
            ("∃", r"$\exists$"),
            ("¬", r"$\lnot$"),
            ("∧", r"$\land$"),
            ("∨", r"$\lor$"),  # noqa: RUF001
            ("⇒", r"$\Rightarrow$"),
            ("⇔", r"$\Leftrightarrow$"),
            ("⊢", r"$\vdash$"),
            ("μ", r"$\mu$"),
            ("λ", r"$\lambda$"),
            ("×", r"$\cross$"),  # noqa: RUF001
            ("ℕ", r"$\nat$"),  # noqa: RUF001
            ("ℤ", r"$\num$"),  # noqa: RUF001
            ("⌢", r"$\cat$"),
            ("≤", r"$\leq$"),
            ("≥", r"$\geq$"),
            ("≠", r"$\neq$"),
            ("→", r"$\rightarrow$"),
            ("←", r"$\leftarrow$"),
            ("↔", r"$\leftrightarrow$"),
        ]
        result = text
        for symbol, latex in replacements:
            result = result.replace(symbol, latex)
        return result

    def _process_paragraph_text(self, text: str) -> str:
        """Process paragraph text: convert operators, handle inline math, etc.

        This is a helper method that processes paragraph text without adding
        spacing or formatting commands. Used both in _generate_paragraph()
        and when rendering paragraphs inline with part labels.
        """
        # Escape special LaTeX characters FIRST
        # # is a macro parameter character
        # ^ is a superscript character (only valid in math mode)
        # Must escape before any other processing that might add LaTeX commands
        text = text.replace("#", r"\#")
        text = text.replace("^", r"\textasciicircum{}")

        # Convert sequence literals FIRST to protect <x> patterns
        # Must happen before _process_inline_math() which can break up < and >
        text = self._convert_sequence_literals(text)

        # Process inline math expressions (includes formula detection)
        text = self._process_inline_math(text)

        # Process citations: [cite key] → \citep{key}
        text = self._process_citations(text)

        # Then convert remaining symbolic operators to LaTeX math symbols
        # Only replace if NOT already wrapped in math mode
        # Do NOT convert and/or/not - those are English words in prose context
        # CRITICAL: Process by length (longest first) to avoid partial matches

        # 5-character operators (process first)
        text = self._replace_outside_math(text, "77->", r"\ffun")  # Finite pfun

        # 4-character operators
        text = self._replace_outside_math(text, ">->>", r"\bij")  # Bijection
        text = self._replace_outside_math(text, "+->>", r"\psurj")  # Partial surjection
        text = self._replace_outside_math(text, "-->>", r"\surj")  # Total surjection

        # 3-character operators (process before 2-character)
        text = self._replace_outside_math(
            text, "<=>", r"\Leftrightarrow"
        )  # Equivalence
        text = self._replace_outside_math(text, "|>>", r"\nrres")  # Range corestriction
        text = self._replace_outside_math(
            text, "<<|", r"\ndres"
        )  # Domain corestriction
        text = self._replace_outside_math(text, "|->", r"\mapsto")  # Maplet (before ->)
        text = self._replace_outside_math(text, "<->", r"\rel")  # Relation type
        text = self._replace_outside_math(text, "-|>", r"\pinj")  # Partial injection
        text = self._replace_outside_math(
            text, ">+>", r"\pinj"
        )  # Partial injection (alt)
        text = self._replace_outside_math(text, ">->", r"\inj")  # Total injection
        text = self._replace_outside_math(text, "+->", r"\pfun")  # Partial function

        # 2-character operators (process after all longer operators)
        text = self._replace_outside_math(text, "=>", r"\Rightarrow")  # Implication
        text = self._replace_outside_math(text, "<|", r"\dres")  # Domain restriction
        text = self._replace_outside_math(text, "|>", r"\rres")  # Range restriction
        text = self._replace_outside_math(
            text, "->", r"\fun"
        )  # Total function (after |->)
        text = self._replace_outside_math(text, "++", r"\oplus")  # Override
        text = self._replace_outside_math(text, "o9", r"\circ")  # Composition
        text = self._replace_outside_math(text, "⌢", r"\cat")  # Concatenation
        text = self._replace_outside_math(text, "↾", r"\filter")  # Filter (Unicode)
        # Sequence filter (ASCII)
        text = self._replace_outside_math(text, " filter ", r" \filter ")
        text = self._replace_outside_math(text, "⊎", r"\uplus")  # Bag union (Unicode)
        # Bag union (ASCII)
        text = self._replace_outside_math(text, " bag_union ", r" \uplus ")

        # Additional Unicode symbols that need conversion in TEXT blocks
        text = self._replace_outside_math(text, "∈", r"\in")  # Element of
        text = self._replace_outside_math(text, "∉", r"\notin")  # Not element of
        text = self._replace_outside_math(text, "⊂", r"\subset")  # Proper subset
        text = self._replace_outside_math(text, "⊆", r"\subseteq")  # Subset or equal
        text = self._replace_outside_math(text, "⊃", r"\supset")  # Proper superset
        text = self._replace_outside_math(text, "⊇", r"\supseteq")  # Superset or equal
        text = self._replace_outside_math(text, "∪", r"\cup")  # noqa: RUF001
        text = self._replace_outside_math(text, "∩", r"\cap")  # Intersection
        text = self._replace_outside_math(text, "∅", r"\emptyset")  # Empty set
        text = self._replace_outside_math(text, "∀", r"\forall")  # For all
        text = self._replace_outside_math(text, "∃", r"\exists")  # Exists
        text = self._replace_outside_math(text, "¬", r"\lnot")  # Negation
        text = self._replace_outside_math(text, "∧", r"\land")  # Logical and
        text = self._replace_outside_math(text, "∨", r"\lor")  # noqa: RUF001
        text = self._replace_outside_math(text, "⇒", r"\Rightarrow")  # Implies
        text = self._replace_outside_math(text, "⇔", r"\Leftrightarrow")  # Iff
        text = self._replace_outside_math(text, "⊢", r"\vdash")  # Turnstile
        text = self._replace_outside_math(text, "μ", r"\mu")  # Mu
        text = self._replace_outside_math(text, "λ", r"\lambda")  # Lambda
        text = self._replace_outside_math(text, "×", r"\cross")  # noqa: RUF001
        text = self._replace_outside_math(text, "ℕ", r"\nat")  # noqa: RUF001
        text = self._replace_outside_math(text, "ℤ", r"\num")  # noqa: RUF001
        text = self._replace_outside_math(text, "≤", r"\leq")
        text = self._replace_outside_math(text, "≥", r"\geq")
        text = self._replace_outside_math(text, "≠", r"\neq")
        text = self._replace_outside_math(text, "→", r"\rightarrow")
        text = self._replace_outside_math(text, "←", r"\leftarrow")
        text = self._replace_outside_math(text, "↔", r"\leftrightarrow")

        # Convert keywords to symbols (QA fixes)
        # Negative lookbehind (?<!\\) ensures we don't match LaTeX commands like \forall
        # These are for standalone keywords in prose, not parsed quantifier expressions
        # Order matters: exists1+ must come before exists1 to avoid partial match
        text = re.sub(r"(?<!\\)exists1\+", r"$\\exists$", text)  # exists1+ → ∃
        text = re.sub(r"(?<!\\)\bexists1\b", r"$\\exists_1$", text)  # exists1 → ∃₁
        text = re.sub(r"(?<!\\)\bexists\b", r"$\\exists$", text)  # exists → ∃
        text = re.sub(r"(?<!\\)\bemptyset\b", r"$\\emptyset$", text)  # emptyset → ∅
        text = re.sub(r"(?<!\\)\bforall\b", r"$\\forall$", text)  # forall → ∀

        # Convert "elem" and "not elem" for set membership
        # NOTE: "not elem" is English prose, not "notin" keyword
        # NOTE: Pattern for "not elem" must come before "elem" to avoid partial match
        # Pattern: expression followed by "not elem"/"elem" + capitalized set name
        # Matches: identifier/number, optionally with operators (-, +, *, /)
        # Examples: "0 elem N", "4 - 0 elem N", "x - 1 not elem N"
        # NOTE: "not in" and "in" are no longer converted after migration to elem
        text = re.sub(
            r"\b(\w+(?:\s*[\+\-\*/]\s*\w+)*)\s+not\s+elem\s+([A-Z]\w*)\b",
            r"$\1 \\notin \2$",
            text,
        )  # x - 1 not elem N → $x - 1 \notin N$
        text = re.sub(
            r"\b(\w+(?:\s*[\+\-\*/]\s*\w+)*)\s+elem\s+([A-Z]\w*)\b",
            r"$\1 \\in \2$",
            text,
        )  # 4 - 0 elem N → $4 - 0 \in N$

        # Convert bare comparison operators (garbled character fix - final pass)
        # Catches cases not handled by _process_inline_math() (complex expressions)
        # Tracks math mode to avoid nested $...$
        text = self._convert_comparison_operators(text)

        # Escape underscores outside math mode (final pass)
        # Prevents LaTeX errors when identifiers like count_N appear in prose
        return self._escape_underscores_outside_math(text)

    @generate_document_item.register(Paragraph)
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

    @generate_document_item.register(PureParagraph)
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

    @generate_document_item.register(LatexBlock)
    def _generate_latex_block(self, node: LatexBlock) -> list[str]:
        """Generate LaTeX for raw LaTeX passthrough block.

        LATEX: blocks output raw LaTeX with NO escaping.
        The LaTeX is passed directly through to the output.
        """
        lines: list[str] = []
        lines.append(node.latex)  # Raw LaTeX, no processing
        lines.append("")
        return lines

    @generate_document_item.register(PageBreak)
    def _generate_pagebreak(self, node: PageBreak) -> list[str]:
        """Generate LaTeX for page break.

        PAGEBREAK: inserts a page break in PDF output.
        """
        return [r"\newpage", ""]

    @generate_document_item.register(Contents)
    def _generate_contents(self, node: Contents) -> list[str]:
        """Generate LaTeX for table of contents.

        CONTENTS: generates \tableofcontents (sections only, depth 1)
        CONTENTS: full generates \tableofcontents with depth 2 (sections + subsections)
        CONTENTS: 2 also generates \tableofcontents with depth 2
        """
        lines: list[str] = []
        # Determine depth: empty = 1 (sections only)
        # "full" or "2" = 2 (sections + subsections)
        if node.depth.lower() in ("full", "2"):
            lines.append(r"\setcounter{tocdepth}{2}")
        else:
            lines.append(r"\setcounter{tocdepth}{1}")
        lines.append(r"\tableofcontents")
        lines.append("")
        return lines

    @generate_document_item.register(PartsFormat)
    def _generate_parts_format(self, node: PartsFormat) -> list[str]:
        """Generate LaTeX for parts format directive.

        PartsFormat directive is already applied at document level during parsing,
        so we return empty list here (no LaTeX output needed).
        """
        return []

    def _convert_comparison_operators(self, text: str) -> str:
        """Convert bare comparison operators to math mode, avoiding nested math.

        Handles: >=, <=, >, <, | (pipe)
        Only converts when NOT inside existing $...$ math mode.
        """
        result: list[str] = []
        i = 0
        in_math = False  # Track if we're inside $...$ math mode

        while i < len(text):
            # Check for $ to track math mode transitions
            if text[i] == "$":
                in_math = not in_math
                result.append(text[i])
                i += 1
                continue

            # Only try conversions if NOT in math mode
            if not in_math:
                # Try >= first (multi-char before single-char)
                if i + 1 < len(text) and text[i : i + 2] == ">=":
                    result.append(r"$\geq$")
                    i += 2
                    continue
                # Try <=
                if i + 1 < len(text) and text[i : i + 2] == "<=":
                    result.append(r"$\leq$")
                    i += 2
                    continue
                # Try > (only with surrounding spaces)
                if (
                    text[i] == ">"
                    and (i == 0 or text[i - 1].isspace())
                    and (i + 1 >= len(text) or text[i + 1].isspace())
                ):
                    result.append(r"$>$")
                    i += 1
                    continue
                # Try < (only with surrounding spaces or end of string)
                # Special case: also convert at end like "then <x>"
                if (
                    text[i] == "<"
                    and (i == 0 or text[i - 1].isspace())
                    and (i + 1 >= len(text) or text[i + 1].isspace())
                ):
                    result.append(r"$<$")
                    i += 1
                    continue
                # Try | (pipe/bullet - causes garbled output in text mode)
                # Only convert if preceded by space or $ (end of math mode)
                # and followed by space/newline/end
                if text[i] == "|":
                    prev_ok = i == 0 or text[i - 1].isspace() or text[i - 1] == "$"
                    next_ok = (
                        i + 1 >= len(text)
                        or text[i + 1].isspace()
                        or text[i + 1] == "\n"
                    )
                    if prev_ok and next_ok:
                        result.append(r"$\mid$")
                        i += 1
                        continue

            # No match, copy character as-is
            result.append(text[i])
            i += 1

        return "".join(result)

    def _convert_sequence_literals(self, text: str, *, wrap_math: bool = True) -> str:
        """Convert sequence literals <...> to math mode \\langle ... \\rangle.

        Handles patterns like:
        - <> → $\\langle \\rangle$
        - <a> → $\\langle a \\rangle$
        - <x, y> → $\\langle x, y \\rangle$
        - <1, 2, 3> → $\\langle 1, 2, 3 \\rangle$
        - <<x, y>, <>> → $\\langle \\langle x, y \\rangle, \\langle \\rangle \\rangle$

        Uses balanced bracket matching to handle nested sequences correctly.
        Must NOT match operators like <=> or <-> or comparison operators.

        Args:
            text: Text containing sequence literals
            wrap_math: If True, wrap results in $...$. False for recursive calls.
        """
        # Keep processing until no more angle brackets remain
        # This handles cases where parsing fails and we need multiple passes
        result = text
        max_iterations = 10  # Prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            # Find all balanced angle bracket pairs (handles nesting)
            all_matches = self._find_balanced_angles(result)

            if not all_matches:
                # No more sequences to convert
                break

            # Filter to find only outermost, non-overlapping matches
            # A match is outermost if it's not contained within any other match
            def is_contained(match: tuple[int, int], other: tuple[int, int]) -> bool:
                """Check if match is strictly contained within other."""
                return (
                    other[0] < match[0] < other[1] or other[0] < match[1] < other[1]
                ) and match != other

            outermost_matches = [
                m
                for m in all_matches
                if not any(is_contained(m, other) for other in all_matches)
            ]

            # Sort by start position (descending) to process rightmost first
            # This preserves positions during replacement
            matches_sorted = sorted(outermost_matches, key=lambda m: m[0], reverse=True)

            # Process matches from right to left
            for start_pos, end_pos in matches_sorted:
                sequence_text = result[start_pos:end_pos]

                # Sanity check: should still start/end with angle brackets
                if not sequence_text.startswith("<") or not sequence_text.endswith(">"):
                    continue

                content = sequence_text[1:-1]  # Strip < and >

                # Try to parse the ORIGINAL content (not converted)
                # The parser will handle nested sequences correctly
                # Try to parse and generate LaTeX for sequence content
                parsed_successfully = False
                latex = ""  # Will be set by either branch
                try:
                    lexer = Lexer(content)
                    tokens = lexer.tokenize()
                    parser = Parser(tokens)
                    ast = parser.parse()

                    # Generate LaTeX for the sequence content
                    # Note: parser.parse() returns Document | Expr
                    if isinstance(ast, Expr):
                        # Successfully parsed as expression
                        if content.strip() == "":
                            latex = r"\langle \rangle"
                        else:
                            latex_content = self.generate_expr(ast)
                            latex = rf"\langle {latex_content} \rangle"
                        parsed_successfully = True
                except (LexerError, ParserError):
                    # Parsing failed - will use fallback below
                    pass

                if not parsed_successfully:
                    # Fallback: convert operators without full parsing
                    if not content.strip():
                        latex = r"\langle \rangle"
                    else:
                        content_with_ops = self._convert_operators_bare(content)
                        latex = rf"\langle {content_with_ops} \rangle"

                # Wrap in math mode only on first iteration (outermost sequences)
                if wrap_math and iteration == 0:
                    result = result[:start_pos] + f"${latex}$" + result[end_pos:]
                else:
                    result = result[:start_pos] + latex + result[end_pos:]

            iteration += 1

        return result

    def _find_balanced_braces(self, text: str) -> list[tuple[int, int]]:
        """Find all balanced brace pairs in text.

        Returns list of (start_pos, end_pos) tuples for each balanced {...}.
        Handles nested braces correctly.
        """
        matches: list[tuple[int, int]] = []
        i = 0
        while i < len(text):
            if text[i] == "{":
                # Found opening brace, find matching closing brace
                depth = 1
                start = i
                i += 1
                while i < len(text) and depth > 0:
                    if text[i] == "{":
                        depth += 1
                    elif text[i] == "}":
                        depth -= 1
                    i += 1
                if depth == 0:
                    # Found balanced pair
                    matches.append((start, i))
            else:
                i += 1
        return matches

    def _find_balanced_parens(self, text: str) -> list[tuple[int, int]]:
        """Find all balanced parenthesis pairs in text.

        Returns list of (start_pos, end_pos) tuples for each balanced (...).
        Handles nested parentheses correctly.
        """
        matches: list[tuple[int, int]] = []
        i = 0
        while i < len(text):
            if text[i] == "(":
                # Found opening paren, find matching closing paren
                depth = 1
                start = i
                i += 1
                while i < len(text) and depth > 0:
                    if text[i] == "(":
                        depth += 1
                    elif text[i] == ")":
                        depth -= 1
                    i += 1
                if depth == 0:
                    # Found balanced pair
                    matches.append((start, i))
            else:
                i += 1
        return matches

    def _find_balanced_angles(self, text: str) -> list[tuple[int, int]]:
        """Find all balanced angle bracket pairs in text for sequences.

        Returns list of (start_pos, end_pos) tuples for each balanced <...>.
        Handles nested angle brackets correctly by finding ALL pairs, including nested.

        Distinguishes sequences from operators:
        - Sequences: <>, <x>, <a, b>, <<x>, <y>>
        - Operators: <=>, <->, <|, |>, <<|, |>>

        Strategy: For each opening <, find its matching >, record the pair,
        then continue searching from just after the opening < to find nested pairs.
        """
        matches: list[tuple[int, int]] = []
        i = 0
        while i < len(text):
            if text[i] == "<":
                # Check if this is part of an operator
                if i + 1 < len(text):
                    next_char = text[i + 1]
                    # Skip operators: <=>, <->, <|, <<|
                    if next_char in "=-|":
                        i += 1
                        continue

                # Found opening angle, find matching closing angle
                depth = 1
                start = i
                j = i + 1
                while j < len(text) and depth > 0:
                    if text[j] == "<":
                        # Check if operator start
                        if j + 1 < len(text) and text[j + 1] in "=-|":
                            j += 2  # Skip operator
                            continue
                        depth += 1
                    elif text[j] == ">":
                        # Check if operator end (=>, ->, |>, |>>)
                        if j > 0 and text[j - 1] in "=-|":
                            j += 1
                            continue
                        depth -= 1
                    j += 1
                if depth == 0:
                    # Found balanced pair
                    matches.append((start, j))
                # Continue from next position to find nested/adjacent pairs
                i += 1
            else:
                i += 1
        return matches

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

    # -------------------------------------------------------------------------
    # Inline Math Pipeline Stages
    # -------------------------------------------------------------------------
    # These methods form a pipeline that transforms prose text by detecting
    # mathematical expressions and wrapping them in $...$ for LaTeX.
    # Order matters: earlier stages must run before later ones.
    # -------------------------------------------------------------------------

    def _process_manual_markup(self, text: str) -> str:
        """Stage -1.5: Convert bracketed operator markup to LaTeX symbols.

        Converts explicit markup like [and], [or], [not] to LaTeX symbols.
        Must run first before any expression parsing.

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

    def _process_logical_formulas(self, text: str) -> str:
        """Stage -1: Detect logical formulas with =>, <=>, lnot, land, lor.

        Matches expressions like "p => (lnot p => p)" and wraps in math mode.
        Stops at sentence boundaries (is, as, are, etc.) or punctuation.
        Only LaTeX-style keywords (lnot, land, lor), not English.
        """
        result = text
        formula_pattern = (
            r"(\()?(?:lnot\s+)?([a-zA-Z]\w*)\s*(=>|<=>)\s*[^.!?]*?"
            r"(?=\s+(?:is|as|are|for|to|be|a|an|the|in|on|at|by|with|"
            r"holds|means|implies|shows|proves|states|says|gives|follows|"
            r"so|then|therefore|hence|thus|because|since|when|where|which|that)\b|[.!?]|$)"
        )

        matches = list(re.finditer(formula_pattern, result))
        for match in reversed(matches):
            start_pos = match.start()
            end_pos = match.end()

            # Check if already in math mode
            before = result[:start_pos]
            dollars_before = before.count("$")
            if dollars_before % 2 == 1:
                continue

            formula_text = result[start_pos:end_pos].strip()

            # Try to parse as logical expression
            try:
                lexer = Lexer(formula_text)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()

                if isinstance(ast, Expr):
                    math_latex = self.generate_expr(ast)
                    result = result[:start_pos] + f"${math_latex}$" + result[end_pos:]
            except (LexerError, ParserError):
                # Parsing failed - expression is not valid math, leave as prose
                pass

        return result

    def _process_parenthesized_logic(self, text: str) -> str:
        """Stage -0.5: Detect parenthesized logical expressions.

        Matches balanced parentheses containing logical operators like
        (p lor q), (p land q), ((p => r) land ...).
        Also handles (lnot p => lnot q) which Pattern -1 misses.
        Only LaTeX-style keywords (lnot, land, lor), not English.
        """
        result = text
        paren_matches = self._find_balanced_parens(result)

        for start_pos, end_pos in reversed(paren_matches):
            # Check if already in math mode
            before = result[:start_pos]
            dollars_before = before.count("$")
            if dollars_before % 2 == 1:
                continue

            paren_text = result[start_pos:end_pos]

            # Only process if it contains logical operators or keywords
            # Look for: lor, land, lnot, elem, =>, <=>
            has_logic = bool(
                re.search(r"\blor\b", paren_text)
                or re.search(r"\bland\b", paren_text)
                or re.search(r"\blnot\b", paren_text)
                or re.search(r"\belem\b", paren_text)
                or "=>" in paren_text
                or "<=>" in paren_text
            )

            if not has_logic:
                continue

            # Try to parse as logical expression
            try:
                lexer = Lexer(paren_text)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()

                if isinstance(ast, Expr):
                    math_latex = self.generate_expr(ast)
                    result = result[:start_pos] + f"${math_latex}$" + result[end_pos:]
            except (LexerError, ParserError):
                # Parsing failed - expression is not valid math, leave as prose
                pass

        return result

    def _process_standalone_keywords(self, text: str) -> str:
        """Stage -0.3: Convert standalone logical keywords to symbols.

        Converts lor, land, lnot, elem to their LaTeX equivalents.
        These should ALWAYS render as symbols, never as literal text.
        Special case: lnot followed by single variable (lnot p) -> $\\lnot p$
        """
        result = text

        # First, handle "lnot <variable>" as a unit
        lnot_var_pattern = r"\blnot\s+([a-zA-Z])\b"
        matches = list(re.finditer(lnot_var_pattern, result))
        for match in reversed(matches):
            start_pos = match.start()
            end_pos = match.end()

            # Check if already in math mode
            before = result[:start_pos]
            dollars_before = before.count("$")
            if dollars_before % 2 == 1:
                continue  # Already in math mode

            var_name = match.group(1)
            result = result[:start_pos] + f"$\\lnot {var_name}$" + result[end_pos:]

        # Then handle other standalone keywords
        standalone_keywords = {
            r"\blor\b": "$\\lor$",
            r"\bland\b": "$\\land$",
            r"\blnot\b": "$\\lnot$",  # Only matches lnot NOT followed by variable
            r"\belem\b": "$\\in$",
        }

        for pattern, replacement in standalone_keywords.items():
            # Find all matches and replace from right to left (to preserve positions)
            matches = list(re.finditer(pattern, result))
            for match in reversed(matches):
                start_pos = match.start()
                end_pos = match.end()

                # Check if already in math mode
                before = result[:start_pos]
                dollars_before = before.count("$")
                if dollars_before % 2 == 1:
                    continue  # Already in math mode

                # Replace with math mode wrapped keyword
                result = result[:start_pos] + replacement + result[end_pos:]

        return result

    def _process_superscripts(self, text: str) -> str:
        """Stage 0: Wrap standalone superscripts in math mode.

        Matches patterns like x^2, a_i^2, 2^n, x^{2n}.
        Skips sequence concatenation (<x> ^ <y>).
        """
        result = text
        superscript_pattern = r"(\w+_?\w*)\^(\{[^}]+\}|\w+)"

        matches = list(re.finditer(superscript_pattern, result))
        for match in reversed(matches):
            start_pos = match.start()
            end_pos = match.end()

            # Check if already in math mode
            before = result[:start_pos]
            dollars_before = before.count("$")
            if dollars_before % 2 == 1:
                continue  # Already in math mode

            # Check if this looks like sequence concatenation (<x> ^ <y>)
            # Look for closing > before the ^
            context_before = result[max(0, start_pos - 10) : start_pos]
            if ">" in context_before and context_before.rstrip().endswith(">"):
                continue  # This is sequence concatenation, skip

            expr = match.group(0)
            # Wrap in math mode: x^2 -> $x^{2}$
            result = result[:start_pos] + f"${expr}$" + result[end_pos:]

        return result

    def _process_relational_image(self, text: str) -> str:
        """Stage 0.5: Detect relational image notation R(| S |).

        Matches patterns:
        1. identifier(| ... |) - simple relation like R(| S |)
        2. (expr)(| ... |) - composition like (R o9 S)(| A |)
        3. standalone (| ... |) - describing the notation in prose
        """
        result = text
        relimg_pattern = r"(?:(\([^)]+\)|[a-zA-Z_]\w*)\s*)?\(\|[^$]*?\|\)"

        matches = list(re.finditer(relimg_pattern, result))
        for match in reversed(matches):
            start_pos = match.start()
            end_pos = match.end()

            # Check if already in math mode
            before = result[:start_pos]
            dollars_before = before.count("$")
            if dollars_before % 2 == 1:
                continue  # Already in math mode

            math_text = match.group(0)

            # Skip if identifier is a common prose word
            first_token = math_text.split("(|")[0].strip()
            if first_token.lower() in {
                "the",
                "a",
                "an",
                "this",
                "that",
                "image",
                "relation",
                "set",
                "function",
                "gives",
                "returns",
                "where",
                "when",
                "which",
            }:
                continue

            # Special case: standalone (| ... |) with ellipsis for describing notation
            if "(| ... |)" in math_text or "(| |)" in math_text:
                # Replace with LaTeX notation
                math_latex = math_text.replace(
                    "(| ... |)", r"$\limg \ldots \rimg$"
                ).replace("(| |)", r"$\limg \rimg$")
                result = result[:start_pos] + math_latex + result[end_pos:]
                continue

            # Try to parse as expression
            try:
                lexer = Lexer(math_text)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()

                # Check if we got a valid expression
                if isinstance(ast, Expr):
                    # Generate LaTeX
                    math_latex = self.generate_expr(ast)
                    result = result[:start_pos] + f"${math_latex}$" + result[end_pos:]
            except (LexerError, ParserError):
                # Parsing failed - expression is not valid math, leave as prose
                pass

        return result

    def _process_set_expressions(self, text: str) -> str:
        """Stage 1: Detect set expressions { ... }.

        Matches balanced braces and parses as set comprehensions or literals.
        Handles nested braces correctly.
        """
        result = text
        brace_matches = self._find_balanced_braces(result)

        # Process matches in reverse order to preserve positions
        for start_pos, end_pos in reversed(brace_matches):
            math_text = result[start_pos:end_pos]
            try:
                # Try to parse as math expression
                lexer = Lexer(math_text)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()

                # Check if it's a set expression (comprehension or literal)
                if isinstance(ast, (SetComprehension, SetLiteral)):
                    # Generate LaTeX for the expression
                    math_latex = self.generate_expr(ast)
                    # Wrap in $...$
                    result = result[:start_pos] + f"${math_latex}$" + result[end_pos:]
            except (LexerError, ParserError):
                # Parsing failed - expression is not valid math, leave as prose
                pass

        return result

    def _process_quantifiers(self, text: str) -> str:
        """Stage 2: Detect quantifier expressions.

        Matches forall, exists, exists1, mu with their predicates.
        Strategy: Find keyword, then try parsing increasingly longer substrings.
        """
        result = text
        quant_keywords = ["forall", "exists", "exists1", "mu"]
        for keyword in quant_keywords:
            # Find all occurrences of quantifier keywords
            pattern = rf"\b{keyword}\b"
            matches = list(re.finditer(pattern, result))

            # Process matches in reverse order to preserve positions
            for match in reversed(matches):
                start_pos = match.start()

                # Try to parse increasingly longer substrings from this point
                # Stop at sentence boundaries or when parsing fails
                for end_offset in range(
                    len(result) - start_pos, 0, -1
                ):  # Try longest first
                    end_pos = start_pos + end_offset
                    # Don't go past sentence boundaries
                    if any(
                        result[start_pos:end_pos].count(boundary) > 0
                        for boundary in [". ", "! ", "? "]
                    ):
                        # Found a sentence boundary - try up to that point
                        for boundary in [". ", "! ", "? "]:
                            if boundary in result[start_pos:end_pos]:
                                end_pos = start_pos + result[start_pos:end_pos].index(
                                    boundary
                                )
                                break

                    math_text = result[start_pos:end_pos].strip()

                    # Must contain a pipe for quantifier syntax
                    if "|" not in math_text:
                        continue

                    try:
                        # Try to parse as quantifier
                        lexer = Lexer(math_text)
                        tokens = lexer.tokenize()
                        parser = Parser(tokens)
                        ast = parser.parse()

                        if isinstance(ast, Quantifier):
                            # Check if parsed expression contains prose words
                            # (due to space-separated application)
                            prose_words = {
                                "is",
                                "are",
                                "be",
                                "was",
                                "were",
                                "true",
                                "false",
                                "the",
                                "a",
                                "an",
                                "in",
                                "on",
                                "at",
                                "to",
                                "of",
                                "for",
                                "with",
                                "as",
                                "by",
                                "from",
                                "that",
                                "syntax",
                                "valid",
                                "here",
                                "there",
                            }

                            # Check if math_text ends with any prose words
                            # Split and check last few tokens
                            text_words = math_text.lower().split()
                            if text_words and text_words[-1] in prose_words:
                                # Contains prose word - try shorter substring
                                continue
                            if len(text_words) >= 2 and text_words[-2] in prose_words:
                                # Second-to-last word is prose - try shorter
                                continue

                            # Check if we're cutting off a word ("is" -> "i" + "s")
                            if end_pos < len(result) and end_pos > 0:
                                prev_char = result[end_pos - 1]
                                next_char = result[end_pos]
                                # If both sides are alphanumeric, splitting a word
                                if prev_char.isalnum() and next_char.isalnum():
                                    # We're in the middle of a word - skip this
                                    continue

                            # Successfully parsed! Generate LaTeX
                            math_latex = self.generate_expr(ast)
                            # Wrap in $...$
                            result = (
                                result[:start_pos]
                                + f"${math_latex}$"
                                + result[end_pos:]
                            )
                            break  # Move to next match
                    except (LexerError, ParserError):
                        # This substring doesn't parse - try shorter one
                        continue

        return result

    def _process_type_declarations(self, text: str) -> str:
        """Stage 2.5: Detect type declarations (identifier : type).

        Matches patterns like "x : N" or "f : A -> B".
        Stops at commas, periods, or common prose words.
        """
        result = text

        # Build pattern: identifier : type_expr
        # Type expr stops at prose words using negative lookahead
        prose_pattern = (
            r"(?:where|and|or|but|if|then|else|shadows|gives|returns|which|that|"
            r"is|are|was|were|be|been|have|has|had|the|a|an|this)"
        )
        neg_lookahead = r"(?!" + prose_pattern + r"\b)"
        type_word = r"[a-zA-Z_][^\s,]*"
        type_continuation = r"(?:\s+" + neg_lookahead + type_word + r")*"
        type_expr_part = r"(" + type_word + type_continuation + r")"
        type_decl_pattern = r"\b([a-zA-Z_]\w*)\s*:\s*" + type_expr_part

        # Words that appear BEFORE colons in prose (not type declarations)
        prose_intro_words = {
            "proof",
            "theorem",
            "induction",
            "example",
            "note",
            "strategy",
            "hint",
            "warning",
            "remark",
            "observation",
            "claim",
            "lemma",
            "corollary",
            "definition",
            "assumption",
            "goal",
            "objective",
            "result",
            "conclusion",
            "summary",
            "overview",
            "introduction",
            "background",
            "context",
            "constructive",
            "non",
            "strong",
            "main",
            "base",
        }

        matches = list(re.finditer(type_decl_pattern, result))
        for match in reversed(matches):
            start_pos = match.start()
            end_pos = match.end()

            # Check if already in math mode
            before = result[:start_pos]
            dollars_before = before.count("$")
            if dollars_before % 2 == 1:
                continue  # Already in math mode

            # Extract the identifier (word before colon)
            identifier = match.group(1).lower()

            # Skip if identifier is a prose intro word (like "proof:", "theorem:")
            if identifier in prose_intro_words:
                continue

            # Extract the matched expression
            expr = match.group(0)

            # Try to parse as a type declaration
            try:
                lexer = Lexer(expr)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()

                # If it parses successfully, generate LaTeX
                if isinstance(ast, Expr):
                    math_latex = self.generate_expr(ast)
                    result = result[:start_pos] + f"${math_latex}$" + result[end_pos:]
            except (LexerError, ParserError):
                # Parsing failed - check if this looks like prose (not math)
                # Common English words that appear in prose but not in math
                expr_words = set(expr.lower().split())
                if expr_words & PROSE_WORDS:
                    # Contains prose words - skip this match
                    continue

                # If parsing fails, manually process the identifier and operators
                # Extract identifier from "identifier : type_expr" pattern
                match_parts = re.match(r"([a-zA-Z_]\w*)\s*:\s*(.+)", expr)
                if match_parts:
                    identifier_name = match_parts.group(1)
                    type_part = match_parts.group(2)

                    # Process identifier through normal logic for underscore handling
                    id_node = Identifier(line=0, column=0, name=identifier_name)
                    identifier_latex = self._generate_identifier(id_node)

                    # Convert operators in type part (use comprehensive converter)
                    type_latex = self._convert_operators_bare(type_part)

                    # Combine
                    full_latex = f"{identifier_latex} : {type_latex}"
                    result = result[:start_pos] + f"${full_latex}$" + result[end_pos:]
                else:
                    # Fallback: just convert operators
                    expr_with_ops = self._convert_operators_bare(expr)
                    result = (
                        result[:start_pos] + f"${expr_with_ops}$" + result[end_pos:]
                    )

        return result

    def _process_function_applications(self, text: str) -> str:
        """Stage 2.75: Detect function application followed by operator.

        Matches patterns like "f_name x <= 5".
        ONLY matches identifiers with underscores to avoid false positives.
        """
        result = text
        math_op_pattern = r"(77->|\+->|-\|>|<-\||->|>->|>->>|<=>|=>|>=|<=|!=|>|<|=)"
        func_app_pattern = (
            r"\b([a-zA-Z_]\w*_\w+)\s+"  # Function name (must contain underscore)
            r"([a-zA-Z_]\w*)\s*"  # Argument
            + math_op_pattern  # Operator
            + r"\s*([a-zA-Z_0-9]\w*)"  # Value
        )

        matches = list(re.finditer(func_app_pattern, result))
        for match in reversed(matches):
            start_pos = match.start()
            end_pos = match.end()

            # Check if already in math mode
            before = result[:start_pos]
            dollars_before = before.count("$")
            if dollars_before % 2 == 1:
                continue  # Already in math mode

            expr = match.group(0)

            # Try to parse the full expression
            try:
                lexer = Lexer(expr)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()

                if isinstance(ast, Expr):
                    math_latex = self.generate_expr(ast)
                    result = result[:start_pos] + f"${math_latex}$" + result[end_pos:]
            except (LexerError, ParserError):
                # Parsing failed - manually process components
                # Extract: func_name arg operator value
                parts = expr.split()
                if len(parts) >= 3:
                    func_name = parts[0]
                    arg_name = parts[1]
                    op_and_value = " ".join(parts[2:])

                    # Process function identifier
                    func_node = Identifier(line=0, column=0, name=func_name)
                    func_latex = self._generate_identifier(func_node)

                    # Process argument identifier
                    arg_node = Identifier(line=0, column=0, name=arg_name)
                    arg_latex = self._generate_identifier(arg_node)

                    # Convert operators in rest
                    op_and_value_latex = op_and_value.replace("<=", r"\leq")
                    op_and_value_latex = op_and_value_latex.replace(">=", r"\geq")
                    op_and_value_latex = op_and_value_latex.replace("!=", r"\neq")

                    # Combine as function application
                    full_latex = f"{func_latex}({arg_latex}) {op_and_value_latex}"
                    result = result[:start_pos] + f"${full_latex}$" + result[end_pos:]

        return result

    def _process_simple_expressions(self, text: str) -> str:
        """Stage 3: Detect simple inline math expressions.

        Matches expressions with operators like x > 1, f +-> g.
        Strategy: Match sequences of identifiers/numbers connected by operators.
        """
        result = text

        # All operators that need math mode
        math_op_pattern = r"(77->|\+->|-\|>|<-\||->|>->|>->>|<=>|=>|>=|<=|!=|>|<|=)"

        # Operand pattern: identifier OR decimal number
        # This ensures "5.5" stays together as a decimal, not split at the period
        operand = r"(?:[a-zA-Z_]\w*|\d+(?:\.\d+)?)"

        # Pattern: identifier/number, followed by (operator identifier/number)+
        # This matches chains like "p <=> x > 1" and "x = 5.5"
        full_pattern = (
            r"\b"
            + operand
            + r"\s*"  # First identifier/number
            + math_op_pattern  # Operator
            + r"\s*"
            + operand  # Second operand
            + r"(?:\s*"
            + math_op_pattern
            + r"\s*"
            + operand
            + r")*"  # More ops
        )

        matches = list(re.finditer(full_pattern, result))

        # Process matches in reverse order to preserve positions
        for match in reversed(matches):
            # Check if already in math mode (look for $ before)
            start_pos = match.start()
            end_pos = match.end()

            # Look backwards for $
            before = result[:start_pos]

            # Count $ symbols before this position
            dollars_before = before.count("$")
            # If odd number of $, we're already in math mode
            if dollars_before % 2 == 1:
                continue

            # Extract the matched expression
            expr = match.group(0)

            # Convert the operator to LaTeX
            try:
                # Try to parse and generate proper LaTeX
                lexer = Lexer(expr)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()

                # Generate LaTeX for the expression if it's an Expr
                if isinstance(ast, Expr):
                    math_latex = self.generate_expr(ast)
                    # Wrap in $...$
                    result = result[:start_pos] + f"${math_latex}$" + result[end_pos:]
            except (LexerError, ParserError):
                # Parsing failed - wrap expression as-is
                result = result[:start_pos] + f"${expr}$" + result[end_pos:]

        return result

    def _process_inline_math(self, text: str) -> str:
        """Process inline math expressions in text via pipeline stages.

        Detects patterns like:
        - Superscripts: x^2, a_i^2, 2^n (wrap in math mode)
        - Set comprehensions: { x : N | x > 0 }
        - Set comprehensions with nested braces: {p : P . p |-> {p}}
        - Quantifiers: forall x : N | predicate

        Parses them and converts to $...$ wrapped LaTeX.

        Pipeline stages (order matters):
        1. Manual markup: [operator] -> LaTeX symbols
        2. Logical formulas: p => q, p <=> q
        3. Parenthesized logic: (p lor q)
        4. Standalone keywords: lor, land, lnot, elem
        5. Superscripts: x^2
        6. Relational image: R(| S |)
        7. Set expressions: { ... }
        8. Quantifiers: forall, exists, exists1, mu
        9. Type declarations: x : T
        10. Function application: f x > y
        11. Simple expressions: x > 1
        """
        result = text
        result = self._process_manual_markup(result)
        result = self._process_logical_formulas(result)
        result = self._process_parenthesized_logic(result)
        result = self._process_standalone_keywords(result)
        result = self._process_superscripts(result)
        result = self._process_relational_image(result)
        result = self._process_set_expressions(result)
        result = self._process_quantifiers(result)
        result = self._process_type_declarations(result)
        result = self._process_function_applications(result)
        return self._process_simple_expressions(result)

    @generate_document_item.register(TruthTable)
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

    def _convert_operators_to_latex(self, text: str) -> str:
        """Convert operator keywords to LaTeX symbols in text."""
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

    def _escape_justification(self, text: str) -> str:
        """Escape operators in justification text for LaTeX.

        CRITICAL: Operators must be replaced in order of length (longest first)
        to avoid partial matches. For example, |-> must be replaced before ->
        otherwise -> gets replaced first, leaving | and causing incorrect output.

        Also handles sequences like <> and <a, b, c> which must be processed
        BEFORE other operators containing < or >.
        """
        result = text

        # Handle sequences FIRST (before operators containing < or >)
        # Match sequences: < followed by anything except < or >, then >
        # This handles both <> (empty) and <a, b, c> (non-empty)
        result = re.sub(r"<\s*>", r"$\\langle \\rangle$", result)  # Empty sequence
        result = re.sub(r"<([^<>]+)>", r"$\\langle \1 \\rangle$", result)  # Non-empty

        # 5-character operators (process first)
        result = result.replace("77->", r"$\ffun$")  # Finite partial function

        # 4-character operators
        result = result.replace(">->>", r"$\bij$")  # Bijection
        result = result.replace("+->>", r"$\psurj$")  # Partial surjection
        result = result.replace("-->>", r"$\surj$")  # Total surjection

        # 3-character operators (process before 2-character)
        result = result.replace("<=>", r"$\Leftrightarrow$")  # Logical equivalence
        result = result.replace("<<|", r"$\ndres$")  # Domain corestriction
        result = result.replace("|>>", r"$\nrres$")  # Range corestriction
        result = result.replace("|->", r"$\mapsto$")  # Maplet (MUST be before ->)
        result = result.replace("<->", r"$\rel$")  # Relation type
        result = result.replace(">+>", r"$\pinj$")  # Partial injection
        result = result.replace("-|>", r"$\pinj$")  # Partial injection (alt)
        result = result.replace(">->", r"$\inj$")  # Total injection
        result = result.replace("+->", r"$\pfun$")  # Partial function

        # 2-character operators (process after all longer operators)
        result = result.replace("=>", r"$\Rightarrow$")  # Logical implication
        result = result.replace("<|", r"$\dres$")  # Domain restriction
        result = result.replace("|>", r"$\rres$")  # Range restriction
        result = result.replace("->", r"$\fun$")  # Total function (AFTER |-> and +->)
        result = result.replace("++", r"$\oplus$")  # Override
        result = result.replace("o9", r"$\circ$")  # Composition

        # Single-character operators
        result = result.replace("^", r"$\cat$")  # Sequence concatenation

        # Word-based operators (use word boundaries to avoid partial matches)
        # After migration: only LaTeX-style keywords are converted (not English)
        result = re.sub(r"\bland\b", r"$\\land$", result)
        result = re.sub(r"\blor\b", r"$\\lor$", result)
        result = re.sub(r"\blnot\b", r"$\\lnot$", result)
        result = re.sub(r"\belem\b", r"$\\in$", result)  # Set membership
        result = re.sub(r"\bdom\b", r"$\\dom$", result)
        result = re.sub(r"\bran\b", r"$\\ran$", result)
        result = re.sub(r"\bcomp\b", r"$\\comp$", result)
        result = re.sub(r"\binv\b", r"$\\inv$", result)
        result = re.sub(r"\bid\b", r"$\\id$", result)

        # Convert Z notation keywords to symbols (QA fixes)
        # Order matters: exists1+ before exists1 to avoid partial match
        result = re.sub(r"(?<!\\)exists1\+", r"$\\exists$", result)  # exists1+ → ∃
        result = re.sub(r"(?<!\\)\bexists1\b", r"$\\exists_1$", result)  # exists1 → ∃₁
        result = re.sub(r"(?<!\\)\bexists\b", r"$\\exists$", result)  # exists → ∃
        result = re.sub(r"(?<!\\)\bemptyset\b", r"$\\emptyset$", result)  # emptyset → ∅
        result = re.sub(r"(?<!\\)\bforall\b", r"$\\forall$", result)  # forall → ∀

        # Escape underscores in identifiers for prose rendering (not subscripts)
        # Must happen AFTER all operator replacements to avoid interfering
        # Pattern: word characters around underscore, not already in math mode
        # This handles cases like count_N, total_S in justification text
        # Escapes as count\_N (prose) not $count_N$ (subscript)
        return re.sub(
            r"(?<!\$)(\w+_\w+)(?!\$)", lambda m: m.group(1).replace("_", r"\_"), result
        )

    @generate_document_item.register(ArgueChain)
    def _generate_argue_chain(self, node: ArgueChain) -> list[str]:
        r"""Generate LaTeX for equivalence chain using array environment.

        Both EQUIV: and ARGUE: keywords generate this output (EQUIV is alias).
        Uses standard LaTeX array instead of argue environment for better control.
        Wraps array in display math \[...\] for proper spacing. Centers the block
        and right-aligns justifications. Auto-scales if wider than page.
        """
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

        # Wrap in adjustbox to scale if wider than available width
        lines.append(r"\adjustbox{max width=" + max_width + r"}{%")

        lines.append(r"$\displaystyle")
        # Use l@{\hspace{2em}}r: left-aligned expressions, right-aligned justifications
        lines.append(r"\begin{array}{l@{\hspace{2em}}r}")

        # Set context for line break formatting
        self._in_equiv_block = True

        # Generate steps
        for i, step in enumerate(node.steps):
            expr_latex = self.generate_expr(step.expression)

            # No leading & - start directly with expression for flush left
            # First step: expression; subsequent: \Leftrightarrow expression
            line = expr_latex if i == 0 else r"\Leftrightarrow " + expr_latex

            # Add justification if present (flush right)
            if step.justification:
                escaped_just = self._escape_justification(step.justification)
                line += r" & [\mbox{" + escaped_just + "}]"

            # Add line break except for last line
            if i < len(node.steps) - 1:
                line += r" \\"

            lines.append(line)

        # Reset context
        self._in_equiv_block = False

        lines.append(r"\end{array}$%")
        # Close adjustbox wrapper
        lines.append(r"}")
        # Close center environment (only if we opened it)
        if not self._in_inline_part:
            lines.append(r"\end{center}")
        # Add trailing spacing for separation from following content
        lines.append(r"\bigskip")
        lines.append("")

        return lines

    @generate_document_item.register(InfruleBlock)
    def _generate_infrule_block(self, node: InfruleBlock) -> list[str]:
        r"""Generate LaTeX for infrule block.

        Uses fuzz's infrule environment with premises, \derive separator,
        and conclusion. Two-column format: expression & label.
        """
        lines: list[str] = []

        lines.append(r"\begin{infrule}")

        # Generate premises
        for premise_expr, label in node.premises:
            expr_latex = self.generate_expr(premise_expr)
            line = "  " + expr_latex + " &"

            # Add label if present
            if label:
                escaped_label = self._escape_justification(label)
                line += r" \mbox{" + escaped_label + "}"

            line += r" \\"
            lines.append(line)

        # Add \derive separator
        lines.append(r"  \derive \\")

        # Generate conclusion
        conclusion_expr, conclusion_label = node.conclusion
        conclusion_latex = self.generate_expr(conclusion_expr)
        line = "  " + conclusion_latex + " &"

        # Add label if present
        if conclusion_label:
            escaped_label = self._escape_justification(conclusion_label)
            line += r" \mbox{" + escaped_label + "}"

        lines.append(line)

        lines.append(r"\end{infrule}")
        lines.append("")

        return lines

    @generate_document_item.register(GivenType)
    def _generate_given_type(self, node: GivenType) -> list[str]:
        """Generate LaTeX for given type declaration."""
        lines: list[str] = []
        # Generate as: [A, B, C] in zed environment
        names_str = ", ".join(node.names)
        lines.append(f"\\begin{{zed}}[{names_str}]\\end{{zed}}")
        lines.append("")
        return lines

    @generate_document_item.register(FreeType)
    def _generate_free_type(self, node: FreeType) -> list[str]:
        """Generate LaTeX for free type definition.

        Examples:
        - Status ::= active | inactive (simple branches)
        - Tree ::= stalk | leaf \\ldata N \\rdata |
          branch \\ldata Tree \\cross Tree \\rdata
        """
        lines: list[str] = []

        # Generate each branch with proper LaTeX formatting
        branch_strs: list[str] = []
        for branch in node.branches:
            if branch.parameters is None:
                # Simple branch: just the name
                branch_strs.append(branch.name)
            else:
                # Parameterized constructor: name \\ldata params \\rdata
                # Special handling: if params is SequenceLiteral, extract contents
                # (user writes <<...>> in ASCII to represent constructor delimiters)
                if isinstance(branch.parameters, SequenceLiteral):
                    # Generate contents without sequence delimiters
                    # \ldata ... \rdata already provide the delimiters
                    if branch.parameters.elements:
                        params_latex = self.generate_expr(branch.parameters.elements[0])
                    else:
                        params_latex = ""
                else:
                    params_latex = self.generate_expr(branch.parameters)
                branch_strs.append(f"{branch.name} \\ldata {params_latex} \\rdata")

        # Join branches with |
        branches_str = " | ".join(branch_strs)

        # Wrap in zed environment for proper formatting
        lines.append(f"\\begin{{zed}}{node.name} ::= {branches_str}\\end{{zed}}")
        lines.append("")
        return lines

    @generate_document_item.register(SyntaxBlock)
    def _generate_syntax_block(self, node: SyntaxBlock) -> list[str]:
        """Generate LaTeX for syntax environment (aligned free type definitions).

        Generates column-aligned LaTeX with & separators:
        \\begin{syntax}
        TypeName & ::= & branch1 | branch2
        \\also
        AnotherType & ::= & branch1 \\\\
        & | & branch2
        \\end{syntax}
        """
        lines: list[str] = []
        lines.append("\\begin{syntax}")

        for group_idx, group in enumerate(node.groups):
            # Add \also between groups (but not before first group)
            if group_idx > 0:
                lines.append("\\also")

            for def_idx, definition in enumerate(group):
                # Generate branches for this definition
                branch_lines = self._generate_syntax_definition_branches(definition)

                # Determine if we need \\ at the end of this definition
                is_last_in_group = def_idx == len(group) - 1
                is_last_group = group_idx == len(node.groups) - 1
                needs_line_break = not (is_last_in_group and is_last_group)

                # First line: TypeName & ::= & branches
                first_line = branch_lines[0]
                if needs_line_break and len(branch_lines) == 1:
                    # Only one line and not the last: add \\
                    first_line += " \\\\"
                lines.append(first_line)

                # Continuation lines: & | & branches
                for cont_idx, continuation in enumerate(branch_lines[1:]):
                    is_last_continuation = cont_idx == len(branch_lines) - 2
                    if needs_line_break and is_last_continuation:
                        continuation += " \\\\"
                    lines.append(continuation)

        lines.append("\\end{syntax}")
        lines.append("")
        return lines

    def _generate_syntax_definition_branches(
        self, definition: SyntaxDefinition
    ) -> list[str]:
        """Generate branch lines for a single type definition in syntax block.

        Returns list of lines:
        - First line: "TypeName & ::= & branch1 | branch2 | ..."
        - Continuation lines (if any): "& | & branch3 | branch4 | ..."
        """
        # Generate LaTeX for each branch
        branch_strs: list[str] = []
        for branch in definition.branches:
            if branch.parameters is None:
                branch_strs.append(branch.name)
            else:
                # Generate parameter expression
                if isinstance(branch.parameters, SequenceLiteral):
                    if branch.parameters.elements:
                        params_latex = self.generate_expr(branch.parameters.elements[0])
                    else:
                        params_latex = ""
                else:
                    params_latex = self.generate_expr(branch.parameters)
                branch_strs.append(f"{branch.name} \\ldata {params_latex} \\rdata")

        # For now, put all branches on one line
        # Future enhancement: could split long lines across multiple rows
        branches_str = " | ".join(branch_strs)
        first_line = f"{definition.name} & ::= & {branches_str}"

        return [first_line]

    @generate_document_item.register(Abbreviation)
    def _generate_abbreviation(self, node: Abbreviation) -> list[str]:
        r"""Generate LaTeX for abbreviation definition.

        Supports optional generic parameters.

        Note: Abbreviations must be wrapped in \begin{zed}...\end{zed}
        for fuzz type checker to recognize them.

        Fuzz syntax requires generic parameters AFTER the name: Name[X, Y]
        not before: [X, Y]Name

        Processes abbreviation names through _generate_identifier() for compound
        identifiers like R+, R*, R~ (partial support, GitHub #3 still open).
        """
        lines: list[str] = []
        expr_latex = self.generate_expr(node.expression)

        # Process name through _generate_identifier() for compound identifiers
        name_latex = self._generate_identifier(
            Identifier(line=0, column=0, name=node.name)
        )

        # Wrap in zed environment for fuzz compatibility
        # Fuzz requires: Name[X] not [X]Name
        if node.generic_params:
            params_str = ", ".join(node.generic_params)
            abbrev = f"{name_latex}[{params_str}] == {expr_latex}"
            lines.append("\\begin{zed}")
            lines.append(abbrev)
            lines.append("\\end{zed}")
        else:
            abbrev = f"{name_latex} == {expr_latex}"
            lines.append("\\begin{zed}")
            lines.append(abbrev)
            lines.append("\\end{zed}")

        lines.append("")
        return lines

    @generate_document_item.register(AxDef)
    def _generate_axdef(self, node: AxDef) -> list[str]:
        """Generate LaTeX for axiomatic definition.

        Supports optional generic parameters.
        Multiple declarations appear on separate lines with line breaks.
        """
        lines: list[str] = []

        # Add generic parameters if present
        if node.generic_params:
            params_str = ", ".join(node.generic_params)
            lines.append(f"\\begin{{axdef}}[{params_str}]")
        else:
            lines.append(r"\begin{axdef}")

        # Generate declarations on separate lines
        if node.declarations:
            for i, decl in enumerate(node.declarations):
                # Process variable through identifier logic for underscore handling
                var_latex = self._generate_identifier(
                    Identifier(line=0, column=0, name=decl.variable)
                )
                type_latex = self.generate_expr(decl.type_expr)
                # Post-process: add parentheses for nested special functions
                # Critical for fuzz: P (P Z) must be \power (\power Z)
                # not \power \power Z which causes validation errors
                special_ops = [
                    r"\power \power",
                    r"\power \finset",
                    r"\finset \power",
                    r"\seq \seq",
                    r"\iseq \iseq",
                    r"\bag \bag",
                ]
                for pattern in special_ops:
                    if pattern in type_latex:
                        # Find second operator and wrap from there
                        parts = type_latex.split(pattern, 1)
                        if len(parts) == 2:
                            second_part = pattern.split()[-1] + " " + parts[1]
                            type_latex = (
                                parts[0] + pattern.split()[0] + f" ({second_part})"
                            )
                            break

                # Build full declaration line for overflow check
                decl_line = f"{var_latex} : {type_latex}"
                self._check_overflow(
                    decl_line,
                    decl.type_expr.line,
                    "axdef declaration",
                    f"{decl.variable} : ...",
                )

                # Add line break after each declaration except the last
                if i < len(node.declarations) - 1:
                    lines.append(f"{decl_line} \\\\")
                else:
                    lines.append(decl_line)

        # Generate where clause if predicate groups exist
        if node.predicates and any(group for group in node.predicates):
            lines.append(r"\where")

            # Iterate through predicate groups (separated by blank lines)
            for group_idx, group in enumerate(node.predicates):
                # Generate predicates in current group
                for pred_idx, pred in enumerate(group):
                    # Top-level predicates: pass parent=None for smart parenthesization
                    pred_latex = self.generate_expr(pred, parent=None)

                    # Check for overflow in where clause predicates
                    self._check_overflow(
                        pred_latex,
                        pred.line,
                        "axdef where clause",
                    )

                    # Use \\ as separator within group
                    if pred_idx < len(group) - 1:
                        lines.append(f"{pred_latex} \\\\")
                    else:
                        lines.append(pred_latex)

                # Add \also between groups (not after last group)
                if group_idx < len(node.predicates) - 1:
                    lines.append(r"\also")

        lines.append(r"\end{axdef}")
        lines.append("")

        return lines

    @generate_document_item.register(GenDef)
    def _generate_gendef(self, node: GenDef) -> list[str]:
        """Generate LaTeX for generic definition.

        Generic definitions always have generic parameters (required).
        Multiple declarations appear on separate lines with line breaks.
        """
        lines: list[str] = []

        # Generic parameters are always present for gendef
        params_str = ", ".join(node.generic_params)
        lines.append(f"\\begin{{gendef}}[{params_str}]")

        # Generate declarations on separate lines
        if node.declarations:
            for i, decl in enumerate(node.declarations):
                # Process variable through identifier logic for underscore handling
                var_latex = self._generate_identifier(
                    Identifier(line=0, column=0, name=decl.variable)
                )
                type_latex = self.generate_expr(decl.type_expr)
                # Post-process: add parentheses for nested special functions
                # Critical for fuzz: P (P Z) must be \power (\power Z)
                # not \power \power Z which causes validation errors
                special_ops = [
                    r"\power \power",
                    r"\power \finset",
                    r"\finset \power",
                    r"\seq \seq",
                    r"\iseq \iseq",
                    r"\bag \bag",
                ]
                for pattern in special_ops:
                    if pattern in type_latex:
                        # Find second operator and wrap from there
                        parts = type_latex.split(pattern, 1)
                        if len(parts) == 2:
                            second_part = pattern.split()[-1] + " " + parts[1]
                            type_latex = (
                                parts[0] + pattern.split()[0] + f" ({second_part})"
                            )
                            break

                # Build full declaration line for overflow check
                decl_line = f"  {var_latex}: {type_latex}"
                self._check_overflow(
                    decl_line,
                    decl.type_expr.line,
                    "gendef declaration",
                    f"{decl.variable} : ...",
                )

                # Add line break after each declaration except the last
                if i < len(node.declarations) - 1:
                    lines.append(f"{decl_line} \\\\")
                else:
                    lines.append(decl_line)

        # Generate where clause if predicate groups exist
        if node.predicates and any(group for group in node.predicates):
            lines.append(r"\where")

            # Iterate through predicate groups (separated by blank lines)
            for group_idx, group in enumerate(node.predicates):
                # Generate predicates in current group
                for pred_idx, pred in enumerate(group):
                    # Top-level predicates: pass parent=None for smart parenthesization
                    pred_latex = self.generate_expr(pred, parent=None)

                    # Check for overflow in where clause predicates
                    self._check_overflow(
                        pred_latex,
                        pred.line,
                        "gendef where clause",
                    )

                    # Fuzz requires \\ after each predicate except the last in group
                    if self.use_fuzz and pred_idx < len(group) - 1:
                        lines.append(f"  {pred_latex} \\\\")
                    else:
                        lines.append(f"  {pred_latex}")

                # Add \also between groups (not after last group)
                if group_idx < len(node.predicates) - 1:
                    lines.append(r"\also")

        lines.append(r"\end{gendef}")
        lines.append("")

        return lines

    @generate_document_item.register(Zed)
    def _generate_zed(self, node: Zed) -> list[str]:
        """Generate LaTeX for zed block (unboxed paragraph).

        Zed blocks contain Z notation constructs:
        - Given types: [A, B, C]
        - Free types: Type ::= branch1 | branch2
        - Abbreviations: Name == expression
        - Predicates: forall x : N | P

        Supports mixed content (multiple construct types in one block).
        """
        lines: list[str] = []

        lines.append(r"\begin{zed}")

        # Handle Document content (multiple items in zed block)
        if isinstance(node.content, Document):
            for idx, item in enumerate(node.content.items):
                # Add \also separator before all items except the first
                # Note: fuzz requires \also between Z paragraphs, not \\
                if idx > 0:
                    lines.append(r"\also")

                # Generate given types: [A, B, C]
                if isinstance(item, GivenType):
                    names_str = ", ".join(item.names)
                    given_line = f"[{names_str}]"
                    self._check_overflow(
                        given_line,
                        item.line,
                        "zed given types",
                    )
                    lines.append(given_line)

                # Generate free types: Type ::= branch1 | branch2
                elif isinstance(item, FreeType):
                    branch_strs: list[str] = []
                    for branch in item.branches:
                        if branch.parameters is None:
                            branch_strs.append(branch.name)
                        else:
                            params_latex = self.generate_expr(branch.parameters)
                            branch_str = f"{branch.name} \\ldata {params_latex} \\rdata"
                            branch_strs.append(branch_str)
                    branches_str = " | ".join(branch_strs)
                    free_type_line = f"{item.name} ::= {branches_str}"
                    self._check_overflow(
                        free_type_line,
                        item.line,
                        "zed free type",
                        f"{item.name} ::= ...",
                    )
                    lines.append(free_type_line)

                # Generate abbreviations: Name == expression
                elif isinstance(item, Abbreviation):
                    expr_latex = self.generate_expr(item.expression)
                    name_latex = self._generate_identifier(
                        Identifier(line=0, column=0, name=item.name)
                    )
                    if item.generic_params:
                        params_str = ", ".join(item.generic_params)
                        abbrev_line = f"{name_latex}[{params_str}] == {expr_latex}"
                    else:
                        abbrev_line = f"{name_latex} == {expr_latex}"
                    self._check_overflow(
                        abbrev_line,
                        item.line,
                        "zed abbreviation",
                        f"{item.name} == ...",
                    )
                    lines.append(abbrev_line)

                # Generate expressions/predicates
                elif isinstance(item, Expr):
                    content_latex = self.generate_expr(item)
                    self._check_overflow(
                        content_latex,
                        item.line,
                        "zed predicate",
                    )
                    lines.append(f"{content_latex}")
        else:
            # Single expression (backward compatible)
            content_latex = self.generate_expr(node.content)
            self._check_overflow(
                content_latex,
                node.content.line,
                "zed predicate",
            )
            lines.append(f"{content_latex}")

        lines.append(r"\end{zed}")
        lines.append("")

        return lines

    @generate_document_item.register(Schema)
    def _generate_schema(self, node: Schema) -> list[str]:
        """Generate LaTeX for schema definition.

        Supports optional generic parameters and anonymous schemas (name=None).
        Multiple declarations appear on separate lines with line breaks.

        Processes schema names through _generate_identifier() for compound
        identifiers like S+, S*, S~ (partial support, GitHub #3 still open).
        """
        lines: list[str] = []

        # Determine schema name (empty string for anonymous)
        # Process name through _generate_identifier() for compound identifiers
        if node.name is not None:
            schema_name = self._generate_identifier(
                Identifier(line=0, column=0, name=node.name)
            )
        else:
            schema_name = ""

        # Context for overflow warnings
        schema_context = f"schema {schema_name}" if schema_name else "anonymous schema"

        # Add generic parameters if present
        if node.generic_params:
            params_str = ", ".join(node.generic_params)
            lines.append(f"\\begin{{schema}}{{{schema_name}}}[{params_str}]")
        else:
            lines.append(r"\begin{schema}{" + schema_name + "}")

        # Generate declarations on separate lines
        if node.declarations:
            for i, decl in enumerate(node.declarations):
                # Process variable through identifier logic for underscore handling
                var_latex = self._generate_identifier(
                    Identifier(line=0, column=0, name=decl.variable)
                )
                type_latex = self.generate_expr(decl.type_expr)
                # Post-process: add parentheses for nested special functions
                # Critical for fuzz: P (P Z) must be \power (\power Z)
                # not \power \power Z which causes validation errors
                special_ops = [
                    r"\power \power",
                    r"\power \finset",
                    r"\finset \power",
                    r"\seq \seq",
                    r"\iseq \iseq",
                    r"\bag \bag",
                ]
                for pattern in special_ops:
                    if pattern in type_latex:
                        # Find second operator and wrap from there
                        parts = type_latex.split(pattern, 1)
                        if len(parts) == 2:
                            second_part = pattern.split()[-1] + " " + parts[1]
                            type_latex = (
                                parts[0] + pattern.split()[0] + f" ({second_part})"
                            )
                            break

                # Build full declaration line for overflow check
                decl_line = f"{var_latex} : {type_latex}"
                self._check_overflow(
                    decl_line,
                    decl.type_expr.line,
                    f"{schema_context} declaration",
                    f"{decl.variable} : ...",
                )

                # Add line break after each declaration except the last
                if i < len(node.declarations) - 1:
                    lines.append(f"{decl_line} \\\\")
                else:
                    lines.append(decl_line)

        # Generate where clause if predicate groups exist
        if node.predicates and any(group for group in node.predicates):
            lines.append(r"\where")

            # Iterate through predicate groups (separated by blank lines)
            for group_idx, group in enumerate(node.predicates):
                # Generate predicates in current group
                for pred_idx, pred in enumerate(group):
                    # Top-level predicates: pass parent=None for smart parenthesization
                    pred_latex = self.generate_expr(pred, parent=None)

                    # Check for overflow in where clause predicates
                    self._check_overflow(
                        pred_latex,
                        pred.line,
                        f"{schema_context} where clause",
                    )

                    # Use \\ as separator within group
                    if pred_idx < len(group) - 1:
                        lines.append(f"{pred_latex} \\\\")
                    else:
                        lines.append(pred_latex)

                # Add \also between groups (not after last group)
                if group_idx < len(node.predicates) - 1:
                    lines.append(r"\also")

        lines.append(r"\end{schema}")
        lines.append("")

        return lines

    @generate_document_item.register(ProofTree)
    def _generate_proof_tree(self, node: ProofTree) -> list[str]:
        """Generate LaTeX for proof tree (auto-scales if needed)."""
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

        # Wrap in adjustbox to scale if wider than available width
        lines.append(r"\adjustbox{max width=" + max_width + r"}{%")

        # Generate proof tree in display math
        proof_latex = self._generate_proof_node_infer(node.conclusion)
        lines.append(r"$\displaystyle")
        lines.append(proof_latex)
        lines.append(r"$%")
        # Close adjustbox wrapper
        lines.append(r"}")
        # Close center environment (only if we opened it)
        if not self._in_inline_part:
            lines.append(r"\end{center}")
        # Add trailing spacing for separation from following content
        lines.append(r"\bigskip")
        lines.append("")

        return lines

    def _format_boxed_assumption(self, expr: Expr, label: int | None) -> str:
        """Generate boxed assumption with corner brackets ⌈expr⌉[n]."""
        expr_latex = self.generate_expr(expr)
        # Use \ulcorner and \urcorner for corner brackets (requires amsmath)
        if label is not None:
            return f"\\ulcorner {expr_latex} \\urcorner^{{[{label}]}}"
        return f"\\ulcorner {expr_latex} \\urcorner"

    def _calculate_tree_depth(self, node: ProofNode | CaseAnalysis) -> int:
        """Calculate the depth of a proof tree (number of inference levels)."""
        if isinstance(node, CaseAnalysis):
            if not node.steps:
                return 0

            # For case analysis, count sequential steps (not just nested depth)
            # Sequential steps stack vertically, increasing height
            sibling_count = 0
            sequential_count = 0

            for step in node.steps:
                if step.is_sibling:
                    if sequential_count == 0:
                        sibling_count += 1
                    else:
                        # Sibling after sequential - treat as sequential
                        sequential_count += 1
                else:
                    sequential_count += 1

            # Height is based on sequential steps + 1 for sibling layer (if any)
            # Plus the depth of any nested children
            sibling_layer = 1 if sibling_count > 0 else 0
            max_child_depth = max(
                (self._calculate_tree_depth(step) for step in node.steps), default=0
            )

            return sibling_layer + sequential_count + max_child_depth

        if not node.children:
            return 0

        return 1 + max(self._calculate_tree_depth(child) for child in node.children)

    def _generate_proof_node_infer(self, node: ProofNode) -> str:
        """
        Generate \\infer macro for a proof node (bottom-up natural deduction).

        Returns LaTeX string for this node and its supporting premises.

        Handles synthetic top-level case analysis nodes.
        """
        # Check for synthetic top-level case analysis node
        # These are created when proof starts with CASE statements
        if (
            isinstance(node.expression, Identifier)
            and node.expression.name == "[case_analysis]"
            and node.justification == "case analysis"
        ):
            # Don't render the synthetic node itself, just its case children
            case_latexes: list[str] = []
            for child in node.children:
                if isinstance(child, CaseAnalysis):
                    # Use existing case analysis generation method
                    case_latexes.append(self._generate_case_analysis(child))
                else:
                    # Must be ProofNode
                    case_latexes.append(self._generate_proof_node_infer(child))

            # Join cases side-by-side with &
            return " & ".join(case_latexes) if case_latexes else ""

        # If this is an assumption node, it should appear as a boxed premise
        if node.is_assumption:
            # The assumption itself is a premise (leaf)
            assumption_latex = self._format_boxed_assumption(
                node.expression, node.label
            )

            # If it has children, they are derivations from this assumption
            # The assumption should be the base of the tree
            if not node.children:
                return assumption_latex

            # For now, treat the first child as the main derivation from the
            # assumption. This is a simplified approach - full natural deduction
            # requires dependency analysis.
            if len(node.children) == 1 and isinstance(node.children[0], ProofNode):
                single_child = node.children[0]
                # Generate child with assumption as its premise
                return self._generate_inference_from_assumption(
                    single_child, assumption_latex, node.label
                )

            # Multiple children or case analysis - need special handling
            return self._generate_complex_assumption_scope(node, assumption_latex)

        # Generate expression for conclusion
        expr_latex = self.generate_expr(node.expression)

        # Check for assumption reference FIRST (before checking children)
        # Pattern: "from N" where N is a digit
        # This should render as boxed assumption notation regardless of children
        if node.justification:
            just_lower = node.justification.lower()
            # Check if this is purely a "from N" reference (not "rule from N")
            from_only_match = re.match(r"^\s*from\s+(\d+)\s*$", just_lower)
            if from_only_match:
                ref_label = from_only_match.group(1)
                # Render as boxed assumption reference
                # If this node has children, they should be rendered below
                if node.children:
                    # Generate children as premises
                    child_latexes = [
                        self._generate_proof_node_infer(child)
                        for child in node.children
                        if isinstance(child, ProofNode)
                    ]
                    premises = "\n  ".join(child_latexes)
                    boxed = f"\\ulcorner {expr_latex} \\urcorner^{{[{ref_label}]}}"
                    return f"\\infer{{{boxed}}}{{\n  {premises}\n}}"
                # Leaf node - just return the boxed reference
                return f"\\ulcorner {expr_latex} \\urcorner^{{[{ref_label}]}}"

        # If no children, return expression (possibly with justification)
        if not node.children:
            # Check if justification indicates a reference (not a derivation rule)
            if node.justification:
                just_lower = node.justification.lower()
                # References like "copy", etc. should not be wrapped in \infer
                if "copy" in just_lower:
                    # Just return the expression - it's a reference
                    return expr_latex
                # Otherwise it's a derivation rule, wrap in \infer
                just = self._format_justification_label(node.justification)
                return f"\\infer[{just}]{{{expr_latex}}}{{}}"
            return expr_latex

        # Group children by siblings
        # Siblings (marked with ::) should be rendered side-by-side with &
        child_groups: list[list[str]] = []
        current_group: list[str] = []
        # Track case analysis with indices for raiseproof handling
        case_children: list[tuple[int, CaseAnalysis]] = []

        for idx, child in enumerate(node.children):
            if isinstance(child, CaseAnalysis):
                # Track case analysis for raiseproof handling
                case_children.append((idx, child))
                # Close current group before case
                if current_group:
                    child_groups.append(current_group)
                    current_group = []
            else:
                # child is ProofNode (only other type in union)
                child_latex = self._generate_proof_node_infer(child)

                if child.is_sibling and current_group:
                    # Add to current sibling group
                    current_group.append(child_latex)
                elif child.is_assumption and current_group:
                    # Assumptions should be laid out horizontally with siblings
                    # for proper spacing (e.g., in => elim with p => r & p)
                    current_group.append(child_latex)
                else:
                    # Start new group
                    if current_group:
                        child_groups.append(current_group)
                    current_group = [child_latex]

        # Add last group
        if current_group:
            child_groups.append(current_group)

        # Generate premises by joining siblings with &
        # Put & on its own line to avoid LaTeX parser issues with nested contexts
        non_case_premises = ["\n&\n".join(group) for group in child_groups]

        # If we have case analysis, apply raiseproof for vertical layout
        if case_children:
            # Identify disjunction siblings (for or-elim)
            disjunction_premises = [
                premise
                for group in child_groups
                for premise in group
                if r"\lor" in premise  # Check if this is a disjunction
            ]

            # Generate raised cases with staggered heights
            raised_cases: list[str] = []
            for case_position, (_idx, case) in enumerate(case_children):
                case_latex = self._generate_case_analysis(case)
                depth = self._calculate_tree_depth(case)

                # STAGGERED HEIGHT FORMULA:
                # First case: 6-8ex (minimal)
                # Subsequent cases: 18-24ex (much taller to avoid overlap)
                if case_position == 0:
                    # First case: minimal height
                    height = 6 + (depth * 2)  # Conservative for first case
                    # raiseproof naturally protects nested & from outer \infer alignment
                    raised = f"\\raiseproof{{{height}ex}}{{{case_latex}}}"
                else:
                    # Subsequent cases: taller + horizontal spacing
                    height = 18 + (depth * 4)  # Much taller for subsequent cases
                    # raiseproof naturally protects nested & from outer \infer alignment
                    raised = f"\\hskip 6em \\raiseproof{{{height}ex}}{{{case_latex}}}"

                raised_cases.append(raised)

            # Combine: disjunction premises first (if any), then raised case branches
            if disjunction_premises:
                all_premises = disjunction_premises + raised_cases
            else:
                # No disjunction - might be other premises before cases
                all_premises = non_case_premises + raised_cases

            # Put & on its own line to avoid LaTeX parser issues with nested contexts
            premises = "\n&\n".join(all_premises)
        else:
            # No case analysis - use normal premises
            premises = "\n  ".join(non_case_premises)

        # Generate justification label
        if node.justification:
            # Escape LaTeX special characters in justification
            just = self._format_justification_label(node.justification)
            return f"\\infer[{just}]{{{expr_latex}}}{{\n  {premises}\n}}"
        # No justification - use plain \infer
        return f"\\infer{{{expr_latex}}}{{\n  {premises}\n}}"

    def _generate_inference_from_assumption(
        self, node: ProofNode, assumption_latex: str, assumption_label: int | None
    ) -> str:
        """Generate an inference that derives from a boxed assumption."""
        expr_latex = self.generate_expr(node.expression)

        # If this node has no children, it directly derives from the assumption
        if not node.children:
            if node.justification:
                just = self._format_justification_label(node.justification)
                return f"\\infer[{just}]{{{expr_latex}}}{{{assumption_latex}}}"
            return f"\\infer{{{expr_latex}}}{{{assumption_latex}}}"

        # Node has children - generate them recursively
        # Children should ultimately reference the assumption as their premise
        return self._generate_proof_node_infer_with_assumption(
            node, assumption_latex, assumption_label
        )

    def _generate_proof_node_infer_with_assumption(
        self, node: ProofNode, assumption_latex: str, assumption_label: int | None
    ) -> str:
        """Generate inference node with leaves referencing the given assumption."""
        expr_latex = self.generate_expr(node.expression)

        # Base case: no children means this should derive from the assumption
        if not node.children:
            if node.justification:
                just_lower = node.justification.lower()
                # References like "from 1", "copy", etc. should not be wrapped in \infer
                if "from" in just_lower or "copy" in just_lower:
                    # Extract assumption label if present (e.g., "from 1" -> "1")
                    from_match = re.search(r"from\s+(\d+)", just_lower)
                    if from_match:
                        ref_label = from_match.group(1)
                        # Render as boxed assumption reference
                        return f"\\ulcorner {expr_latex} \\urcorner^{{[{ref_label}]}}"
                    # Just return the expression - it's a reference without label
                    return expr_latex
                # Otherwise it's a derivation rule
                just = self._format_justification_label(node.justification)
                return f"\\infer[{just}]{{{expr_latex}}}{{{assumption_latex}}}"
            return expr_latex

        # Process children
        premises: list[str] = []
        for child in node.children:
            if isinstance(child, CaseAnalysis):
                premises.append(self._generate_case_analysis(child))
            elif child.is_assumption:
                # Child is its own assumption - process independently
                child_latex = self._generate_proof_node_infer(child)
                premises.append(child_latex)
            else:
                child_latex = self._generate_proof_node_infer_with_assumption(
                    child, assumption_latex, assumption_label
                )
                premises.append(child_latex)

        # Join premises
        premises_str = " & ".join(premises) if premises else assumption_latex

        # Generate with justification
        if node.justification:
            just = self._format_justification_label(node.justification)
            return f"\\infer[{just}]{{{expr_latex}}}{{{premises_str}}}"
        return f"\\infer{{{expr_latex}}}{{{premises_str}}}"

    def _generate_complex_assumption_scope(
        self, assumption_node: ProofNode, assumption_latex: str
    ) -> str:
        """Handle complex assumption scopes with multiple children or case analysis."""
        # Group children into sibling groups and sequential derivations
        # Siblings (marked with ::) are horizontal, non-siblings nest vertically

        children = assumption_node.children
        if not children:
            return assumption_latex

        # Separate siblings from sequential derivations
        sibling_group: list[ProofNode | CaseAnalysis] = []
        sequential: list[ProofNode | CaseAnalysis] = []

        for child in children:
            if isinstance(child, CaseAnalysis):
                # Case analysis can appear in sibling position
                if not sequential:
                    sibling_group.append(child)
                else:
                    sequential.append(child)
            elif child.is_sibling:
                # Only add to sibling group if we haven't started sequential yet
                if not sequential:
                    sibling_group.append(child)
                else:
                    # Sibling after non-sibling - this is a new context
                    sequential.append(child)
            else:
                # Non-sibling - starts sequential derivations
                sequential.append(child)

        # Generate sibling group (derives directly from assumption)
        sibling_latex_parts: list[str] = []
        for child in sibling_group:
            if isinstance(child, CaseAnalysis):
                sibling_latex_parts.append(self._generate_case_analysis(child))
            else:
                child_latex = self._generate_proof_node_infer_with_assumption(
                    child, assumption_latex, assumption_node.label
                )
                sibling_latex_parts.append(child_latex)

        # Combine siblings horizontally with &
        if sibling_latex_parts:
            current_premises = " & ".join(sibling_latex_parts)
        else:
            current_premises = assumption_latex

        # Now build sequential derivations vertically on top
        # Each sequential step uses the previous result as its premise
        for child in sequential:
            if isinstance(child, CaseAnalysis):
                child_latex = self._generate_case_analysis(child)
            # Generate the child
            # If it has children, we need to process them recursively
            elif child.children:
                # This node has children - need to generate a full subtree
                # The subtree should use current_premises as its base
                expr_latex = self.generate_expr(child.expression)

                # Generate children
                child_premises_parts: list[str] = []
                has_case_analysis = False
                for grandchild in child.children:
                    if isinstance(grandchild, CaseAnalysis):
                        child_premises_parts.append(
                            self._generate_case_analysis(grandchild)
                        )
                        has_case_analysis = True
                    else:
                        # Recurse to handle nested structure
                        grandchild_latex = self._generate_proof_node_infer(grandchild)
                        child_premises_parts.append(grandchild_latex)

                # Include siblings from parent scope as additional premises.
                # Special case: for or-elim with case analysis, only include
                # disjunction siblings. Other siblings (like extracted
                # conjuncts) are handled within case branches.
                if sibling_latex_parts and child_premises_parts:
                    if has_case_analysis:
                        # Only include disjunction siblings as top-level
                        # premises for or-elim
                        disjunction_siblings: list[str] = []
                        for i, sib_child in enumerate(sibling_group):
                            if (
                                isinstance(sib_child, ProofNode)
                                and isinstance(sib_child.expression, BinaryOp)
                                and sib_child.expression.operator == "or"
                            ):
                                disjunction_siblings.append(sibling_latex_parts[i])

                        # Apply \raiseproof to case branches for vertical
                        # layout. STAGGERED STRATEGY: Different cases get
                        # different heights + horizontal spacing
                        raised_cases: list[str] = []

                        # Collect all case indices first
                        case_indices: list[int] = []
                        for idx, grandchild in enumerate(child.children):
                            if isinstance(grandchild, CaseAnalysis):
                                case_indices.append(idx)

                        # Generate raised cases with staggered heights
                        for case_position, idx in enumerate(case_indices):
                            grandchild = child.children[idx]
                            depth = self._calculate_tree_depth(grandchild)
                            case_latex = child_premises_parts[idx]

                            # STAGGERED HEIGHT FORMULA:
                            # First case: 6-8ex (minimal)
                            # Subsequent cases: 18-24ex (much taller to
                            # avoid overlap)
                            if case_position == 0:
                                # First case: minimal height
                                height = 6 + (depth * 2)  # Conservative for first case
                                raised = f"\\raiseproof{{{height}ex}}{{{case_latex}}}"
                            else:
                                # Subsequent cases: taller + horizontal
                                # spacing
                                height = 18 + (
                                    depth * 4
                                )  # Much taller for subsequent cases
                                raised = (
                                    f"\\hskip 6em "
                                    f"\\raiseproof{{{height}ex}}"
                                    f"{{{case_latex}}}"
                                )

                            raised_cases.append(raised)

                        # Combine: disjunction siblings first, then raised
                        # case branches
                        all_premises = disjunction_siblings + raised_cases
                        child_premises = " & ".join(all_premises)
                    else:
                        # Not case analysis - include all siblings
                        all_premises = sibling_latex_parts + child_premises_parts
                        child_premises = " & ".join(all_premises)
                elif child_premises_parts:
                    child_premises = " & ".join(child_premises_parts)
                else:
                    child_premises = current_premises

                if child.justification:
                    just = self._format_justification_label(child.justification)
                    child_latex = f"\\infer[{just}]{{{expr_latex}}}{{{child_premises}}}"
                else:
                    child_latex = f"\\infer{{{expr_latex}}}{{{child_premises}}}"
            else:
                # No children - derive directly from current_premises
                expr_latex = self.generate_expr(child.expression)

                if child.justification:
                    just = self._format_justification_label(child.justification)
                    child_latex = (
                        f"\\infer[{just}]{{{expr_latex}}}{{{current_premises}}}"
                    )
                else:
                    child_latex = f"\\infer{{{expr_latex}}}{{{current_premises}}}"

            # This becomes the new premise for next step
            current_premises = child_latex

        return current_premises

    def _generate_case_analysis(self, case: CaseAnalysis) -> str:
        """Generate LaTeX for case analysis branch."""
        # For each case, generate the proof steps
        # Cases are typically rendered as separate inference branches
        if not case.steps:
            return f"\\mbox{{case {case.case_name}}}"

        # Generate the first step (usually the conclusion of this case)
        # In many cases, there's just one step per case
        if len(case.steps) == 1:
            return self._generate_proof_node_infer(case.steps[0])

        # Multiple steps - need to group siblings horizontally, rest vertically
        # Separate siblings from sequential steps
        sibling_group: list[ProofNode] = []
        sequential: list[ProofNode] = []

        for step in case.steps:
            if step.is_sibling:
                # Only add to sibling group if we haven't started sequential yet
                if not sequential:
                    sibling_group.append(step)
                else:
                    sequential.append(step)
            else:
                # Non-sibling - starts sequential derivations
                sequential.append(step)

        # Generate sibling group
        # When multiple siblings exist in a case, the LAST one wraps earlier
        # This ensures each \raiseproof contains exactly ONE top-level \infer
        if sibling_group:
            if len(sibling_group) == 1:
                # Single step - straightforward
                current_result = self._generate_proof_node_infer(sibling_group[0])
            else:
                # Multiple sibling steps: last step wraps earlier ones as premises
                # Generate earlier siblings as complete inference trees
                earlier_parts = [
                    self._generate_proof_node_infer(s) for s in sibling_group[:-1]
                ]

                # Last step becomes the outer wrapper
                last_step = sibling_group[-1]
                expr_latex = self.generate_expr(last_step.expression)

                # Combine earlier siblings with last step's own premises
                all_premises = earlier_parts.copy()
                if last_step.children:
                    # Last step has its own children/premises too
                    for child in last_step.children:
                        if isinstance(child, ProofNode):
                            all_premises.append(self._generate_proof_node_infer(child))
                        else:
                            # child is CaseAnalysis (only other type in union)
                            all_premises.append(self._generate_case_analysis(child))

                premises_str = " & ".join(all_premises) if all_premises else ""

                # Generate outer infer for last step
                if last_step.justification:
                    just = self._format_justification_label(last_step.justification)
                    current_result = (
                        f"\\infer[{just}]{{{expr_latex}}}{{{premises_str}}}"
                    )
                else:
                    current_result = f"\\infer{{{expr_latex}}}{{{premises_str}}}"
        else:
            # No siblings, start with first sequential
            if not sequential:
                return ""
            current_result = self._generate_proof_node_infer(sequential[0])
            sequential = sequential[1:]

        # Build sequential steps vertically on top
        for step in sequential:
            expr_latex = self.generate_expr(step.expression)

            if step.justification:
                just = self._format_justification_label(step.justification)
                current_result = f"\\infer[{just}]{{{expr_latex}}}{{{current_result}}}"
            else:
                current_result = f"\\infer{{{expr_latex}}}{{{current_result}}}"

        return current_result

    def _format_justification_label(self, just: str) -> str:
        """
        Format justification text for \\infer label.

        Converts patterns:
        - "=> intro from 1" → "$\\Rightarrow$-intro^{[1]}" (discharge superscript)
        - "and elim 1" → "$\\land$-elim-1" (left/right projection, regular text)
        - "or intro 2" → "$\\lor$-intro-2" (left/right injection, regular text)
        """
        # First, check for discharge pattern: "rule from N" or "rule[N]"
        # Match: operator + rule name + (from N | [N])
        discharge_pattern = r"^(.*?)\s+(intro|elim)\s+(?:from\s+(\d+)|\[(\d+)\])$"
        match = re.match(discharge_pattern, just)

        if match:
            operator_part = match.group(1).strip()
            rule_name = match.group(2)
            label_num = match.group(3) or match.group(4)

            # Convert operator to LaTeX (no $ delimiters - already in math mode)
            # CRITICAL: Process by length (longest first) to avoid partial matches
            op_latex: str = operator_part

            # 5-character operators
            op_latex = op_latex.replace("77->", r"\ffun")

            # 4-character operators
            op_latex = op_latex.replace(">->>", r"\bij")
            op_latex = op_latex.replace("+->>", r"\psurj")
            op_latex = op_latex.replace("-->>", r"\surj")

            # 3-character operators (process before 2-character)
            op_latex = op_latex.replace("<=>", r"\Leftrightarrow")
            op_latex = op_latex.replace("<<|", r"\ndres")
            op_latex = op_latex.replace("|>>", r"\nrres")
            op_latex = op_latex.replace("|->", r"\mapsto")  # MUST be before ->
            op_latex = op_latex.replace("<->", r"\rel")
            op_latex = op_latex.replace(">+>", r"\pinj")
            op_latex = op_latex.replace("-|>", r"\pinj")
            op_latex = op_latex.replace(">->", r"\inj")
            op_latex = op_latex.replace("+->", r"\pfun")

            # 2-character operators (process after longer operators)
            op_latex = op_latex.replace("=>", r"\Rightarrow")
            op_latex = op_latex.replace("<|", r"\dres")
            op_latex = op_latex.replace("|>", r"\rres")
            op_latex = op_latex.replace("->", r"\fun")  # AFTER |-> and +->
            op_latex = op_latex.replace("++", r"\oplus")
            op_latex = op_latex.replace("o9", r"\circ")

            # Word-based operators (both English and L-prefixed forms)
            op_latex = re.sub(r"\bland\b", r"\\land", op_latex)  # land → \land
            op_latex = re.sub(r"\blor\b", r"\\lor", op_latex)  # lor → \lor
            op_latex = re.sub(r"\blnot\b", r"\\lnot", op_latex)  # lnot → \lnot
            op_latex = re.sub(r"\band\b", r"\\land", op_latex)  # and → \land
            op_latex = re.sub(r"\bor\b", r"\\lor", op_latex)  # or → \lor
            op_latex = re.sub(r"\bnot\b", r"\\lnot", op_latex)  # not → \lnot
            op_latex = re.sub(r"\bin\b", r"\\in", op_latex)  # Set membership
            op_latex = re.sub(r"\bdom\b", r"\\dom", op_latex)
            op_latex = re.sub(r"\bran\b", r"\\ran", op_latex)
            op_latex = re.sub(r"\bcomp\b", r"\\comp", op_latex)
            op_latex = re.sub(r"\binv\b", r"\\inv", op_latex)
            op_latex = re.sub(r"\bid\b", r"\\id", op_latex)

            # Z notation keywords (QA fixes - matches _escape_justification)
            # Order matters: exists1+ before exists1 to avoid partial match
            op_latex = re.sub(r"exists1\+", r"\\exists", op_latex)  # exists1+ → ∃
            op_latex = re.sub(r"\bexists1\b", r"\\exists_1", op_latex)  # exists1 → ∃₁
            op_latex = re.sub(r"\bexists\b", r"\\exists", op_latex)  # exists → ∃
            op_latex = re.sub(r"\bemptyset\b", r"\\emptyset", op_latex)  # emptyset → ∅
            op_latex = re.sub(r"\bforall\b", r"\\forall", op_latex)  # forall → ∀

            # Format as: operator-rule^{[label]}
            # Use \textrm instead of \mbox to work correctly in math mode contexts
            return f"{op_latex}\\textrm{{-{rule_name}}}^{{[{label_num}]}}"

        # Check for rule subscript pattern: "operator rule N" (like "and elim 1")
        # Match: operator + rule name + number (1 or 2)
        subscript_pattern = r"^(.*?)\s+(intro|elim)\s*([12])$"
        match = re.match(subscript_pattern, just)

        if match:
            operator_part = match.group(1).strip()
            rule_name = match.group(2)
            subscript_num = match.group(3)

            # Convert operator to LaTeX (no $ delimiters - already in math mode)
            # CRITICAL: Process by length (longest first) to avoid partial matches
            op_latex = operator_part

            # 5-character operators
            op_latex = op_latex.replace("77->", r"\ffun")

            # 4-character operators
            op_latex = op_latex.replace(">->>", r"\bij")
            op_latex = op_latex.replace("+->>", r"\psurj")
            op_latex = op_latex.replace("-->>", r"\surj")

            # 3-character operators (process before 2-character)
            op_latex = op_latex.replace("<=>", r"\Leftrightarrow")
            op_latex = op_latex.replace("<<|", r"\ndres")
            op_latex = op_latex.replace("|>>", r"\nrres")
            op_latex = op_latex.replace("|->", r"\mapsto")  # MUST be before ->
            op_latex = op_latex.replace("<->", r"\rel")
            op_latex = op_latex.replace(">+>", r"\pinj")
            op_latex = op_latex.replace("-|>", r"\pinj")
            op_latex = op_latex.replace(">->", r"\inj")
            op_latex = op_latex.replace("+->", r"\pfun")

            # 2-character operators (process after longer operators)
            op_latex = op_latex.replace("=>", r"\Rightarrow")
            op_latex = op_latex.replace("<|", r"\dres")
            op_latex = op_latex.replace("|>", r"\rres")
            op_latex = op_latex.replace("->", r"\fun")  # AFTER |-> and +->
            op_latex = op_latex.replace("++", r"\oplus")
            op_latex = op_latex.replace("o9", r"\circ")

            # Word-based operators (both English and L-prefixed forms)
            op_latex = re.sub(r"\bland\b", r"\\land", op_latex)  # land → \land
            op_latex = re.sub(r"\blor\b", r"\\lor", op_latex)  # lor → \lor
            op_latex = re.sub(r"\blnot\b", r"\\lnot", op_latex)  # lnot → \lnot
            op_latex = re.sub(r"\band\b", r"\\land", op_latex)  # and → \land
            op_latex = re.sub(r"\bor\b", r"\\lor", op_latex)  # or → \lor
            op_latex = re.sub(r"\bnot\b", r"\\lnot", op_latex)  # not → \lnot
            op_latex = re.sub(r"\bin\b", r"\\in", op_latex)  # Set membership
            op_latex = re.sub(r"\bdom\b", r"\\dom", op_latex)
            op_latex = re.sub(r"\bran\b", r"\\ran", op_latex)
            op_latex = re.sub(r"\bcomp\b", r"\\comp", op_latex)
            op_latex = re.sub(r"\binv\b", r"\\inv", op_latex)
            op_latex = re.sub(r"\bid\b", r"\\id", op_latex)

            # Z notation keywords (QA fixes - matches _escape_justification)
            # Order matters: exists1+ before exists1 to avoid partial match
            op_latex = re.sub(r"exists1\+", r"\\exists", op_latex)  # exists1+ → ∃
            op_latex = re.sub(r"\bexists1\b", r"\\exists_1", op_latex)  # exists1 → ∃₁
            op_latex = re.sub(r"\bexists\b", r"\\exists", op_latex)  # exists → ∃
            op_latex = re.sub(r"\bemptyset\b", r"\\emptyset", op_latex)  # emptyset → ∅
            op_latex = re.sub(r"\bforall\b", r"\\forall", op_latex)  # forall → ∀

            # Format as: operator-rule-number (just regular text, no subscript)
            # Use \textrm instead of \mbox to work correctly in math mode contexts
            return f"{op_latex}\\textrm{{-{rule_name}-{subscript_num}}}"

        # No special pattern - process normally
        # CRITICAL: Process by length (longest first) to avoid partial matches
        result = just

        # 5-character operators
        result = result.replace("77->", r"\ffun")

        # 4-character operators
        result = result.replace(">->>", r"\bij")
        result = result.replace("+->>", r"\psurj")
        result = result.replace("-->>", r"\surj")

        # 3-character operators (process before 2-character)
        result = result.replace("<=>", r"\Leftrightarrow")
        result = result.replace("<<|", r"\ndres")
        result = result.replace("|>>", r"\nrres")
        result = result.replace("|->", r"\mapsto")  # MUST be before ->
        result = result.replace("<->", r"\rel")
        result = result.replace(">+>", r"\pinj")
        result = result.replace("-|>", r"\pinj")
        result = result.replace(">->", r"\inj")
        result = result.replace("+->", r"\pfun")

        # 2-character operators (process after longer operators)
        result = result.replace("=>", r"\Rightarrow")
        result = result.replace("<|", r"\dres")
        result = result.replace("|>", r"\rres")
        result = result.replace("->", r"\fun")  # AFTER |-> and +->
        result = result.replace("++", r"\oplus")
        result = result.replace("o9", r"\circ")

        # Word-based operators (both English and L-prefixed forms)
        result = re.sub(r"\bland\b", r"\\land", result)  # land → \land
        result = re.sub(r"\blor\b", r"\\lor", result)  # lor → \lor
        result = re.sub(r"\blnot\b", r"\\lnot", result)  # lnot → \lnot
        result = re.sub(r"\band\b", r"\\land", result)  # and → \land
        result = re.sub(r"\bor\b", r"\\lor", result)  # or → \lor
        result = re.sub(r"\bnot\b", r"\\lnot", result)  # not → \lnot
        result = re.sub(r"\bin\b", r"\\in", result)  # Set membership
        result = re.sub(r"\bdom\b", r"\\dom", result)
        result = re.sub(r"\bran\b", r"\\ran", result)
        result = re.sub(r"\bcomp\b", r"\\comp", result)
        result = re.sub(r"\binv\b", r"\\inv", result)
        result = re.sub(r"\bid\b", r"\\id", result)

        # Z notation keywords (QA fixes - matches _escape_justification)
        # Order matters: exists1+ before exists1 to avoid partial match
        result = re.sub(r"exists1\+", r"\\exists", result)  # exists1+ → ∃
        result = re.sub(r"\bexists1\b", r"\\exists_1", result)  # exists1 → ∃₁
        result = re.sub(r"\bexists\b", r"\\exists", result)  # exists → ∃
        result = re.sub(r"\bemptyset\b", r"\\emptyset", result)  # emptyset → ∅
        result = re.sub(r"\bforall\b", r"\\forall", result)  # forall → ∀

        # Wrap ALL remaining text sequences in \mathrm{} for proper spacing
        # In math mode, spaces between letters are ignored, so we must wrap
        # text phrases to preserve word spacing.
        #
        # Strategy: Find sequences of words (letters/digits/underscores + spaces)
        # that aren't LaTeX commands (not preceded by \) and wrap them.
        # This handles phrases like "inductive hypothesis", "strong IH", etc.
        return self._wrap_text_in_mathrm(result)

    def _wrap_text_in_mathrm(self, text: str) -> str:
        """Wrap non-operator text sequences in \\mbox{} for proper math mode spacing.

        In math mode, spaces between bare letters are ignored. This function
        identifies text segments (between operators/symbols) and wraps them
        in \\mbox{} to preserve word spacing.

        Note: We use \\mbox{} instead of \\mathrm{} because \\mbox{} preserves
        spaces between words, while \\mathrm{} ignores them in math mode.

        Examples:
        - "inductive hypothesis" → "\\mbox{inductive hypothesis}"
        - "\\land intro" → "\\land \\mbox{intro}"
        - "strong IH, a < n" → "\\mbox{strong IH}, a < n"
        """
        # Pattern: Match sequences of words (with spaces between them)
        # that are NOT LaTeX commands (not preceded by \)
        # A "text segment" is: word (optional: space + word)*
        # where word = [a-zA-Z_][a-zA-Z0-9_]*
        #
        # We need to be careful not to match:
        # - LaTeX commands like \land, \mbox{}, etc.
        # - Single letters that are math variables (like a, b, n)
        # - Numbers that are math
        #
        # Strategy: Find word sequences of 2+ words OR single words that are
        # clearly text (not single letters, not LaTeX commands)

        # First, handle multi-word sequences (these are definitely text)
        # Pattern: word + (space + word)+  (2 or more words with spaces)
        # Use lookbehind to exclude matches inside LaTeX commands like \lor
        # (?<![a-zA-Z\\]) ensures we don't start inside a command or word
        word = r"[a-zA-Z_][a-zA-Z0-9_]*"
        multi_word_pattern = rf"(?<![a-zA-Z\\])({word}(?:\s+{word})+)"

        def wrap_multi(m: re.Match[str]) -> str:
            return f"\\mbox{{{m.group(1)}}}"

        text = re.sub(multi_word_pattern, wrap_multi, text)

        # Then handle known single-word text that should be wrapped
        # (rule names, common justification words)
        text_words = [
            "elim",
            "intro",
            "assumption",
            "premise",
            "from",
            "case",
            "contradiction",
            "middle",
            "excluded",
            "false",
            "definition",
            "substitution",
            "arithmetic",
            "algebra",
            "factoring",
            "equality",
            "trivial",
            "singleton",
            "factorization",
            "construction",
            "verification",
            "dichotomy",
            "known",
            "identity",
            "simplification",
            "logic",
            "previous",
            "line",
            "proof",
            "steps",
            "separately",
            "proved",
            "inductive",
            "step",
            "minimality",
            "well",
            "ordering",
            "principle",
            "choice",
            "axiom",
            "lemma",
            "direct",
            "negation",
            "trichotomy",
            "integers",
            "multiplication",
            "factorizations",
            "composite",
            "hypothesis",
            "diagonal",
            "method",
            "differs",
            "digit",
            "countable",
            "enumeration",
            "preservation",
            "terminates",
            "termination",
            "condition",
            "invariant",
            "exponent",
            "law",
        ]

        for word in text_words:
            # Only wrap if not already in \mbox{} and not a LaTeX command
            pattern = rf"(?<!\\)(?<!\{{)\b{word}\b(?!\}})"
            text = re.sub(pattern, rf"\\mbox{{{word}}}", text)

        return text
