# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. Read @README.md for more information.

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
- Run tool: `./cp_graph.py <pipeline.json> [output_graph.graphml] [options]`
- Run tests: `python test_cp_graph.py`
- Visualization: `dot -Tpng <output_file>.dot -o <output_file>.png`
- Note: The tool uses a pixi shebang to automatically provide all dependencies including GraphViz

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

## Implementation Notes

### Module Identification
Modules use stable SHA-256 hash-based IDs combining module type and I/O pattern:
- Format: `ModuleType_8hexchars` (e.g., `SaveImages_46180921`)
- Ensures consistent IDs across pipeline reorderings
- Hash input: sorted inputs + sorted outputs

### Data Node Unification
Each data item (image/object) has a single node regardless of usage:
- Node ID format: `type__name` (e.g., `image__DNA`, `object__Cells`)
- Edge types preserve connection semantics (regular vs list inputs)
- List inputs normalized to base type for node creation

### Graph Filtering Philosophy
Filters can remove or highlight nodes/edges:
- All filter functions return `(filtered_graph, count_affected)`
- Highlight mode preserves structure while marking filtered elements
- Single parent enforcement keeps highest module_num as parent (last producer wins)
