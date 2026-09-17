#!/usr/bin/env python3
"""
Fast van der Waals volume calculator for proteins
Using efficient grid-based method with chunked processing
"""

import numpy as np
from collections import defaultdict

# van der Waals radii in Angstroms
VDW_RADII = {
    'H': 1.20, 'C': 1.70, 'N': 1.55, 'O': 1.52, 'S': 1.80,
    'P': 1.80, 'F': 1.47, 'CL': 1.75, 'BR': 1.85, 'I': 1.98,
    'FE': 1.40, 'MG': 1.73, 'CA': 2.31, 'ZN': 1.39, 'NA': 2.27,
    'K': 2.75, 'MN': 1.61, 'CU': 1.40, 'NI': 1.63, 'CO': 1.67,
    'SE': 1.90
}

def parse_pdb_fast(filename):
    """Parse PDB file - only heavy atoms (no hydrogens)"""
    atoms = []
    n_chains = set()

    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('ATOM'):
                try:
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    chain = line[21]
                    n_chains.add(chain)

                    # Extract element
                    if len(line) > 76:
                        element = line[76:78].strip().upper()
                    else:
                        atom_name = line[12:16].strip()
                        element = atom_name[0].upper()

                    # Skip hydrogens for speed
                    if element == 'H':
                        continue

                    radius = VDW_RADII.get(element, 1.70)
                    atoms.append([x, y, z, radius])
                except:
                    continue

    return np.array(atoms), len(n_chains)

def fast_grid_volume(atoms, grid_spacing=1.5):
    """Fast grid-based volume calculation"""
    if len(atoms) == 0:
        return 0

    coords = atoms[:, :3]
    radii = atoms[:, 3]

    # Bounding box
    min_coord = coords.min(axis=0) - radii.max() - 1
    max_coord = coords.max(axis=0) + radii.max() + 1

    # Create coarse grid
    nx = int((max_coord[0] - min_coord[0]) / grid_spacing) + 1
    ny = int((max_coord[1] - min_coord[1]) / grid_spacing) + 1
    nz = int((max_coord[2] - min_coord[2]) / grid_spacing) + 1

    print(f"  Grid size: {nx} x {ny} x {nz} = {nx*ny*nz:,} points")

    # Process in slices for memory efficiency
    volume = 0

    for iz in range(nz):
        z = min_coord[2] + iz * grid_spacing

        for iy in range(ny):
            y = min_coord[1] + iy * grid_spacing

            for ix in range(nx):
                x = min_coord[0] + ix * grid_spacing
                point = np.array([x, y, z])

                # Check if inside any atom (vectorized)
                distances = np.sqrt(np.sum((coords - point)**2, axis=1))
                if np.any(distances <= radii):
                    volume += 1

        # Progress
        if iz % 10 == 0:
            print(f"  Progress: {100*iz/nz:.0f}%", end='\r')

    print(f"  Progress: 100%")

    return volume * (grid_spacing ** 3)

def calculate_gyration_radius(atoms):
    """Calculate radius of gyration"""
    coords = atoms[:, :3]
    center = coords.mean(axis=0)
    rg = np.sqrt(np.mean(np.sum((coords - center)**2, axis=1)))
    return rg

def estimate_volume_from_atoms(n_atoms):
    """Empirical formula for protein volume based on atom count"""
    # Approximately 11-12 Å³ per non-hydrogen atom for proteins
    return n_atoms * 11.5

