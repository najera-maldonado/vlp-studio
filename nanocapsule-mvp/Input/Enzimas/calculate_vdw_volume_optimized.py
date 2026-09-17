#!/usr/bin/env python3
"""
Optimized van der Waals volume calculator for proteins
Using vectorized operations for faster computation
"""

import numpy as np
from scipy.spatial.distance import cdist
from collections import defaultdict

# van der Waals radii in Angstroms
VDW_RADII = {
    'H': 1.20, 'C': 1.70, 'N': 1.55, 'O': 1.52, 'S': 1.80,
    'P': 1.80, 'F': 1.47, 'CL': 1.75, 'BR': 1.85, 'I': 1.98,
    'FE': 1.40, 'MG': 1.73, 'CA': 2.31, 'ZN': 1.39, 'NA': 2.27,
    'K': 2.75, 'MN': 1.61, 'CU': 1.40, 'NI': 1.63, 'CO': 1.67,
    'SE': 1.90
}

def parse_pdb(filename):
    """Parse PDB file efficiently"""
    atoms = []

    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('ATOM') or line.startswith('HETATM'):
                try:
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])

                    # Extract element
                    if len(line) > 76:
                        element = line[76:78].strip().upper()
                    else:
                        atom_name = line[12:16].strip()
                        element = ''.join([c for c in atom_name if c.isalpha()])[:2].upper()

                    if len(element) > 1 and element[1].isdigit():
                        element = element[0]

                    radius = VDW_RADII.get(element, 1.70)
                    atoms.append([x, y, z, radius, element])
                except:
                    continue

    return atoms

def calculate_volume_grid(atoms, grid_spacing=0.5):
    """Calculate volume using grid-based method (faster than Monte Carlo)"""
    if not atoms:
        return 0, 0

    coords = np.array([[a[0], a[1], a[2]] for a in atoms])
    radii = np.array([a[3] for a in atoms])

    # Bounding box
    max_radius = radii.max()
    min_coord = coords.min(axis=0) - max_radius - 1
    max_coord = coords.max(axis=0) + max_radius + 1

    # Create grid
    x_points = np.arange(min_coord[0], max_coord[0], grid_spacing)
    y_points = np.arange(min_coord[1], max_coord[1], grid_spacing)
    z_points = np.arange(min_coord[2], max_coord[2], grid_spacing)

    total_points = len(x_points) * len(y_points) * len(z_points)
    print(f"    Using grid with ~{total_points:,} points (spacing: {grid_spacing} Å)")

    inside_count = 0

    # Process in chunks for memory efficiency
    chunk_size = min(50, len(z_points))

    for z_start in range(0, len(z_points), chunk_size):
        z_end = min(z_start + chunk_size, len(z_points))
        z_chunk = z_points[z_start:z_end]

        # Create grid points for this chunk
        xx, yy, zz = np.meshgrid(x_points, y_points, z_chunk, indexing='ij')
        grid_points = np.stack([xx.ravel(), yy.ravel(), zz.ravel()], axis=1)

        # Vectorized distance calculation
        distances = cdist(grid_points, coords)

        # Check if points are inside any atom
        inside = np.any(distances <= radii[np.newaxis, :], axis=1)
        inside_count += np.sum(inside)

        # Progress
        progress = (z_end / len(z_points)) * 100
        print(f"    Progress: {progress:.0f}%", end='\r')

    volume = inside_count * (grid_spacing ** 3)
    print()  # New line after progress

    return volume, inside_count

def analyze_enzyme(pdb_file, name):
    """Analyze a single enzyme"""
    print(f"\n{name}")
    print("-" * 50)

    atoms = parse_pdb(pdb_file)
    if not atoms:
        print(f"  ERROR: No atoms found in {pdb_file}")
        return None

    print(f"  Atoms: {len(atoms)}")

    # Count elements
    elements = defaultdict(int)
    for atom in atoms:
        elements[atom[4]] += 1

    # Show main elements
    main_elements = sorted(elements.items(), key=lambda x: x[1], reverse=True)[:5]
    element_str = ', '.join([f"{e}: {c}" for e, c in main_elements])
    print(f"  Main elements: {element_str}")

    # Calculate volume
    print(f"  Calculating van der Waals volume...")

    # Use adaptive grid spacing based on number of atoms
    if len(atoms) > 5000:
        grid_spacing = 0.8
    elif len(atoms) > 3000:
        grid_spacing = 0.6
    else:
        grid_spacing = 0.5

    volume, points = calculate_volume_grid(atoms, grid_spacing)

    print(f"  Van der Waals volume: {volume:.1f} Å³")
    print(f"  Van der Waals volume: {volume/1000:.3f} nm³")
    print(f"  Grid points inside: {points:,}")

    return {
        'name': name,
        'n_atoms': len(atoms),
        'volume_A3': volume,
        'volume_nm3': volume/1000,
        'elements': dict(elements)
    }

def main():
    """Main analysis"""
    print("="*60)
    print("VAN DER WAALS VOLUME ANALYSIS FOR VIRAL CAPSID PACKING")
    print("="*60)

    enzymes = [
        ('Alkaline_Phosphatase_1ED8/enzima_centered.pdb', 'Alkaline Phosphatase (1ED8)'),
        ('EGFP_4EUL/enzima_centered.pdb', 'EGFP (4EUL)'),
        ('GCase_1OGS/enzima_centered.pdb', 'Glucocerebrosidase (1OGS)'),
        ('Luciferasa_1LCI/enzima_centered.pdb', 'Luciferase (1LCI)')
    ]

    results = []

    for pdb_file, enzyme_name in enzymes:
        result = analyze_enzyme(pdb_file, enzyme_name)
        if result:
            results.append(result)

    # Summary table
    print("\n" + "="*60)
    print("SUMMARY - VAN DER WAALS VOLUMES")
    print("="*60)

    print(f"\n{'Enzyme':<30} {'Atoms':<8} {'Volume (Å³)':<12} {'Volume (nm³)':<12}")
    print("-"*62)

    for r in sorted(results, key=lambda x: x['volume_A3']):
        print(f"{r['name']:<30} {r['n_atoms']:<8} {r['volume_A3']:<12.1f} {r['volume_nm3']:<12.3f}")

    # Statistics
    volumes = [r['volume_A3'] for r in results]

    print("\n" + "="*60)
    print("PACKING ANALYSIS FOR VIRAL CAPSIDS")
    print("="*60)

    print(f"\nVolume Range:")
    print(f"  Smallest: {min(volumes):.1f} Å³ ({min(volumes)/1000:.3f} nm³)")
    print(f"  Largest:  {max(volumes):.1f} Å³ ({max(volumes)/1000:.3f} nm³)")
    print(f"  Ratio:    {max(volumes)/min(volumes):.2f}x")

    print(f"\nRelative Volumes (normalized to smallest):")
    min_vol = min(volumes)
    for r in sorted(results, key=lambda x: x['volume_A3']):
        ratio = r['volume_A3'] / min_vol
        bar = '█' * int(ratio * 10)
        print(f"  {r['name']:<30} {ratio:>4.2f}x {bar}")

    print(f"\nAverage Volume: {np.mean(volumes):.1f} ± {np.std(volumes):.1f} Å³")
    print(f"                ({np.mean(volumes)/1000:.3f} ± {np.std(volumes)/1000:.3f} nm³)")

    print("\n" + "="*60)
    print("Analysis complete - Ready for capsid packing comparison")
    print("="*60)

if __name__ == "__main__":
    main()