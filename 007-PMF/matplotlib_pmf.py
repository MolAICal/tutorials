import sys
import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Call plot_pmf function to generate the figure
"""
Create PMF plot using matplotlib.

Args:
    xray (numpy.ndarray): Array of x coordinates
    yray (numpy.ndarray): Array of y coordinates
    zmat (numpy.ndarray): Matrix of PMF values
    pmf_draw_mode (str): Drawing mode ('conshd' or 'contur')
    pmf_color_levels (int): Number of color levels
    pmf_fig_label (str): Label for contour lines ('float' or 'none')
    pmf_x_label (str): Label for x-axis
    pmf_y_label (str): Label for y-axis
    pmf_fig_name (str): Output figure filename
"""

# Set default parameters
pmf_draw_mode = 'contur'
pmf_color_levels = 10
pmf_fig_label = 'float'
pmf_x_label = 'x-axis'
pmf_y_label = 'y-axis'
pmf_fig_name = 'pmf_figure.png'

# Read data from pmf_data_plot.dat file
data = np.loadtxt('pmf_data_plot.dat')

# Extract columns from data
x_values = data[:, 0]  # First column for xray
y_values = data[:, 1]  # Second column for yray
z_values = data[:, 2]  # Third column for zmat_normalized[i, j]

# Get unique x and y values
xray = np.unique(x_values)
yray = np.unique(y_values)

# Create empty matrix for z values
zmat = np.zeros((len(xray), len(yray)))

# Fill the matrix with z values
for i, x in enumerate(x_values):
    x_idx = np.where(xray == x)[0][0]
    y_idx = np.where(yray == y_values[i])[0][0]
    zmat[x_idx, y_idx] = z_values[i]


# Get min and max values from matrix
z_min = np.nanmin(zmat)
z_max = np.nanmax(zmat)

# Create figure
plt.figure(figsize=(10, 7))

# Create meshgrid for plotting
X, Y = np.meshgrid(xray, yray)
Z = zmat.T  # Transpose for correct orientation

# Set up color levels
levels = np.linspace(z_min, z_max, pmf_color_levels)

# Create custom colormap similar to DISLIN default
colors = plt.cm.jet(np.linspace(0, 1, 256))
cmap = LinearSegmentedColormap.from_list('custom_jet', colors)
# Set thicker frame
plt.rcParams['axes.linewidth'] = 1.0

def label_contours_with_gap_precise(ax, contour_set,
                                    fmt="%.2f",
                                    text_size=12,
                                    gap_padding=0.02):
    """
    Label contour lines with values, avoid overlap with other labels,
    and create a precise gap in the contour line exactly where the label is drawn.

    Parameters:
        ax          : Matplotlib Axes
        contour_set : plt.contour return object
        fmt         : Format string for labels
        text_size   : Font size for labels
        gap_padding : Extra fraction of axis range to extend the gap (default 0.02)
    """
    existing_bboxes = []

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_range = xlim[1] - xlim[0]
    y_range = ylim[1] - ylim[0]

    for level, collection in zip(contour_set.levels, contour_set.collections):
        for path in collection.get_paths():
            vertices = path.vertices
            if len(vertices) < 10:
                continue

            idx = len(vertices) // 2
            x, y = vertices[idx]

            # Compute rotation angle
            if idx < len(vertices) - 1:
                dx, dy = vertices[idx + 1] - vertices[idx - 1]
                angle = np.degrees(np.arctan2(dy, dx))
            else:
                angle = 0

            # Draw the label
            txt = ax.text(x, y, fmt % level, fontsize=text_size,
                          rotation=angle, ha="center", va="center")
            ax.figure.canvas.draw()
            bbox_disp = txt.get_window_extent()
            bbox_data = bbox_disp.transformed(ax.transData.inverted())  # Convert to data coords

            # Check overlap
            overlap = any(bbox_data.overlaps(bb) for bb in existing_bboxes)
            if overlap:
                txt.remove()
                continue
            existing_bboxes.append(bbox_data)

            # -----------------------------
            # Create precise gap in contour line
            # -----------------------------
            # Extend bbox a bit
            x0 = bbox_data.x0 - gap_padding * x_range
            x1 = bbox_data.x1 + gap_padding * x_range
            y0 = bbox_data.y0 - gap_padding * y_range
            y1 = bbox_data.y1 + gap_padding * y_range

            # Find vertices inside bbox and replace with NaN
            mask = (vertices[:, 0] >= x0) & (vertices[:, 0] <= x1) & \
                   (vertices[:, 1] >= y0) & (vertices[:, 1] <= y1)
            vertices[mask, :] = np.nan

            # Update path vertices
            path.vertices = vertices


if pmf_draw_mode.lower() == 'conshd':
    # Filled contour plot
    # Add filled contour with gradient colors
    contour_filled = plt.contourf(X, Y, Z, levels=levels, cmap=cmap, alpha=1.0, extend='both')

    # Line contour plot with colored lines
    contour_lines = plt.contour(X, Y, Z, levels=levels, colors='k', linewidths=1.0)

    # Add color bar with 2 decimal places for the filled contour
    cbar = plt.colorbar(contour_filled, format='%.2f')
    cbar.ax.tick_params(labelsize=15, width=1.5, length=3.0)
    cbar.outline.set_linewidth(1.0)

    # Add labels to contour lines if requested
    if pmf_fig_label.lower() == 'float':
        label_contours_with_gap_precise(plt.gca(), contour_lines, fmt="%.2f", text_size=15, gap_padding=0.001)

elif pmf_draw_mode.lower() == 'contur':
    # Line contour plot with colored lines
    contour_lines = plt.contour(X, Y, Z, levels=levels, cmap=cmap, linewidths=2.5)

    # Create a color bar with gradient colors for the contour lines
    cbar = plt.colorbar(contour_lines, format='%.2f')
    cbar.ax.tick_params(labelsize=15, width=1.5, length=3.0)
    cbar.outline.set_linewidth(1.0)

    # Add labels to contour lines if requested
    if pmf_fig_label.lower() == 'float':
        label_contours_with_gap_precise(plt.gca(), contour_lines, fmt="%.2f", text_size=15, gap_padding=0.001)

# Set labels and title
plt.xlabel(pmf_x_label, fontsize=15)
plt.ylabel(pmf_y_label, fontsize=15)
# plt.title('PMF Energy Landscape')

# Increase tick font size and make tick lines thicker
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)

# Make tick lines thicker
plt.tick_params(axis='both', which='major', width=1.5, length=6.0)
plt.tick_params(axis='both', which='minor', width=1.5, length=4.0)

# Save figure
plt.tight_layout()
plt.savefig(pmf_fig_name, dpi=300)
print(f"Figure saved as {pmf_fig_name}")

plt.show()
