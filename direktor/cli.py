"""
CLI interface for Direktor.
"""
import argparse
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to sys.path to import core modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from direktor.core.main import main as direktor_main

def main():
    parser = argparse.ArgumentParser(description="Generate a video from text input.")
    parser.add_argument("input_file", help="Path to the input text file")
    parser.add_argument("--stage", type=int, choices=range(1, 7), default=6, 
                        help="Stage to start from (1-6)")
    
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