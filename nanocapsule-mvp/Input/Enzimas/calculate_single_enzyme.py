#!/usr/bin/env python3
"""
Calculate van der Waals volume for a single enzyme
Memory-efficient implementation
"""

import numpy as np
import sys

# van der Waals radii in Angstroms
VDW_RADII = {
    'H': 1.20, 'C': 1.70, 'N': 1.55, 'O': 1.52, 'S': 1.80,
    'P': 1.80, 'F': 1.47, 'CL': 1.75, 'BR': 1.85, 'I': 1.98,
    'FE': 1.40, 'MG': 1.73, 'CA': 2.31, 'ZN': 1.39, 'NA': 2.27,
    'K': 2.75, 'MN': 1.61, 'CU': 1.40, 'NI': 1.63, 'CO': 1.67,
    'SE': 1.90
}

def parse_pdb(filename):
    """Parse PDB file"""
    atoms = []
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('ATOM') or line.startswith('HETATM'):
                try:
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])

                    if len(line) > 76:
                        element = line[76:78].strip().upper()
                    else:
                        atom_name = line[12:16].strip()
                        element = ''.join([c for c in atom_name if c.isalpha()])[:2].upper()

                    if len(element) > 1 and element[1].isdigit():
                        element = element[0]

                    radius = VDW_RADII.get(element, 1.70)
                    atoms.append({'coord': np.array([x, y, z]), 'radius': radius})
                except:
                    continue
    return atoms

def calculate_volume_monte_carlo(atoms, n_samples=50000):
    """Calculate volume using Monte Carlo with reduced samples"""
    if not atoms:
        return 0

    # Get bounding box
    coords = np.array([a['coord'] for a in atoms])
    radii = np.array([a['radius'] for a in atoms])

    min_coord = coords.min(axis=0) - radii.max() - 1
    max_coord = coords.max(axis=0) + radii.max() + 1
    box_volume = np.prod(max_coord - min_coord)

    # Monte Carlo sampling
    inside = 0
    batch_size = 1000

    for i in range(0, n_samples, batch_size):
        batch = min(batch_size, n_samples - i)
        points = np.random.uniform(min_coord, max_coord, (batch, 3))

        for point in points:
            # Check if point is inside any atom
            for atom in atoms:
                if np.linalg.norm(point - atom['coord']) <= atom['radius']:
                    inside += 1
                    break

        if (i + batch_size) % 10000 == 0:
            print(f"  Progress: {min(i + batch_size, n_samples)}/{n_samples}", end='\r')

    print()
    volume = (inside / n_samples) * box_volume
    return volume

def main():
    if len(sys.argv) != 3:
        print("Usage: python calculate_single_enzyme.py <pdb_file> <enzyme_name>")
        sys.exit(1)

    pdb_file = sys.argv[1]
    enzyme_name = sys.argv[2]

    print(f"\nAnalyzing {enzyme_name}")
    print("-" * 40)

    atoms = parse_pdb(pdb_file)
    print(f"Atoms found: {len(atoms)}")

    print("Calculating van der Waals volume...")
    volume = calculate_volume_monte_carlo(atoms, n_samples=50000)

    print(f"\nResults for {enzyme_name}:")
    print(f"  Van der Waals volume: {volume:.1f} Å³")
    print(f"  Van der Waals volume: {volume/1000:.3f} nm³")

    # Save result to file
    with open(f"volume_{enzyme_name.replace(' ', '_').replace('(', '').replace(')', '')}.txt", 'w') as f:
        f.write(f"{enzyme_name}\t{len(atoms)}\t{volume:.1f}\t{volume/1000:.3f}\n")

    return volume

if __name__ == "__main__":
    main()