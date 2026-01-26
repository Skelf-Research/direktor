"""
CLI interface for Direktor.
"""

import argparse
import os
import sys

from dotenv import load_dotenv

from direktor.core.pipeline import main as direktor_main


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate a video from text input.",
        prog="direktor",
    )
    parser.add_argument("input_file", help="Path to the input text file")
    parser.add_argument(
        "--stage",
        type=int,
        choices=range(1, 7),
        default=6,
        help="Stage to run up to (1-6). Default: 6 (complete pipeline)",
    )

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist.")
        sys.exit(1)

    # Load environment variables
    load_dotenv()

    # Run the main function
    direktor_main(args.input_file, args.stage)


if __name__ == "__main__":
    main()
