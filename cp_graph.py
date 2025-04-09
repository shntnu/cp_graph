# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "networkx",
#     "pydot",
# ]
#
# ///

#!/usr/bin/env python

import json
import networkx as nx
from pathlib import Path

# Constants for the specific setting types we're looking for
INPUT_IMAGE_TYPE = "cellprofiler_core.setting.subscriber.image_subscriber._image_subscriber.ImageSubscriber"
OUTPUT_IMAGE_TYPE = (
    "cellprofiler_core.setting.text.alphanumeric.name.image_name._image_name.ImageName"
)


def extract_module_io(module):
    """Extract input and output images from a module"""
    input_images = []
    output_images = []

    # Get module identification
    module_attrs = module.get("attributes", {})
    module_num = module_attrs.get("module_num", 0)
    module_name = module_attrs.get("module_name", "Unknown")
    module_enabled = module_attrs.get("enabled", True)

    for setting in module.get("settings", []):
        setting_name = setting.get("name", "")
        setting_value = setting.get("value", "")

        # Skip if value is "None" or empty
        if not setting_value or setting_value == "None":
            continue

        # Check for input image subscribers
        if setting_name == INPUT_IMAGE_TYPE:
            input_images.append(setting_value)

        # Check for output image names
        elif setting_name == OUTPUT_IMAGE_TYPE:
            output_images.append(setting_value)

    return {
        "module_num": module_num,
        "module_name": module_name,
        "inputs": input_images,
        "outputs": output_images,
        "enabled": module_enabled,
    }


def create_image_dependency_graph(pipeline_json, include_disabled=False):
    """Create a dependency graph from images flowing between modules"""
    G = nx.DiGraph()

    # Process each module to build the graph
    modules_io = []
    for module in pipeline_json.get("modules", []):
        module_io = extract_module_io(module)
        modules_io.append(module_io)

        # Skip disabled modules if not explicitly included
        if not module_io["enabled"] and not include_disabled:
            continue

        # Skip modules with no inputs or outputs
        if not module_io["inputs"] and not module_io["outputs"]:
            continue

        # Add all images as nodes
        for image in module_io["inputs"] + module_io["outputs"]:
            if not G.has_node(image):
                G.add_node(image, type="image")

        # Create a stable identifier for the module that isn't dependent on module_num
        # Use module_name + hash of input/output patterns to create a more stable ID
        module_type = module_io["module_name"]
        module_inputs = ",".join(sorted(module_io["inputs"]))
        module_outputs = ",".join(sorted(module_io["outputs"]))
        
        # Create a stable unique identifier using module type and its IO patterns
        # This is more resilient to module reordering in the pipeline
        hash_val = hash(module_inputs + '|' + module_outputs) & 0xFFFFFFFF
        stable_id = f"{module_type}_{hash_val:x}"
        
        # Keep the original module number in the label for reference
        original_num = module_io["module_num"]
        module_label = f"{module_io['module_name']} #{original_num}"

        # Add disabled status to label if module is disabled
        if not module_io["enabled"]:
            module_label += " (disabled)"

        G.add_node(
            stable_id,
            type="module",
            label=module_label,
            module_name=module_io["module_name"],
            module_num=module_io["module_num"],
            original_num=original_num,
            stable_id=stable_id,
            enabled=module_io["enabled"],
        )

        # Add edges from inputs to module
        for input_img in module_io["inputs"]:
            G.add_edge(input_img, stable_id, type="input")

        # Add edges from module to outputs
        for output_img in module_io["outputs"]:
            G.add_edge(stable_id, output_img, type="output")

    return G, modules_io


