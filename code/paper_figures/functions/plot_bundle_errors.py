import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter
from scipy.stats import kruskal
import scikit_posthocs as sp

sys.path.append(os.path.abspath('/Users/user/Downloads/sift2_unbiased/code/paper_figures/functions'))

def plot_bundle_errors(
    dfs,
    title_main,
    categories,
    rotate_xticks=None,
    log_y=False,
    min_n=5,
    minimal=False,
    total_errors=None,
    no_stats=False,
):
    """
    Plot boxplots + strip plots for error distributions across multiple connectome matrices.

    Parameters
    ----------
    dfs : list of pd.DataFrame
        Each DataFrame contains a connectome error matrix.
    title_main : str
        Title of the plot.
    categories : list of str
        Labels for each connectome condition.
    rotate_xticks : int or None
        Angle for rotating x-axis labels.
    log_y : bool
        Apply log scale to y-axis if True.
    min_n : int
        Minimum samples required per category for statistical testing.
    minimal : bool
        If True, produce simplified/minimal plot styling.
    total_errors : list[float] or None
        Optional list of total errors to annotate below the x-axis.
    no_stats : bool
        Disable statistical testing when True.

    Returns
    -------
    pd.DataFrame
        Summary statistics (median, Q1, Q3, IQR, n) per category.
    """

    # Combine data
    combined = []
    for df, category in zip(dfs, categories):
        upper_idx = np.triu_indices_from(df, k=0)
        errors = df.values[upper_idx]
        errors = errors[np.isfinite(errors)]
        combined.append(pd.DataFrame({"Error": errors, "Category": category}))

    plot_df = pd.concat(combined, ignore_index=True)

    # Statistical tests
    counts = plot_df.groupby("Category").size()
    run_stats = all(counts.get(cat, 0) >= min_n for cat in categories)
    dunn = None

    if run_stats and not no_stats:
        groups = [plot_df.loc[plot_df.Category == c, "Error"] for c in categories]
        H, p_kw = kruskal(*groups)
        print(f"Kruskal–Wallis H={H:.2f}, p={p_kw:.3g}")

        dunn = sp.posthoc_dunn(
            plot_df, val_col="Error", group_col="Category", p_adjust="holm"
        ).reindex(index=categories, columns=categories)

    elif not no_stats:
        print(f"Skipping stats: need ≥{min_n} per category\n{counts}")

    # Set up plot
    _, ax = plt.subplots(figsize=(9, 5))
    palette = ["red", "orange", "steelblue", "skyblue"]

    sns.boxplot(
        x="Category", y="Error", data=plot_df,
        order=categories, ax=ax, palette=palette, fliersize=0
    )
    sns.stripplot(
        x="Category", y="Error", data=plot_df,
        order=categories, size=5, jitter=0.2, alpha=0.3, color="black", ax=ax
    )

    # Labels and formatting
    ax.set_ylabel(r"bundle-wise error ($\varepsilon_{i,j}^{\mathrm{diff}}$)", fontsize=18)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0f}%"))
    max_err = plot_df.Error.max()

    # Define y-axis limits for later annotations
    if log_y:
        positive_errors = plot_df.Error[plot_df.Error > 0]
        y_min = positive_errors.min()
        y_max = positive_errors.max()
    else:
        y_min = plot_df.Error.min()
        y_max = plot_df.Error.max()

    # Compute stats summary
    stats = (
        plot_df.groupby("Category")["Error"]
        .agg(median="median",
             q1=lambda x: np.percentile(x, 25),
             q3=lambda x: np.percentile(x, 75))
        .assign(iqr=lambda df: df.q3 - df.q1)
        .reindex(categories)
    )

    # Significance bars
    first_y = None
    if run_stats and not no_stats and dunn is not None:

        def stars(p):
            return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""

        pairs = [(i, j) for i in range(len(categories)) for j in range(i + 1, len(categories))]
        bar_height_factor = 1.2 if log_y else 1.05
        level_multipliers = np.logspace(np.log10(1.2), np.log10(1000.0), len(pairs)) if log_y else np.linspace(1.05, 1.35, len(pairs))

        for (i, j), lvl in zip(pairs, level_multipliers):
            pval = dunn.loc[categories[i], categories[j]]
            s = stars(pval)
            if not s:
                continue

            y0 = max_err * lvl
            y1 = y0 * bar_height_factor if log_y else y0 + 0.5 * (y_max - y_min)
            first_y = y0 if first_y is None else min(first_y, y0)

            ax.plot([i, i, j, j], [y0, y1, y1, y0], lw=1.5, c="black")
            y_star = y1 * 2 if log_y else y1 - 0.01 * (y_max - y_min) 
            ax.text((i + j) / 2, y_star, s, ha="center", va="top", fontsize=12)

    # Total error boxes 
    y_box = (
        first_y / 1.25 if first_y is not None
        else y_min + 0.05 * (y_max - y_min)
    )

    if total_errors is not None:
        for i, err in enumerate(total_errors):
            ax.text(
                i, y_box,
                rf"$\mathbf{{Total\ Error}}$" + f"\n{err:.2f}%",
                ha="center", va="bottom", fontsize=12,
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white',
                          edgecolor='gray', alpha=0.7)
            )

    # Ticks, scaling, minimal mode
    if rotate_xticks:
        plt.xticks(rotation=rotate_xticks)
    if log_y:
        ax.set_yscale('log', base=10)

    if minimal:
        ax.set_title('')
        ax.set_xlabel('')
        ax.set_ylabel('')
        for lbl in ax.get_xticklabels():
            lbl.set_fontweight('bold')
    else:
        ax.set_title(title_main, fontsize=16, fontweight="bold")

    # Styling
    ax.yaxis.set_label_position('right')
    ax.yaxis.tick_right()
    ax.tick_params(axis='y', length=0)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.tight_layout()
    plt.show()

    # Return summary statistics
    stats_summary = stats.assign(
        n=plot_df.groupby("Category").size().reindex(categories)
    ).round(2)
    stats_summary.columns = ["Median", "Q1", "Q3", "IQR", "n"]

    return stats_summary