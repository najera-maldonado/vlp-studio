#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt

# Read data
data = np.loadtxt('capside_ryg.dat', skiprows=1)
frames = data[:, 0]
ryg_avg = data[:, 1]
ryg_max = data[:, 2]

# Convert frames to time (ns) - assuming 10,000 frames = 1000 ns
time_ns = frames * 1000 / 10000

# Create figure
fig, ax = plt.subplots(figsize=(12, 8))

# Plot both RoG curves
ax.plot(time_ns, ryg_avg, 'b-', linewidth=1.5, label='RoG Average', alpha=0.8)
ax.plot(time_ns, ryg_max, 'r-', linewidth=1.5, label='RoG Maximum', alpha=0.8)

# Formatting
ax.set_xlabel('Time (ns)', fontsize=14)
ax.set_ylabel('Radius of Gyration (Å)', fontsize=14)
ax.set_title('Capsid Radius of Gyration - 1000 ns MD Simulation', fontsize=16, fontweight='bold')
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3)

# Set axis limits
ax.set_xlim(0, 1000)

# Add statistics text box
avg_mean = np.mean(ryg_avg)
avg_std = np.std(ryg_avg)
max_mean = np.mean(ryg_max)
max_std = np.std(ryg_max)

stats_text = f'RoG Average: {avg_mean:.2f} ± {avg_std:.2f} Å\nRoG Maximum: {max_mean:.2f} ± {max_std:.2f} Å'
ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=11,
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig('capside_ryg_plot.png', dpi=300, bbox_inches='tight')
plt.savefig('capside_ryg_plot.pdf', bbox_inches='tight')
plt.show()

print(f"Statistics:")
print(f"RoG Average: {avg_mean:.3f} ± {avg_std:.3f} Å")
print(f"RoG Maximum: {max_mean:.3f} ± {max_std:.3f} Å")
print(f"Total simulation time: {time_ns[-1]:.1f} ns")
print(f"Total frames: {len(frames)}")