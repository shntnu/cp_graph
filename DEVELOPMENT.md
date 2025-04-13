# CellProfiler Pipeline Dependency Graph Tool - Development Summary

## Project Overview
We've built a tool to extract and visualize data dependencies from CellProfiler pipelines by analyzing the JSON format that CellProfiler uses. This tool helps understand how various data types (images, objects, and lists) flow between modules in a pipeline.

## Key Discoveries
1. CellProfiler pipelines in JSON format contain detailed information about:
   - Module configurations (enabled/disabled status, module type, settings)
   - Various data types are defined by specific setting types:
     - Images (via ImageSubscriber/ImageName)
     - Objects (via LabelSubscriber/LabelName)
     - Image Lists (via ImageListSubscriber)
     - Object Lists (via LabelListSubscriber)

2. Each module in the pipeline can be represented as a node in a processing graph that:
   - Takes specific named data items as inputs
   - Produces specific named data items as outputs
   - May be enabled or disabled
   - May handle multiple data types (images, objects, lists)

## CellProfiler Pipeline JSON Format

Based on analysis of the examples/illum.json file and the CellProfiler Core codebase, here is a detailed overview of the JSON format structure:

### Top-level Structure
```json
{
    "version": "v6",
    "has_image_plane_details": false,
    "date_revision": 500,
    "module_count": 22,
    "modules": [
        { /* Module 1 */ },
        { /* Module 2 */ },
        /* ... */
    ]
}
```

- `version`: Indicates the pipeline format version (e.g., "v6")
- `has_image_plane_details`: Boolean flag for additional image metadata
- `date_revision`: Version number for date handling
- `module_count`: Number of modules in the pipeline
- `modules`: Array of module objects

### Module Structure
Each module is represented as an object with two main sections:

```json
{
    "attributes": {
        "module_num": 1,
        "notes": [],
        "show_window": false,
        "wants_pause": false,
        "svn_version": "Unknown",
        "enabled": true,
        "variable_revision_number": 6,
        "batch_state": "array([], dtype=uint8)",
        "module_name": "LoadData",
        "module_path": "cellprofiler_core.modules.loaddata.LoadData"
    },
    "settings": [
        { /* Setting 1 */ },
        { /* Setting 2 */ },
        /* ... */
    ]
}
```

#### Module Attributes
- `module_num`: Sequential number in the pipeline
- `notes`: Optional user notes about the module
- `show_window`: Whether to display the module window in GUI
- `wants_pause`: Whether to pause execution after this module
- `enabled`: Whether the module is active in the pipeline
- `variable_revision_number`: Version of this module's settings format
- `module_name`: Short name of the module
- `module_path`: Fully qualified import path to the module class

#### Settings
Each setting is represented as an object:

```json
{
    "name": "cellprofiler_core.setting.subscriber.image_subscriber._image_subscriber.ImageSubscriber",
    "text": "Select the input image",
    "value": "OrigDNA"
}
```

- `name`: Fully qualified class path of the setting type
- `text`: Human-readable description of the setting
- `value`: The actual configured value of the setting

### Setting Types
The pipeline uses a variety of setting types:

1. **Data References**:
   - **Image Inputs/Outputs**:
     - Input images: `cellprofiler_core.setting.subscriber.image_subscriber._image_subscriber.ImageSubscriber`
     - Output images: `cellprofiler_core.setting.text.alphanumeric.name.image_name._image_name.ImageName`
   - **Object Inputs/Outputs**:
     - Input objects: `cellprofiler_core.setting.subscriber._label_subscriber.LabelSubscriber`
     - Output objects: `cellprofiler_core.setting.text.alphanumeric.name._label_name.LabelName`
   - **List Inputs**:
     - Image lists: `cellprofiler_core.setting.subscriber.list_subscriber._image_list_subscriber.ImageListSubscriber`
     - Object lists: `cellprofiler_core.setting.subscriber.list_subscriber._label_list_subscriber.LabelListSubscriber`

2. **Basic Types**:
   - Binary (Yes/No): `cellprofiler_core.setting._binary.Binary`
   - Text: `cellprofiler_core.setting.text._text.Text`
   - Integer: `cellprofiler_core.setting.text.number.integer._integer.Integer`
   - Float: `cellprofiler_core.setting.text.number._float.Float`

3. **Complex Types**:
   - Choice (dropdown): `cellprofiler_core.setting.choice._choice.Choice`
   - MultiChoice: `cellprofiler_core.setting.multichoice._multichoice.MultiChoice`
   - Directory: `cellprofiler_core.setting.text._directory.Directory`
   - Filename: `cellprofiler_core.setting.text._filename.Filename`
   - Hidden counts: `cellprofiler_core.setting._hidden_count.HiddenCount`

