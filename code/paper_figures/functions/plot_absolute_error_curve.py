import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import numpy as np
from scipy.interpolate import PchipInterpolator

sys.path.append(os.path.abspath('/Users/user/Downloads/sift2_unbiased/code/paper_figures/functions'))

from sum_upper_triangle import sum_upper_triangle

def plot_absolute_error_curve(errors, x_label, y_label, title, ylim=None,legend=True, total_error=False):
    """
    Plot error curves for different bundle categories based on the provided errors.
    
    Parameters:
        errors: tuple of dicts (errors_true_effect, errors_true_no_effect, errors_false)
        x_label: label for the x-axis
        y_label: label for the y-axis
        title: plot title
        ylim: limits for the y-axis
        legend: whether to show legend
        total_error: if True, plot the total error curve instead of individual categories

    Returns:
        DataFrame with mean errors for each category at each regularisation strength.
    """
    errors_true, errors_false = errors

    # Gather data for overall error curve 
    strengths = sorted(errors_true.keys())
    
    # If total_error is requested, prepare additional combined curve
    total_sums = None
    if total_error:
        total_sums = [
            sum_upper_triangle(errors_true[s]) +
            sum_upper_triangle(errors_false[s])
            for s in strengths
        ]

    # Create the figure
    plt.figure(figsize=(8, 6))
    plt.ylabel(y_label, fontsize=12)
    plt.xlabel(x_label, fontsize=12)
    plt.title(title, fontsize=14)
    plt.xscale("log")
   
    label_true = "True Bundle"
    label_false = "False Bundle"

    # For each category, for each reg_strength, compute the sum of upper-triangle errors
    true_sums = [sum_upper_triangle(errors_true[strength]) for strength in strengths]
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
        plt.plot(x_line, y_line, color=color, linestyle=linestyle,
                linewidth=linewidth, alpha=alpha, label=label)

    plot_category_spline(strengths, true_sums,  color='green', label=label_true)
    plot_category_spline(strengths, false_sums, color='red',   label=label_false)

    if total_sums is not None:
        plot_category_spline(strengths, total_sums, color='black', label='Total Error',
                            linestyle='--', linewidth=12, alpha=0.5)

    plt.yticks(fontsize=20)
    plt.xticks(fontsize=17)

    if legend:
          plt.legend(fontsize=10)
    if ylim is not None:
        plt.ylim(ylim)

    plt.show()
