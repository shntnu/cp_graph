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
import hashlib
import networkx as nx
from pathlib import Path

# Constants for the specific setting types we're looking for
# Input types
INPUT_IMAGE_TYPE = "cellprofiler_core.setting.subscriber.image_subscriber._image_subscriber.ImageSubscriber"
INPUT_LABEL_TYPE = (
    "cellprofiler_core.setting.subscriber._label_subscriber.LabelSubscriber"
)
INPUT_IMAGE_LIST_TYPE = "cellprofiler_core.setting.subscriber.list_subscriber._image_list_subscriber.ImageListSubscriber"
INPUT_LABEL_LIST_TYPE = "cellprofiler_core.setting.subscriber.list_subscriber._label_list_subscriber.LabelListSubscriber"

# Output types
OUTPUT_IMAGE_TYPE = (
    "cellprofiler_core.setting.text.alphanumeric.name.image_name._image_name.ImageName"
)
OUTPUT_LABEL_TYPE = (
    "cellprofiler_core.setting.text.alphanumeric.name._label_name.LabelName"
)


def extract_module_io(module):
    """Extract inputs and outputs of various data types from a module"""
    # Initialize dictionaries for different types of inputs/outputs
    inputs = {"image": [], "object": [], "image_list": [], "object_list": []}
    outputs = {
        "image": [],
        "object": [],
        # Note: Lists are typically consumed, not produced
    }

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

        # Input types
        if setting_name == INPUT_IMAGE_TYPE:
            inputs["image"].append(setting_value)
        elif setting_name == INPUT_LABEL_TYPE:
            inputs["object"].append(setting_value)
        elif setting_name == INPUT_IMAGE_LIST_TYPE:
            # Split comma-separated list and add each item
            values = [v.strip() for v in setting_value.split(",") if v.strip()]
            inputs["image_list"].extend(values)
        elif setting_name == INPUT_LABEL_LIST_TYPE:
            # Split comma-separated list and add each item
            values = [v.strip() for v in setting_value.split(",") if v.strip()]
            inputs["object_list"].extend(values)

        # Output types
        elif setting_name == OUTPUT_IMAGE_TYPE:
            outputs["image"].append(setting_value)
        elif setting_name == OUTPUT_LABEL_TYPE:
            outputs["object"].append(setting_value)

    return {
        "module_num": module_num,
        "module_name": module_name,
        "inputs": inputs,
        "outputs": outputs,
        "enabled": module_enabled,
    }


def create_dependency_graph(
    pipeline_json,
    include_disabled=False,
    include_objects=True,
    include_lists=True,
    include_images=True,
):
    """Create a dependency graph showing data flow between modules"""
    G = nx.DiGraph()

    # Process each module to build the graph
    modules_io = []
    for module in pipeline_json.get("modules", []):
        module_io = extract_module_io(module)
        modules_io.append(module_io)

        # Skip disabled modules if not explicitly included
        if not module_io["enabled"] and not include_disabled:
            continue

        # Check if module has any inputs or outputs of any enabled type
        has_io = False
        for input_type, inputs in module_io["inputs"].items():
            # Skip if this data type should not be included
            if not inputs:
                continue

            # Check type-specific inclusion flags
            if input_type == "image" and not include_images:
                continue
            if input_type == "object" and not include_objects:
                continue
            if "list" in input_type and not include_lists:
                continue

            has_io = True
            break

        for output_type, outputs in module_io["outputs"].items():
            # Skip if this data type should not be included
            if not outputs:
                continue

            # Check type-specific inclusion flags
            if output_type == "image" and not include_images:
                continue
            if output_type == "object" and not include_objects:
                continue

            has_io = True
            break

        if not has_io:
            continue

        # Create a stable identifier for the module that isn't dependent on module_num
        module_type = module_io["module_name"]

        # Collect all inputs/outputs for hash generation
        all_inputs = []
        all_outputs = []

        for input_type, inputs in module_io["inputs"].items():
            # Only include enabled data types
            if (
                (input_type == "image" and include_images)
                or (input_type == "object" and include_objects)
                or ("list" in input_type and include_lists)
            ):
                all_inputs.extend([f"{input_type}__{inp}" for inp in inputs])

        for output_type, outputs in module_io["outputs"].items():
            # Only include enabled data types
            if (output_type == "image" and include_images) or (
                output_type == "object" and include_objects
            ):
                all_outputs.extend([f"{output_type}__{out}" for out in outputs])

        # Sort for stability
        all_inputs.sort()
        all_outputs.sort()

        # Create a stable unique identifier using a deterministic hash function
        io_pattern = ",".join(all_inputs) + "|" + ",".join(all_outputs)
        # Use SHA-256 hash which is deterministic across runs
        hash_obj = hashlib.sha256(io_pattern.encode('utf-8'))
        hash_val = int(hash_obj.hexdigest()[:8], 16)
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

        # Add data nodes and edges for each type
        for input_type, inputs in module_io["inputs"].items():
            # Skip if this data type is not included
            if (
                (input_type == "image" and not include_images)
                or (input_type == "object" and not include_objects)
                or ("list" in input_type and not include_lists)
            ):
                continue

            for input_item in inputs:
                # Create node ID with type prefix using double underscore to avoid dot port syntax
                node_id = f"{input_type}__{input_item}"

                # Add node if it doesn't exist
                if not G.has_node(node_id):
                    G.add_node(
                        node_id, type=input_type, name=input_item, label=input_item
                    )

                # Add edge from input to module
                G.add_edge(node_id, stable_id, type=f"{input_type}_input")

        for output_type, outputs in module_io["outputs"].items():
            # Skip if this data type is not included
            if (output_type == "image" and not include_images) or (
                output_type == "object" and not include_objects
            ):
                continue

            for output_item in outputs:
                # Create node ID with type prefix using double underscore to avoid dot port syntax
                node_id = f"{output_type}__{output_item}"

                # Add node if it doesn't exist
                if not G.has_node(node_id):
                    G.add_node(
                        node_id, type=output_type, name=output_item, label=output_item
                    )

                # Add edge from module to output
                G.add_edge(stable_id, node_id, type=f"{output_type}_output")

    return G, modules_io


