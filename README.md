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

**Data Type Options:**
- `--data-type [all|images_only|objects_only|no_lists]` - Filter by data type (default: all)

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

### Detection of Structural Equivalence and Differences

The tool excels at two critical comparison tasks:

1. **Confirming Structural Equivalence** 

   When comparing `illum.json` with `illum_isoform.json` (identical structure but different module numbering):
   
   ```bash
   python cp_graph.py examples/illum.json examples/output/illum_ultra.dot --ultra-minimal
   python cp_graph.py examples/illum_isoform.json examples/output/illum_isoform_ultra.dot --ultra-minimal
   diff examples/output/illum_ultra.dot examples/output/illum_isoform_ultra.dot
   ```
   
   This produces no output, confirming the two pipelines are structurally identical despite their different module numbering.

2. **Detecting Real Functional Differences**

   When comparing `illum.json` with `illum_mod.json` (where a SaveImages module is disabled):
   
   ```bash
   python cp_graph.py examples/illum.json examples/output/illum_ultra.dot --ultra-minimal
   python cp_graph.py examples/illum_mod.json examples/output/illum_mod_ultra.dot --ultra-minimal
   diff examples/output/illum_ultra.dot examples/output/illum_mod_ultra.dot
   ```
   
   This reveals the actual structural differences:
   
   ```diff
   12d11
   < SaveImages_46180921 [type=module];
   54d52
   < image__UpsampledIllumZO1 -> SaveImages_46180921;
   ```
   
   This clearly shows the missing SaveImages module and its connection, despite all visual noise from module numbering being removed.


## Additional Features

### Handling Disabled Modules

By default, the tool ignores modules with `enabled: false` in their attributes. Use the `--include-disabled` flag to include these modules in your graph (shown with pink background and dashed borders).

### Example Files & Commands

The repository is structured with:
- `examples/` - Sample CellProfiler pipeline files:
  - `illum.json` - Basic illumination correction pipeline
  - `illum_isoform.json` - Structurally identical to `illum.json` but with different module numbering
  - `illum_mod.json` - Modified illumination pipeline with a disabled SaveImages module
  - `analysis.json` - More complex pipeline demonstrating various data types
- `examples/output/` - Pre-generated graph outputs for reference

Below are example commands showing common usage patterns:

```bash
# Basic illumination pipeline example
python cp_graph.py examples/illum.json examples/output/illum_graph.dot

# Basic visualization
dot -Tpng examples/output/illum_graph.dot -o examples/output/illum_graph.png

# Additional illumination pipeline options
python cp_graph.py examples/illum.json examples/output/illum_graph_no_format.dot --no-formatting
python cp_graph.py examples/illum.json examples/output/illum_graph_disabled.dot --include-disabled
python cp_graph.py examples/illum.json examples/output/illum_graph_ids.dot --explain-ids

# Analyze complex pipeline (all data types)
python cp_graph.py examples/analysis.json examples/output/analysis_full.dot

# Filter complex pipeline by data type
python cp_graph.py examples/analysis.json examples/output/analysis_objects.dot --data-type objects_only
python cp_graph.py examples/analysis.json examples/output/analysis_images.dot --data-type images_only
python cp_graph.py examples/analysis.json examples/output/analysis_no_lists.dot --data-type no_lists

# Generate visualizations
dot -Tpng examples/output/analysis_full.dot -o examples/output/analysis_full.png
dot -Tpng examples/output/analysis_objects.dot -o examples/output/analysis_objects.png
dot -Tpng examples/output/analysis_images.dot -o examples/output/analysis_images.png
dot -Tpng examples/output/analysis_no_lists.dot -o examples/output/analysis_no_lists.png

# Converting pipelines with different options
python cp_graph.py examples/illum_mod.json examples/output/illum_mod.dot # Standard
python cp_graph.py examples/illum_mod.json examples/output/illum_mod_ultra.dot --ultra-minimal # For diff comparison
python cp_graph.py examples/illum_mod.json examples/output/illum_mod_include.dot --include-disabled # Show disabled modules
```

## Visualization (Secondary Feature)

While the primary purpose is computational analysis and comparison, the tool also supports visualization:

### Visual Styling

The graph visually represents different elements:

- **Images**: Gray ovals
- **Objects**: Green ovals
- **Image Lists**: Yellow rounded rectangles
- **Object Lists**: Cyan rounded rectangles
- **Processing Modules**: Blue boxes with the module name and number
- **Disabled Modules**: Pink boxes with dashed borders (when included)
- **Connections**: Arrows showing the flow between data nodes and modules

Note: When comparing standard DOT files generated with different versions of the tool, you may notice differences in attribute ordering (e.g., `fillcolor` and `fontname` attributes in different order). These differences are purely cosmetic and don't affect visualization or functionality. If exact byte-for-byte consistency is needed for diff comparisons, use the `--ultra-minimal` option which excludes these styling attributes entirely.

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

### Data Type Filtering Views

While the illumination pipeline (`illum.json`) demonstrates the basic features, the tool shows its real power with more complex pipelines like the analysis pipeline (`examples/analysis.json`). For complex pipelines, filtering by data type becomes essential to understand specific aspects of the workflow:

**Complete Analysis Pipeline** (unfiltered):
This complex cellular analysis pipeline combines multiple data types - images (gray), objects (green), and lists (yellow/cyan) - making it challenging to focus on specific workflow aspects:
![Complete Analysis](examples/output/analysis_full.png)

**Filtered Views of the Analysis Pipeline:**

**Objects Only View** (--data-type objects_only):
Isolates just the cellular object relationships in the pipeline:
![Objects Only](examples/output/analysis_objects.png)

**Images Only View** (--data-type images_only):
Shows only image processing and transformation:
![Images Only](examples/output/analysis_images.png)

**No Lists View** (--data-type no_lists):
Excludes list data while keeping both images and objects:
![No Lists](examples/output/analysis_no_lists.png)

## Requirements

- Python 3.11+
- NetworkX library
- PyDot (for DOT output)
- Click (for CLI interface)

Install dependencies with:

```bash
pip install networkx pydot click
```

Or use UV (recommended):

```bash
uv pip install networkx pydot click
```