### Data Flow Representation
Data flows through the pipeline by name:
1. A module creates data (image, object) with specific names using settings like `ImageName` or `LabelName`
2. Another module references this data by name using subscriber settings like `ImageSubscriber` or `LabelSubscriber`
3. Some modules consume or produce collections via list subscribers like `ImageListSubscriber` or `LabelListSubscriber`
4. These named connections create implicit dependencies between modules

### Version Handling
- Each module has its own `variable_revision_number`
- The pipeline as a whole has a `version` field
- These support backward compatibility as the codebase evolves

### Special Cases
- Certain modules act as sources (like LoadData) bringing in external images
- Some modules are just processors (transform inputs to outputs)
- Some modules act as sinks (like SaveImages) with no further propagation

## Technical Implementation
We created `cp_graph.py` which:
1. Parses the JSON pipeline file
2. Extracts module metadata and enabled status
3. Identifies input and output data (images, objects, lists) for each module
4. Builds a directed graph where:
   - Nodes represent data items (images, objects) with a unified representation
   - Nodes also represent modules, using stable hash-based identifiers
   - Edges preserve connection types to maintain semantics (regular vs. list inputs)
   - Edge types indicate the original data usage pattern
5. Creates a standardized representation for comparison purposes
6. Outputs the graph in standard formats (DOT, GraphML, GEXF)

The script uses a modular design with:
- Type definitions using TypedDict for clear interfaces
- Small, focused functions with well-defined responsibilities
- Click for command-line interface handling
- Consistent styling and formatting throughout

## Core Features
1. **Standardized Graph Representation**: 
   - Uses stable module identifiers based on module type and I/O connections
   - Implements deterministic SHA-256 hashing for consistent identifiers across runs
   - Consistently orders nodes and edges for reliable comparisons
   - Designed to be invariant to module reordering in the pipeline

2. **Pipeline Comparison Support**:
   - Focuses on structural data flow (deliberately excludes module settings)
   - Creates canonical representations that can be compared with diff tools
   - Provides ultra-minimal mode for byte-for-byte identical output of equivalent pipelines
   - Ignores irrelevant differences while highlighting structural changes

3. **Unified Data Representation**:
   - Tracks multiple types of data flow:
     - Images (via ImageSubscriber and ImageName)
     - Objects (via LabelSubscriber and LabelName)
     - Image Lists (via ImageListSubscriber)
     - Object Lists (via LabelListSubscriber)
   - Uses a unified node representation for each data entity
   - Preserves connection semantics through edge type information
   - Visual differentiation between data types with distinctive styling

4. **Additional Features**:
   - **Disabled Module Handling**: By default, ignores modules with `enabled: false` attribute
   - **Module Info on Edges**: Shows module name and number on graph edges
   - **Flexible Outputs**: Supports multiple graph formats
   - **Formatting Control**: Option to strip visual styling for comparison focus
   - **Stable ID Mapping**: Explains the relationship between node IDs and original module numbers

5. **Command-Line Options**:
   - `--no-formatting`: Strips all formatting for topology-focused comparison
   - `--no-module-info`: Hides module information on edges
   - `--ultra-minimal`: Creates minimal output with only essential structure for exact diff comparison
   - `--include-disabled`: Includes disabled modules in the graph
   - `--explain-ids`: Shows mapping between stable IDs and original module numbers
   - `--rank-nodes`: Positions source nodes at top and sink nodes at bottom
   - `--rank-ignore-filtered`: Ignores filtered nodes when calculating rank positions
   - `--quiet` or `-q`: Suppress informational output

## Documentation
Created `README.md` with:
- Detailed usage instructions
- Command-line options
- Explanation of how the tool works
- Examples with examples/illum.json
- Installation requirements

## Use Cases
1. Understanding complex pipeline data flows
2. Visualizing data transformation paths with a unified representation
3. Debugging missing connections
4. Documentation for CellProfiler pipelines
5. Identifying unused data or redundant operations
6. Comprehensive overview of all data relationships in a pipeline
7. Understanding module dependencies for pipeline optimization

## Future Extension Points
To extend this tool in the future, consider:
1. Support for analyzing measurements and metadata
2. Integration with CellProfiler as a plugin
3. Interactive visualization capabilities
4. Deeper analysis of module parameters
5. Filtering connections by specific module categories
6. Allowing simplified views of complex pipelines
7. Enhanced visual distinction for different connection types
8. Visual styles customization options

## Recent Improvements

### Deterministic Module Identification
One key improvement is replacing Python's built-in `hash()` function with deterministic SHA-256 hashing. The built-in hash is intentionally randomized across Python process runs (for security reasons), which was causing inconsistent module IDs between executions. By switching to SHA-256:

```python
# Create a stable unique identifier using a deterministic hash function
io_pattern = ",".join(all_inputs) + "|" + ",".join(all_outputs)
# Use SHA-256 hash which is deterministic across runs
hash_obj = hashlib.sha256(io_pattern.encode('utf-8'))
hash_val = int(hash_obj.hexdigest()[:8], 16)
stable_id = f"{module_type}_{hash_val:x}"
```

