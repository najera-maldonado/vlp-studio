#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt

# Read RMSD data
data_all = np.loadtxt('capside_rmsd_all.dat', comments='#')
data_backbone = np.loadtxt('capside_rmsd_backbone.dat', comments='#')

# Extract frame numbers and RMSD values
frames_all = data_all[:, 0]
rmsd_all = data_all[:, 1]

frames_backbone = data_backbone[:, 0]
rmsd_backbone = data_backbone[:, 1]

# Convert frames to nanoseconds (1000 ns total simulation)
# Assuming 10000 frames for 1000 ns = 0.1 ns per frame
time_all = (frames_all - 1) * 0.1
time_backbone = (frames_backbone - 1) * 0.1

# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(time_all, rmsd_all, label='All atoms', linewidth=1.5, color='blue')
plt.plot(time_backbone, rmsd_backbone, label='Backbone', linewidth=1.5, color='red')

plt.xlabel('Time (ns)')
plt.ylabel('RMSD (Å)')
plt.title('Capsid RMSD Evolution')
plt.legend()
plt.grid(True, alpha=0.3)

# Save the plot
plt.tight_layout()
plt.savefig('capside_rmsd_plot.png', dpi=300, bbox_inches='tight')
plt.show()

print("RMSD plot saved as capside_rmsd_plot.png")
print(f"All atoms - Final RMSD: {rmsd_all[-1]:.2f} Å at {time_all[-1]:.1f} ns")
print(f"Backbone - Final RMSD: {rmsd_backbone[-1]:.2f} Å at {time_backbone[-1]:.1f} ns")