# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This tool converts CellProfiler pipelines into standardized graph representations to analyze data flow between modules. It enables precise comparison of pipeline structures while deliberately excluding module settings. The tool tracks multiple data types (images, objects, lists) using a unified representation optimized for detecting structural changes between pipeline versions.

### Core Purpose

The primary purpose of this tool is to provide a standardized way to represent and compare pipeline structures. It allows users to:
- Generate consistent graph representations that ignore irrelevant differences (like module reordering)
- Detect meaningful structural changes between pipeline versions
- Track data flow through complex pipelines with multiple data types
- Convert pipeline structure to standard graph formats for programmatic analysis
- Visualize pipeline structure as a directed graph with intuitive color coding for different data types

## Commands
- Run tool: `python cp_graph.py <pipeline.json> [output_graph.graphml] [options]`
- Alternative with UV: `uv run --script cp_graph.py <pipeline.json> [output_graph.graphml] [options]`
- Visualization: `dot -Tpng <output_file>.dot -o <output_file>.png`

### Common Options
- `--highlight-filtered`: Highlight nodes that would be filtered instead of removing them (uses yellow/salmon coloring with dashed borders)
- `--root-nodes=<name1,name2>`: Filter to only keep paths from specified root nodes
- `--remove-unused-data`: Remove or highlight image nodes not used as inputs
- `--include-disabled`: Include disabled modules in the graph
- `--exclude-module-types=<type1,type2>`: Exclude specific module types from the graph

## Code Style
- Python 3.11+ with type annotations
- Use NetworkX for graph operations
- Consistent 4-space indentation 
- Descriptive variable names (snake_case for variables/functions)
- DocStrings for functions explaining purpose and parameters
- Maintain backwards compatibility with existing CellProfiler JSON structures
- Functions should handle one specific task, modularizing when possible
- Preserve the standardized representation approach for consistent graph output
- Maintain color conventions for different data types (images in gray, objects in green, modules in blue, filtered nodes in salmon/yellow with dashed borders)
- Follow the unified data node representation pattern (single node per data item)
- Preserve the stable module identification system using SHA-256 hashing
- Respect the established node and edge typing system with clear type prefixes (image__, object__)
- Maintain deterministic node and edge ordering in graph outputs
- Use TypedDict for structured data representation
- Use Path library for handling file paths
- Follow the established CLI pattern using Click for command-line options
- Use consistent error handling patterns with appropriate exceptions and messages