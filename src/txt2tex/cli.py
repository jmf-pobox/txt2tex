"""Command-line interface for txt2tex."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from txt2tex.latex_gen import LaTeXGenerator
from txt2tex.lexer import Lexer, LexerError
from txt2tex.parser import Parser, ParserError


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
        "--zed",
        action="store_true",
        help="Use zed-* packages instead of fuzz package (fuzz is default)",
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
    except FileNotFoundError:
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        return 1
    except PermissionError:
        print(f"Error: Permission denied reading: {args.input}", file=sys.stderr)
        return 1
    except IsADirectoryError:
        print(f"Error: Expected a file, got a directory: {args.input}", file=sys.stderr)
        return 1
    except UnicodeDecodeError as e:
        print(f"Error: File encoding issue: {e}", file=sys.stderr)
        return 1

    # Process
    try:
        lexer = Lexer(text)
        tokens = lexer.tokenize()

        parser_obj = Parser(tokens)
        ast = parser_obj.parse()

        generator = LaTeXGenerator(use_fuzz=not args.zed, toc_parts=args.toc_parts)
        latex = generator.generate_document(ast)
    except LexerError as e:
        print(f"Error processing input: {e}", file=sys.stderr)
        return 1
    except ParserError as e:
        print(f"Error processing input: {e}", file=sys.stderr)
        return 1

    # Write output
    output_path = args.output or args.input.with_suffix(".tex")
    try:
        output_path.write_text(latex)
        print(f"Generated: {output_path}")
    except PermissionError:
        print(f"Error: Permission denied writing: {output_path}", file=sys.stderr)
        return 1
    except IsADirectoryError:
        print(f"Error: Cannot write to directory: {output_path}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
