# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "networkx",
#     "pydot",
#     "click",
# ]
#
# ///

#!/usr/bin/env python

# ----- IMPORTS -----
import json
import hashlib
import sys
from pathlib import Path
import networkx as nx
import click
from typing import Dict, List, Set, Tuple, Any, Optional, TypedDict, TypeVar, TextIO

# ----- CONSTANTS AND CONFIGURATION -----
# CellProfiler setting types
# Input types
INPUT_IMAGE_TYPE = "cellprofiler_core.setting.subscriber.image_subscriber._image_subscriber.ImageSubscriber"
INPUT_LABEL_TYPE = "cellprofiler_core.setting.subscriber._label_subscriber.LabelSubscriber"
INPUT_IMAGE_LIST_TYPE = "cellprofiler_core.setting.subscriber.list_subscriber._image_list_subscriber.ImageListSubscriber"
INPUT_LABEL_LIST_TYPE = "cellprofiler_core.setting.subscriber.list_subscriber._label_list_subscriber.LabelListSubscriber"

# Output types
OUTPUT_IMAGE_TYPE = "cellprofiler_core.setting.text.alphanumeric.name.image_name._image_name.ImageName"
OUTPUT_LABEL_TYPE = "cellprofiler_core.setting.text.alphanumeric.name._label_name.LabelName"

# Node types
NODE_TYPE_MODULE = "module"
NODE_TYPE_IMAGE = "image"
NODE_TYPE_OBJECT = "object"
NODE_TYPE_IMAGE_LIST = "image_list"
NODE_TYPE_OBJECT_LIST = "object_list"

# Edge types - match original format exactly for compatibility
EDGE_TYPE_INPUT = "input"
EDGE_TYPE_OUTPUT = "output"

# Style constants
STYLE_COLORS = {
    NODE_TYPE_MODULE: {
        "enabled": "lightblue",
        "disabled": "lightpink"
    },
    NODE_TYPE_IMAGE: "lightgray",
    NODE_TYPE_OBJECT: "lightgreen",
    NODE_TYPE_IMAGE_LIST: "lightyellow", 
    NODE_TYPE_OBJECT_LIST: "lightcyan"
}

# Graph styles
STYLE_SHAPES = {
    NODE_TYPE_MODULE: "box",
    NODE_TYPE_IMAGE: "ellipse",
    NODE_TYPE_OBJECT: "ellipse",
    NODE_TYPE_IMAGE_LIST: "box",
    NODE_TYPE_OBJECT_LIST: "box"
}

# Type definitions
class ModuleInputs(TypedDict):
    """Dictionary of module inputs by data type"""
    image: List[str]
    object: List[str]
    image_list: List[str]
    object_list: List[str]

class ModuleOutputs(TypedDict):
    """Dictionary of module outputs by data type"""
    image: List[str]
    object: List[str]

class ModuleInfo(TypedDict):
    """Information about a module extracted from the pipeline"""
    module_num: int
    module_name: str
    inputs: ModuleInputs
    outputs: ModuleOutputs
    enabled: bool

# Return type for main functions
GraphData = Tuple[nx.DiGraph, List[ModuleInfo]]


