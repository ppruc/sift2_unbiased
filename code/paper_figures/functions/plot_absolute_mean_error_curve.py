import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import numpy as np
from scipy.interpolate import PchipInterpolator


sys.path.append(os.path.abspath('/Users/user/Downloads/sift2_unbiased/code/paper_figures/functions'))

def mean_upper_triangle(mat):
    """Compute the mean of the upper-triangular (i <= j) entries of a square matrix."""
    mat = np.asarray(mat)
    iu = np.triu_indices_from(mat, k=0)
    vals = mat[iu]
    # Ignore NaNs and infs that may occur in the error matrices
    vals = vals[np.isfinite(vals)]
    return np.nan if vals.size == 0 else vals.mean()


def _upper_triangle_vals(mat):
    """Return finite upper-triangular values (i <= j) as a 1D array."""
    mat = np.asarray(mat)
    iu = np.triu_indices_from(mat, k=0)
    vals = mat[iu]
    return vals[np.isfinite(vals)]


def plot_absolute_mean_error_curve(errors, x_label, y_label, title, ylim=None, legend=True, total_error=False):
    """
    Plot smoothed mean-absolute-error (MAE) curves across regularisation strengths for two bundle categories:
    (1) true bundles, (2) false bundles.

    For each regularisation strength, the function computes the **mean of the upper-triangular entries**
    of the error matrix for each category (i.e., MAE per category) and plots smooth curves obtained using
    PCHIP interpolation in log-space. Optionally, a combined total MAE curve can also be plotted as the sum of the category-wise MAEs.

    Parameters:
        errors: tuple of dicts (errors_true, errors_false)
        x_label: label for the x-axis
        y_label: label for the y-axis
        title: plot title
        ylim: limits for the y-axis
        legend: whether to show legend
        total_error: if True, plot the combined MAE curve in addition to individual categories

    Returns:
        None
    """
    errors_true, errors_false = errors

    strengths = sorted(errors_true.keys())

    # If total_error is requested, compute total MAE as the sum of category-wise MAEs
    total_means = None
    if total_error:
        total_means = []
        for s in strengths:
            m_true = mean_upper_triangle(errors_true[s])
            m_false = mean_upper_triangle(errors_false[s])

            # If both categories are NaN, keep NaN; otherwise sum valid means
            if np.isnan(m_true) and np.isnan(m_false):
                total_means.append(np.nan)
            else:
                total_means.append(np.nansum([m_true, m_false]))

    # Per-category Mean Absolute Error
    true_means = [mean_upper_triangle(errors_true[strength]) for strength in strengths]
    false_means = [mean_upper_triangle(errors_false[strength]) for strength in strengths]

    # Create the figure
    plt.figure(figsize=(8, 6))
    plt.ylabel(y_label, fontsize=12)
    plt.xlabel(x_label, fontsize=12)
    plt.title(title, fontsize=14)
    plt.xscale("log")

    label_true = "True Bundle"
    label_false = "False Bundle"

    def plot_category_spline(xs, ys, color, label, linestyle='-', linewidth=10, alpha=0.7):
        xs = np.asarray(xs, dtype=float)
        ys = np.asarray(ys, dtype=float)

        mask = (xs > 0) & np.isfinite(xs) & np.isfinite(ys)
        xs = xs[mask]
        ys = ys[mask]

        if xs.size < 2:
            if xs.size == 1:
                plt.scatter(xs, ys, color=color, s=30, alpha=alpha, label=label)
            return

        log_xs = np.log10(xs)
        spline = PchipInterpolator(log_xs, ys)
        log_x_line = np.linspace(log_xs.min(), log_xs.max(), 200)
        y_line = spline(log_x_line)
        x_line = 10 ** log_x_line

        plt.plot(x_line, y_line, color=color,
                linestyle=linestyle, linewidth=linewidth, alpha=alpha, label=label)

    plot_category_spline(strengths, true_means,  color='green', label=label_true)
    plot_category_spline(strengths, false_means, color='red',   label=label_false)

    if total_means is not None:
        plot_category_spline(strengths, total_means,
                            color='black', label='Total MAE',
                            linestyle='--', linewidth=12, alpha=0.5)

    plt.yticks(fontsize=20)
    plt.xticks(fontsize=17)

    if legend:
        plt.legend(fontsize=10)
    if ylim is not None:
        plt.ylim(ylim)

    plt.show()
