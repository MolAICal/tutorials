import os
import re
import argparse
import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages  # used for PDF output

class ADMETVisualizer:
    MAX_HEIGHT_INCH = 50  # Maximum figure height

    def __init__(self, file_path, items_per_fig=None):
        self.file_path = file_path
        self.items_per_fig = items_per_fig
        self.data = {}
        # prefer Times New Roman when available; matplotlib will fall back if not present
        plt.rcParams['font.family'] = 'Times New Roman'
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.size'] = 11

    def parse_data(self):
        """Parse results.dat file into self.data dictionary.
        self.data is a dict: { ligand_name: [entry, ...], ... }
        where entry = {"name": item_name, "pred": pred, "val1": val1, "val2": val2, "type": "classification"/"regression"}
        """
        if not os.path.exists(self.file_path):
            print(f"Error: {self.file_path} not found.")
            return

        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        mol_blocks = re.split(r'## The \d+\w* molecule ##', content)
        for block in mol_blocks:
            block = block.strip()
            if not block:
                continue
            lines = block.splitlines()
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                match = re.match(r'(\d+):\s*(.+)', line)
                if match:
                    # item index and name line
                    item_index = int(match.group(1))
                    item_name = match.group(2).strip()
                    # skip next header line (expected "Predicted Confidence Credibility")
                    i += 1
                    if i >= len(lines):
                        break
                    # read the data line
                    i += 1
                    if i >= len(lines):
                        break
                    data_line = lines[i].strip()
                    tokens = data_line.split()
                    if len(tokens) >= 4:
                        ligand_name = tokens[0]     # molecule name
                        pred = tokens[1]
                        try:
                            val1 = float(tokens[2])
                        except:
                            val1 = None
                        try:
                            val2 = float(tokens[3])
                        except:
                            val2 = None
                        entry_type = "regression" if self._is_number(pred) else "classification"
                        entry = {
                            "name": item_name,
                            "pred": pred,
                            "val1": val1,
                            "val2": val2,
                            "type": entry_type
                        }
                        if ligand_name not in self.data:
                            self.data[ligand_name] = []
                        self.data[ligand_name].append(entry)
                i += 1

    def _is_number(self, s):
        """Return True if string s can be converted to float."""
        try:
            float(s)
            return True
        except:
            return False

    def plot_all(self):
        """Generate PNGs and a combined PDF for each molecule (existing behavior)."""
        for ligand_name, entries in self.data.items():
            output_dir = ligand_name
            os.makedirs(output_dir, exist_ok=True)

            if self.items_per_fig is None:
                max_items_per_fig = max(1, int(self.MAX_HEIGHT_INCH / 3))
            else:
                max_items_per_fig = max(1, int(self.items_per_fig))

            # Prepare PDF for this molecule
            pdf_path = os.path.join(output_dir, f"{ligand_name}.pdf")
            pdf_pages = PdfPages(pdf_path)

            for i in range(0, len(entries), max_items_per_fig):
                chunk = entries[i:i + max_items_per_fig]
                fig = self._create_figure(ligand_name, chunk, i, output_dir, max_items_per_fig, save_png=True)
                # Save this figure into PDF
                pdf_pages.savefig(fig, bbox_inches='tight')
                plt.close(fig)

            pdf_pages.close()
        print("Visualization completed successfully (PNG + PDF).")

    def _create_figure(self, ligand_name, chunk, start_idx, output_dir, max_items_per_fig, save_png=False):
        """Create a figure with multiple subplots for a chunk of entries. Optionally save PNG.
        Returns the Matplotlib figure object so caller can save it into a PDF.
        """
        # dynamic figure height and spacing: increase height when many subplots
        row_height = 3.0
        fig_height = min(max(2.8, row_height * len(chunk)), self.MAX_HEIGHT_INCH)
        fig, axes = plt.subplots(len(chunk), 1, figsize=(11.7, fig_height))
        if len(chunk) == 1:
            axes = np.array([axes])

        # give more left margin so y-labels and left-side texts don't overlap
        left_margin = 0.20
        right_margin = 0.98
        top_margin = 0.95
        bottom_margin = 0.08

        for idx, entry in enumerate(chunk):
            ax = axes[idx]
            if entry["type"] == "classification":
                labels = []
                values = []
                if entry["val1"] is not None:
                    labels.append("Confidence")
                    values.append(entry["val1"])
                if entry["val2"] is not None:
                    labels.append("Credibility")
                    values.append(entry["val2"])
                if not labels:
                    labels = ["Confidence"]
                    values = [0.0]
                # plot horizontal bars
                barh_height = 0.6
                if len(labels) >= 3:
                    barh_height = max(0.35, 0.9 / len(labels))
                bars = ax.barh(labels, values, height=barh_height, color=['#3498db', '#e67e22'])

                # compute xlimit with padding; ensure at least 1.08 range to show percent-like values and room for labels
                max_val = max(values) if values else 0.0
                # add absolute padding 0.08 and relative padding
                xlim_upper = max(1.08, max_val + 0.08, max_val * 1.08)
                if max_val >= 0.95:
                    xlim_upper = max(xlim_upper, 1.08)
                ax.set_xlim(0, xlim_upper)
                ax.set_title(f"{entry['name']} - Prediction: {entry['pred']}", fontsize=14, fontweight='bold')
                ax.grid(axis='x', linestyle='--', alpha=0.7)

                # place annotation labels smartly to avoid overlap and clipping
                # for horizontal bars: prefer inside if close to right boundary; otherwise place slightly outside,
                # but ensure outside position doesn't exceed 90% of xlim_upper (to avoid overlapping top-border area)
                for bar in bars:
                    width = bar.get_width()
                    pad = xlim_upper * 0.02
                    outside_x = width + pad
                    inside_x = max(width - pad, 0.01)
                    threshold = xlim_upper - (0.06 * xlim_upper)
                    # if outside would be too close to right edge, put inside
                    if outside_x > xlim_upper * 0.90 or outside_x > threshold:
                        txt_x = inside_x
                        ha = 'right'
                        color = 'white'
                    else:
                        txt_x = outside_x
                        ha = 'left'
                        color = 'black'
                    y_pos = bar.get_y() + bar.get_height() / 2
                    ax.text(txt_x, y_pos, f'{width:.2f}', va='center', ha=ha, fontsize=10, color=color, clip_on=True)

                ax.margins(y=0.28)
                ax.set_xlabel("")

            else:
                # regression: plot predicted value with asymmetric error bars
                try:
                    pred_val = float(entry["pred"])
                except:
                    pred_val = 0.0
                low_bound = entry["val1"] if entry["val1"] is not None else pred_val
                high_bound = entry["val2"] if entry["val2"] is not None else pred_val
                try:
                    low = float(low_bound)
                except:
                    low = pred_val
                try:
                    high = float(high_bound)
                except:
                    high = pred_val
                err_low = max(0.0, pred_val - low)
                err_high = max(0.0, high - pred_val)

                ax.errorbar(pred_val, 0, xerr=[[err_low], [err_high]], fmt='o',
                            color='red', capsize=6, markersize=8)
                ax.set_yticks([])
                ax.set_title(f"{entry['name']} (Numerical Analysis)", fontsize=14, fontweight='bold')
                ax.set_xlabel(f"Predicted Value: {pred_val}", fontsize=12)

                min_span = 0.5
                x_min = pred_val - max(err_low * 1.2, min_span * 0.25)
                x_max = pred_val + max(err_high * 1.2, min_span * 0.25)
                if x_min == x_max:
                    x_min = pred_val - 0.5
                    x_max = pred_val + 0.5
                span = x_max - x_min
                x_min = x_min - 0.08 * span
                x_max = x_max + 0.08 * span
                ax.set_xlim(x_min, x_max)

                # numeric label: prefer horizontal alignment near the point (same y), offset left/right as needed
                offset = max(0.04 * span, 0.02)
                left_x = pred_val - offset
                right_x = pred_val + offset
                if left_x < x_min + 0.01 * span:
                    tx = right_x
                    ha = 'left'
                else:
                    tx = left_x
                    ha = 'right'
                # place at same vertical level as the point (y=0) with vertical centering
                ax.text(tx, 0.0, f"{pred_val:.2f}", ha=ha, va='center', fontsize=10, color='red', clip_on=True)
                ax.grid(axis='x', linestyle='--', alpha=0.5)
                ax.margins(y=0.25)

        # global layout adjustments to avoid clipping labels:
        fig.tight_layout(pad=1.0)
        fig.subplots_adjust(left=left_margin, right=right_margin, top=top_margin, bottom=bottom_margin)

        # Save PNG if requested
        if save_png:
            part_num = (start_idx // max_items_per_fig) + 1
            file_name = f"{ligand_name}_part_{part_num}.png"
            plt.savefig(os.path.join(output_dir, file_name), dpi=150, bbox_inches='tight')
        return fig  # return figure for PDF saving

    # ----------------------------
    # New feature: merged-by-item (enhanced)
    # ----------------------------
    def plot_merged_by_item(self):
        """For each ADMET item, merge results from all molecules into one plot.
        Save each item-plot as PNG into 'merge_lig' folder and collect all pages into merged_items.pdf.
        Features:
          - show prediction string (pred) under each ligand name
          - legend placed inside the top of the axes to avoid overlap with x-ticks
          - automatic pagination when many ligands
          - classification annotations moved downward/inside when possible to avoid overlap
          - regression annotations horizontally aligned near corresponding points
        """
        # parameters: ligands per page (tune this if you need denser/looser pages)
        LIGANDS_PER_PAGE = 20

        # collect unique item names in a stable order (appearance order)
        seen = []
        for ligand_entries in self.data.values():
            for e in ligand_entries:
                if e['name'] not in seen:
                    seen.append(e['name'])
        all_items = seen  # ordered list of item names

        merge_dir = "merge_lig"
        os.makedirs(merge_dir, exist_ok=True)

        pdf_path = os.path.join(merge_dir, "merged_items.pdf")
        pdf_pages = PdfPages(pdf_path)

        for item_name in all_items:
            # collect per-ligand data for this item
            ligands = []
            preds_strs = []  # store pred string for display (e.g., 'Active')
            types = []   # entry type per ligand
            confs = []   # val1 for classification (or None)
            creds = []   # val2 for classification (or None)
            preds_num = []  # numeric predicted value for regression (or None)
            lows = []    # lower bound (for regression)
            highs = []   # upper bound (for regression)

            for ligand, entries in sorted(self.data.items()):
                found = None
                for e in entries:
                    if e['name'] == item_name:
                        found = e
                        break
                if found:
                    ligands.append(ligand)
                    preds_strs.append(found['pred'])
                    types.append(found['type'])
                    if found['type'] == "classification":
                        confs.append(found['val1'] if found['val1'] is not None else np.nan)
                        creds.append(found['val2'] if found['val2'] is not None else np.nan)
                        preds_num.append(None)
                        lows.append(None)
                        highs.append(None)
                    else:  # regression
                        try:
                            pred_val_num = float(found['pred'])
                        except:
                            pred_val_num = np.nan
                        preds_num.append(pred_val_num)
                        confs.append(None)
                        creds.append(None)
                        low = None
                        high = None
                        if found['val1'] is not None:
                            try:
                                low = float(found['val1'])
                            except:
                                low = None
                        if found['val2'] is not None:
                            try:
                                high = float(found['val2'])
                            except:
                                high = None
                        lows.append(low)
                        highs.append(high)

            if not ligands:
                continue  # no data for this item across all ligands

            n = len(ligands)
            # compute number of pages
            pages = math.ceil(n / LIGANDS_PER_PAGE)
            for page_idx in range(pages):
                start = page_idx * LIGANDS_PER_PAGE
                end = min(n, (page_idx + 1) * LIGANDS_PER_PAGE)
                lig_slice = ligands[start:end]
                pred_slice = preds_strs[start:end]
                type_slice = types[start:end]
                conf_slice = confs[start:end]
                cred_slice = creds[start:end]
                predsnum_slice = preds_num[start:end]
                lows_slice = lows[start:end]
                highs_slice = highs[start:end]

                m = len(lig_slice)
                # determine figure height: adapt to number of ligands to avoid x tick collision
                fig_height = min(max(3, 0.25 * m + 2.0), self.MAX_HEIGHT_INCH)
                fig, ax = plt.subplots(figsize=(11.7, fig_height))

                # adjust xtick label fontsize based on m
                if m <= 8:
                    xtick_fs = 10
                elif m <= 20:
                    xtick_fs = 9
                elif m <= 40:
                    xtick_fs = 8
                else:
                    xtick_fs = 7

                left_margin = 0.20
                right_margin = 0.98
                # move title further up to avoid overlap with annotations (leave room for legend inside top)
                top_margin = 0.86
                # reserve extra bottom margin for legend and two-line tick labels
                bottom_margin = 0.26 + min(0.35, 0.01 * max(0, m - 6))

                num_class = sum(1 for t in type_slice if t == "classification")
                num_reg = sum(1 for t in type_slice if t == "regression")

                # prepare x positions
                x = np.arange(m)

                # build tick labels as two-line: ligand name \n pred-string
                tick_labels = [f"{lig_slice[i]}\n{pred_slice[i]}" for i in range(m)]

                if num_class >= num_reg:
                    # grouped vertical bar chart with two series: Confidence and Credibility per ligand
                    width = 0.35
                    conf_vals = [0.0 if v is None or (isinstance(v, float) and np.isnan(v)) else v for v in conf_slice]
                    cred_vals = [0.0 if v is None or (isinstance(v, float) and np.isnan(v)) else v for v in cred_slice]
                    b1 = ax.bar(x - width/2, conf_vals, width, label='Confidence')
                    b2 = ax.bar(x + width/2, cred_vals, width, label='Credibility')

                    # determine y-limit with additional top buffer to host legend inside top and avoid overlap
                    max_h = 0.0
                    if conf_vals:
                        max_h = max(max_h, max(conf_vals))
                    if cred_vals:
                        max_h = max(max_h, max(cred_vals))
                    # baseline top headroom similar to previous logic
                    ylim_top = max(1.25, max_h + 0.14, max_h * 1.18)
                    # add extra absolute buffer
                    extra_buffer = max(0.25, 0.10 * max_h)
                    ylim_top = max(ylim_top, max_h + extra_buffer)

                    # ----------------------------
                    # ADJUST: place legend at data y = 1.18 (user requested)
                    # Ensure ylim_top is large enough to include legend_y
                    # ----------------------------
                    LEGEND_DATA_Y = 1.18
                    # ensure we leave a small margin above legend
                    ylim_top = max(ylim_top, LEGEND_DATA_Y + 0.02 * max(1.0, max_h))

                    # compute allowed annotation max (place annotations below legend_y by small guard)
                    TOP_GUARD = 0.02 * max(1.0, max_h)
                    ann_max_allowed = LEGEND_DATA_Y - TOP_GUARD

                    # finally set y limits using adjusted ylim_top
                    ax.set_ylim(0, ylim_top)

                    # annotate numeric labels: place them above bar ends but strictly below legend data y
                    ann_final_max = 0.0
                    for rect in b1:
                        h = rect.get_height()
                        center_x = rect.get_x() + rect.get_width() / 2.0
                        ann_y = h + 0.03 * ylim_top
                        # cap annotation below ann_max_allowed
                        ann_y = min(ann_y, ann_max_allowed)
                        if ann_y > ann_max_allowed * 0.98:
                            ann_y = max(h - 0.02 * ylim_top, h * 0.5)
                            ann_y = max(ann_y, 0.01 * ylim_top)
                        ann_final_max = max(ann_final_max, ann_y)
                        ax.text(center_x, ann_y, f'{h:.2f}', ha='center', va='bottom', fontsize=8, color='black', clip_on=True)

                    for rect in b2:
                        h = rect.get_height()
                        center_x = rect.get_x() + rect.get_width() / 2.0
                        ann_y = h + 0.03 * ylim_top
                        ann_y = min(ann_y, ann_max_allowed)
                        if ann_y > ann_max_allowed * 0.98:
                            ann_y = max(h - 0.02 * ylim_top, h * 0.5)
                            ann_y = max(ann_y, 0.01 * ylim_top)
                        ann_final_max = max(ann_final_max, ann_y)
                        ax.text(center_x, ann_y, f'{h:.2f}', ha='center', va='bottom', fontsize=8, color='black', clip_on=True)

                    # set xticks and labels
                    ax.set_xticks(x)
                    ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=xtick_fs)
                    ax.set_ylabel("Confidence / Credibility", fontsize=12)
                    # title moved upward by y param to avoid overlap; remove part x/y info for tidiness
                    ax.set_title(f"{item_name} - All molecules (classification)",
                                 fontsize=14, fontweight='bold', y=1.03)

                    # place legend at data coordinate y = 1.18, centered at mean x
                    legend_x = np.mean(x) if m > 0 else 0.5
                    ax.legend(loc='center', bbox_to_anchor=(legend_x, LEGEND_DATA_Y),
                              bbox_transform=ax.transData, ncol=2, frameon=False)
                    ax.grid(axis='y', linestyle='--', alpha=0.4)
                else:
                    # regression-style: plot predicted numeric values with asymmetric errorbars
                    y = [predsnum_slice[i] if predsnum_slice[i] is not None else np.nan for i in range(m)]
                    yerr_lower = []
                    yerr_upper = []
                    for i in range(m):
                        pred_val_num = predsnum_slice[i]
                        low = lows_slice[i]
                        high = highs_slice[i]
                        if pred_val_num is None or (isinstance(pred_val_num, float) and np.isnan(pred_val_num)):
                            yerr_lower.append(0.0)
                            yerr_upper.append(0.0)
                        else:
                            if low is None:
                                low_e = 0.0
                            else:
                                low_e = max(0.0, pred_val_num - low)
                            if high is None:
                                high_e = 0.0
                            else:
                                high_e = max(0.0, high - pred_val_num)
                            yerr_lower.append(low_e)
                            yerr_upper.append(high_e)
                    yerr = np.array([yerr_lower, yerr_upper])
                    ax.errorbar(x, y, yerr=yerr, fmt='o', ecolor='red', capsize=5, markersize=6, color='black')

                    # compute y-limits
                    valid_y = [y[i] for i in range(m) if y[i] is not None and not (isinstance(y[i], float) and np.isnan(y[i]))]
                    if valid_y:
                        min_y = min(valid_y)
                        max_y = max(valid_y)
                    else:
                        min_y, max_y = 0.0, 1.0
                    pad = (max_y - min_y) * 0.12 if (max_y - min_y) > 0 else 0.5
                    y_bottom = min_y - pad
                    y_top = max_y + pad
                    if y_bottom == y_top:
                        y_bottom -= 0.5
                        y_top += 0.5
                    ax.set_ylim(y_bottom, y_top)

                    # place numeric labels to left of points (or right if left too tight)
                    for i_pt, yi in enumerate(y):
                        if yi is not None and not (isinstance(yi, float) and np.isnan(yi)):
                            offset = max(0.04 * max(1, m), 0.04)
                            left_x = i_pt - offset
                            right_x = i_pt + offset
                            if left_x < 0:
                                tx = right_x
                                ha = 'left'
                            else:
                                tx = left_x
                                ha = 'right'
                            ax.text(tx, yi, f"{yi:.2f}", ha=ha, va='center', fontsize=8, color='red', clip_on=True)

                    ax.set_xticks(x)
                    ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=xtick_fs)
                    ax.set_ylabel("Predicted Value", fontsize=12)
                    # remove part x/y from regression title as well
                    ax.set_title(f"{item_name} - All molecules (regression)",
                                 fontsize=14, fontweight='bold', y=1.03)
                    ax.grid(axis='y', linestyle='--', alpha=0.4)

                # final layout tweaks for this fig
                fig.tight_layout(pad=1.0)
                fig.subplots_adjust(left=left_margin, right=right_margin, top=top_margin, bottom=bottom_margin)

                # create safe filename
                safe_name = re.sub(r'[^A-Za-z0-9_\-]', '_', item_name)[:160]
                png_path = os.path.join(merge_dir, f"{safe_name}_part_{page_idx+1}.png")
                plt.savefig(png_path, dpi=150, bbox_inches='tight')
                pdf_pages.savefig(fig, bbox_inches='tight')
                plt.close(fig)

        pdf_pages.close()
        print(f"Merged plots saved into '{merge_dir}' (PNG + merged_items.pdf).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ADMET results visualizer.")
    parser.add_argument("-i", "--input", default="results.dat", help="Input results.dat file")
    parser.add_argument("-n", "--num_items", type=int, default=None,
                        help="Number of ADMET items per figure (default: auto)")
    parser.add_argument("--merge", action='store_true', help="Generate merged plots by ADMET item (one plot per item across molecules)")
    args = parser.parse_args()

    visualizer = ADMETVisualizer(file_path=args.input, items_per_fig=args.num_items)
    visualizer.parse_data()
    visualizer.plot_all()
    if args.merge:
        visualizer.plot_merged_by_item()