def main(pipeline_path, output_path=None, no_module_info=False, include_disabled=False, no_formatting=False):
    """Process a CellProfiler pipeline and create an image dependency graph"""
    # Load the pipeline JSON
    with open(pipeline_path, "r") as f:
        pipeline = json.load(f)

    # Create the graph
    G, modules_io = create_image_dependency_graph(pipeline, include_disabled)

    # Print pipeline summary
    print(f"Pipeline: {pipeline_path}")

    image_nodes = [n for n, attr in G.nodes(data=True) if attr.get("type") == "image"]
    module_nodes = [n for n, attr in G.nodes(data=True) if attr.get("type") == "module"]

    enabled_modules = [n for n in module_nodes if G.nodes[n].get("enabled", True)]
    disabled_modules = [n for n in module_nodes if not G.nodes[n].get("enabled", True)]

    print(
        f"Graph has {len(image_nodes)} images and {len(module_nodes)} modules "
        + f"({len(enabled_modules)} enabled, {len(disabled_modules)} disabled) with {len(G.edges())} connections"
    )

    # Print image connections
    print("\nConnections:")
    for edge in G.edges(data=True):
        src, dst, attrs = edge
        src_type = G.nodes[src].get("type")
        dst_type = G.nodes[dst].get("type")

        if src_type == "image" and dst_type == "module":
            # Input connection
            module_name = G.nodes[dst].get("module_name")
            module_num = G.nodes[dst].get("module_num")
            module_enabled = G.nodes[dst].get("enabled", True)
            status = " (disabled)" if not module_enabled else ""
            print(f"  {src} → [{module_name} #{module_num}{status}] (Input)")
        elif src_type == "module" and dst_type == "image":
            # Output connection
            module_name = G.nodes[src].get("module_name")
            module_num = G.nodes[src].get("module_num")
            module_enabled = G.nodes[src].get("enabled", True)
            status = " (disabled)" if not module_enabled else ""
            print(f"  [{module_name} #{module_num}{status}] → {dst} (Output)")

    # Save the graph if requested
    if output_path:
        ext = Path(output_path).suffix.lower()

        # Apply visual attributes for different node types
        if not no_formatting:
            for node, attrs in G.nodes(data=True):
                if attrs.get("type") == "module":
                    # Module nodes styling
                    G.nodes[node]["shape"] = "box"
                    G.nodes[node]["style"] = "filled"
                    
                    # Style disabled modules differently
                    if attrs.get("enabled", True):
                        G.nodes[node]["fillcolor"] = "lightblue"
                    else:
                        G.nodes[node]["fillcolor"] = "lightpink"
                        G.nodes[node]["style"] = "filled,dashed"
                    
                    G.nodes[node]["fontname"] = "Helvetica-Bold"
                else:
                    # Image nodes styling
                    G.nodes[node]["shape"] = "ellipse"
                    G.nodes[node]["style"] = "filled"
                    G.nodes[node]["fillcolor"] = "lightgray"

        # If no_module_info is True, simplify edges
        if no_module_info:
            for edge in G.edges():
                # Remove any edge labels
                if "label" in G.edges[edge]:
                    del G.edges[edge]["label"]

        if ext == ".graphml":
            nx.write_graphml(G, output_path)
        elif ext == ".gexf":
            nx.write_gexf(G, output_path)
        elif ext == ".dot":
            try:
                # For DOT format, set proper display labels
                for node, attrs in G.nodes(data=True):
                    if attrs.get("type") == "module":
                        G.nodes[node]["label"] = attrs.get("label")

                # Ensure consistent ordering in DOT output
                G_ordered = nx.DiGraph()

                # Add nodes in sorted order by name
                for node in sorted(G.nodes()):
                    G_ordered.add_node(node, **G.nodes[node])

                # Add edges in sorted order
                edge_list = sorted(G.edges(data=True), key=lambda x: (x[0], x[1]))
                for src, dst, attrs in edge_list:
                    G_ordered.add_edge(src, dst, **attrs)

                nx.drawing.nx_pydot.write_dot(G_ordered, output_path)
            except ImportError:
                print("Warning: pydot not available. Saving as GraphML instead.")
                nx.write_graphml(G, output_path.replace(ext, ".graphml"))
        else:
            # Default to GraphML
            nx.write_graphml(G, output_path)

        print(f"Graph saved to: {output_path}")

    return G, modules_io


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Create a graph representation of a CellProfiler pipeline"
    )
    parser.add_argument("pipeline", help="CellProfiler pipeline JSON file")
    parser.add_argument(
        "output", nargs="?", help="Output graph file (.graphml, .gexf, or .dot)"
    )
    parser.add_argument(
        "--no-module-info",
        action="store_true",
        help="Hide module information on graph edges",
    )
    parser.add_argument(
        "--include-disabled",
        action="store_true",
        help="Include disabled modules in the graph",
    )
    parser.add_argument(
        "--no-formatting",
        action="store_true",
        help="Strip formatting information from graph output (colors, shapes, etc.)",
    )
    parser.add_argument(
        "--explain-ids",
        action="store_true",
        help="Print explanation of stable node IDs and their source modules",
    )

    args = parser.parse_args()

    G, modules_io = main(args.pipeline, args.output, args.no_module_info, args.include_disabled, args.no_formatting)
    
    # If explain_ids is enabled, print a mapping of stable IDs to original module numbers
    if args.explain_ids:
        print("\nStable module ID mapping:")
        module_nodes = [n for n, attr in G.nodes(data=True) if attr.get("type") == "module"]
        for node in sorted(module_nodes):
            attrs = G.nodes[node]
            orig_num = attrs.get("original_num", "?")
            module_name = attrs.get("module_name", "Unknown")
            enabled = "" if attrs.get("enabled", True) else " (disabled)"
            print(f"  {node} → {module_name} #{orig_num}{enabled}")
