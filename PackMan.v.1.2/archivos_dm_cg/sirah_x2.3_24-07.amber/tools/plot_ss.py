import argparse
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator
import seaborn as sns
import os
import sys

def plot_ss_data(filename, plot_type, dpi=300, tu='us', dt=1e-04, H_col='darkviolet', E_col='yellow', C_col='aqua', out='ss_mtx.png', width=10, height=8, x_label_fontsize=14, y_label_fontsize=14, y_num_major_ticks=12,
                 x_num_major_ticks=10, x_tick_size=12, y_tick_size=12, title=None, title_size=16):
    """
    Plot secondary structure data from an input file.
    """
    
    # Configure the plot size
    plt.figure(figsize=(width, height))

    
    # Color scheme
    colors = [H_col, E_col, C_col]
    cmap = plt.matplotlib.colors.ListedColormap(colors)

    # Define the time unit (tu) and adjust dt accordingly
    if tu == 'ns':
        dt = 1e-01
    else:
        dt = 1e-04

    if filename == "ss_by_frame.xvg" or plot_type == 'frame':
        data = pd.read_csv(filename, sep='\s+', skiprows=2,
                           names=['frame', 'H(%)', 'E(%)', 'C(%)'])

        # Convert frames to microseconds
        data['frame'] = data['frame'] * dt

        # Plot
        line_h, = plt.plot(data['frame'], data['H(%)'], label='H', linestyle='-', lw=0.5, color=colors[0])
        line_e, = plt.plot(data['frame'], data['E(%)'], label='E', linestyle='-', lw=0.5, color=colors[1])
        line_c, = plt.plot(data['frame'], data['C(%)'], label='C', linestyle='-', lw=0.5, color=colors[2])

        # Automatically adjust axis limits
        plt.xlim(data['frame'].min(), data['frame'].max())
        plt.ylim(data[['H(%)', 'E(%)', 'C(%)']].min().min(), data[['H(%)', 'E(%)', 'C(%)']].max().max())

        # Add legend with squares and matching colors
        legend_elements = [
            Line2D([0], [0], marker='s', color='w', label='H', markersize=12, markerfacecolor=colors[0], markeredgecolor=colors[0]),
            Line2D([0], [0], marker='s', color='w', label='E', markersize=12, markerfacecolor=colors[1], markeredgecolor=colors[1]),
            Line2D([0], [0], marker='s', color='w', label='C', markersize=12, markerfacecolor=colors[2], markeredgecolor=colors[2])
        ]

        plt.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(0.99, 0.5), frameon=False, fontsize=14)

    elif filename == "ss_by_res.xvg" or plot_type == 'res':
        # Read data from the file and create a DataFrame
        data = pd.read_csv(filename, sep='\s+', skiprows=2,
                           names=['ResidueNumber', 'H(%)', 'E(%)', 'C(%)'])

        bars_h = plt.bar(data['ResidueNumber'], data['H(%)'], label='H', color=colors[0])
        bars_e = plt.bar(data['ResidueNumber'], data['E(%)'], label='E', bottom=data['H(%)'], color=colors[1])
        bars_c = plt.bar(data['ResidueNumber'], data['C(%)'], label='C', bottom=data['H(%)'] + data['E(%)'], color=colors[2])

        # Automatically adjust axis limits
        plt.xlim(data['ResidueNumber'].min(), data['ResidueNumber'].max())
        plt.ylim(data[['H(%)', 'E(%)', 'C(%)']].min().min(), data[['H(%)', 'E(%)', 'C(%)']].max().max())

        # Add legend with squares and matching colors
        legend_elements = [
            Line2D([0], [0], marker='s', color='w', label='H', markersize=12, markerfacecolor=colors[0], markeredgecolor=colors[0]),
            Line2D([0], [0], marker='s', color='w', label='E', markersize=12, markerfacecolor=colors[1], markeredgecolor=colors[1]),
            Line2D([0], [0], marker='s', color='w', label='C', markersize=12, markerfacecolor=colors[2], markeredgecolor=colors[2])
        ]

        plt.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(0.99, 0.5), frameon=False, fontsize=14)

    elif filename == "ss.mtx" or plot_type == 'mtx':
        data = pd.read_csv(filename, sep='\s+', skiprows=1, header=None)

        data[0] = data[0]*dt

        # Replace 'H' with 1, 'E' with 2, and 'C' with 3 in all columns except the first (frame)
        data.iloc[:, 1:] = data.iloc[:, 1:].replace({'H': 1, 'E': 2, 'C': 3})

        data.set_index(0, inplace=True)

        # Transpose the DataFrame so that residues are on the x-axis and time on the y-axis
        data_transposed = data.transpose()

        new_row = data_transposed.iloc[0].copy()
        new_row[0] = 1
        new_row[1] = 2
        new_row[2] = 3

        df = pd.DataFrame(new_row).transpose().append(data_transposed, ignore_index=True)

        sns.heatmap(df, cmap=cmap, cbar=False)

        # Adjust x-axis ticks
        num_cols = len(df.columns)
        min_val = int(df.columns.min())
        max_val = int(df.columns.max())
        density = num_cols / (max_val - min_val)
        sample_ticks = range(0, len(df.columns), int(density))
        plt.xticks(sample_ticks, [int(x) for x in df.columns[sample_ticks]], rotation=0)

        # Set y-axis limits
        y_max = data_transposed.shape[0]

        # Configure the number of ticks on the y-axis
        num_ticks = y_max
        locator = MultipleLocator(y_max // (num_ticks - 1))
        plt.gca().yaxis.set_major_locator(locator)

        # Adjust y-axis ticks
        tick_positions = [int(x) for x in plt.yticks()[0]] 
        tick_positions = [x+0.5 for x in tick_positions]
        tick_labels = [str(int(x)) for x in plt.yticks()[0]]
        plt.yticks(tick_positions, tick_labels)
        plt.ylim(1, y_max+1)
        plt.yticks(rotation=0)
        
        # Define colors for H, E, and C
        legend_elements = [Line2D([0], [0], marker='s', color='w', label='H', markersize=12, markerfacecolor=colors[0]),
                           Line2D([0], [0], marker='s', color='w', label='E', markersize=12, markerfacecolor=colors[1]),
                           Line2D([0], [0], marker='s', color='w', label='C', markersize=12, markerfacecolor=colors[2])]

        # Add legend with squares and matching colors
        plt.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(0.99, 0.5), frameon=False, fontsize=14)

    # Configure axis labels
    if filename.lower() in ['ss.mtx', 'ss_by_frame.xvg'] or plot_type in ['mtx', 'frame']:
        if tu == 'us':
            plt.xlabel('Time ($\mu$s)', fontsize=x_label_fontsize)
        else:
            plt.xlabel('Time (ns)', fontsize=x_label_fontsize)

        if filename.lower() != 'ss.mtx' or plot_type != 'mtx':
            plt.ylabel('Percentage', fontsize=y_label_fontsize)
        else:
            plt.ylabel('Residue', fontsize=y_label_fontsize)
    else:
        plt.xlabel('Residue Number', fontsize=y_label_fontsize)
        plt.ylabel('Percentage', fontsize=y_label_fontsize)

    # Configure tick sizes on x and y axes
    plt.xticks(fontsize=x_tick_size)
    plt.yticks(fontsize=y_tick_size)

    # Configure title and title size
    if title is not None:
        plt.title(title, fontsize=title_size)

    # Configure the number of major tick locators on the y-axis
    plt.locator_params(axis='y', nbins=y_num_major_ticks)

    # Configure the number of major tick locators on the x-axis
    plt.locator_params(axis='x', nbins=x_num_major_ticks)

    # Save the plot as a PNG image
    plt.savefig(out, dpi=dpi, bbox_inches='tight')

    # Show the plot
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a PNG image from an input file (ss.mtx, ss_by_frame.xvg, or ss_by_res.xvg) generated by SIRAH.')
    parser.add_argument('-i', dest='filename', metavar='[input]', type=str, default='ss.mtx', help='Input file name')
    parser.add_argument('-t', dest='plot_type', metavar='[type]', type=str, default=None, help='Type of plot: frame, res, or mtx')
    parser.add_argument('-d', dest='dpi', metavar='[dpi]', type=int, default=300, help='DPI for saving the figure')
    parser.add_argument('-tu', dest='tu', metavar='[tu]', type=str, default='us', help='Time unit: us or ns')
    parser.add_argument('-dt', dest='dt', metavar='[dt]', type=float, default=1e-04, help='Time between consecutive frames')
    parser.add_argument('-H', dest='H_col', metavar='[helix-color]', type=str, default='darkviolet', help='Alpha-helix color')
    parser.add_argument('-E', dest='E_col', metavar='[beta-sheet color]', type=str, default='yellow', help='Beta-sheet color')
    parser.add_argument('-C', dest='C_col', metavar='[coil color]', type=str, default='aqua', help='Coil color')
    parser.add_argument('-o', dest='out', metavar='[out name]', type=str, default=None, help='Image output name')
    parser.add_argument('-wt', dest='width', metavar='[width]', type=float, default=10, help='Image width (inches)')
    parser.add_argument('-ht', dest='height', metavar='[height]', type=float, default=8, help='Image height (inches)')
    parser.add_argument('-xfs', dest='x_label_fontsize', metavar='[xlab fontsize]', type=int, default=14, help='Fontsize for x-axis labels')
    parser.add_argument('-yfs', dest='y_label_fontsize', metavar='[ylab fontsize]', type=int, default=14, help='Fontsize for y-axis labels')
    parser.add_argument('-yticks', dest='y_num_major_ticks', metavar='[y # ticks]', type=int, default=10, help='Number of major tick locators on the y-axis')
    parser.add_argument('-xticks', dest='x_num_major_ticks', metavar='[x # ticks]', type=int, default=10, help='Number of major tick locators on the x-axis')
    parser.add_argument('-xtsize', dest='x_tick_size', metavar='[xtsize]', type=int, default=12, help='Size of ticks on the x-axis')
    parser.add_argument('-ytsize', dest='y_tick_size', metavar='[ytsize]', type=int, default=12, help='Size of ticks on the y-axis')
    parser.add_argument('-title', dest='title', metavar='[title]', type=str, default=None, help='Title of the plot')
    parser.add_argument('-ttsize', dest='title_size', metavar='[title_size]', type=int, default=16, help='Size of the plot title')
    parser.add_argument('--version', action='store_true', help='Print version and exit')

    args = parser.parse_args()
    
    if args.version:
        print("Version 1.0 [September 2023]")
        sys.exit(0)

    if args.out is None:
        input_filename = os.path.splitext(args.filename)[0]
        args.out = input_filename

    # Check if the input file is valid
    if args.filename not in ['ss.mtx', 'ss_by_frame.xvg', 'ss_by_res.xvg']:
        if args.plot_type is None or args.plot_type not in ['frame', 'res', 'mtx']:
            print("Error: Please provide a valid input file (-i) or specify the plot type (-t frame/res/mtx).")
            sys.exit(1)

    plot_ss_data(args.filename, args.plot_type, args.dpi, args.tu, args.dt, args.H_col, args.E_col, args.C_col, args.out, args.width, args.height, args.x_label_fontsize, args.y_label_fontsize, args.y_num_major_ticks,
                 args.x_num_major_ticks, args.x_tick_size, args.y_tick_size, args.title, args.title_size)
