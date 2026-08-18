#!/usr/bin/env python3
import sys
import os
import subprocess
import argparse
import shutil

def run_mace4(input_file, start_size=1, end_size=10, timeout=30):
    # 1. Check if Mace4 executable exists on the system
    if not shutil.which("mace4"):
        print("Error: 'mace4' executable was not found in your system PATH.")
        print("Make sure Prover9/Mace4 is installed and added to your environment variables.")
        sys.exit(1)

    # 2. Check if the input file exists using absolute path to avoid directory confusion
    abs_input_path = os.path.abspath(input_file)
    if not os.path.isfile(abs_input_path):
        print(f"Error: Input file does not exist at path:\n  {abs_input_path}")
        print(f"\nCurrent Working Directory is:\n  {os.getcwd()}")
        sys.exit(1)

    # Command to run Mace4 with domain sizes
    cmd = [
        "mace4",
        "-n", str(start_size),
        "-N", str(end_size)
    ]

    print(f"Running Mace4 on '{abs_input_path}' (Domain sizes: {start_size} to {end_size})...")

    try:
        # Open the input file and pipe it into Mace4's standard input
        with open(abs_input_path, "r") as infile:
            result = subprocess.run(
                cmd,
                stdin=infile,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )

        output = result.stdout

        # Check output for counterexamples
        if "Model" in output or "interpretation" in output or "=== MODEL ===" in output:
            print("\n================ Counterexample Found ================\n")
            print(output)
        else:
            print("No counterexample found within the specified domain sizes.")
            if result.stderr:
                print("Mace4 stderr:\n", result.stderr)

    except subprocess.TimeoutExpired:
        print(f"Error: Mace4 timed out after {timeout} seconds.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Generate counterexamples using Mace4.")
    parser.add_argument("input_file", help="Path to the input file (.in)")
    parser.add_argument("-n", "--start", type=int, default=1, help="Starting domain size")
    parser.add_argument("-N", "--end", type=int, default=10, help="Ending domain size")
    parser.add_argument("-t", "--timeout", type=int, default=30, help="Timeout in seconds")

    args = parser.parse_args()
    run_mace4(args.input_file, args.start, args.end, args.timeout)

if __name__ == "__main__":
    main()