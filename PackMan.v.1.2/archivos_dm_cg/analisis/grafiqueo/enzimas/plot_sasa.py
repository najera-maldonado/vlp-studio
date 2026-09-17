#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

def plot_sasa_data(enzyme_num=None):
    # Determine enzyme number from directory path or argument
    if enzyme_num is None:
        # Try to extract from current working directory path
        current_path = os.getcwd()

        # Look for enzimaN pattern in the path
        path_parts = current_path.split(os.sep)
        for part in path_parts:
            if part.startswith('enzima') and len(part) > 6:
                try:
                    enzyme_num = part[6:]  # Extract number after "enzima"
                    if enzyme_num.isdigit():
                        break
                except:
                    continue

        # If not found, default to 1
        if enzyme_num is None or not str(enzyme_num).isdigit():
            enzyme_num = '1'

    # Define file names based on enzyme number
    input_file = f'enzima{enzyme_num}_sasa.dat'
    output_file = f'enzima{enzyme_num}_sasa_plot.png'

    # Read the SASA data file
    try:
        # Load SASA data
        data = np.loadtxt(input_file, comments='#')
        frames = data[:, 0]
        sasa = data[:, 1]

        # Convert frames to nanoseconds (1000 ns total simulation)
        time_ns = frames / len(frames) * 1000

        # Create the plot
        plt.figure(figsize=(12, 6))

        # Plot SASA curve
        plt.plot(time_ns, sasa, label='SASA', linewidth=1.2, color='green')

        # Customize the plot
        plt.xlabel('Time (ns)')
        plt.ylabel('SASA (Ų)')
        plt.title(f'Solvent Accessible Surface Area - Enzyme {enzyme_num}')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Set layout and save
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.show()

        print(f"Plot saved as '{output_file}'")
        print(f"SASA: {len(frames)} frames ({time_ns[-1]:.3f} ns), range: {sasa.min():.3f} - {sasa.max():.3f} Ų")
        print(f"Average SASA: {sasa.mean():.3f} Ų")

    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        return False
    except Exception as e:
        print(f"Error reading data files: {e}")
        return False

    return True

if __name__ == "__main__":
    # Allow enzyme number as command line argument
    enzyme_num = None
    if len(sys.argv) > 1:
        enzyme_num = sys.argv[1]

    plot_sasa_data(enzyme_num)