import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import numpy as np
from scipy.interpolate import PchipInterpolator

sys.path.append(os.path.abspath('/Users/user/Downloads/sift2_unbiased/code/paper_figures/functions'))

from sum_upper_triangle import sum_upper_triangle

def plot_differential_error_curve(errors, x_label, y_label, title, ylim=None,legend=True, total_error=False):
    """
    Plot smoothed error curves across regularisation strengths for three bundle categories:
    (1) true bundles with a simulated effect,
    (2) true bundles without an effect,
    (3) false bundles.

    The function computes, for each regularisation strength, the **sum of the upper-triangular
    entries** of the error matrix for each category (i.e., total error magnitude per category),
    and plots smooth curves obtained using PCHIP interpolation in log-space. Optionally, a
    combined total error curve (sum of all three categories) can also be plotted.

    Parameters
    ----------
    errors : tuple of dict
        Tuple containing three dictionaries:
        (errors_true_effect, errors_true_no_effect, errors_false),
        where each dictionary maps regularisation_strength -> error_matrix.
        Each error_matrix is a 2D array represeting the bundle-wise error values for that category and regularisation strength.
        
    x_label : str
        Label for the x-axis.

    y_label : str
        Label for the y-axis.

    title : str
        Plot title.

    ylim : tuple or None, optional
        y-axis limits. If None, limits are determined automatically.

    legend : bool, optional
        Whether to display a legend.

    total_error : bool, optional
        If True, also plot a combined curve representing the sum of the three
        category-wise error sums for each regularisation strength.

    Returns
    -------
    None
        This function produces a matplotlib plot but does not return data.
    """
    errors_true_effect, errors_true_no_effect, errors_false = errors
    
    # If total_error is requested, prepare additional combined curve but do not exit
    total_sums = None
    if total_error:
        strengths = sorted(errors_true_effect.keys())
        total_sums = [
            sum_upper_triangle(errors_true_effect[s]) +
            sum_upper_triangle(errors_true_no_effect[s]) +
            sum_upper_triangle(errors_false[s])
            for s in strengths
        ]

    # Gather data for overall error curve (using nonzero upper-triangle sums)
    strengths = sorted(errors_true_effect.keys())

    # Create the figure
    plt.figure(figsize=(8, 6))
    plt.ylabel(y_label, fontsize=12)
    plt.xlabel(x_label, fontsize=12)
    plt.title(title, fontsize=14)
    plt.xscale("log")

   
    label_true_effect = "True Bundle with Effect"
    label_true_no_effect = "True Bundle without Effect"
    label_false = "False Bundle"

    # For each category, for each reg_strength, compute the sum of upper-triangle errors
    true_effect_sums = [sum_upper_triangle(errors_true_effect[strength]) for strength in strengths]
    true_no_effect_sums = [sum_upper_triangle(errors_true_no_effect[strength]) for strength in strengths]
    false_sums = [sum_upper_triangle(errors_false[strength]) for strength in strengths]

    # Define a helper to plot a spline given x, y, color, and label
    def plot_category_spline(xs, ys, color, label, linestyle='-', linewidth=10, alpha=0.7):
        xs = np.array(xs)
        ys = np.array(ys)
        log_xs = np.log10(xs)
        spline = PchipInterpolator(log_xs, ys)
        log_x_line = np.linspace(log_xs.min(), log_xs.max(), 200)
        y_line = spline(log_x_line)
        x_line = 10**log_x_line

        plt.plot(x_line, y_line,
                color=color, linestyle=linestyle,
                linewidth=linewidth, alpha=alpha,
                label=label)

    plot_category_spline(strengths, true_effect_sums, color='green', label=label_true_effect)
    plot_category_spline(strengths, true_no_effect_sums, color='orange', label=label_true_no_effect)
    plot_category_spline(strengths, false_sums, color='red', label=label_false)

    if total_sums is not None:
        plot_category_spline(
            strengths, total_sums,
            color='black',
            label='Total Error',
            linestyle='--',
            linewidth=12,
            alpha=0.5
        )

    plt.yticks(fontsize=20)
    plt.xticks(fontsize=17)

    if legend:
          plt.legend(fontsize=10)
    if ylim is not None:
        plt.ylim(ylim)

    plt.show()
