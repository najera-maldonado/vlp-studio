#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import glob

def plot_rmsf_data(enzyme_num=None):
    # Auto-detect enzyme number if not provided
    if enzyme_num is None:
        # Look for RMSF data files in current directory
        rmsf_files = glob.glob('enzima*_rmsf_all.dat')
        if not rmsf_files:
            print("No RMSF data files found (enzima*_rmsf_all.dat)")
            return False
        # Extract enzyme number from first file found
        enzyme_num = rmsf_files[0].split('_')[0].replace('enzima', '')
        print(f"Auto-detected enzyme number: {enzyme_num}")
    # Read the RMSF data files
    try:
        # Load all-atom RMSF data
        data_all = np.loadtxt(f'enzima{enzyme_num}_rmsf_all.dat', comments='#')
        residues_all = np.arange(1, len(data_all) + 1)  # Renumber from 1 to N
        rmsf_all = data_all[:, 1]

        # Load backbone RMSF data
        data_backbone = np.loadtxt(f'enzima{enzyme_num}_rmsf_backbone.dat', comments='#')
        residues_backbone = np.arange(1, len(data_backbone) + 1)  # Renumber from 1 to N
        rmsf_backbone = data_backbone[:, 1]

        # Create the plot
        plt.figure(figsize=(12, 6))

        # Plot both RMSF curves
        plt.plot(residues_all, rmsf_all, label='All atoms', linewidth=1.2, color='blue')
        plt.plot(residues_backbone, rmsf_backbone, label='Backbone', linewidth=1.2, color='red')

        # Customize the plot
        plt.xlabel('Residue Number')
        plt.ylabel('RMSF (Å)')
        plt.title(f'Root Mean Square Fluctuation - Enzyme {enzyme_num}')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Set layout and save
        plt.tight_layout()
        plt.savefig(f'enzima{enzyme_num}_rmsf_plot.png', dpi=300, bbox_inches='tight')
        plt.show()

        print(f"Plot saved as 'enzima{enzyme_num}_rmsf_plot.png'")
        print(f"All-atom RMSF: {len(residues_all)} residues, range: {rmsf_all.min():.3f} - {rmsf_all.max():.3f} Å")
        print(f"Backbone RMSF: {len(residues_backbone)} residues, range: {rmsf_backbone.min():.3f} - {rmsf_backbone.max():.3f} Å")

    except Exception as e:
        print(f"Error reading data files: {e}")
        return False

    return True

if __name__ == "__main__":
    # Check if enzyme number provided as command line argument
    enzyme_num = None
    if len(sys.argv) > 1:
        try:
            enzyme_num = sys.argv[1]
            print(f"Using enzyme number from command line: {enzyme_num}")
        except ValueError:
            print(f"Invalid enzyme number: {sys.argv[1]}")
            sys.exit(1)

    plot_rmsf_data(enzyme_num)