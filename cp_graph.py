# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "networkx",
# ]
#
# ///

#!/usr/bin/env python

import json
import networkx as nx
import sys
from pathlib import Path

# Constants for the specific setting types we're looking for
INPUT_IMAGE_TYPE = "cellprofiler_core.setting.subscriber.image_subscriber._image_subscriber.ImageSubscriber"
OUTPUT_IMAGE_TYPE = "cellprofiler_core.setting.text.alphanumeric.name.image_name._image_name.ImageName"

def extract_module_io(module):
    """Extract input and output images from a module"""
    input_images = []
    output_images = []
    
    # Get module identification
    module_attrs = module.get("attributes", {})
    module_num = module_attrs.get("module_num", 0)
    module_name = module_attrs.get("module_name", "Unknown")
    
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
        "outputs": output_images
    }

def create_image_dependency_graph(pipeline_json):
    """Create a dependency graph from images flowing between modules"""
    G = nx.DiGraph()
    
    # Process each module to build the graph
    modules_io = []
    for module in pipeline_json.get("modules", []):
        module_io = extract_module_io(module)
        modules_io.append(module_io)
        
        # Add all images as nodes
        for image in module_io["inputs"] + module_io["outputs"]:
            if not G.has_node(image):
                G.add_node(image, type="image")
                
        # Add edges from each module's inputs to its outputs
        for input_img in module_io["inputs"]:
            for output_img in module_io["outputs"]:
                G.add_edge(
                    input_img, 
                    output_img, 
                    module=module_io["module_name"],
                    module_num=module_io["module_num"]
                )
    
    return G, modules_io

def main(pipeline_path, output_path=None):
    """Process a CellProfiler pipeline and create an image dependency graph"""
    # Load the pipeline JSON
    with open(pipeline_path, 'r') as f:
        pipeline = json.load(f)
    
    # Create the graph
    G, modules_io = create_image_dependency_graph(pipeline)
    
    # Print pipeline summary
    print(f"Pipeline: {pipeline_path}")
    print(f"Graph has {len(G.nodes())} images and {len(G.edges())} connections")
    
    # Print image connections
    print("\nImage Connections:")
    for edge in G.edges(data=True):
        src, dst, attrs = edge
        print(f"  {src} → {dst} (Module: {attrs['module']} #{attrs['module_num']})")
    
    # Save the graph if requested
    if output_path:
        ext = Path(output_path).suffix.lower()
        
        if ext == '.graphml':
            nx.write_graphml(G, output_path)
        elif ext == '.gexf':
            nx.write_gexf(G, output_path)
        elif ext == '.dot':
            try:
                nx.drawing.nx_pydot.write_dot(G, output_path)
            except ImportError:
                print("Warning: pydot not available. Saving as GraphML instead.")
                nx.write_graphml(G, output_path.replace(ext, '.graphml'))
        else:
            # Default to GraphML
            nx.write_graphml(G, output_path)
        
        print(f"Graph saved to: {output_path}")
    
    return G, modules_io

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cp_dependency_graph.py pipeline.json [output_graph.graphml]")
        sys.exit(1)
    
    pipeline_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    main(pipeline_path, output_path)
