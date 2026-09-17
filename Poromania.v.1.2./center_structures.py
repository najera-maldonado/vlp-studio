#!/usr/bin/env python3
import os
from pathlib import Path

def center_pdb_structure(pdb_file):
    """Center a PDB structure at 0,0,0 by calculating center of mass and translating"""
    atoms = []
    with open(pdb_file, 'r') as f:
        for line in f:
            if line.startswith('ATOM  ') or line.startswith('HETATM'):
                atoms.append(line)

    if not atoms:
        print(f"No ATOM records found in {pdb_file}")
        return

    # Calculate center of mass
    total_x = total_y = total_z = 0.0
    atom_count = 0

    for line in atoms:
        x = float(line[30:38].strip())
        y = float(line[38:46].strip())
        z = float(line[46:54].strip())
        total_x += x
        total_y += y
        total_z += z
        atom_count += 1

    center_x = total_x / atom_count
    center_y = total_y / atom_count
    center_z = total_z / atom_count

    print(f"Original center: ({center_x:.2f}, {center_y:.2f}, {center_z:.2f})")

    # Write centered structure
    with open(pdb_file, 'r') as f_in:
        lines = f_in.readlines()

    with open(pdb_file, 'w') as f_out:
        for line in lines:
            if line.startswith('ATOM  ') or line.startswith('HETATM'):
                # Extract coordinates
                x = float(line[30:38].strip()) - center_x
                y = float(line[38:46].strip()) - center_y
                z = float(line[46:54].strip()) - center_z

                # Replace coordinates in line
                new_line = (line[:30] +
                           f"{x:8.3f}" +
                           f"{y:8.3f}" +
                           f"{z:8.3f}" +
                           line[54:])
                f_out.write(new_line)
            else:
                f_out.write(line)

def main():
    # Center all mutant structures
    mutants_dir = Path("mutants")
    for mut_dir in mutants_dir.glob("mut_*"):
        receptor_pdb = mut_dir / "receptor.pdb"
        if receptor_pdb.exists():
            print(f"Centering {mut_dir.name}...")
            center_pdb_structure(receptor_pdb)
        else:
            print(f"No receptor.pdb found in {mut_dir}")

    # Center the original structure if it exists
    if Path("poronatural.pdb").exists():
        print("Centering poronatural.pdb...")
        center_pdb_structure("poronatural.pdb")

if __name__ == "__main__":
    main()