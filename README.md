# CellProfiler Pipeline Graph Analysis Tool

This tool converts CellProfiler pipelines into standardized graph representations, focusing exclusively on image flow between modules. It enables precise comparison of pipeline image processing structures while deliberately excluding module settings and non-image outputs. By extracting only image dependencies from JSON pipeline files, it creates consistent, comparable representations optimized for detecting structural changes between pipeline versions.

## Core Functionality

- **Pipeline Comparison**: Generate consistent graph representations to detect functional differences between pipelines
- **Computational Analysis**: Convert pipeline structure to standard graph formats for programmatic analysis
- **Standardized Output**: Create canonical representations that ignore irrelevant differences (like module reordering)
- **Visualization**: View pipeline structure as a directed graph (a useful side benefit)

## Usage

```bash
python cp_graph.py <pipeline.json> [output_graph.graphml] [options]
```

- `pipeline.json` - Your CellProfiler pipeline file (v6 JSON format)
- `output_graph.graphml` - Optional output file (supports .graphml, .gexf, or .dot formats)

Options:
- `--no-formatting` - Strip all formatting information to focus on topology for comparison
- `--no-module-info` - Hide module information on graph edges
- `--include-disabled` - Include disabled modules in the graph (excluded by default)
- `--explain-ids` - Print mapping of stable node IDs to original module numbers

## Pipeline Comparison

### Scope and Limitations

This tool is intentionally narrowly scoped to analyze and compare:
- Which modules exist in the pipeline
- How images flow between modules
- The topological structure of image processing

It deliberately excludes:
- Specific module parameter settings
- Non-image data (objects, measurements, CSV outputs)
- Module internal processing logic

These limitations are intentional to keep the graph focused on overall pipeline structure and image flow patterns.

### How Graph Standardization Works

1. **Stable Module Identifiers**:
   - Image nodes use their actual names from the pipeline (e.g., "OrigDNA")
   - Module nodes use a hash-based identifier that combines:
     - Module type (e.g., "Resize")
     - Alphabetically sorted list of input images
     - Alphabetically sorted list of output images
   - This ensures the same module gets the same identifier regardless of pipeline ordering
   - Original module numbers are maintained in node labels for reference

2. **Consistent Serialization**:
   - Nodes are sorted lexicographically when writing files
   - Edges are sorted by source node first, then destination node
   - This creates identical file content for functionally equivalent pipelines

3. **Technical Implementation**:
   - Extracts only input images (`ImageSubscriber`) and output images (`ImageName`)
   - Creates nodes for images and modules with their connections
   - Provides the `--explain-ids` option to show mapping between stable IDs and original numbers

### Comparison Capabilities

This approach makes it possible to:

1. Compare two pipeline versions using simple file diff tools
2. Detect real functional changes vs. just module reordering
3. Create canonical representations of pipeline structure

```bash
# Generate stripped-down topology representations for two pipelines
python cp_graph.py pipeline1.json pipeline1.dot --no-formatting
python cp_graph.py pipeline2.json pipeline2.dot --no-formatting

# Compare using standard diff tools
diff pipeline1.dot pipeline2.dot
```

## Additional Features

### Handling Disabled Modules

By default, the tool ignores modules with `enabled: false` in their attributes. Use the `--include-disabled` flag to include these modules in your graph (shown with pink background and dashed borders).

### Example Commands

```bash
# Basic comparison-ready output
python cp_graph.py 1_CP_Illum.json 1_CP_Illum_graph.dot --no-formatting

# Include disabled modules
python cp_graph.py 1_CP_Illum.json 1_CP_Illum_graph.dot --include-disabled

# Show stable module ID mapping
python cp_graph.py 1_CP_Illum.json 1_CP_Illum_graph.dot --explain-ids
```

## Visualization (Secondary Feature)

While the primary purpose is computational analysis and comparison, the tool also supports visualization:

### Visual Styling

The graph visually represents different elements:

- **Images**: Gray ovals 
- **Processing Modules**: Blue boxes with the module name and number
- **Disabled Modules**: Pink boxes with dashed borders (when included)
- **Connections**: Arrows showing the flow between images and modules

### Rendering the Graph

If you have Graphviz installed, you can render a DOT file to an image:

```bash
dot -Tpng 1_CP_Illum_graph.dot -o 1_CP_Illum_graph.png
```

![image](1_CP_Illum_graph.png)

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