# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Run Commands
- Run script: `python cp_graph.py <pipeline.json> [output_graph.graphml]`
- Run with options: `python cp_graph.py <pipeline.json> [output] --no-module-info --include-disabled --no-formatting`
- Generate image from DOT: `dot -Tpng <file>.dot -o <file>.png`
- Install dependencies: `pip install networkx pydot`

### Command Line Options
- `--no-formatting`: Strip all formatting information to focus on topology for comparison
- `--no-module-info`: Hide module information on graph edges
- `--include-disabled`: Include disabled modules in the graph
- `--explain-ids`: Print mapping of stable node IDs to original module numbers

### Tool Purpose & Scope
- Primary purpose: Standardized graph representation for comparing pipeline structures
- Focus: Image flow analysis only (module parameter settings and non-image outputs are excluded)
- Visualization is a secondary feature; the primary goal is to create consistent, comparable graph representations

## Code Style Guidelines
- Python 3.11+ compatibility
- Use PEP 8 formatting conventions
- Imports: standard library first, then third-party, then local modules
- Use type hints where appropriate
- Variables: snake_case for variables and functions
- Constants: UPPER_CASE
- Handle errors with try/except blocks when appropriate (see pydot import handling)
- Use f-strings for string formatting
- Use Path objects from pathlib for file operations
- Include docstrings for functions explaining purpose and parameters
- Keep functions focused on a single responsibility