# ----- PIPELINE PARSING FUNCTIONS -----
def extract_module_io(module: Dict[str, Any]) -> ModuleInfo:
    """
    Extract inputs and outputs of various data types from a CellProfiler module.
    
    Args:
        module: A dictionary representing a CellProfiler module from the pipeline JSON
        
    Returns:
        ModuleInfo object containing:
            - module_num: The number of the module in the pipeline
            - module_name: The name of the module
            - inputs: Dictionary of input data categories with data item names
            - outputs: Dictionary of output data categories with data item names
            - enabled: Boolean indicating if the module is enabled
    """
    # Initialize dictionaries for different types of inputs/outputs with proper typing
    inputs: ModuleInputs = {
        NODE_TYPE_IMAGE: [], 
        NODE_TYPE_OBJECT: [], 
        NODE_TYPE_IMAGE_LIST: [], 
        NODE_TYPE_OBJECT_LIST: []
    }
    
    outputs: ModuleOutputs = {
        NODE_TYPE_IMAGE: [],
        NODE_TYPE_OBJECT: [],
        # Note: Lists are typically consumed, not produced
    }

    # Get module identification from attributes
    module_attrs = module.get("attributes", {})
    module_num = module_attrs.get("module_num", 0)
    module_name = module_attrs.get("module_name", "Unknown")
    module_enabled = module_attrs.get("enabled", True)

    # Process each setting in the module
    for setting in module.get("settings", []):
        setting_name = setting.get("name", "")
        setting_value = setting.get("value", "")

        # Skip if value is "None" or empty
        if not setting_value or setting_value == "None":
            continue

        # Process input settings
        if setting_name == INPUT_IMAGE_TYPE:
            inputs[NODE_TYPE_IMAGE].append(setting_value)
        elif setting_name == INPUT_LABEL_TYPE:
            inputs[NODE_TYPE_OBJECT].append(setting_value)
        elif setting_name == INPUT_IMAGE_LIST_TYPE:
            # Split comma-separated list and add each item
            values = [v.strip() for v in setting_value.split(",") if v.strip()]
            inputs[NODE_TYPE_IMAGE_LIST].extend(values)
        elif setting_name == INPUT_LABEL_LIST_TYPE:
            # Split comma-separated list and add each item
            values = [v.strip() for v in setting_value.split(",") if v.strip()]
            inputs[NODE_TYPE_OBJECT_LIST].extend(values)

        # Process output settings
        elif setting_name == OUTPUT_IMAGE_TYPE:
            outputs[NODE_TYPE_IMAGE].append(setting_value)
        elif setting_name == OUTPUT_LABEL_TYPE:
            outputs[NODE_TYPE_OBJECT].append(setting_value)

    # Construct and return the module information
    return {
        "module_num": module_num,
        "module_name": module_name,
        "inputs": inputs,
        "outputs": outputs,
        "enabled": module_enabled,
    }


# ----- GRAPH CONSTRUCTION FUNCTIONS -----
def create_dependency_graph(
    pipeline_json: Dict[str, Any],
    include_disabled: bool = False,
    include_objects: bool = True,
    include_lists: bool = True,
    include_images: bool = True,
) -> GraphData:
    """
    Create a dependency graph showing data flow between modules.
    
    Args:
        pipeline_json: The JSON representation of a CellProfiler pipeline
        include_disabled: Whether to include disabled modules
        include_objects: Whether to include object data nodes
        include_lists: Whether to include list data nodes
        include_images: Whether to include image data nodes
        
    Returns:
        A tuple of (graph, modules_info) where:
            - graph is a NetworkX DiGraph representing the pipeline
            - modules_info is a list of ModuleInfo dictionaries
    """
    G = nx.DiGraph()
    
    # Data type filter configuration
    data_filters = {
        "include_images": include_images,
        "include_objects": include_objects,
        "include_lists": include_lists
    }

    # Process each module to build the graph
    modules_info: List[ModuleInfo] = []
    
    for module in pipeline_json.get("modules", []):
        # Extract module inputs and outputs
        module_info = extract_module_io(module)
        modules_info.append(module_info)

        # Skip disabled modules if not explicitly included
        if not module_info["enabled"] and not include_disabled:
            continue
            
        # Skip modules with no relevant I/O data based on data type filters
        if not _module_has_relevant_io(module_info, **data_filters):
            continue

        # Generate stable module ID and add module node
        stable_id = _create_stable_module_id(module_info, **data_filters)
        _add_module_node(G, module_info, stable_id)
        
        # Add data nodes and their connections to the module
        _add_module_data_connections(G, module_info, stable_id, **data_filters)

    return G, modules_info


