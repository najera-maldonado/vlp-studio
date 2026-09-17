#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import glob
import argparse
import sys

def find_enzyme_directories(base_path='.'):
    """
    Automatically find all enzyme directories (enzimaX format)
    Returns sorted list of enzyme directory names and their numbers
    """
    enzyme_dirs = []
    enzyme_numbers = []

    # Look for directories matching enzimaX pattern
    pattern = os.path.join(base_path, 'enzima*')
    potential_dirs = glob.glob(pattern)

    for dir_path in potential_dirs:
        if os.path.isdir(dir_path):
            dir_name = os.path.basename(dir_path)
            # Extract number from enzima directory name
            if dir_name.startswith('enzima'):
                try:
                    num_str = dir_name.replace('enzima', '')
                    enzyme_num = int(num_str)
                    enzyme_dirs.append(dir_name)
                    enzyme_numbers.append(enzyme_num)
                except ValueError:
                    continue

    # Sort by enzyme number
    if enzyme_numbers:
        sorted_pairs = sorted(zip(enzyme_numbers, enzyme_dirs))
        enzyme_numbers, enzyme_dirs = zip(*sorted_pairs)
        enzyme_numbers = list(enzyme_numbers)
        enzyme_dirs = list(enzyme_dirs)

    return enzyme_dirs, enzyme_numbers

def read_data_file(filepath):
    """Read data from .dat file"""
    if not os.path.exists(filepath):
        return None, None
    try:
        data = np.loadtxt(filepath, skiprows=1)
        if data.size == 0:
            return None, None
        return data[:, 0], data[:, 1]  # first col, second col
    except:
        return None, None

def plot_rmsd_comparison(enzyme_dirs, enzyme_numbers, base_path='.', output_prefix=''):
    """Create comparison plots for RMSD data"""

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    n_enzymes = len(enzyme_dirs)
    colors = plt.cm.tab10(np.linspace(0, 1, max(10, n_enzymes)))

    print("RMSD Analysis Results:")
    print("=" * 60)
    print(f"Found {n_enzymes} enzymes: {', '.join(enzyme_dirs)}")
    print("=" * 60)

    # Plot backbone RMSD
    backbone_data_found = False
    for i, (enzyme_dir, enzyme_num) in enumerate(zip(enzyme_dirs, enzyme_numbers)):
        filepath = os.path.join(base_path, enzyme_dir, 'rmsd', f'{enzyme_dir}_rmsd_backbone.dat')
        frames, rmsd = read_data_file(filepath)
        if frames is not None and rmsd is not None:
            ax1.plot(frames, rmsd, label=f'Enzima {enzyme_num}', color=colors[i], linewidth=1.5)
            backbone_data_found = True

    if backbone_data_found:
        ax1.set_xlabel('Frame')
        ax1.set_ylabel('RMSD Backbone (Å)')
        ax1.set_title(f'Comparison of Backbone RMSD Across {n_enzymes} Enzymes')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)

    # Plot all-atom RMSD
    all_atom_data_found = False
    for i, (enzyme_dir, enzyme_num) in enumerate(zip(enzyme_dirs, enzyme_numbers)):
        filepath = os.path.join(base_path, enzyme_dir, 'rmsd', f'{enzyme_dir}_rmsd_all.dat')
        frames, rmsd = read_data_file(filepath)
        if frames is not None and rmsd is not None:
            ax2.plot(frames, rmsd, label=f'Enzima {enzyme_num}', color=colors[i], linewidth=1.5)
            all_atom_data_found = True

    if all_atom_data_found:
        ax2.set_xlabel('Frame')
        ax2.set_ylabel('RMSD All-Atom (Å)')
        ax2.set_title(f'Comparison of All-Atom RMSD Across {n_enzymes} Enzymes')
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.grid(True, alpha=0.3)

    if backbone_data_found or all_atom_data_found:
        plt.tight_layout()
        plt.savefig(f'{output_prefix}rmsd_comparison.png', dpi=300, bbox_inches='tight')
        plt.savefig(f'{output_prefix}rmsd_comparison.pdf', bbox_inches='tight')
        plt.show()

    # Print statistics
    print("RMSD Statistics Summary:")
    print("=" * 80)
    print(f"{'Enzyme':<10} {'Backbone Avg':<15} {'Backbone Final':<17} {'All-Atom Avg':<15} {'All-Atom Final':<17}")
    print("-" * 80)

    for enzyme_dir, enzyme_num in zip(enzyme_dirs, enzyme_numbers):
        bb_file = os.path.join(base_path, enzyme_dir, 'rmsd', f'{enzyme_dir}_rmsd_backbone.dat')
        all_file = os.path.join(base_path, enzyme_dir, 'rmsd', f'{enzyme_dir}_rmsd_all.dat')

        _, bb_rmsd = read_data_file(bb_file)
        _, all_rmsd = read_data_file(all_file)

        bb_avg = np.mean(bb_rmsd) if bb_rmsd is not None else float('nan')
        bb_final = bb_rmsd[-1] if bb_rmsd is not None else float('nan')
        all_avg = np.mean(all_rmsd) if all_rmsd is not None else float('nan')
        all_final = all_rmsd[-1] if all_rmsd is not None else float('nan')

        print(f"Enzima {enzyme_num:<3} {bb_avg:<15.3f} {bb_final:<17.3f} {all_avg:<15.3f} {all_final:<17.3f}")

