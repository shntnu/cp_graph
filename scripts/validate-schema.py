#!/usr/bin/env -S pixi exec --spec jsonschema -- python
#!/usr/bin/env python3
"""
JSON Schema validation script for CellProfiler dependency graphs.
Reads a JSON schema and validates a JSON file against it.
"""

import json
import sys
import argparse
from pathlib import Path
try:
    import jsonschema
    from jsonschema import validate, ValidationError, SchemaError
except ImportError:
    print("Error: jsonschema package is required.")
    sys.exit(1)


def load_json_file(file_path):
    """Load and parse a JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{file_path}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading '{file_path}': {e}")
        sys.exit(1)


def validate_json_against_schema(json_data, schema_data, json_file_path):
    """Validate JSON data against a schema"""
    try:
        # First, validate that the schema itself is valid
        jsonschema.Draft7Validator.check_schema(schema_data)
        # print("✓ Schema is valid")
        
        # Then validate the JSON data against the schema
        validate(instance=json_data, schema=schema_data)
        print(f"✓ '{json_file_path}' is valid against the schema")
        return True
        
    except SchemaError as e:
        print(f"✗ Schema error: {e.message}")
        if hasattr(e, 'path') and e.path:
            print(f"  Path: {' -> '.join(str(p) for p in e.path)}")
        return False
        
    except ValidationError as e:
        print(f"✗ Validation error in '{json_file_path}': {e.message}")
        if hasattr(e, 'absolute_path') and e.absolute_path:
            print(f"  Path: {' -> '.join(str(p) for p in e.absolute_path)}")
        if hasattr(e, 'instance'):
            print(f"  Invalid value: {e.instance}")
        return False
        
    except Exception as e:
        print(f"✗ Unexpected error during validation: {e}")
        return False


def print_summary(json_data):
    """Print a summary of the dependency graph"""
    try:
        if 'metadata' in json_data:
            metadata = json_data['metadata']
            print(f"\nDependency Graph Summary:")
            print(f"  Total modules: {metadata.get('total_modules', 'unknown')}")
            print(f"  Total edges: {metadata.get('total_edges', 'unknown')}")
        
        if 'modules' in json_data:
            modules = json_data['modules']
            print(f"  Module count (actual): {len(modules)}")
            
            # Count dependency types
            image_deps = object_deps = measurement_deps = 0
            for module in modules:
                for dep_list in [module.get('inputs', []), module.get('outputs', [])]:
                    for dep in dep_list:
                        dep_type = dep.get('type', '')
                        if dep_type == 'image':
                            image_deps += 1
                        elif dep_type == 'object':
                            object_deps += 1
                        elif dep_type == 'measurement':
                            measurement_deps += 1
            
            print(f"  Image dependencies: {image_deps}")
            print(f"  Object dependencies: {object_deps}")
            print(f"  Measurement dependencies: {measurement_deps}")
            
    except Exception as e:
        print(f"Warning: Could not generate summary: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate a JSON file against the CellProfiler dependency graph schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_dependency_json.py data.json
  python validate_dependency_json.py --summary pipeline-deps.json
        """
    )
    
    parser.add_argument(
        'json_file',
        help='Path to the JSON file to validate'
    )
    
    parser.add_argument(
        '--summary', '-s',
        action='store_true',
        help='Print a summary of the dependency graph after validation'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Fixed schema path
    schema_path = Path(__file__).resolve().parent
    schema_path = Path(f"{schema_path}/../cp5-dep-graph-schema.json")
    json_path = Path(args.json_file).expanduser()
    
    if not schema_path.exists():
        print(f"Error: Schema file '{schema_path}' does not exist")
        print("Make sure the schema file is located at '../cp5-dep-graph-schema.json'")
        sys.exit(1)
        
    if not json_path.exists():
        print(f"Error: JSON file '{json_path}' does not exist")
        sys.exit(1)
    
    if args.verbose:
        print(f"Schema file: {schema_path} (fixed location)")
        print(f"JSON file: {json_path}")
        print()
    
    # Load files
    print("Loading files...")

    schema_data = load_json_file(schema_path)
    json_data = load_json_file(json_path)
    
    if args.verbose:
        print(f"✓ Loaded schema ({len(json.dumps(schema_data))} bytes)")
        print(f"✓ Loaded JSON data ({len(json.dumps(json_data))} bytes)")
        print()
    
    # Validate
    print("Validating...")

    is_valid = validate_json_against_schema(json_data, schema_data, json_path)
    
    # Print summary if requested and validation passed
    if args.summary and is_valid:
        print_summary(json_data)
    
    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