def _module_has_relevant_io(
    module_info: ModuleInfo,
    include_images: bool,
    include_objects: bool, 
    include_lists: bool
) -> bool:
    """
    Check if a module has any inputs or outputs of enabled data types.
    
    Args:
        module_info: Module information dictionary from extract_module_io
        include_images: Whether to include image data
        include_objects: Whether to include object data
        include_lists: Whether to include list data
        
    Returns:
        True if the module has any relevant I/O, False otherwise
    """
    # Check inputs by data type
    for input_type, inputs in module_info["inputs"].items():
        # Skip empty input lists
        if not inputs:
            continue
            
        # Check against filter settings
        if input_type == NODE_TYPE_IMAGE and include_images:
            return True
        if input_type == NODE_TYPE_OBJECT and include_objects:
            return True
        if input_type in (NODE_TYPE_IMAGE_LIST, NODE_TYPE_OBJECT_LIST) and include_lists:
            return True
            
    # Check outputs by data type
    for output_type, outputs in module_info["outputs"].items():
        # Skip empty output lists
        if not outputs:
            continue
            
        # Check against filter settings
        if output_type == NODE_TYPE_IMAGE and include_images:
            return True
        if output_type == NODE_TYPE_OBJECT and include_objects:
            return True
            
    # No relevant I/O found
    return False


def _create_stable_module_id(
    module_info: ModuleInfo,
    include_images: bool,
    include_objects: bool,
    include_lists: bool
) -> str:
    """
    Create a stable unique identifier for a module based on its I/O pattern.
    
    Args:
        module_info: Module information dictionary from extract_module_io
        include_images: Whether to include image data
        include_objects: Whether to include object data
        include_lists: Whether to include list data
        
    Returns:
        A string identifier that is stable across runs and module reorderings
    """
    module_type = module_info["module_name"]
    
    # Collect all inputs/outputs for hash generation
    all_inputs: List[str] = []
    all_outputs: List[str] = []

    # Helper function to check if a data type should be included
    def should_include_type(data_type: str) -> bool:
        if data_type == NODE_TYPE_IMAGE:
            return include_images
        elif data_type == NODE_TYPE_OBJECT:
            return include_objects
        elif data_type in (NODE_TYPE_IMAGE_LIST, NODE_TYPE_OBJECT_LIST):
            return include_lists
        return False
    
    # Process inputs - only add those that match the filters
    for input_type, inputs in module_info["inputs"].items():
        if should_include_type(input_type):
            # Create prefixed input identifiers
            input_ids = [f"{input_type}__{inp}" for inp in inputs]
            all_inputs.extend(input_ids)

    # Process outputs - only add those that match the filters
    for output_type, outputs in module_info["outputs"].items():
        if should_include_type(output_type):
            # Create prefixed output identifiers
            output_ids = [f"{output_type}__{out}" for out in outputs]
            all_outputs.extend(output_ids)

    # Sort for deterministic ordering (crucial for consistent hashing)
    all_inputs.sort()
    all_outputs.sort()

    # Create a stable unique identifier using a deterministic hash function
    # We need to ensure our hash function matches the original implementation exactly
    
    # Format is: inputs|outputs where both are comma-separated and sorted
    io_pattern = ",".join(all_inputs) + "|" + ",".join(all_outputs)
    
    # Use SHA-256 hash which is deterministic across runs
    hash_obj = hashlib.sha256(io_pattern.encode('utf-8'))
    # Take exactly 8 hex characters as in the original
    hash_val = int(hash_obj.hexdigest()[:8], 16)
    
    # Format exactly as original: module_name_hash
    stable_id = f"{module_type}_{hash_val:x}"
    
    # Debug the hash generation
    #print(f"Hash for {module_type}: input='{io_pattern}', hash={hash_val:x}, id={stable_id}")
    
    return stable_id


def _add_module_node(G: nx.DiGraph, module_info: ModuleInfo, stable_id: str) -> None:
    """
    Add a module node to the graph with all relevant attributes.
    
    Args:
        G: The NetworkX graph to add the node to
        module_info: Module information dictionary
        stable_id: The stable identifier for the module
    """
    # Keep the original module number in the label for reference
    original_num = module_info["module_num"]
    module_name = module_info["module_name"]
    
    # Create human-readable label
    module_label = f"{module_name} #{original_num}"

    # Add disabled status to label if module is disabled
    if not module_info["enabled"]:
        module_label += " (disabled)"

    # Add module node with all relevant attributes
    G.add_node(
        stable_id,
        type=NODE_TYPE_MODULE,           # Node type identifier
        label=module_label,              # Display label
        module_name=module_name,         # Original module name
        module_num=module_info["module_num"],  # Original module number
        original_num=original_num,       # For reference
        stable_id=stable_id,             # The calculated stable ID
        enabled=module_info["enabled"],  # Enabled status
    )