def main():
    print("="*70)
    print("FAST VAN DER WAALS VOLUME CALCULATOR FOR VIRAL CAPSID PACKING")
    print("="*70)

    enzymes = [
        ('Alkaline_Phosphatase_1ED8/enzima_centered.pdb', 'Alkaline Phosphatase (1ED8)'),
        ('EGFP_4EUL/enzima_centered.pdb', 'EGFP (4EUL)'),
        ('GCase_1OGS/enzima_centered.pdb', 'Glucocerebrosidase (1OGS)'),
        ('Luciferasa_1LCI/enzima_centered.pdb', 'Luciferase (1LCI)')
    ]

    results = []

    for pdb_file, enzyme_name in enzymes:
        print(f"\n{enzyme_name}")
        print("-" * 50)

        try:
            atoms, n_chains = parse_pdb_fast(pdb_file)
            n_atoms = len(atoms)

            print(f"  Heavy atoms: {n_atoms}")
            print(f"  Chains: {n_chains}")

            # Calculate radius of gyration
            rg = calculate_gyration_radius(atoms)
            print(f"  Radius of gyration: {rg:.1f} Å")

            # Method 1: Empirical estimate
            vol_empirical = estimate_volume_from_atoms(n_atoms)
            print(f"  Empirical volume: {vol_empirical:.0f} Å³")

            # Method 2: Grid-based (coarse)
            print(f"  Calculating grid-based volume...")

            # Adaptive grid spacing based on size
            if n_atoms > 5000:
                spacing = 2.0
            elif n_atoms > 3000:
                spacing = 1.8
            else:
                spacing = 1.5

            vol_grid = fast_grid_volume(atoms, grid_spacing=spacing)
            print(f"  Grid-based volume: {vol_grid:.0f} Å³ (spacing: {spacing} Å)")

            # Average of methods
            vol_avg = (vol_empirical + vol_grid) / 2

            results.append({
                'name': enzyme_name,
                'n_atoms': n_atoms,
                'n_chains': n_chains,
                'rg': rg,
                'vol_empirical': vol_empirical,
                'vol_grid': vol_grid,
                'vol_avg': vol_avg
            })

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    # Summary table
    print("\n" + "="*70)
    print("SUMMARY - VAN DER WAALS VOLUMES")
    print("="*70)

    print(f"\n{'Enzyme':<30} {'Atoms':<7} {'Chains':<7} {'Rg (Å)':<8} {'Volume (Å³)':<12} {'Volume (nm³)':<10}")
    print("-"*82)

    for r in results:
        print(f"{r['name']:<30} {r['n_atoms']:<7} {r['n_chains']:<7} "
              f"{r['rg']:<8.1f} {r['vol_avg']:<12.0f} {r['vol_avg']/1000:<10.3f}")

    # Analysis for capsid packing
    print("\n" + "="*70)
    print("ANALYSIS FOR VIRAL CAPSID PACKING")
    print("="*70)

    volumes = [r['vol_avg'] for r in results]

    print(f"\nVolume Statistics:")
    print(f"  Minimum: {min(volumes):.0f} Å³ ({min(volumes)/1000:.3f} nm³)")
    print(f"  Maximum: {max(volumes):.0f} Å³ ({max(volumes)/1000:.3f} nm³)")
    print(f"  Average: {np.mean(volumes):.0f} Å³ ({np.mean(volumes)/1000:.3f} nm³)")
    print(f"  Std Dev: {np.std(volumes):.0f} Å³")

    print(f"\nSize Ratios (relative to smallest):")
    min_vol = min(volumes)
    for r in sorted(results, key=lambda x: x['vol_avg']):
        ratio = r['vol_avg'] / min_vol
        bar = '█' * int(ratio * 10)
        print(f"  {r['name']:<30} {ratio:>4.2f}x {bar}")

    print(f"\nPacking Considerations:")
    for r in results:
        packing_diameter = 2 * (3 * r['vol_avg'] / (4 * np.pi)) ** (1/3)
        print(f"  {r['name']:<30} effective diameter: {packing_diameter:.1f} Å")

    # Save results
    with open('vdw_volumes_results.txt', 'w') as f:
        f.write("Enzyme\tAtoms\tChains\tRg(Å)\tVolume(Å³)\tVolume(nm³)\n")
        for r in results:
            f.write(f"{r['name']}\t{r['n_atoms']}\t{r['n_chains']}\t"
                   f"{r['rg']:.1f}\t{r['vol_avg']:.0f}\t{r['vol_avg']/1000:.3f}\n")

    print(f"\nResults saved to: vdw_volumes_results.txt")
    print("="*70)

if __name__ == "__main__":
    main()