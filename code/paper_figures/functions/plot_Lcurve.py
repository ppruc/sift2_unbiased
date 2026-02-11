import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from scipy.interpolate import PchipInterpolator

def plot_Lcurve(dfs, x_col, y_col, strength_col, labels=None, x_label="", y_label="", title="",  annot=False, save_png=None, to_draw=None, ylim=None, xlim=None, annot_curve_idx=0,no_yticks=False):
    """
    Plots multiple L-curves to inspect regularisation behaviour and fits a polynomial to each.

    Parameters:
        dfs : list of pandas.DataFrame or pandas.DataFrame
            DataFrames containing x, y, and strength columns.
        x_col : str
            Name of the column for x values.
        y_col : str
            Name of the column for y values.
        strength_col : str
            Name of the column for regularisation strengths.
        labels : list of str, optional
            Labels for each L-curve.
        x_label : str
            Label for the x-axis.
        y_label : str
            Label for the y-axis.
        title : str
            Plot title.
        annot : bool
            Annotate points with strength values.
        save_png : str, optional
            Directory to save the plot as a PNG file.
        fit_degree : int
            Degree of polynomial to fit.
        label_min_sep_px : int
            Minimum pixel distance between annotation anchors; use when overlapping labels.
        annot_mode : {"dedupe", "all"}
            If "dedupe" (default), only one label is drawn within 'label_min_sep_px' pixels.
        to_draw : tuple(list_of_labels_to_draw, label_to_bold), optional
            Labels to annotate manually; highlight label_to_bold in bold.
        ylim : tuple, optional
            Y-axis limits.
        xlim : tuple, optional
            X-axis limits.
        annot_curve_idx : int
            Index of the curve for which annotations should be drawn (default=0 = first curve).

    Returns:
        None
    """
    if isinstance(dfs, pd.DataFrame):
        dfs = [dfs]
    if labels is None:
        labels = [f"L-curve {i+1}" for i in range(len(dfs))]

    plt.figure(figsize=(6, 6))
    pending_annots = []  # [(x, y, text)] collected across selected series

    for i, (df, label) in enumerate(zip(dfs, labels)):
        x = df[x_col].values
        y = df[y_col].values
        strengths = df.index if strength_col is None else df[strength_col].values
        scatter = plt.scatter(x, y, marker="o", label=label)
        color = scatter.get_facecolor()[0]

        # Shape-preserving PCHIP fit in log–log space
        try:
            x_vals = np.asarray(x, dtype=float)
            y_vals = np.asarray(y, dtype=float)
            mask = (x_vals > 0) & (y_vals > 0) & np.isfinite(x_vals) & np.isfinite(y_vals)
            x_vals = x_vals[mask]
            y_vals = y_vals[mask]

            if x_vals.size >= 2:
                order = np.argsort(x_vals)
                x_sorted = x_vals[order]
                y_sorted = y_vals[order]

                _, unique_indices = np.unique(x_sorted, return_index=True)
                x_sorted = x_sorted[unique_indices]
                y_sorted = y_sorted[unique_indices]

                X = np.log10(x_sorted)
                Y = np.log10(y_sorted)

                x_fit = np.geomspace(x_sorted.min(), x_sorted.max(), 200)
                f = PchipInterpolator(X, Y)
                Y_fit = f(np.log10(x_fit))
                y_fit = 10 ** Y_fit
                plt.plot(x_fit, y_fit, color=color, linestyle="--")
            else:
                print(f"Not enough valid points to fit curve for {label}")
        except Exception as e:
            print(f"Could not fit PCHIP curve for {label}: {e}")

        # Only collect annotations for the specified curve index
        if annot and i == annot_curve_idx:
            for idx, strength in enumerate(strengths):
                pending_annots.append((x[idx], y[idx], f"{strength:.1e}"))

    plt.xlabel(x_label, fontsize=18)
    plt.ylabel(y_label, fontsize=18)
    plt.title(title, fontsize=18)
    plt.legend(fontsize=14)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.tight_layout()
    plt.xscale("log")
    plt.yscale("log")

    if no_yticks:
        ax = plt.gca()
        ax.set_yticklabels([])  # Keeps tick marks but removes labels

    # Draw annotations
    if annot and pending_annots:
        ax = plt.gca()

        if isinstance(to_draw, tuple) and len(to_draw) == 2:
            allowed_labels_raw, bold_label_raw = to_draw
            # Convert to consistent string format
            allowed_labels = {f"{float(lbl):.1e}" for lbl in allowed_labels_raw}
            bold_label = f"{float(bold_label_raw):.1e}"
            to_draw_filtered = [pt for pt in pending_annots if pt[2] in allowed_labels]
        else:
            to_draw_filtered = pending_annots  # default: all
            bold_label = None

        for (x0, y0, text) in to_draw_filtered:
            is_bold = (bold_label is not None) and (text == bold_label)
            ax.annotate(
                text,
                xy=(x0, y0),
                xytext=(3, 3),
                textcoords='offset points',
                fontsize=14 if not is_bold else 16,
                fontweight='bold' if is_bold else 'normal',
                clip_on=True,
            )

    if xlim is not None:
        plt.xlim(xlim)
    if ylim is not None:
        plt.ylim(ylim)

    if save_png is not None:
        os.makedirs(save_png, exist_ok=True)
        plt.savefig(os.path.join(save_png, "l_curve.png"), dpi=200, bbox_inches="tight")

    plt.show()