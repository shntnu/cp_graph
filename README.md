# CellProfiler Pipeline Dependency Graph

This tool extracts image dependency relationships from CellProfiler pipelines and creates a graph representation.

## Usage

```bash
python cp_dependency_graph.py <pipeline.json> [output_graph.graphml] [options]
```

- `pipeline.json` - Your CellProfiler pipeline file (v6 JSON format)
- `output_graph.graphml` - Optional output file (supports .graphml, .gexf, or .dot formats)

Options:
- `--no-module-info` - Hide module information on graph edges
- `--include-disabled` - Include disabled modules in the graph (excluded by default)

## How It Works

The script looks for two specific types of settings in each module:

1. Input images: `cellprofiler_core.setting.subscriber.image_subscriber._image_subscriber.ImageSubscriber`
2. Output images: `cellprofiler_core.setting.text.alphanumeric.name.image_name._image_name.ImageName`

For each enabled module, it creates connections from all inputs to all outputs, building a complete image dependency graph.

## Handling Disabled Modules

By default, the script ignores modules that have `enabled: false` in their attributes, as these aren't actually executed in the pipeline. If you want to include disabled modules in your graph, use the `--include-disabled` flag.

## Example with 1_CP_Illum.json

```bash
# Basic usage (includes only enabled modules)
python cp_dependency_graph.py 1_CP_Illum.json 1_CP_Illum_graph.dot

# Include disabled modules
python cp_dependency_graph.py 1_CP_Illum.json 1_CP_Illum_graph.dot --include-disabled

# Hide module info on edges
python cp_dependency_graph.py 1_CP_Illum.json 1_CP_Illum_graph.dot --no-module-info
```

The script will print a summary of all connections and save the graph to the specified format.

## Module Information on Edges

By default, the edges in the graph include module information (name and number). This helps identify which module created each transformation.

For example, in the DOT format, edges will include labels like:
```
"OrigDNA" -> "DownsampledDNA" [label="Resize #2"];
```

This makes it clear that the "Resize" module (number 2) transformed "OrigDNA" into "DownsampledDNA".

## Visualizing the Output

### Using Graphviz

If you have Graphviz installed, you can render a DOT file to an image:

```bash
dot -Tpng 1_CP_Illum_graph.dot -o 1_CP_Illum_graph.png
```

### Using Other Tools

The generated files can be opened with:
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
