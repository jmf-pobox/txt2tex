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
        description="Convert whiteboard-style mathematical notation to LaTeX"
    )
    parser.add_argument("input", help="Input text (expression or file path)")
    parser.add_argument(
        "-o", "--output", help="Output file (default: stdout)", type=Path
    )
    parser.add_argument(
        "--fuzz",
        action="store_true",
        help="Use fuzz package instead of zed-* packages",
    )
    parser.add_argument(
        "-e",
        "--expr",
        action="store_true",
        help="Treat input as expression (not file)",
    )

    args = parser.parse_args()

    # Read input
    if args.expr:
        text = args.input
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: File not found: {input_path}", file=sys.stderr)
            return 1
        text = input_path.read_text()

    # Process
    try:
        # Lex
        lexer = Lexer(text)
        tokens = lexer.tokenize()

        # Parse
        parser_obj = Parser(tokens)
        ast = parser_obj.parse()

        # Generate LaTeX
        generator = LaTeXGenerator(use_fuzz=args.fuzz)
        latex = generator.generate_document(ast)

        # Output
        if args.output:
            args.output.write_text(latex)
            print(f"Generated: {args.output}")
        else:
            print(latex)

        return 0

    except (LexerError, ParserError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
