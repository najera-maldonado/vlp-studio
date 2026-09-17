# Conversion of Glucosylceramide (GYE) to Coarse-Grained

## Overview
Manual conversion of glucosylceramide from all-atom to SIRAH coarse-grained representation.

## Chemical Structure
- **IUPAC Name**: N-[(E,2S,3R)-3-hydroxy-1-[(2R,5S,6R)-3,4,5-trihydroxy-6-(hydroxymethyl)oxan-2-yl]oxyoctadec-4-en-2-yl]tetracosanamide
- **SMILES**: `CCCCCCCCCCCCCCCCCCCCCCCC(=O)N[C@@H](CO[C@H]1C(C([C@@H]([C@H](O1)CO)O)O)O)[C@@H](/C=C/CCCCCCCCCCCCC)O`

## Molecular Components
1. **Tetracosanamide chain**: 24 carbons (C24:0 fatty acid)
2. **Sphingosine backbone**: 18 carbons with E-4 double bond
3. **β-D-Glucose head**: 6-carbon sugar with hydroxyl groups

## SIRAH CG Mapping (17 beads total)

### Glucose Head (4 beads)
- **GC** (atom 1): Anomeric carbon region
- **GO** (atom 2): Ring oxygen and C2 region
- **GC** (atom 3): C3-C4 region
- **GO** (atom 4): C5-C6 and hydroxymethyl region

### Linker Region (2 beads)
- **BGL** (atom 5): Glycerol backbone connection
- **BCE** (atom 6): Amide linkage region

### Sphingosine Chain (5 beads, 18C)
- **BC1** (atom 7): C1-C3 region (~4C)
- **BC2** (atom 8): C4-C7 with double bond (~4C)
- **BC3** (atom 9): C8-C11 region (~4C)
- **BC4** (atom 10): C12-C15 region (~4C)
- **BCT** (atom 11): C16-C18 terminal (~3C)

### Fatty Acid Chain (6 beads, 24C)
- **BF1** (atom 12): C1-C4 region
- **BF2** (atom 13): C5-C8 region
- **BF3** (atom 14): C9-C12 region
- **BF4** (atom 15): C13-C16 region
- **BF5** (atom 16): C17-C20 region
- **BF6** (atom 17): C21-C24 terminal region

## Files Generated
- `GYE_cg_manual.pdb`: Manual CG structure
- `GYE_custom.map`: Custom mapping file (not used due to atom type issues)

## Notes
- Standard SIRAH cgconv.pl failed due to lack of predefined GYE parameters
- Manual mapping follows SIRAH conventions: ~4 carbons per bead for aliphatic chains
- Coordinates derived from center-of-mass of corresponding all-atom groups
- Compatible with SIRAH force field topology generation