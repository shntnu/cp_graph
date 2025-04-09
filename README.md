# CellProfiler Pipeline Graph Analysis Tool

This tool converts CellProfiler pipelines into standardized graph representations to analyze data flow between modules. It enables precise comparison of pipeline structures while deliberately excluding module settings. The tool tracks multiple data types (images, objects, lists) and creates consistent, comparable representations optimized for detecting structural changes between pipeline versions.

## Core Functionality

- **Pipeline Comparison**: Generate consistent graph representations to detect functional differences between pipelines
- **Multi-type Data Flow**: Track images, objects, and list inputs through the pipeline
- **Computational Analysis**: Convert pipeline structure to standard graph formats for programmatic analysis
- **Standardized Output**: Create canonical representations that ignore irrelevant differences (like module reordering)
- **Visualization**: View pipeline structure as a directed graph with color coding for different data types

## Usage

```bash
# Run with regular Python
python cp_graph.py <pipeline.json> <output_file> [options]

# Run with UV to automatically install dependencies (recommended)
uv run --script cp_graph.py <pipeline.json> <output_file> [options]
```

- `pipeline.json` - Your CellProfiler pipeline file (v6 JSON format)
- `output_file` - Output file path (supports .graphml, .gexf, or .dot formats)

Options:

**Display Options:**
- `--no-formatting` - Strip all formatting information to focus on topology for comparison
- `--no-module-info` - Hide module information on graph edges
- `--ultra-minimal` - Create minimal output with only essential structure for exact diff comparison
- `--explain-ids` - Print mapping of stable node IDs to original module numbers

**Content Filtering Options:**
- `--include-disabled` - Include disabled modules in the graph (excluded by default)

**Data Type Options:** (mutually exclusive)
- `--images-only` - Include only image flow in the graph (default: include all types)
- `--objects-only` - Include only object flow in the graph (default: include all types)
- `--no-lists` - Exclude list inputs in the graph (default: include all types)

## Pipeline Comparison

### Scope and Limitations

This tool is designed to analyze and compare:
- Which modules exist in the pipeline
- How data (images, objects, lists) flows between modules
- The topological structure of data processing

It deliberately excludes:
- Specific module parameter settings
- Measurement outputs and CSV data
- Module internal processing logic

These limitations are intentional to keep the graph focused on overall pipeline structure and data flow patterns. You can further refine the scope using the data type filtering options to focus on specific aspects of the pipeline.

### How Graph Standardization Works

1. **Stable Module Identifiers**:
   - Data nodes use their actual names with type prefixes (e.g., "image__OrigDNA", "object__Nuclei")
   - Module nodes use a hash-based identifier that combines:
     - Module type (e.g., "Resize")
     - Alphabetically sorted list of all inputs with their types
     - Alphabetically sorted list of all outputs with their types
   - This ensures the same module gets the same identifier regardless of pipeline ordering
   - Original module numbers are maintained in node labels for reference

2. **Consistent Serialization**:
   - Nodes are sorted lexicographically when writing files
   - Edges are sorted by source node first, then destination node
   - This creates identical file content for functionally equivalent pipelines

3. **Technical Implementation**:
   - Extracts multiple data types:
     - Images: `ImageSubscriber` (input) and `ImageName` (output)
     - Objects: `LabelSubscriber` (input) and `LabelName` (output)
     - Lists: `ImageListSubscriber` and `LabelListSubscriber` (inputs)
   - Creates distinct nodes for each data type with appropriate visual styling
   - Provides the `--explain-ids` option to show mapping between stable IDs and original numbers

### Comparison Capabilities

This approach makes it possible to:

1. Compare two pipeline versions using simple file diff tools
2. Detect real functional changes vs. just module reordering
3. Create canonical representations of pipeline structure

```bash
# Generate stripped-down topology representations for comparison
python cp_graph.py examples/illum.json examples/output/illum.dot --no-formatting
python cp_graph.py examples/illum_isoform.json examples/output/illum_isoform.dot --no-formatting

# Compare using standard diff tools
diff examples/output/illum.dot examples/output/illum_isoform.dot
```

## Additional Features

### Handling Disabled Modules

By default, the tool ignores modules with `enabled: false` in their attributes. Use the `--include-disabled` flag to include these modules in your graph (shown with pink background and dashed borders).

### Example Files & Commands

The repository is structured with:
- `examples/` - Sample CellProfiler pipeline files:
  - `illum.json` and `illum_isoform.json` - Structurally identical pipelines with different module numbering
  - `analysis.json` - More complex pipeline demonstrating various data types
  - `ref_*.json` - Additional reference pipeline examples
- `examples/output/` - Pre-generated graph outputs for reference

Below are example commands showing common usage patterns:

```bash
# Basic comparison-ready output
python cp_graph.py examples/illum.json examples/output/illum_graph.dot --no-formatting

# Include disabled modules
python cp_graph.py examples/illum.json examples/output/illum_graph.dot --include-disabled

# Show stable module ID mapping
python cp_graph.py examples/illum.json examples/output/illum_graph.dot --explain-ids

# Track specific data types
python cp_graph.py examples/analysis.json examples/output/objects_only.dot --objects-only
python cp_graph.py examples/analysis.json examples/output/images_only.dot --images-only
python cp_graph.py examples/analysis.json examples/output/no_lists.dot --no-lists

# Generate visualizations for the different data type views
dot -Tpng examples/output/objects_only.dot -o examples/output/objects_only.png
dot -Tpng examples/output/images_only.dot -o examples/output/images_only.png
dot -Tpng examples/output/no_lists.dot -o examples/output/no_lists.png

# Exact byte-for-byte comparison of structurally identical pipelines
python cp_graph.py examples/illum.json examples/output/illum_ultra.dot --ultra-minimal
python cp_graph.py examples/illum_isoform.json examples/output/illum_isoform_ultra.dot --ultra-minimal
diff examples/output/illum_ultra.dot examples/output/illum_isoform_ultra.dot # Should produce no output if identical
```

## Visualization (Secondary Feature)

While the primary purpose is computational analysis and comparison, the tool also supports visualization:

### Data Type Filtering Views

The same pipeline can be viewed with different data type filters to focus on specific aspects:

**Objects Only View** (--objects-only):
![Objects Only](examples/output/analysis_objects.png)

**Images Only View** (--images-only):
![Images Only](examples/output/analysis_images.png)

**No Lists View** (--no-lists):
![No Lists](examples/output/analysis_no_lists.png)

### Visual Styling

The graph visually represents different elements:

- **Images**: Gray ovals
- **Objects**: Green ovals
- **Image Lists**: Yellow rounded rectangles
- **Object Lists**: Cyan rounded rectangles
- **Processing Modules**: Blue boxes with the module name and number
- **Disabled Modules**: Pink boxes with dashed borders (when included)
- **Connections**: Arrows showing the flow between data nodes and modules

### Rendering the Graph

If you have Graphviz installed, you can render a DOT file to an image:

```bash
dot -Tpng examples/output/illum_graph.dot -o examples/output/illum_graph.png
```

![image](examples/output/illum_graph.png)

The generated files can also be opened with:
- GraphML (.graphml): yEd, Cytoscape, or other graph visualization software
- GEXF (.gexf): Gephi
- DOT (.dot): Graphviz, OmniGraffle

## Requirements

- Python 3.x
- NetworkX library
- PyDot (optional, for DOT output)

Install dependencies with:

```bash
pip install networkx pydot
```