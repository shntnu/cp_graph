#!/usr/bin/env bash
#
# Regenerate all example outputs for the cp_graph documentation
# ⚠️  WARNING: Overwrites test reference files! Only run from main branch or after verifying fixes.
#
# Usage: ./scripts/regenerate_all_examples.sh

set -e  # Exit on error

echo "Regenerating all example outputs..."

# Create output directory if it doesn't exist
mkdir -p examples/output

# ========================================
# Basic Examples (illum pipeline)
# ========================================
echo "Generating illum examples..."

# Basic graph
./cp_graph.py examples/illum.json examples/output/illum.dot
pixi exec --spec "graphviz" dot -Tpng examples/output/illum.dot -o examples/output/illum.png

# Highlighted filtering
./cp_graph.py examples/illum.json examples/output/illum_highlight.dot \
    --root-nodes=OrigDNA --remove-unused-images --highlight-filtered
pixi exec --spec "graphviz" dot -Tpng examples/output/illum_highlight.dot -o examples/output/illum_highlight.png

# Filtered (nodes removed)
./cp_graph.py examples/illum.json examples/output/illum_filtered.dot \
    --root-nodes=OrigDNA --remove-unused-images
pixi exec --spec "graphviz" dot -Tpng examples/output/illum_filtered.dot -o examples/output/illum_filtered.png

# Ultra minimal for comparison
./cp_graph.py examples/illum.json examples/output/illum_ultra.dot --ultra-minimal
./cp_graph.py examples/illum_isoform.json examples/output/illum_isoform_ultra.dot --ultra-minimal
./cp_graph.py examples/illum_mod.json examples/output/illum_mod_ultra.dot --ultra-minimal

# # Additional examples from Advanced Usage section
# # These are not rendered in the documentation, but are mentioned in the README.md as examples.
# echo "Generating additional advanced examples..."

# # Include disabled modules
# ./cp_graph.py examples/illum.json examples/output/illum_disabled.dot --include-disabled
# pixi exec --spec "graphviz" dot -Tpng examples/output/illum_disabled.dot -o examples/output/illum_disabled.png

# # Show module ID mappings
# ./cp_graph.py examples/illum.json examples/output/illum_ids.dot --explain-ids
# pixi exec --spec "graphviz" dot -Tpng examples/output/illum_ids.dot -o examples/output/illum_ids.png

# # Node ranking for better layout
# ./cp_graph.py examples/illum.json examples/output/illum_ranked.dot --rank-nodes
# pixi exec --spec "graphviz" dot -Tpng examples/output/illum_ranked.dot -o examples/output/illum_ranked.png

# ========================================
# Complex Analysis Pipeline
# ========================================
echo "Generating analysis pipeline examples..."

# Basic analysis graph
./cp_graph.py examples/analysis.json examples/output/analysis.dot
pixi exec --spec "graphviz" dot -Tpng examples/output/analysis.dot -o examples/output/analysis.png

# Filtered analysis (main README example)
./cp_graph.py \
   examples/analysis.json \
   examples/output/analysis_filtered.dot \
   --rank-nodes \
   --remove-unused-images \
   --exclude-module-types=ExportToSpreadsheet \
   --highlight-filtered \
   --rank-ignore-filtered \
   --root-nodes=CorrPhalloidin,CorrZO1,CorrDNA,Cycle01_DAPI,Cycle01_A,Cycle01_T,Cycle01_G,Cycle01_C,Cycle02_DAPI,Cycle02_A,Cycle02_T,Cycle02_G,Cycle02_C,Cycle03_DAPI,Cycle03_A,Cycle03_T,Cycle03_G,Cycle03_C
pixi exec --spec "graphviz" dot -Tpng examples/output/analysis_filtered.dot -o examples/output/analysis_filtered.png

# # Additional examples
# # These are not rendered in the documentation, but are mentioned in the README.md as examples.
# # Ranked and filtered analysis
# ./cp_graph.py \
#    examples/analysis.json \
#    examples/output/analysis_ranked_filtered.dot \
#    --rank-nodes \
#    --root-nodes=CorrPhalloidin,CorrZO1 \
#    --remove-unused-images
# pixi exec --spec "graphviz" dot -Tpng examples/output/analysis_ranked_filtered.dot -o examples/output/analysis_ranked_filtered.png

# # Clean ranked with highlighted filtering
# ./cp_graph.py \
#    examples/analysis.json \
#    examples/output/analysis_clean_ranked.dot \
#    --rank-nodes \
#    --rank-ignore-filtered \
#    --root-nodes=CorrPhalloidin,CorrZO1 \
#    --highlight-filtered
# pixi exec --spec "graphviz" dot -Tpng examples/output/analysis_clean_ranked.dot -o examples/output/analysis_clean_ranked.png

# ========================================
# CellProfiler 5 Dependency Graphs
# ========================================
echo "Generating CP5 dependency graph examples..."

# Basic ExampleFly dependency graph
./cp_graph.py examples/ExampleFly.json examples/output/ExampleFly.dot --highlight-filtered --rank-nodes --remove-unused-objects --remove-unused-images
pixi exec --spec "graphviz" dot -Tpng examples/output/ExampleFly.dot -o examples/output/ExampleFly.png

# ExampleFly with measurements shown (filtered)
./cp_graph.py --remove-unused-objects --remove-unused-measurements --dependency-graph \
    examples/ExampleFly-dep-graph.json examples/output/ExampleFly-measurement.dot
pixi exec --spec "graphviz" dot -Tpng examples/output/ExampleFly-measurement.dot -o examples/output/ExampleFly-measurement.png

# ExampleFly with measurements and liveness styling
./cp_graph.py --dependency-graph --remove-unused-measurements --track-liveness --rank-nodes \
  examples/ExampleFlyMeas-liveness-dep.json examples/output/ExampleFly-liveness.dot
pixi exec --spec "graphviz" dot -Tpng examples/output/ExampleFly-liveness.dot -o examples/output/ExampleFly-liveness.png

echo "Done! All example outputs have been regenerated."
echo "Files created in: examples/output/"
