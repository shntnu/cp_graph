# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `--filter-objects` flag to filter unused objects along with images (PR #1 by @gnodar01)
- `--no-single-parent` flag to allow multiple parents for data nodes
- Support for additional CellProfiler setting types:
  - CropImageSubscriber, CropImageName for crop module connections
  - FileImageSubscriber, FileImageName for file-based images
  - OutlineImageSubscriber, OutlineImageName for outline images
  - ExternalImageName for external image references
- ExampleFly.json pipeline demonstrating crop modules and object filtering
- Pre-commit hooks for code quality (ruff, trailing whitespace, file endings)

### Fixed
- Crop modules now properly show as parents of their output images
- NamesAndTypes correctly shown as parent of OrigX images
- Resolved multiple parent issues where deactivated settings created phantom connections
- `filter_multiple_parents` API consistency - now returns (graph, edges_affected) tuple
- `filter_multiple_parents` now supports highlight_filtered mode
- Fixed typo: changed 'quit' to 'quiet' in filter output messages

### Changed
- **BREAKING**: Switched from `uv run --script` to Pixi shebang for dependency management
  - Script is now directly executable: `./cp_graph.py` instead of `uv run --script cp_graph.py`
  - GraphViz is automatically provided by Pixi (no separate installation needed)
- Enhanced edge tracking and reporting for duplicate parent filtering
- Improved visual feedback when highlighting filtered edges (dashed red lines)

## [0.10.0] - 2025-04-13

### Added
- Core graph generation from CellProfiler v6 JSON pipelines
- Stable module identification using SHA-256 hashing for consistent comparisons
- Unified data node representation (single node per data item regardless of usage)
- Multiple output formats: DOT (Graphviz), GraphML, GEXF
- Command-line interface using Click

### Features
- **Filtering Options:**
  - `--root-nodes` to focus on paths from specific inputs
  - `--remove-unused-data` to eliminate unused image nodes
  - `--exclude-module-types` to skip specific module types
  - `--include-disabled` to show disabled modules
  - `--highlight-filtered` to visualize filters without removing nodes

- **Visualization Options:**
  - `--rank-nodes` for top-to-bottom layout (sources at top, sinks at bottom)
  - `--rank-ignore-filtered` to exclude filtered nodes from ranking
  - `--no-formatting` to strip visual styling
  - `--ultra-minimal` for exact structural comparison
  - `--explain-ids` to show stable ID mappings

- **Visual Styling:**
  - Gray ovals for images
  - Green ovals for objects
  - Blue boxes for enabled modules
  - Pink boxes for disabled modules
  - Yellow/salmon with dashed borders for filtered nodes

### Technical Foundation
- Deterministic graph ordering for reliable comparisons
- Edge type preservation for connection semantics
- Support for image lists and object lists
- Robust handling of node IDs with special characters
- PEP 723 inline dependency metadata for UV compatibility
