#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import glob

def plot_rmsd_data(enzyme_num=None):
    # Auto-detect enzyme number if not provided
    if enzyme_num is None:
        # Look for RMSD data files in current directory
        rmsd_files = glob.glob('enzima*_rmsd_all.dat')
        if not rmsd_files:
            print("No RMSD data files found (enzima*_rmsd_all.dat)")
            return False
        # Extract enzyme number from first file found
        enzyme_num = rmsd_files[0].split('_')[0].replace('enzima', '')
        print(f"Auto-detected enzyme number: {enzyme_num}")
    # Read the RMSD data files
    try:
        # Load all-atom RMSD data
        data_all = np.loadtxt(f'enzima{enzyme_num}_rmsd_all.dat', comments='#')
        frames_all = data_all[:, 0]
        rmsd_all = data_all[:, 1]

        # Load backbone RMSD data
        data_backbone = np.loadtxt(f'enzima{enzyme_num}_rmsd_backbone.dat', comments='#')
        frames_backbone = data_backbone[:, 0]
        rmsd_backbone = data_backbone[:, 1]

        # Create the plot
        plt.figure(figsize=(10, 6))

        # Plot both RMSD curves
        plt.plot(frames_all, rmsd_all, label='All atoms', linewidth=1.5, color='blue')
        plt.plot(frames_backbone, rmsd_backbone, label='Backbone', linewidth=1.5, color='red')

        # Customize the plot
        plt.xlabel('Frame')
        plt.ylabel('RMSD (Å)')
        plt.title(f'RMSD Evolution - Enzyme {enzyme_num}')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Set layout and save
        plt.tight_layout()
        plt.savefig(f'enzima{enzyme_num}_rmsd_plot.png', dpi=300, bbox_inches='tight')
        plt.show()

        print(f"Plot saved as 'enzima{enzyme_num}_rmsd_plot.png'")
        print(f"All-atom RMSD: {len(frames_all)} frames, range: {rmsd_all.min():.3f} - {rmsd_all.max():.3f} Å")
        print(f"Backbone RMSD: {len(frames_backbone)} frames, range: {rmsd_backbone.min():.3f} - {rmsd_backbone.max():.3f} Å")

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

    plot_rmsd_data(enzyme_num)