def _add_module_data_connections(
    G: nx.DiGraph,
    module_info: ModuleInfo,
    stable_id: str,
    include_images: bool,
    include_objects: bool,
    include_lists: bool
) -> None:
    """
    Add all data nodes and their connections to a module in the graph.
    
    Args:
        G: The NetworkX graph
        module_info: Module information dictionary
        stable_id: The stable ID for the module
        include_images: Whether to include image data
        include_objects: Whether to include object data
        include_lists: Whether to include list data
    """
    # Add input connections (data nodes → module)
    _add_input_connections(G, module_info, stable_id, include_images, include_objects, include_lists)
    
    # Add output connections (module → data nodes)
    _add_output_connections(G, module_info, stable_id, include_images, include_objects)


def _add_input_connections(
    G: nx.DiGraph,
    module_info: ModuleInfo,
    stable_id: str,
    include_images: bool,
    include_objects: bool,
    include_lists: bool
) -> None:
    """
    Add all input data nodes and connections to the module in the graph.
    
    Args:
        G: The NetworkX graph
        module_info: Module information dictionary
        stable_id: The stable ID for the module
        include_images: Whether to include image data
        include_objects: Whether to include object data
        include_lists: Whether to include list data
    """
    # Helper function to check if a data type should be included
    def should_include_type(data_type: str) -> bool:
        if data_type == NODE_TYPE_IMAGE:
            return include_images
        elif data_type == NODE_TYPE_OBJECT:
            return include_objects
        elif data_type in (NODE_TYPE_IMAGE_LIST, NODE_TYPE_OBJECT_LIST):
            return include_lists
        return False
    
    # Process each input type
    for input_type, inputs in module_info["inputs"].items():
        # Skip if this data type is not included
        if not should_include_type(input_type):
            continue

        # Process each input item
        for input_item in inputs:
            # Create node ID with type prefix using double underscore to avoid dot port syntax
            node_id = f"{input_type}__{input_item}"

            # Add node if it doesn't exist
            if not G.has_node(node_id):
                G.add_node(
                    node_id, 
                    type=input_type,
                    name=input_item, 
                    label=input_item
                )

            # Add edge from input to module
            G.add_edge(
                node_id, 
                stable_id, 
                type=f"{input_type}_{EDGE_TYPE_INPUT}"
            )


def _add_output_connections(
    G: nx.DiGraph,
    module_info: ModuleInfo,
    stable_id: str,
    include_images: bool,
    include_objects: bool
) -> None:
    """
    Add all output data nodes and connections from the module in the graph.
    
    Args:
        G: The NetworkX graph
        module_info: Module information dictionary
        stable_id: The stable ID for the module
        include_images: Whether to include image data
        include_objects: Whether to include object data
    """
    # Helper function to check if a data type should be included
    def should_include_type(data_type: str) -> bool:
        if data_type == NODE_TYPE_IMAGE:
            return include_images
        elif data_type == NODE_TYPE_OBJECT:
            return include_objects
        return False
    
    # Process each output type
    for output_type, outputs in module_info["outputs"].items():
        # Skip if this data type is not included
        if not should_include_type(output_type):
            continue

        # Process each output item
        for output_item in outputs:
            # Create node ID with type prefix using double underscore to avoid dot port syntax
            node_id = f"{output_type}__{output_item}"

            # Add node if it doesn't exist
            if not G.has_node(node_id):
                G.add_node(
                    node_id, 
                    type=output_type, 
                    name=output_item, 
                    label=output_item
                )

            # Add edge from module to output
            G.add_edge(
                stable_id, 
                node_id, 
                type=f"{output_type}_{EDGE_TYPE_OUTPUT}"
            )