This ensures that identical pipeline structures always receive identical module identifiers, regardless of process restart.

### Ultra-Minimal Output Mode
A new `--ultra-minimal` option was added that produces identical DOT files for structurally equivalent pipelines. This mode:

1. Strips all non-essential attributes from nodes and edges
2. Retains only fundamental type information and connectivity
3. Ensures byte-for-byte identical output for equivalent pipelines
4. Enables reliable diff-based comparison between structurally equivalent pipelines with different module numbering

### Node Ranking for Improved Visualization
The tool now supports the `--rank-nodes` option to improve graph layout in DOT format:

1. Source nodes (input images with no incoming edges) are positioned at the top of the graph
2. Sink nodes (SaveImages, Measure*, Export* modules) are positioned at the bottom
3. This creates a more intuitive top-to-bottom data flow in the visualized graph
4. Use with `--rank-ignore-filtered` to exclude filtered nodes from rank calculations when highlighting is used

The implementation uses Graphviz's rank attribute to enforce node positioning:

```dot
{rank = min; image__CorrDNA; image__Cycle01_DAPI; ...}  # Source nodes at top
{rank = max; SaveImages_22818067; MeasureObjectIntensity_40d9dc39; ...}  # Sink nodes at bottom
```

### Robust Node ID Handling
The tool now properly handles node IDs with spaces and special characters:

1. Node IDs are properly quoted in the DOT output if they contain spaces
2. This is handled early in the graph creation process for consistency
3. Ensures proper visualization of pipelines with complex naming schemes

The tool includes several sample pipelines in the `examples/` directory:
- `examples/illum.json` and `examples/illum_isoform.json`: Structurally identical illumination correction pipelines with different module numbering (perfect for demonstrating the stable ID feature)
- `examples/analysis.json`: A more complex analysis pipeline that showcases various data types (images, objects, and lists) in a multi-step workflow
- Rendered outputs are stored in the `examples/output/` directory

## Technical References
- CellProfiler Core repo: https://github.com/CellProfiler/core
- CellProfiler pipeline JSON structure: Example in examples/illum.json
- NetworkX documentation: https://networkx.org/documentation/stable/
- Graphviz documentation: https://graphviz.org/documentation/

## Running the Tool

The script includes PEP 723 dependency metadata, which allows it to be run directly with UV:

```bash
# Run with UV to automatically install dependencies
uv run --script cp_graph.py <pipeline.json> [output_graph.graphml] [options]
```

This is the recommended approach as it automatically installs the required dependencies (networkx, pydot, and click) in an isolated environment.

### Dependencies

- Python 3.11+
- NetworkX for graph representation
- PyDot for DOT format output
- Click for command-line interface handling

### Unified Data Node Representation

The latest improvement is the unification of data node representation. Previously, the tool created separate nodes for regular and list inputs of the same data entity (for example, "image__ZO1" and "image_list__ZO1"). This was recognized as an artificial distinction based on how modules define their inputs.

The key changes:

1. Data items are now represented as a single node regardless of how they're consumed
2. Edge types preserve the original connection semantics (regular vs. list inputs) 
3. Graph visualization is cleaner and more accurately represents the true data flow
4. Hash-based module identifiers normalize these representations for consistent comparisons

This unified approach results in a more intuitive graph with fewer redundant nodes, while still preserving all necessary information about connection types in the edge metadata.

The tool is functional in its current state and can be used to analyze any CellProfiler pipeline in v6 JSON format. It provides a comprehensive view of data flow with a unified data representation that makes complex pipelines easier to understand.

## Limitations

The way CellProfiler pipeline files work creates some inherent challenges in accurately representing data flow:

1. **Complex Input/Output Relationships**: Determining true inputs and outputs requires parsing module-specific settings logic. A module may have an ImageSubscriber setting but other settings might cause it to be ignored.

2. **Plugin-Specific Behavior**: Some plugins like CallBarcodes and similar modules don't explicitly specify all inputs. For instance, these modules might internally process multiple cycle images but only the first cycle appears as an explicit input in the JSON.

3. **ExportToSpreadsheet Consumption**: It's difficult to accurately determine exactly which measurements ExportToSpreadsheet modules consume, as they often use patterns rather than explicit references.

4. **Unused Objects**: Some created objects may never be used, but detecting this can be challenging.

Despite these limitations, the tool provides practical solutions:

- The `--root-nodes` option ensures we focus on paths from specific inputs, avoiding spurious connections
- The `--remove-unused-data` option helps eliminate unused data items
- The `--exclude-module-types` option allows skipping problematic modules like ExportToSpreadsheet

This approach of working directly with the JSON file alone is still valuable, as it doesn't require the full CellProfiler codebase to analyze pipeline structure.