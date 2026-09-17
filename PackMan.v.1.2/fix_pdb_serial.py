#!/usr/bin/env python3

import sys
import re

def fix_pdb_serial_numbers(input_file, output_file):
    """
    Fix PDB serial numbers that are in hexadecimal or have formatting issues
    """
    with open(input_file, 'r') as f:
        lines = f.readlines()

    atom_serial = 1
    fixed_lines = []

    for line in lines:
        if line.startswith('ATOM') or line.startswith('HETATM'):
            # Extract components
            record_type = line[0:6]
            # Skip serial number field (will be renumbered)
            atom_name = line[12:16]
            alt_loc = line[16:17]
            res_name = line[17:20]
            chain_id = line[21:22]
            res_seq = line[22:26]
            icode = line[26:27]
            x = line[30:38]
            y = line[38:46]
            z = line[46:54]
            occupancy = line[54:60] if len(line) > 54 else '  1.00'
            temp_factor = line[60:66] if len(line) > 60 else ' 20.00'
            element = line[76:78] if len(line) > 76 else '  '
            charge = line[78:80] if len(line) > 78 else '  '

            # Rebuild line with proper serial number
            new_line = f"{record_type:6s}{atom_serial:5d} {atom_name:4s}{alt_loc:1s}{res_name:3s} {chain_id:1s}{res_seq:4s}{icode:1s}   {x:8s}{y:8s}{z:8s}{occupancy:6s}{temp_factor:6s}      {element:2s}{charge:2s}\n"

            fixed_lines.append(new_line)
            atom_serial += 1
        else:
            # Keep other lines as-is (REMARK, CONECT, etc.)
            if not line.startswith('REMARK'):  # Skip REMARK lines that cause issues
                fixed_lines.append(line)

    with open(output_file, 'w') as f:
        f.writelines(fixed_lines)

    print(f"Fixed PDB serial numbers: {input_file} → {output_file}")
    print(f"Total atoms renumbered: {atom_serial - 1}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 fix_pdb_serial.py input.pdb output.pdb")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    fix_pdb_serial_numbers(input_file, output_file)