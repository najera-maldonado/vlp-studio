#!/bin/bash

# Universal setup script for SIRAH capsid simulations
# Auto-detects capside-*-cg.pdb files and configures gensystem.leap

# Find capsid file
CAPSID_FILE=$(ls capside-*-cg.pdb 2>/dev/null | head -1)

if [ -z "$CAPSID_FILE" ]; then
    echo "Error: No capside-*-cg.pdb file found"
    exit 1
fi

# Extract base name for outputs (remove -cg.pdb suffix)
BASE_NAME=$(basename "$CAPSID_FILE" -cg.pdb)
OUTPUT_BASE="${BASE_NAME}-cg-WAT"

echo "Found capsid file: $CAPSID_FILE"
echo "Output base name: $OUTPUT_BASE"

# Create working gensystem.leap from template
cp gensystem.leap gensystem_working.leap

# Replace placeholders
sed -i "s/AUTO_DETECT_CAPSID/$CAPSID_FILE/g" gensystem_working.leap
sed -i "s/AUTO_DETECT_OUTPUT/$OUTPUT_BASE/g" gensystem_working.leap

echo "Generated gensystem_working.leap for $CAPSID_FILE"
echo "Outputs will be: ${OUTPUT_BASE}.prmtop, ${OUTPUT_BASE}.ncrst, ${OUTPUT_BASE}.pdb"

# Run LEaP
echo "Running LEaP..."
tleap -f gensystem_working.leap

if [ $? -eq 0 ]; then
    echo "SUCCESS: System setup completed"
    echo "Generated files:"
    ls -la ${OUTPUT_BASE}.*
else
    echo "ERROR: LEaP failed"
    exit 1
fi