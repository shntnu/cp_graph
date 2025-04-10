# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run tool: `python cp_graph.py <pipeline.json> [output_graph.graphml] [options]`
- Alternative with UV: `uv run --script cp_graph.py <pipeline.json> [output_graph.graphml] [options]`
- Visualization: `dot -Tpng <output_file>.dot -o <output_file>.png`

## Code Style
- Python 3.11+ with type annotations
- Use NetworkX for graph operations
- Consistent 4-space indentation 
- Descriptive variable names (snake_case for variables/functions)
- DocStrings for functions explaining purpose and parameters
- Maintain backwards compatibility with existing CellProfiler JSON structures
- Functions should handle one specific task, modularizing when possible
- Preserve the standardized representation approach for consistent graph output
- Maintain color conventions for different data types (images, objects)