# ----- GRAPH FORMATTING AND OUTPUT -----
def apply_node_styling(G: nx.DiGraph, no_formatting: bool = False) -> None:
    """
    Apply visual styling attributes to graph nodes based on their types.
    
    Args:
        G: The NetworkX graph
        no_formatting: If True, skip applying styling attributes
    """
    # Skip styling if formatting is disabled
    if no_formatting:
        return
        
    # Process each node in the graph
    for node, attrs in G.nodes(data=True):
        node_type = attrs.get("type")
        
        # Apply basic styling common to all node types
        if node_type in STYLE_SHAPES:
            G.nodes[node]["shape"] = STYLE_SHAPES[node_type]
            
        # Apply type-specific styling
        if node_type == NODE_TYPE_MODULE:
            # Module node styling
            _apply_module_node_styling(G, node, attrs)
        elif node_type in (NODE_TYPE_IMAGE, NODE_TYPE_OBJECT):
            # Data nodes (image, object) styling
            _apply_data_node_styling(G, node, node_type)
        elif node_type in (NODE_TYPE_IMAGE_LIST, NODE_TYPE_OBJECT_LIST):
            # List nodes styling
            _apply_list_node_styling(G, node, node_type)


def _apply_module_node_styling(G: nx.DiGraph, node: str, attrs: Dict[str, Any]) -> None:
    """
    Apply styling specific to module nodes.
    
    Args:
        G: The NetworkX graph
        node: The node identifier
        attrs: Node attributes
    """
    # Base style for all module nodes
    G.nodes[node]["style"] = "filled"
    G.nodes[node]["fontname"] = "Helvetica-Bold"
    
    # Style enabled/disabled modules differently
    if attrs.get("enabled", True):
        # Enabled module
        G.nodes[node]["fillcolor"] = STYLE_COLORS[NODE_TYPE_MODULE]["enabled"]
    else:
        # Disabled module
        G.nodes[node]["fillcolor"] = STYLE_COLORS[NODE_TYPE_MODULE]["disabled"]
        G.nodes[node]["style"] = "filled,dashed"  # Add dashed border


def _apply_data_node_styling(G: nx.DiGraph, node: str, node_type: str) -> None:
    """
    Apply styling specific to data nodes (images, objects).
    
    Args:
        G: The NetworkX graph
        node: The node identifier
        node_type: The type of the node
    """
    # Apply common styling for data nodes
    G.nodes[node]["style"] = "filled"
    
    # Apply type-specific color
    if node_type in STYLE_COLORS:
        G.nodes[node]["fillcolor"] = STYLE_COLORS[node_type]


def _apply_list_node_styling(G: nx.DiGraph, node: str, node_type: str) -> None:
    """
    Apply styling specific to list nodes.
    
    Args:
        G: The NetworkX graph
        node: The node identifier
        node_type: The type of the node
    """
    # Special style for list nodes (rounded boxes)
    G.nodes[node]["style"] = "filled,rounded"
    
    # Apply type-specific color
    if node_type in STYLE_COLORS:
        G.nodes[node]["fillcolor"] = STYLE_COLORS[node_type]


def prepare_for_dot_output(G: nx.DiGraph, ultra_minimal: bool = False) -> nx.DiGraph:
    """
    Prepare graph for DOT format output with consistent ordering.
    
    Args:
        G: The original NetworkX graph
        ultra_minimal: If True, create a stripped-down version with only essential structure
        
    Returns:
        A new NetworkX DiGraph prepared for DOT output
    """
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
        # Set proper display labels for all nodes
        for node, attrs in G.nodes(data=True):
            node_type = attrs.get("type")

            if node_type == NODE_TYPE_MODULE:
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

        # Add nodes in sorted order by name for consistent output
        for node in sorted(G.nodes()):
            G_ordered.add_node(node, **G.nodes[node])

        # Add edges in sorted order
        edge_list = sorted(G.edges(data=True), key=lambda x: (x[0], x[1]))
        for src, dst, attrs in edge_list:
            G_ordered.add_edge(src, dst, **attrs)
            
    return G_ordered


def write_graph_to_file(G: nx.DiGraph, output_path: str, ultra_minimal: bool = False) -> None:
    """
    Write the graph to the specified output file in the appropriate format.
    
    Args:
        G: The NetworkX graph
        output_path: Path to write the output file
        ultra_minimal: If True, create a stripped-down version for exact diff comparison
    """
    ext = Path(output_path).suffix.lower()

    if ext == ".graphml":
        nx.write_graphml(G, output_path)
    elif ext == ".gexf":
        nx.write_gexf(G, output_path)
    elif ext == ".dot":
        try:
            # For DOT format, prepare the graph with consistent ordering
            G_ordered = prepare_for_dot_output(G, ultra_minimal)
            nx.drawing.nx_pydot.write_dot(G_ordered, output_path)
        except ImportError:
            print("Warning: pydot not available. Saving as GraphML instead.")
            nx.write_graphml(G, output_path.replace(ext, ".graphml"))
    else:
        # Default to GraphML
        nx.write_graphml(G, output_path)

    print(f"Graph saved to: {output_path}")


