#!/usr/bin/env -S bash

uv run --script cp_graph.py --remove-unused-data --highlight-filtered --filter-objects "examples/${1}.json" "examples/output/${1}.dot" && pixi exec --spec "graphviz" dot -Tpng "examples/output/${1}.dot" -o "examples/output/${1}.png" && kitten icat "examples/output/${1}.png"
