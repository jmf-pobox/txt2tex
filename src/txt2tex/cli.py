"""Command-line interface for txt2tex."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer
from txt2tex.parser import Parser


def main() -> int:
    """Main entry point for txt2tex CLI."""
    parser = argparse.ArgumentParser(
        description="Convert whiteboard notation to LaTeX",
        prog="txt2tex",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input text file with whiteboard notation",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output LaTeX file (default: input with .tex extension)",
    )
    parser.add_argument(
        "--fuzz",
        action="store_true",
        help="Use fuzz package instead of zed-* packages",
    )
    parser.add_argument(
        "--toc-parts",
        action="store_true",
        help="Include parts (a, b, c) in table of contents",
    )

    args = parser.parse_args()

    # Read input
    try:
        text = args.input.read_text()
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        return 1

    # Process
    try:
        lexer = Lexer(text)
        tokens = lexer.tokenize()

        parser_obj = Parser(tokens)
        ast = parser_obj.parse()

        generator = LaTeXGenerator(use_fuzz=args.fuzz, toc_parts=args.toc_parts)
        latex = generator.generate_document(ast)
    except Exception as e:
        print(f"Error processing input: {e}", file=sys.stderr)
        return 1

    # Write output
    output_path = args.output or args.input.with_suffix(".tex")
    try:
        output_path.write_text(latex)
        print(f"Generated: {output_path}")
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