def print_pipeline_summary(G: nx.DiGraph, pipeline_path: str) -> None:
    """
    Print a summary of the pipeline graph structure.
    
    Args:
        G: The NetworkX graph
        pipeline_path: Path to the original pipeline file
    """
    # Print pipeline summary
    print(f"Pipeline: {pipeline_path}")

    # Count different node types
    node_counts = {}
    for n, attr in G.nodes(data=True):
        node_type = attr.get("type")
        if node_type not in node_counts:
            node_counts[node_type] = 0
        node_counts[node_type] += 1

    module_nodes = [n for n, attr in G.nodes(data=True) if attr.get("type") == NODE_TYPE_MODULE]
    enabled_modules = [n for n in module_nodes if G.nodes[n].get("enabled", True)]
    disabled_modules = [n for n in module_nodes if not G.nodes[n].get("enabled", True)]

    # Print node type counts
    print("Graph contains:")
    for node_type, count in sorted(node_counts.items()):
        if node_type == NODE_TYPE_MODULE:
            print(
                f"  {count} modules ({len(enabled_modules)} enabled, {len(disabled_modules)} disabled)"
            )
        else:
            print(f"  {count} {node_type} nodes")
    print(f"  {len(G.edges())} total connections")


def print_connections(G: nx.DiGraph) -> None:
    """
    Print a human-readable summary of graph connections.
    
    Args:
        G: The NetworkX graph
    """
    print("\nConnections:")
    for edge in G.edges(data=True):
        src, dst, attrs = edge
        src_type = G.nodes[src].get("type")
        dst_type = G.nodes[dst].get("type")

        # Only show module connections
        if dst_type == NODE_TYPE_MODULE:
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

        elif src_type == NODE_TYPE_MODULE:
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


def print_stable_id_mapping(G: nx.DiGraph) -> None:
    """
    Print a mapping of stable module IDs to their original module numbers.
    
    Args:
        G: The NetworkX graph
    """
    print("\nStable module ID mapping:")
    module_nodes = [
        n for n, attr in G.nodes(data=True) if attr.get("type") == NODE_TYPE_MODULE
    ]
    for node in sorted(module_nodes):
        attrs = G.nodes[node]
        orig_num = attrs.get("original_num", "?")
        module_name = attrs.get("module_name", "Unknown")
        enabled = "" if attrs.get("enabled", True) else " (disabled)"
        print(f"  {node} → {module_name} #{orig_num}{enabled}")


# ----- MAIN EXECUTION AND CLI -----
def process_pipeline(
    pipeline_path: str,
    output_path: Optional[str] = None,
    no_module_info: bool = False,
    include_disabled: bool = False,
    no_formatting: bool = False,
    ultra_minimal: bool = False,
    include_objects: bool = True,
    include_lists: bool = True,
    include_images: bool = True,
    explain_ids: bool = False,
    quiet: bool = False,
) -> GraphData:
    """
    Process a CellProfiler pipeline and create a dependency graph.
    
    This is the main processing function that coordinates loading, graph creation,
    visualization and output.
    
    Args:
        pipeline_path: Path to the CellProfiler pipeline JSON file
        output_path: Path to save the generated graph file
        no_module_info: Whether to hide module information on graph edges
        include_disabled: Whether to include disabled modules in the graph
        no_formatting: Whether to strip formatting information from graph output
        ultra_minimal: Whether to create minimal output for exact diff comparison
        include_objects: Whether to include object data nodes
        include_lists: Whether to include list data nodes
        include_images: Whether to include image data nodes
        explain_ids: Whether to print a mapping of stable IDs
        quiet: Whether to suppress output
        
    Returns:
        A tuple of (graph, modules_info) where:
            - graph is a NetworkX DiGraph representing the pipeline
            - modules_info is a list of module information dictionaries
    """
    # Load the pipeline JSON
    try:
        with open(pipeline_path, "r") as f:
            pipeline = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise click.ClickException(f"Error loading pipeline file: {e}")

    # Create the graph with specified data types
    G, modules_info = create_dependency_graph(
        pipeline,
        include_disabled=include_disabled,
        include_objects=include_objects,
        include_lists=include_lists,
        include_images=include_images,
    )

    # Print information about the pipeline if not quiet
    if not quiet:
        print_pipeline_summary(G, pipeline_path)
        print_connections(G)
        
        # Explain stable IDs if requested
        if explain_ids:
            print_stable_id_mapping(G)

    # Save the graph if requested
    if output_path:
        # Apply node styling if formatting is enabled
        apply_node_styling(G, no_formatting)
        
        # If no_module_info is True, simplify edges
        if no_module_info:
            for edge in G.edges():
                # Remove any edge labels
                if "label" in G.edges[edge]:
                    del G.edges[edge]["label"]
        
        # Write the graph to the specified file
        write_graph_to_file(G, output_path, ultra_minimal)

    return G, modules_info