def plot_rmsf_comparison(enzyme_dirs, enzyme_numbers, base_path='.', output_prefix='', residues_per_enzyme=None, zones_of_interest=None):
    """Create comparison plots for RMSF data with zones of interest"""

    if zones_of_interest is None:
        zones_of_interest = []

    # Use provided residues_per_enzyme or ask if not provided
    if residues_per_enzyme is None:
        print("\nRMSF Analysis Configuration:")
        print("=" * 60)
        while True:
            try:
                residues_per_enzyme = int(input("¿Cuántos residuos tiene cada enzima? "))
                if 50 <= residues_per_enzyme <= 2000:
                    break
                else:
                    print("❌ Ingrese un número entre 50 y 2000 residuos")
            except ValueError:
                print("❌ Ingrese un número válido")

        print(f"✅ Configurado: {residues_per_enzyme} residuos por enzima")

    print(f"📊 Renumerando residuos desde 1 hasta {residues_per_enzyme}...")

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 18))

    n_enzymes = len(enzyme_dirs)
    colors = plt.cm.tab10(np.linspace(0, 1, max(10, n_enzymes)))

    print("\nRMSF Analysis Results:")
    print("=" * 60)

    # Storage for average calculation
    backbone_rmsf_data = []
    all_atom_rmsf_data = []

    # Plot backbone RMSF
    backbone_data_found = False
    for i, (enzyme_dir, enzyme_num) in enumerate(zip(enzyme_dirs, enzyme_numbers)):
        filepath = os.path.join(base_path, enzyme_dir, 'rmsf', f'{enzyme_dir}_rmsf_backbone.dat')
        residues, rmsf = read_data_file(filepath)
        if residues is not None and rmsf is not None:
            # Use sequential numbering from 1 to N based on user input
            if len(rmsf) <= residues_per_enzyme:
                residues_norm = np.arange(1, len(rmsf) + 1)
                rmsf_processed = rmsf
            else:
                # Truncate to specified number of residues
                residues_norm = np.arange(1, residues_per_enzyme + 1)
                rmsf_processed = rmsf[:residues_per_enzyme]

            ax1.plot(residues_norm, rmsf_processed, label=f'Enzima {enzyme_num}', color=colors[i], linewidth=1.5, alpha=0.8)
            backbone_rmsf_data.append(rmsf_processed)
            backbone_data_found = True

    if backbone_data_found:
        ax1.set_xlabel('Residue Number')
        ax1.set_ylabel('RMSF Backbone (Å)')
        ax1.set_title(f'Comparison of Backbone RMSF Across {n_enzymes} Enzymes')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)

        # Add zones of interest
        zone_colors = ['red', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        for i, (zone_name, start, end) in enumerate(zones_of_interest):
            color = zone_colors[i % len(zone_colors)]
            ax1.axvspan(start, end, alpha=0.2, color=color, label=f'{zone_name} ({start}-{end})')

        if zones_of_interest:
            # Add second legend for zones
            zone_handles = [patches.Rectangle((0,0),1,1, color=zone_colors[i % len(zone_colors)], alpha=0.2)
                          for i in range(len(zones_of_interest))]
            zone_labels = [f'{name} ({start}-{end})' for name, start, end in zones_of_interest]
            ax1.legend(zone_handles, zone_labels, loc='upper right', title='Zonas de Interés')

    # Plot all-atom RMSF
    all_atom_data_found = False
    for i, (enzyme_dir, enzyme_num) in enumerate(zip(enzyme_dirs, enzyme_numbers)):
        filepath = os.path.join(base_path, enzyme_dir, 'rmsf', f'{enzyme_dir}_rmsf_all.dat')
        residues, rmsf = read_data_file(filepath)
        if residues is not None and rmsf is not None:
            # Use sequential numbering from 1 to N based on user input
            if len(rmsf) <= residues_per_enzyme:
                residues_norm = np.arange(1, len(rmsf) + 1)
                rmsf_processed = rmsf
            else:
                # Truncate to specified number of residues
                residues_norm = np.arange(1, residues_per_enzyme + 1)
                rmsf_processed = rmsf[:residues_per_enzyme]

            ax2.plot(residues_norm, rmsf_processed, label=f'Enzima {enzyme_num}', color=colors[i], linewidth=1.5, alpha=0.8)
            all_atom_rmsf_data.append(rmsf_processed)
            all_atom_data_found = True

    if all_atom_data_found:
        ax2.set_xlabel('Residue Number')
        ax2.set_ylabel('RMSF All-Atom (Å)')
        ax2.set_title(f'Comparison of All-Atom RMSF Across {n_enzymes} Enzymes')
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.grid(True, alpha=0.3)

        # Add zones of interest to second plot too
        for i, (zone_name, start, end) in enumerate(zones_of_interest):
            color = zone_colors[i % len(zone_colors)]
            ax2.axvspan(start, end, alpha=0.2, color=color)

        if zones_of_interest:
            # Add zones legend to second plot
            zone_handles = [patches.Rectangle((0,0),1,1, color=zone_colors[i % len(zone_colors)], alpha=0.2)
                          for i in range(len(zones_of_interest))]
            zone_labels = [f'{name} ({start}-{end})' for name, start, end in zones_of_interest]
            ax2.legend(zone_handles, zone_labels, loc='upper right', title='Zonas de Interés')

    # Plot average RMSF with error bars (third subplot)
    if backbone_rmsf_data and all_atom_rmsf_data:
        # Convert to numpy arrays for easier calculation
        backbone_matrix = np.array(backbone_rmsf_data)
        all_atom_matrix = np.array(all_atom_rmsf_data)

        # Calculate mean and standard deviation
        backbone_mean = np.mean(backbone_matrix, axis=0)
        backbone_std = np.std(backbone_matrix, axis=0)
        all_atom_mean = np.mean(all_atom_matrix, axis=0)
        all_atom_std = np.std(all_atom_matrix, axis=0)

        # Create residue numbers
        residues_x = np.arange(1, len(backbone_mean) + 1)

        # Plot average with error bars
        ax3.errorbar(residues_x, backbone_mean, yerr=backbone_std,
                    label=f'Backbone Average (n={n_enzymes})', color='blue',
                    linewidth=2, alpha=0.8, capsize=3, errorevery=5)
        ax3.errorbar(residues_x, all_atom_mean, yerr=all_atom_std,
                    label=f'All-Atom Average (n={n_enzymes})', color='red',
                    linewidth=2, alpha=0.8, capsize=3, errorevery=5)

        ax3.set_xlabel('Residue Number')
        ax3.set_ylabel('RMSF Average (Å)')
        ax3.set_title(f'Average RMSF Across {n_enzymes} Enzymes with Standard Deviation')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Add zones of interest to average plot too
        for i, (zone_name, start, end) in enumerate(zones_of_interest):
            color = zone_colors[i % len(zone_colors)]
            ax3.axvspan(start, end, alpha=0.2, color=color)

        if zones_of_interest:
            # Add zones legend to average plot
            zone_handles = [patches.Rectangle((0,0),1,1, color=zone_colors[i % len(zone_colors)], alpha=0.2)
                          for i in range(len(zones_of_interest))]
            zone_labels = [f'{name} ({start}-{end})' for name, start, end in zones_of_interest]
            ax3.legend(zone_handles, zone_labels, loc='upper right', title='Zonas de Interés')

    if backbone_data_found or all_atom_data_found:
        plt.tight_layout()
        plt.savefig(f'{output_prefix}rmsf_comparison.png', dpi=300, bbox_inches='tight')
        plt.savefig(f'{output_prefix}rmsf_comparison.pdf', bbox_inches='tight')
        plt.show()

    # Print statistics
    print("RMSF Statistics Summary:")
    print("=" * 70)
    print(f"{'Enzyme':<10} {'Backbone Avg':<15} {'Backbone Max':<15} {'All-Atom Avg':<15} {'All-Atom Max':<15}")
    print("-" * 70)

    for enzyme_dir, enzyme_num in zip(enzyme_dirs, enzyme_numbers):
        bb_file = os.path.join(base_path, enzyme_dir, 'rmsf', f'{enzyme_dir}_rmsf_backbone.dat')
        all_file = os.path.join(base_path, enzyme_dir, 'rmsf', f'{enzyme_dir}_rmsf_all.dat')

        _, bb_rmsf = read_data_file(bb_file)
        _, all_rmsf = read_data_file(all_file)

        bb_avg = np.mean(bb_rmsf) if bb_rmsf is not None else float('nan')
        bb_max = np.max(bb_rmsf) if bb_rmsf is not None else float('nan')
        all_avg = np.mean(all_rmsf) if all_rmsf is not None else float('nan')
        all_max = np.max(all_rmsf) if all_rmsf is not None else float('nan')

        print(f"Enzima {enzyme_num:<3} {bb_avg:<15.3f} {bb_max:<15.3f} {all_avg:<15.3f} {all_max:<15.3f}")

def plot_sasa_comparison(enzyme_dirs, enzyme_numbers, base_path='.', output_prefix=''):
    """Create comparison plots for SASA data"""

    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    n_enzymes = len(enzyme_dirs)
    colors = plt.cm.tab10(np.linspace(0, 1, max(10, n_enzymes)))

    print("\nSASA Analysis Results:")
    print("=" * 60)

    # Plot SASA for all enzymes
    sasa_data_found = False
    for i, (enzyme_dir, enzyme_num) in enumerate(zip(enzyme_dirs, enzyme_numbers)):
        filepath = os.path.join(base_path, enzyme_dir, 'sasa', f'{enzyme_dir}_sasa.dat')
        frames, sasa = read_data_file(filepath)
        if frames is not None and sasa is not None:
            ax.plot(frames, sasa, label=f'Enzima {enzyme_num}', color=colors[i], linewidth=1.5)
            sasa_data_found = True

    if sasa_data_found:
        ax.set_xlabel('Frame')
        ax.set_ylabel('SASA (Ų)')
        ax.set_title(f'Comparison of Solvent Accessible Surface Area Across {n_enzymes} Enzymes')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f'{output_prefix}sasa_comparison.png', dpi=300, bbox_inches='tight')
        plt.savefig(f'{output_prefix}sasa_comparison.pdf', bbox_inches='tight')
        plt.show()

    # Create box plot if we have data
    if sasa_data_found:
        fig2, ax2 = plt.subplots(1, 1, figsize=(10, 6))

        sasa_data = []
        labels = []

        for enzyme_dir, enzyme_num in zip(enzyme_dirs, enzyme_numbers):
            filepath = os.path.join(base_path, enzyme_dir, 'sasa', f'{enzyme_dir}_sasa.dat')
            _, sasa = read_data_file(filepath)
            if sasa is not None:
                sasa_data.append(sasa)
                labels.append(f'Enzima {enzyme_num}')

        if sasa_data:
            box_plot = ax2.boxplot(sasa_data, tick_labels=labels, patch_artist=True)

            # Color the boxes
            for patch, color in zip(box_plot['boxes'], colors[:len(sasa_data)]):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)

            ax2.set_ylabel('SASA (Ų)')
            ax2.set_title(f'Distribution of SASA Values Across {n_enzymes} Enzymes')
            ax2.grid(True, alpha=0.3)

            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'{output_prefix}sasa_boxplot.png', dpi=300, bbox_inches='tight')
            plt.savefig(f'{output_prefix}sasa_boxplot.pdf', bbox_inches='tight')
            plt.show()

    # Print statistics
    print("SASA Statistics Summary:")
    print("=" * 70)
    print(f"{'Enzyme':<10} {'Average SASA':<15} {'Initial SASA':<15} {'Final SASA':<15} {'Std Dev':<15}")
    print("-" * 70)

    for enzyme_dir, enzyme_num in zip(enzyme_dirs, enzyme_numbers):
        filepath = os.path.join(base_path, enzyme_dir, 'sasa', f'{enzyme_dir}_sasa.dat')
        _, sasa = read_data_file(filepath)

        if sasa is not None:
            sasa_avg = np.mean(sasa)
            sasa_init = sasa[0]
            sasa_final = sasa[-1]
            sasa_std = np.std(sasa)

            print(f"Enzima {enzyme_num:<3} {sasa_avg:<15.1f} {sasa_init:<15.1f} {sasa_final:<15.1f} {sasa_std:<15.1f}")