def main(
    pipeline_path,
    output_path=None,
    no_module_info=False,
    include_disabled=False,
    no_formatting=False,
    ultra_minimal=False,
    include_objects=True,
    include_lists=True,
    include_images=True,
):
    """Process a CellProfiler pipeline and create a dependency graph"""
    # Load the pipeline JSON
    with open(pipeline_path, "r") as f:
        pipeline = json.load(f)

    # Create the graph with specified data types
    G, modules_io = create_dependency_graph(
        pipeline,
        include_disabled=include_disabled,
        include_objects=include_objects,
        include_lists=include_lists,
        include_images=include_images,
    )

    # Print pipeline summary
    print(f"Pipeline: {pipeline_path}")

    # Count different node types
    node_counts = {}
    for n, attr in G.nodes(data=True):
        node_type = attr.get("type")
        if node_type not in node_counts:
            node_counts[node_type] = 0
        node_counts[node_type] += 1

    module_nodes = [n for n, attr in G.nodes(data=True) if attr.get("type") == "module"]
    enabled_modules = [n for n in module_nodes if G.nodes[n].get("enabled", True)]
    disabled_modules = [n for n in module_nodes if not G.nodes[n].get("enabled", True)]

    # Print node type counts
    print("Graph contains:")
    for node_type, count in sorted(node_counts.items()):
        if node_type == "module":
            print(
                f"  {count} modules ({len(enabled_modules)} enabled, {len(disabled_modules)} disabled)"
            )
        else:
            print(f"  {count} {node_type} nodes")
    print(f"  {len(G.edges())} total connections")

    # Print connections
    print("\nConnections:")
    for edge in G.edges(data=True):
        src, dst, attrs = edge
        src_type = G.nodes[src].get("type")
        dst_type = G.nodes[dst].get("type")

        # Only show module connections
        if dst_type == "module":
            # Input connection
            module_name = G.nodes[dst].get("module_name")
            module_num = G.nodes[dst].get("module_num")
            module_enabled = G.nodes[dst].get("enabled", True)
            status = " (disabled)" if not module_enabled else ""

            # Extract the actual name without the type prefix
            src_name = G.nodes[src].get(
                "name", src.split("__", 1)[1] if "__" in src else src
            )
            src_disp_type = src_type.replace("_list", " list").replace("_", " ")

            print(
                f"  {src_name} ({src_disp_type}) → [{module_name} #{module_num}{status}]"
            )

        elif src_type == "module":
            # Output connection
            module_name = G.nodes[src].get("module_name")
            module_num = G.nodes[src].get("module_num")
            module_enabled = G.nodes[src].get("enabled", True)
            status = " (disabled)" if not module_enabled else ""

            # Extract the actual name without the type prefix
            dst_name = G.nodes[dst].get(
                "name", dst.split("__", 1)[1] if "__" in dst else dst
            )
            dst_disp_type = dst_type.replace("_list", " list").replace("_", " ")

            print(
                f"  [{module_name} #{module_num}{status}] → {dst_name} ({dst_disp_type})"
            )

    # Save the graph if requested
    if output_path:
        ext = Path(output_path).suffix.lower()

        # Apply visual attributes for different node types
        if not no_formatting:
            for node, attrs in G.nodes(data=True):
                node_type = attrs.get("type")

                if node_type == "module":
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

                elif node_type == "image":
                    # Image nodes styling
                    G.nodes[node]["shape"] = "ellipse"
                    G.nodes[node]["style"] = "filled"
                    G.nodes[node]["fillcolor"] = "lightgray"

                elif node_type == "object":
                    # Object nodes styling
                    G.nodes[node]["shape"] = "ellipse"
                    G.nodes[node]["style"] = "filled"
                    G.nodes[node]["fillcolor"] = "lightgreen"

                elif node_type == "image_list":
                    # Image list nodes styling
                    G.nodes[node]["shape"] = "box"
                    G.nodes[node]["style"] = "filled,rounded"
                    G.nodes[node]["fillcolor"] = "lightyellow"

                elif node_type == "object_list":
                    # Object list nodes styling
                    G.nodes[node]["shape"] = "box"
                    G.nodes[node]["style"] = "filled,rounded"
                    G.nodes[node]["fillcolor"] = "lightcyan"

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
                # For DOT format, prepare the graph
                G_ordered = nx.DiGraph()
                
                # If ultra_minimal is enabled, create a stripped-down version with only essential structure
                if ultra_minimal:
                    # Process nodes - keep only the type attribute
                    for node in sorted(G.nodes()):
                        node_type = G.nodes[node].get("type", "unknown")
                        # Add only the type attribute, nothing else
                        G_ordered.add_node(node, type=node_type)
                    
                    # Process edges - keep no attributes
                    edge_list = sorted(G.edges(data=True), key=lambda x: (x[0], x[1]))
                    for src, dst, _ in edge_list:
                        G_ordered.add_edge(src, dst)
                else:
                    # For DOT format, set proper display labels for all nodes
                    for node, attrs in G.nodes(data=True):
                        node_type = attrs.get("type")

                        if node_type == "module":
                            # Use the provided label for modules
                            G.nodes[node]["label"] = attrs.get("label")
                        else:
                            # For data nodes, use just the name without the type prefix
                            name = attrs.get(
                                "name", node.split("__", 1)[1] if "__" in node else node
                            )
                            # Fix for pydot: ensure we don't have duplicate "name" attributes
                            if "name" in G.nodes[node] and "name" != "label":
                                del G.nodes[node]["name"]
                            G.nodes[node]["label"] = name

                    # Ensure consistent ordering in DOT output
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

    # Display options
    parser.add_argument(
        "--no-module-info",
        action="store_true",
        help="Hide module information on graph edges",
    )
    parser.add_argument(
        "--no-formatting",
        action="store_true",
        help="Strip formatting information from graph output (colors, shapes, etc.)",
    )
    parser.add_argument(
        "--ultra-minimal",
        action="store_true",
        help="Create minimal output with only essential structure for exact diff comparison",
    )
    parser.add_argument(
        "--explain-ids",
        action="store_true",
        help="Print explanation of stable node IDs and their source modules",
    )

    # Content filtering options
    parser.add_argument(
        "--include-disabled",
        action="store_true",
        help="Include disabled modules in the graph",
    )

    # Data type options (mutually exclusive group)
    data_group = parser.add_mutually_exclusive_group()
    data_group.add_argument(
        "--images-only",
        action="store_true",
        help="Include only image flow in the graph (default includes all)",
    )
    data_group.add_argument(
        "--objects-only",
        action="store_true",
        help="Include only object flow in the graph (default includes all)",
    )
    data_group.add_argument(
        "--no-lists",
        action="store_true",
        help="Exclude list inputs in the graph (default includes all)",
    )

    args = parser.parse_args()

    # Determine what data types to include based on arguments
    include_objects = not args.images_only
    include_lists = not args.no_lists and not args.objects_only

    # If objects-only is specified, don't include images
    include_images = not args.objects_only

    G, modules_io = main(
        args.pipeline,
        args.output,
        args.no_module_info,
        args.include_disabled,
        args.no_formatting,
        args.ultra_minimal,
        include_objects=include_objects,
        include_lists=include_lists,
        include_images=include_images,
    )

    # If explain_ids is enabled, print a mapping of stable IDs to original module numbers
    if args.explain_ids:
        print("\nStable module ID mapping:")
        module_nodes = [
            n for n, attr in G.nodes(data=True) if attr.get("type") == "module"
        ]
        for node in sorted(module_nodes):
            attrs = G.nodes[node]
            orig_num = attrs.get("original_num", "?")
            module_name = attrs.get("module_name", "Unknown")
            enabled = "" if attrs.get("enabled", True) else " (disabled)"
            print(f"  {node} → {module_name} #{orig_num}{enabled}")
