#!/usr/bin/env python3
"""
Calculate van der Waals volume of proteins from PDB files
Using Monte Carlo method for accurate volume estimation
"""

import numpy as np
import sys
from collections import defaultdict
import random

# van der Waals radii in Angstroms
VDW_RADII = {
    'H': 1.20,   # Hydrogen
    'C': 1.70,   # Carbon
    'N': 1.55,   # Nitrogen
    'O': 1.52,   # Oxygen
    'S': 1.80,   # Sulfur
    'P': 1.80,   # Phosphorus
    'F': 1.47,   # Fluorine
    'CL': 1.75,  # Chlorine
    'BR': 1.85,  # Bromine
    'I': 1.98,   # Iodine
    'FE': 1.40,  # Iron
    'MG': 1.73,  # Magnesium
    'CA': 2.31,  # Calcium
    'ZN': 1.39,  # Zinc
    'NA': 2.27,  # Sodium
    'K': 2.75,   # Potassium
    'MN': 1.61,  # Manganese
    'CU': 1.40,  # Copper
    'NI': 1.63,  # Nickel
    'CO': 1.67,  # Cobalt
    'SE': 1.90,  # Selenium
}

def parse_pdb(filename):
    """Parse PDB file and extract atom coordinates and types"""
    atoms = []

    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('ATOM') or line.startswith('HETATM'):
                try:
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])

                    # Extract element symbol (columns 76-77 or from atom name)
                    if len(line) > 76:
                        element = line[76:78].strip()
                    else:
                        # Fallback: extract from atom name
                        atom_name = line[12:16].strip()
                        element = ''.join([c for c in atom_name if c.isalpha()])[:2]

                    # Clean up element symbol
                    element = element.upper()
                    if len(element) > 1 and element[1].isdigit():
                        element = element[0]

                    atoms.append({
                        'coord': np.array([x, y, z]),
                        'element': element,
                        'radius': VDW_RADII.get(element, 1.70)  # Default to carbon if unknown
                    })
                except (ValueError, IndexError):
                    continue

    return atoms

def calculate_bounding_box(atoms):
    """Calculate bounding box with padding"""
    coords = np.array([atom['coord'] for atom in atoms])
    max_radius = max(atom['radius'] for atom in atoms)

    min_coord = coords.min(axis=0) - max_radius - 2.0
    max_coord = coords.max(axis=0) + max_radius + 2.0

    return min_coord, max_coord

def is_inside_vdw(point, atoms):
    """Check if a point is inside any atom's van der Waals sphere"""
    for atom in atoms:
        distance = np.linalg.norm(point - atom['coord'])
        if distance <= atom['radius']:
            return True
    return False

def monte_carlo_volume(atoms, n_samples=100000):
    """Estimate van der Waals volume using Monte Carlo method"""
    min_coord, max_coord = calculate_bounding_box(atoms)
    box_volume = np.prod(max_coord - min_coord)

    # Generate random points
    inside_count = 0
    batch_size = 10000

    for i in range(0, n_samples, batch_size):
        current_batch = min(batch_size, n_samples - i)

        # Generate random points in the bounding box
        random_points = np.random.uniform(
            min_coord, max_coord,
            size=(current_batch, 3)
        )

        # Check each point
        for point in random_points:
            if is_inside_vdw(point, atoms):
                inside_count += 1

        # Progress indicator
        if (i + batch_size) % 50000 == 0:
            print(f"  Progress: {min(i + batch_size, n_samples)}/{n_samples} samples", end='\r')

    # Calculate volume
    vdw_volume = (inside_count / n_samples) * box_volume

    return vdw_volume, inside_count, n_samples

def analyze_protein(pdb_file, protein_name):
    """Analyze a single protein"""
    print(f"\nAnalyzing {protein_name}...")
    print(f"  Reading PDB file: {pdb_file}")

    atoms = parse_pdb(pdb_file)
    print(f"  Found {len(atoms)} atoms")

    # Count atom types
    element_counts = defaultdict(int)
    for atom in atoms:
        element_counts[atom['element']] += 1

    print(f"  Atom composition:", dict(element_counts))

    # Calculate volume
    print(f"  Calculating van der Waals volume (Monte Carlo method)...")
    volume, inside, total = monte_carlo_volume(atoms, n_samples=100000)

    print(f"\n  Results for {protein_name}:")
    print(f"    Number of atoms: {len(atoms)}")
    print(f"    Van der Waals volume: {volume:.1f} Å³")
    print(f"    Van der Waals volume: {volume/1000:.2f} nm³")
    print(f"    Monte Carlo accuracy: {inside}/{total} points inside")

    return {
        'name': protein_name,
        'n_atoms': len(atoms),
        'volume_A3': volume,
        'volume_nm3': volume/1000,
        'atom_counts': dict(element_counts)
    }

def main():
    """Main analysis function"""
    print("="*60)
    print("VAN DER WAALS VOLUME CALCULATOR FOR ENZYMES")
    print("="*60)

    # Define enzymes to analyze
    enzymes = [
        ('Alkaline_Phosphatase_1ED8/enzima_centered.pdb', 'Alkaline Phosphatase (1ED8)'),
        ('EGFP_4EUL/enzima_centered.pdb', 'EGFP (4EUL)'),
        ('GCase_1OGS/enzima_centered.pdb', 'Glucocerebrosidase (1OGS)'),
        ('Luciferasa_1LCI/enzima_centered.pdb', 'Luciferase (1LCI)')
    ]

    results = []

    for pdb_file, enzyme_name in enzymes:
        try:
            result = analyze_protein(pdb_file, enzyme_name)
            results.append(result)
        except Exception as e:
            print(f"  Error analyzing {enzyme_name}: {str(e)}")
            continue

    # Print summary table
    print("\n" + "="*60)
    print("SUMMARY OF RESULTS")
    print("="*60)

    print(f"\n{'Enzyme':<30} {'Atoms':<8} {'Volume (Å³)':<15} {'Volume (nm³)':<12}")
    print("-"*65)

    for result in results:
        print(f"{result['name']:<30} {result['n_atoms']:<8} "
              f"{result['volume_A3']:<15.1f} {result['volume_nm3']:<12.2f}")

    # Calculate statistics
    volumes_A3 = [r['volume_A3'] for r in results]
    volumes_nm3 = [r['volume_nm3'] for r in results]

    print("\n" + "="*60)
    print("STATISTICAL ANALYSIS")
    print("="*60)

    print(f"\nVolume Statistics:")
    print(f"  Minimum volume: {min(volumes_A3):.1f} Å³ ({min(volumes_nm3):.2f} nm³)")
    print(f"  Maximum volume: {max(volumes_A3):.1f} Å³ ({max(volumes_nm3):.2f} nm³)")
    print(f"  Average volume: {np.mean(volumes_A3):.1f} Å³ ({np.mean(volumes_nm3):.2f} nm³)")
    print(f"  Std deviation: {np.std(volumes_A3):.1f} Å³ ({np.std(volumes_nm3):.2f} nm³)")

    # Volume ratios
    print(f"\nVolume Ratios (relative to smallest):")
    min_vol = min(volumes_A3)
    for result in results:
        ratio = result['volume_A3'] / min_vol
        print(f"  {result['name']}: {ratio:.2f}x")

    print("\n" + "="*60)
    print("Analysis complete!")

    return results

if __name__ == "__main__":
    main()