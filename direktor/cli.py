"""
CLI interface for Direktor.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from dotenv import load_dotenv

from direktor import __version__
from direktor.core.logger import configure_logging
from direktor.core.pipeline import PipelineResult
from direktor.core.pipeline import main as run_pipeline


def _parse_keywords_file(path: str | None) -> list[tuple[str, float, float]] | None:
    """Load keyword overlays from a JSON file.

    The JSON file should contain a list of ``[keyword, start, end]`` entries.
    """
    if path is None:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [(str(item[0]), float(item[1]), float(item[2])) for item in data]


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate a podcast-style video from a text input.",
        prog="direktor",
    )
    parser.add_argument(
        "input_file",
        help="Path to the input text file",
    )
    parser.add_argument(
        "--stage",
        type=int,
        choices=range(1, 7),
        default=6,
        help="Stage to run up to (1-6). Default: 6 (complete pipeline)",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_dir",
        help="Directory for the final output.mp4. Defaults to the working temp dir.",
    )
    parser.add_argument(
        "--temp-dir",
        help="Temporary working directory. Defaults to temp/<input-hash>.",
    )
    parser.add_argument(
        "--keywords-file",
        help="JSON file containing keyword overlays as [[keyword, start, end], ...].",
    )
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Skip stages whose output files already exist. Default: True",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove the temporary working directory before starting.",
    )
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Skip the narrative content optimization step.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the version and exit.",
    )
    return parser


def _print_progress(message: str, stage: int) -> None:
    """Print a simple progress message to the terminal."""
    print(f"Stage {stage}: {message}")


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entry point.

    Args:
        argv: Optional argument list. Defaults to ``sys.argv[1:]``.

    Returns:
        Exit code (0 on success, 1 on failure).
    """
    load_dotenv()

    parser = _build_parser()
    args = parser.parse_args(argv)

    log_level = "DEBUG" if args.verbose else "INFO"
    configure_logging(log_level)

    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist.", file=sys.stderr)
        return 1

    keywords = _parse_keywords_file(args.keywords_file)

    result: PipelineResult = run_pipeline(
        args.input_file,
        stage=args.stage,
        keywords=keywords,
        output_dir=args.output_dir,
        temp_dir=args.temp_dir,
        clean=args.clean,
        resume=args.resume,
        optimize=not args.no_optimize,
        progress_callback=_print_progress,
    )

    if result.error:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1

    if result.output_file:
        print(f"Video created: {result.output_file}")
    else:
        print(f"Pipeline completed through stage {args.stage}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
