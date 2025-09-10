#!/usr/bin/env python3
"""
Test script for cp_graph.py
Runs the same commands as regenerate_all_examples.sh and verifies outputs match.
"""

import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
import filecmp

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
YELLOW = "\033[93m"


def run_test(name, command, expected_output):
    """Run a single test command and compare output."""
    # Create temp file for output
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".dot", delete=False
    ) as temp_file:
        temp_output = temp_file.name

    try:
        # Replace output path in command with temp path
        test_command = command.replace(str(expected_output), temp_output)

        # Run the command
        result = subprocess.run(
            test_command, shell=True, capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"{RED}✗ {name}: Command failed{RESET}")
            print(f"  Command: {test_command}")
            print(f"  Error: {result.stderr}")
            return False

        # Compare files
        if not Path(expected_output).exists():
            print(f"{YELLOW}⚠ {name}: Expected output not found, creating it{RESET}")
            shutil.copy(temp_output, expected_output)
            return True

        if filecmp.cmp(temp_output, expected_output, shallow=False):
            print(f"{GREEN}✓ {name}{RESET}")
            return True
        else:
            print(f"{RED}✗ {name}: Output differs from expected{RESET}")
            print(f"  Expected: {expected_output}")
            print(f"  Got: {temp_output}")

            # Show diff command for debugging
            print(f"  Run to see differences: diff {expected_output} {temp_output}")

            # Keep temp file for debugging
            debug_file = f"test_output_{Path(expected_output).name}"
            shutil.copy(temp_output, debug_file)
            print(f"  Test output saved to: {debug_file}")

            return False

    finally:
        # Clean up temp file if test passed
        if Path(temp_output).exists() and filecmp.cmp(
            temp_output, expected_output, shallow=False
        ):
            Path(temp_output).unlink()


def main():
    """Run all tests."""
    print("Running cp_graph.py tests...")
    print("=" * 60)

    # Define all test cases (command, expected output file)
    tests = [
        # Basic Examples (illum pipeline)
        (
            "Basic illum graph",
            "./cp_graph.py examples/illum.json examples/output/illum.dot",
            Path("examples/output/illum.dot"),
        ),
        (
            "Illum with highlight filtering",
            "./cp_graph.py examples/illum.json examples/output/illum_highlight.dot --root-nodes=OrigDNA --remove-unused-images --highlight-filtered",
            Path("examples/output/illum_highlight.dot"),
        ),
        (
            "Illum filtered (nodes removed)",
            "./cp_graph.py examples/illum.json examples/output/illum_filtered.dot --root-nodes=OrigDNA --remove-unused-images",
            Path("examples/output/illum_filtered.dot"),
        ),
        (
            "Illum ultra-minimal",
            "./cp_graph.py examples/illum.json examples/output/illum_ultra.dot --ultra-minimal",
            Path("examples/output/illum_ultra.dot"),
        ),
        (
            "Illum isoform ultra-minimal",
            "./cp_graph.py examples/illum_isoform.json examples/output/illum_isoform_ultra.dot --ultra-minimal",
            Path("examples/output/illum_isoform_ultra.dot"),
        ),
        (
            "Illum modified ultra-minimal",
            "./cp_graph.py examples/illum_mod.json examples/output/illum_mod_ultra.dot --ultra-minimal",
            Path("examples/output/illum_mod_ultra.dot"),
        ),
        # Complex Analysis Pipeline
        (
            "Basic analysis graph",
            "./cp_graph.py examples/analysis.json examples/output/analysis.dot",
            Path("examples/output/analysis.dot"),
        ),
        (
            "Analysis filtered (complex)",
            "./cp_graph.py examples/analysis.json examples/output/analysis_filtered.dot --rank-nodes --remove-unused-images --exclude-module-types=ExportToSpreadsheet --highlight-filtered --rank-ignore-filtered --root-nodes=CorrPhalloidin,CorrZO1,CorrDNA,Cycle01_DAPI,Cycle01_A,Cycle01_T,Cycle01_G,Cycle01_C,Cycle02_DAPI,Cycle02_A,Cycle02_T,Cycle02_G,Cycle02_C,Cycle03_DAPI,Cycle03_A,Cycle03_T,Cycle03_G,Cycle03_C",
            Path("examples/output/analysis_filtered.dot"),
        ),
        # CellProfiler 5 Dependency Graphs
        (
            "ExampleFly basic",
            "./cp_graph.py examples/ExampleFly.json examples/output/ExampleFly.dot --highlight-filtered --rank-nodes --remove-unused-objects --remove-unused-images",
            Path("examples/output/ExampleFly.dot"),
        ),
        (
            "ExampleFly with measurements",
            "./cp_graph.py --remove-unused-objects --remove-unused-measurements --dependency-graph examples/ExampleFly-dep-graph.json examples/output/ExampleFly-measurement.dot",
            Path("examples/output/ExampleFly-measurement.dot"),
        ),
        (
            "ExampleFly with measurements and liveness styling",
            "./cp_graph.py --dependency-graph --remove-unused-measurements --track-liveness --rank-nodes examples/ExampleFlyMeas-liveness-dep.json examples/output/ExampleFly-liveness.dot",
            Path("examples/output/ExampleFly-liveness.dot"),
        )
    ]

    # Track results
    passed = 0
    failed = 0

    # Run each test
    for test_name, command, expected_output in tests:
        if run_test(test_name, command, expected_output):
            passed += 1
        else:
            failed += 1

    # Print summary
    print("=" * 60)
    total = passed + failed
    if failed == 0:
        print(f"{GREEN}All {total} tests passed!{RESET}")
        return 0
    else:
        print(f"{RED}{failed} of {total} tests failed{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