def main():
    parser = argparse.ArgumentParser(description='Compare enzyme analysis data dynamically')
    parser.add_argument('--path', '-p', default='.', help='Base path to search for enzyme directories (default: current directory)')
    parser.add_argument('--output-prefix', '-o', default='', help='Prefix for output files (default: none)')
    parser.add_argument('--analysis', '-a', choices=['rmsd', 'rmsf', 'sasa', 'all'], default='all',
                        help='Type of analysis to run (default: all)')
    parser.add_argument('--residues', '-r', type=int, default=None,
                        help='Number of residues per enzyme for RMSF renumbering (if not provided, will ask interactively)')
    parser.add_argument('--zones', '-z', type=str, default=None,
                        help='Zones of interest (catalytic sites) in format: "zone1_name:start1-end1,zone2_name:start2-end2" (if not provided, will ask interactively)')

    args = parser.parse_args()

    # Find enzyme directories
    enzyme_dirs, enzyme_numbers = find_enzyme_directories(args.path)

    if not enzyme_dirs:
        print(f"No enzyme directories found in {os.path.abspath(args.path)}")
        print("Looking for directories matching pattern: enzima*")
        sys.exit(1)

    print(f"Analysis starting for {len(enzyme_dirs)} enzymes...")
    print(f"Base path: {os.path.abspath(args.path)}")
    print(f"Found enzymes: {enzyme_dirs}")
    print("=" * 60)

    # Handle residues configuration for RMSF
    residues_per_enzyme = args.residues
    if args.analysis in ['rmsf', 'all'] and residues_per_enzyme is None:
        print("\n🔧 CONFIGURACIÓN PARA ANÁLISIS RMSF:")
        print("=" * 60)
        while True:
            try:
                residues_per_enzyme = int(input("¿Cuántos residuos tiene cada enzima? "))
                if 50 <= residues_per_enzyme <= 2000:
                    break
                else:
                    print("❌ Ingrese un número entre 50 y 2000 residuos")
            except ValueError:
                print("❌ Ingrese un número válido")

        print(f"✅ Configurado: {residues_per_enzyme} residuos por enzima")
        print("=" * 60)
    elif args.analysis in ['rmsf', 'all'] and residues_per_enzyme is not None:
        print(f"✅ Usando {residues_per_enzyme} residuos por enzima (parámetro de línea de comandos)")

    # Handle zones of interest for RMSF
    zones_of_interest = []
    if args.analysis in ['rmsf', 'all']:
        if args.zones is None:
            print("\n🎯 ZONAS DE INTERÉS (SITIOS CATALÍTICOS):")
            print("=" * 60)
            while True:
                try:
                    num_zones = int(input("¿Cuántas zonas de interés quieres marcar? (0 para ninguna): "))
                    if num_zones >= 0:
                        break
                    else:
                        print("❌ Ingrese un número mayor o igual a 0")
                except ValueError:
                    print("❌ Ingrese un número válido")

            for i in range(num_zones):
                print(f"\nZona {i+1}:")
                while True:
                    zone_name = input(f"  Nombre de la zona (ej: Sitio_Activo, Región_Catalítica): ").strip()
                    if zone_name:
                        break
                    print("❌ Ingrese un nombre válido")

                while True:
                    try:
                        zone_range = input(f"  Rango de residuos para '{zone_name}' (ej: 150-180): ").strip()
                        if '-' in zone_range:
                            start, end = map(int, zone_range.split('-'))
                            if 1 <= start <= end <= residues_per_enzyme:
                                zones_of_interest.append((zone_name, start, end))
                                print(f"  ✅ Zona '{zone_name}': residuos {start}-{end}")
                                break
                            else:
                                print(f"❌ El rango debe estar entre 1 y {residues_per_enzyme}")
                        else:
                            print("❌ Use formato: inicio-fin (ej: 150-180)")
                    except ValueError:
                        print("❌ Use formato: inicio-fin (ej: 150-180)")

            if zones_of_interest:
                print(f"\n✅ Configuradas {len(zones_of_interest)} zonas de interés:")
                for name, start, end in zones_of_interest:
                    print(f"   - {name}: residuos {start}-{end}")
            print("=" * 60)
        else:
            # Parse zones from command line
            if args.zones and args.zones.strip():
                try:
                    for zone_str in args.zones.split(','):
                        if zone_str.strip():  # Skip empty strings
                            name, range_str = zone_str.split(':')
                            start, end = map(int, range_str.split('-'))
                            zones_of_interest.append((name.strip(), start, end))
                    print(f"✅ Usando zonas de interés: {[(n, s, e) for n, s, e in zones_of_interest]}")
                except:
                    print("⚠️ Error parseando zonas. Formato esperado: 'nombre1:inicio1-fin1,nombre2:inicio2-fin2'")
                    zones_of_interest = []
            else:
                print("✅ Sin zonas de interés especificadas")
                zones_of_interest = []

    # Run analyses
    if args.analysis in ['rmsd', 'all']:
        plot_rmsd_comparison(enzyme_dirs, enzyme_numbers, args.path, args.output_prefix)

    if args.analysis in ['rmsf', 'all']:
        plot_rmsf_comparison(enzyme_dirs, enzyme_numbers, args.path, args.output_prefix, residues_per_enzyme, zones_of_interest)

    if args.analysis in ['sasa', 'all']:
        plot_sasa_comparison(enzyme_dirs, enzyme_numbers, args.path, args.output_prefix)

    print(f"\nAnalysis completed for {len(enzyme_dirs)} enzymes!")

if __name__ == "__main__":
    main()