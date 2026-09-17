#!/bin/bash

# Universal Flexible MD script for both pmemd.cuda and sander
# Auto-detects capside-*-cg-WAT pattern files or allows manual specification

# Usage function
show_usage() {
    echo "Universal MD Simulation Script for capside-*-cg-WAT systems"
    echo ""
    echo "Usage: $0 [engine] [system_name] [topology_file]"
    echo ""
    echo "Parameters:"
    echo "  engine       : 'cuda' (default) or 'sander'"
    echo "  system_name  : System name (auto-detected if not provided)"
    echo "  topology_file: Topology file (defaults to system_name.prmtop)"
    echo ""
    echo "Examples:"
    echo "  $0                                           # Auto-detect capside-*-cg-WAT files"
    echo "  $0 cuda                                      # Use CUDA with auto-detection"
    echo "  $0 cuda capside-1_5-cg-WAT                  # Specify system name"
    echo "  $0 sander capside-3_1-cg-WAT                # Use sander with specific system"
    echo "  $0 cuda capside-2_3-cg-WAT capside-2_3-cg-WAT.prmtop  # Full specification"
    echo ""
    echo "File Requirements:"
    echo "  - Topology file: [system_name].prmtop"
    echo "  - Coordinates: [system_name].ncrst (or .rst, .rst7, .inpcrd)"
    echo "  - Input files: em1_WT4.in, em2_WT4.in, eq1_WT4.in, eq2_WT4.in, prod_md_WT4.in"
    echo ""
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

# Function to auto-detect capside-*-cg-WAT files
auto_detect_system() {
    local detected_files=($(ls capside-*-cg-WAT.prmtop 2>/dev/null))

    if [ ${#detected_files[@]} -eq 0 ]; then
        echo "No capside-*-cg-WAT.prmtop files found in current directory" >&2
        return 1
    elif [ ${#detected_files[@]} -eq 1 ]; then
        local prmtop_file="${detected_files[0]}"
        local system_name="${prmtop_file%.prmtop}"
        echo "Auto-detected system: $system_name" >&2
        echo "$system_name"
        return 0
    else
        echo "Multiple capside-*-cg-WAT.prmtop files found:" >&2
        for i in "${!detected_files[@]}"; do
            echo "  $((i+1)): ${detected_files[i]}" >&2
        done
        echo "Please specify which system to use as second argument" >&2
        return 1
    fi
}

# Set default parameters
ENGINE=${1:-cuda}  # cuda or sander

# Auto-detect or use provided system name
if [ -z "$2" ]; then
    echo "Attempting to auto-detect capside-*-cg-WAT system..."
    DETECTED_NAME=$(auto_detect_system)
    if [ $? -ne 0 ]; then
        echo "Auto-detection failed. Please specify system name as second argument."
        exit 1
    fi
    NAME="$DETECTED_NAME"
    PRMTOP="${NAME}.prmtop"
else
    NAME="$2"
    PRMTOP=${3:-${NAME}.prmtop}
fi

# Export GPU device for CUDA
export CUDA_VISIBLE_DEVICES="0"

# Determine which executable to use
if [ "$ENGINE" = "cuda" ]; then
    MD_EXE="pmemd.cuda"
    echo "Using pmemd.cuda (GPU acceleration)"
elif [ "$ENGINE" = "sander" ]; then
    MD_EXE="sander"
    echo "Using sander (CPU)"
else
    echo "Error: Engine must be 'cuda' or 'sander'"
    exit 1
fi

# Enhanced file validation
echo "Validating required files..."

# Check topology file
if [ ! -f "$PRMTOP" ]; then
    echo "Error: Topology file $PRMTOP not found"
    echo "Looking for available topology files:"
    ls -la *.prmtop 2>/dev/null || echo "  No .prmtop files found in current directory"
    exit 1
fi

# Check initial coordinate file
COORD_FILE="${NAME}.ncrst"
if [ ! -f "$COORD_FILE" ]; then
    echo "Error: Initial coordinate file $COORD_FILE not found"
    echo "Looking for available coordinate files:"
    ls -la *.ncrst *.rst *.rst7 *.inpcrd 2>/dev/null || echo "  No coordinate files found in current directory"

    # Try alternative coordinate file extensions
    for ext in rst rst7 inpcrd; do
        if [ -f "${NAME}.${ext}" ]; then
            COORD_FILE="${NAME}.${ext}"
            echo "Found alternative coordinate file: $COORD_FILE"
            break
        fi
    done

    if [ ! -f "$COORD_FILE" ]; then
        exit 1
    fi
fi

# Validate input files exist
echo "Checking input files..."
missing_inputs=()
for input_file in em1_WT4.in em2_WT4.in heat1_0to50.in heat2_50to100.in heat3_100to150.in heat4_150to200.in heat5_200to250.in heat6_250to300.in density_eq.in eq1_WT4.in eq2_WT4.in final_eq.in prod_md_WT4.in; do
    if [ ! -f "$input_file" ]; then
        missing_inputs+=("$input_file")
    fi
done

if [ ${#missing_inputs[@]} -gt 0 ]; then
    echo "Warning: Missing input files: ${missing_inputs[*]}"
    echo "Available .in files:"
    ls -la *.in 2>/dev/null || echo "  No .in files found"
    echo "Continuing with available input files..."
fi

echo "Starting MD simulation with:"
echo "  Engine: $MD_EXE"
echo "  System: $NAME"
echo "  Topology: $PRMTOP"
echo "  Initial coordinates: $COORD_FILE"
echo ""

# Step 1: Energy minimization 1
echo "=== Step 1: Energy Minimization 1 ==="
if [ -f "em1_WT4.in" ]; then
    $MD_EXE -O -i em1_WT4.in -p $PRMTOP -c $COORD_FILE -ref $COORD_FILE -o ${NAME}_em1.out -r ${NAME}_em1.ncrst
    if [ $? -ne 0 ]; then
        echo "Error in minimization step 1"
        exit 1
    fi
    echo "Minimization 1 completed successfully"
else
    echo "Warning: em1_WT4.in not found, skipping minimization 1"
fi

# Step 2: Energy minimization 2
echo "=== Step 2: Energy Minimization 2 ==="
if [ -f "em2_WT4.in" ]; then
    $MD_EXE -O -i em2_WT4.in -p $PRMTOP -c ${NAME}_em1.ncrst -o ${NAME}_em2.out -r ${NAME}_em2.ncrst
    if [ $? -ne 0 ]; then
        echo "Error in minimization step 2"
        exit 1
    fi
    echo "Minimization 2 completed successfully"
else
    echo "Warning: em2_WT4.in not found, skipping minimization 2"
fi

# Step 3: Gradual Heating (0K to 300K in 6 steps)
echo "=== Step 3a: Gradual Heating 0K to 50K ==="
if [ -f "heat1_0to50.in" ]; then
    $MD_EXE -O -i heat1_0to50.in -p $PRMTOP -c ${NAME}_em2.ncrst -ref ${NAME}_em2.ncrst -o ${NAME}_heat1.out -r ${NAME}_heat1.ncrst
    if [ $? -ne 0 ]; then
        echo "Error in heating step 1"
        exit 1
    fi
    echo "Heating 1 (0K->50K) completed successfully"
else
    echo "Warning: heat1_0to50.in not found, skipping gradual heating"
fi

echo "=== Step 3b: Gradual Heating 50K to 100K ==="
if [ -f "heat2_50to100.in" ]; then
    $MD_EXE -O -i heat2_50to100.in -p $PRMTOP -c ${NAME}_heat1.ncrst -ref ${NAME}_heat1.ncrst -o ${NAME}_heat2.out -r ${NAME}_heat2.ncrst
    if [ $? -ne 0 ]; then
        echo "Error in heating step 2"
        exit 1
    fi
    echo "Heating 2 (50K->100K) completed successfully"
else
    echo "Warning: heat2_50to100.in not found, skipping heating step 2"
fi

echo "=== Step 3c: Gradual Heating 100K to 150K ==="
if [ -f "heat3_100to150.in" ]; then
    $MD_EXE -O -i heat3_100to150.in -p $PRMTOP -c ${NAME}_heat2.ncrst -ref ${NAME}_heat2.ncrst -o ${NAME}_heat3.out -r ${NAME}_heat3.ncrst
    if [ $? -ne 0 ]; then
        echo "Error in heating step 3"
        exit 1
    fi
    echo "Heating 3 (100K->150K) completed successfully"
else
    echo "Warning: heat3_100to150.in not found, skipping heating step 3"
fi

echo "=== Step 3d: Gradual Heating 150K to 200K ==="
if [ -f "heat4_150to200.in" ]; then
    $MD_EXE -O -i heat4_150to200.in -p $PRMTOP -c ${NAME}_heat3.ncrst -ref ${NAME}_heat3.ncrst -o ${NAME}_heat4.out -r ${NAME}_heat4.ncrst
    if [ $? -ne 0 ]; then
        echo "Error in heating step 4"
        exit 1
    fi
    echo "Heating 4 (150K->200K) completed successfully"
else
    echo "Warning: heat4_150to200.in not found, skipping heating step 4"
fi

echo "=== Step 3e: Gradual Heating 200K to 250K ==="
if [ -f "heat5_200to250.in" ]; then
    $MD_EXE -O -i heat5_200to250.in -p $PRMTOP -c ${NAME}_heat4.ncrst -ref ${NAME}_heat4.ncrst -o ${NAME}_heat5.out -r ${NAME}_heat5.ncrst
    if [ $? -ne 0 ]; then
        echo "Error in heating step 5"
        exit 1
    fi
    echo "Heating 5 (200K->250K) completed successfully"
else
    echo "Warning: heat5_200to250.in not found, skipping heating step 5"
fi

echo "=== Step 3f: Gradual Heating 250K to 300K ==="
if [ -f "heat6_250to300.in" ]; then
    $MD_EXE -O -i heat6_250to300.in -p $PRMTOP -c ${NAME}_heat5.ncrst -ref ${NAME}_heat5.ncrst -o ${NAME}_heat6.out -r ${NAME}_heat6.ncrst
    if [ $? -ne 0 ]; then
        echo "Error in heating step 6"
        exit 1
    fi
    echo "Heating 6 (250K->300K) completed successfully"
else
    echo "Warning: heat6_250to300.in not found, skipping heating step 6"
fi

# Step 4: Density Equilibration
echo "=== Step 4: Density Equilibration ==="
if [ -f "density_eq.in" ]; then
    $MD_EXE -O -i density_eq.in -p $PRMTOP -c ${NAME}_heat6.ncrst -ref ${NAME}_heat6.ncrst -o ${NAME}_density.out -r ${NAME}_density.ncrst
    if [ $? -ne 0 ]; then
        echo "Error in density equilibration"
        exit 1
    fi
    echo "Density equilibration completed successfully"
else
    echo "Warning: density_eq.in not found, skipping density equilibration"
fi

# Step 5: Equilibration 1
echo "=== Step 5: Equilibration 1 ==="
if [ -f "eq1_WT4.in" ]; then
    # Use density output if available, otherwise fall back to em2
    PREV_COORD="${NAME}_density.ncrst"
    if [ ! -f "$PREV_COORD" ]; then
        PREV_COORD="${NAME}_em2.ncrst"
        echo "Density coordinates not found, using ${NAME}_em2.ncrst"
    fi
    $MD_EXE -O -i eq1_WT4.in -p $PRMTOP -c $PREV_COORD -ref $PREV_COORD -o ${NAME}_eq1.out -r ${NAME}_eq1.ncrst -x ${NAME}_eq1.nc
    if [ $? -ne 0 ]; then
        echo "Error in equilibration step 1"
        exit 1
    fi
    echo "Equilibration 1 completed successfully"
else
    echo "Warning: eq1_WT4.in not found, skipping equilibration 1"
fi

# Step 6: Equilibration 2
echo "=== Step 6: Equilibration 2 ==="
if [ -f "eq2_WT4.in" ]; then
    $MD_EXE -O -i eq2_WT4.in -p $PRMTOP -c ${NAME}_eq1.ncrst -ref ${NAME}_eq1.ncrst -o ${NAME}_eq2.out -r ${NAME}_eq2.ncrst -x ${NAME}_eq2.nc
    if [ $? -ne 0 ]; then
        echo "Error in equilibration step 2"
        exit 1
    fi
    echo "Equilibration 2 completed successfully"
else
    echo "Warning: eq2_WT4.in not found, skipping equilibration 2"
fi

# Step 7: Final Equilibration
echo "=== Step 7: Final Equilibration ==="
if [ -f "final_eq.in" ]; then
    $MD_EXE -O -i final_eq.in -p $PRMTOP -c ${NAME}_eq2.ncrst -ref ${NAME}_eq2.ncrst -o ${NAME}_final_eq.out -r ${NAME}_final_eq.ncrst -x ${NAME}_final_eq.nc
    if [ $? -ne 0 ]; then
        echo "Error in final equilibration"
        exit 1
    fi
    echo "Final equilibration completed successfully"
else
    echo "Warning: final_eq.in not found, skipping final equilibration"
fi

# Step 8: Production MD
echo "=== Step 8: Production MD ==="
if [ -f "prod_md_WT4.in" ]; then
    # Use final_eq output if available, otherwise fall back to eq2
    PROD_COORD="${NAME}_final_eq.ncrst"
    if [ ! -f "$PROD_COORD" ]; then
        PROD_COORD="${NAME}_eq2.ncrst"
        echo "Final equilibration coordinates not found, using ${NAME}_eq2.ncrst"
    fi
    $MD_EXE -O -i prod_md_WT4.in -p $PRMTOP -c $PROD_COORD -o ${NAME}_prod.out -r ${NAME}_prod.ncrst -x ${NAME}_prod.nc
    if [ $? -ne 0 ]; then
        echo "Error in production MD"
        exit 1
    fi
    echo "Production MD completed successfully"
else
    echo "Warning: prod_md_WT4.in not found, skipping production MD"
fi

echo ""
echo "=== MD Simulation Complete ==="
echo "Output files generated:"
echo "  Minimization: ${NAME}_em1.out, ${NAME}_em2.out"
echo "  Gradual Heating: ${NAME}_heat1.out -> ${NAME}_heat6.out"
echo "  Density: ${NAME}_density.out"
echo "  Equilibration: ${NAME}_eq1.out, ${NAME}_eq2.out"
echo "  Final Equilibration: ${NAME}_final_eq.out"
echo "  Production: ${NAME}_prod.out"
echo "  Trajectories: ${NAME}_eq1.nc, ${NAME}_eq2.nc, ${NAME}_final_eq.nc, ${NAME}_prod.nc"
echo "  Final coordinates: ${NAME}_prod.ncrst"