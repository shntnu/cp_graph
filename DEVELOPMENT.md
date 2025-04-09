# CellProfiler Pipeline Dependency Graph Tool - Development Summary

## Project Overview
We've built a tool to extract and visualize image dependencies from CellProfiler pipelines by analyzing the JSON format that CellProfiler uses. This tool helps understand how data flows between modules in a pipeline.

## Key Discoveries
1. CellProfiler pipelines in JSON format contain detailed information about:
   - Module configurations (enabled/disabled status, module type, settings)
   - Image inputs and outputs are defined by specific setting types
   - Input images use: `cellprofiler_core.setting.subscriber.image_subscriber._image_subscriber.ImageSubscriber`
   - Output images use: `cellprofiler_core.setting.text.alphanumeric.name.image_name._image_name.ImageName`

2. Each module in the pipeline can be represented as a node in a processing graph that:
   - Takes specific named images as inputs
   - Produces specific named images as outputs
   - May be enabled or disabled

## CellProfiler Pipeline JSON Format

Based on analysis of the 1_CP_Illum.json file and the CellProfiler Core codebase, here is a detailed overview of the JSON format structure:

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

1. **Image References**:
   - Input images: `cellprofiler_core.setting.subscriber.image_subscriber._image_subscriber.ImageSubscriber`
   - Output images: `cellprofiler_core.setting.text.alphanumeric.name.image_name._image_name.ImageName`

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

### Image Flow Representation
Images flow through the pipeline by name:
1. A module creates an image with a specific name using `ImageName` setting
2. Another module references this image by its name using `ImageSubscriber` setting
3. This creates an implicit dependency between modules

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
3. Identifies input and output images for each module
4. Builds a directed graph where:
   - Nodes represent image names
   - Edges represent transformations from input to output
   - Edge labels show which module performed the transformation
5. Outputs the graph in standard formats (DOT, GraphML, GEXF)

## Features Added
1. **Disabled Module Handling**: By default, ignores modules with `enabled: false` attribute
2. **Module Info on Edges**: Shows module name and number on graph edges
3. **Flexible Outputs**: Supports multiple graph formats
4. **Command-Line Options**:
   - `--no-module-info`: Hides module information on edges
   - `--include-disabled`: Includes disabled modules in the graph

## Documentation
Created `README.md` with:
- Detailed usage instructions
- Command-line options
- Explanation of how the tool works
- Examples with 1_CP_Illum.json
- Installation requirements

## Use Cases
1. Understanding complex pipeline data flows
2. Visualizing image transformation paths
3. Debugging missing connections
4. Documentation for CellProfiler pipelines
5. Identifying unused images or redundant operations

## Future Extension Points
To extend this tool in the future, consider:
1. Support for analyzing other types (objects, measurements)
2. Integration with CellProfiler as a plugin
3. Interactive visualization capabilities
4. Deeper analysis of module parameters
5. Filtering connections by image type or module category
6. Allowing simplified views of complex pipelines

## Technical References
- CellProfiler Core repo: https://github.com/CellProfiler/core
- CellProfiler pipeline JSON structure: Example in 1_CP_Illum.json
- NetworkX documentation: https://networkx.org/documentation/stable/
- Graphviz documentation: https://graphviz.org/documentation/

The tool is functional in its current state and can be used to analyze any CellProfiler pipeline in v6 JSON format.