class DataTypeChoice:
    """Helper class to manage data type filtering options"""
    ALL = "all"
    IMAGES_ONLY = "images_only"
    OBJECTS_ONLY = "objects_only"
    NO_LISTS = "no_lists"


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("pipeline", type=click.Path(exists=True, dir_okay=False, readable=True))
@click.argument("output", type=click.Path(dir_okay=False, writable=True), required=False)
# Display options
@click.option("--no-module-info", is_flag=True, help="Hide module information on graph edges")
@click.option("--no-formatting", is_flag=True, help="Strip formatting (colors, shapes, etc.)")
@click.option("--ultra-minimal", is_flag=True, help="Create minimal output for exact diff comparison")
@click.option("--explain-ids", is_flag=True, help="Print mapping of stable IDs to module numbers")
# Content filtering options
@click.option("--include-disabled", is_flag=True, help="Include disabled modules in the graph")
# Output options
@click.option("--quiet", "-q", is_flag=True, help="Suppress informational output")
# Data type selection as a mutually exclusive choice
@click.option("--data-type", 
              type=click.Choice([DataTypeChoice.ALL, 
                               DataTypeChoice.IMAGES_ONLY, 
                               DataTypeChoice.OBJECTS_ONLY, 
                               DataTypeChoice.NO_LISTS], 
                              case_sensitive=False),
              default=DataTypeChoice.ALL,
              help="Filter data types to include in the graph")
def cli(
    pipeline: str,
    output: Optional[str],
    no_module_info: bool,
    no_formatting: bool,
    ultra_minimal: bool,
    explain_ids: bool,
    include_disabled: bool,
    quiet: bool,
    data_type: str,
) -> None:
    """
    Create a graph representation of a CellProfiler pipeline.
    
    PIPELINE: Path to the CellProfiler pipeline JSON file
    
    OUTPUT: Optional path for output graph file (.graphml, .gexf, or .dot)
    
    Examples:
    
    \b
    # Basic usage - creates DOT file from pipeline
    python cp_graph.py examples/illum.json examples/output/illum_graph.dot
    
    \b
    # Create ultra-minimal output for comparing pipeline structure
    python cp_graph.py examples/illum.json examples/output/illum_ultra.dot --ultra-minimal
    
    \b
    # View only image data flow
    python cp_graph.py examples/analysis.json examples/output/analysis_images.dot --data-type images_only
    """
    # Determine what data types to include based on choice
    include_objects = data_type != DataTypeChoice.IMAGES_ONLY
    include_lists = data_type not in (DataTypeChoice.NO_LISTS, DataTypeChoice.OBJECTS_ONLY)
    include_images = data_type != DataTypeChoice.OBJECTS_ONLY
    
    try:
        # Run the main processing function
        process_pipeline(
            pipeline,
            output,
            no_module_info,
            include_disabled,
            no_formatting,
            ultra_minimal,
            include_objects=include_objects,
            include_lists=include_lists,
            include_images=include_images,
            explain_ids=explain_ids,
            quiet=quiet,
        )
    except click.ClickException as e:
        e.show()
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
