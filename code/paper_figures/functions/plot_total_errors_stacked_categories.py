import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def plot_total_errors_stacked_categories(errors_list, labels=None, method_labels=None, title="Total Error Comparison", custom_colors=None, ylabel="",ylim=None):
    """
    Plot a stacked bar chart comparing total error contributions from different bundle categories,
    with a styled box below each bar showing the total error.

    Parameters:
        errors_list: list of lists of floats
            Each inner list contains error contributions for a method across bundle categories.
        labels: list of str
            The bundle category labels (e.g., ["True (With Effect)", "True (No Effect)", "False Positives"]).
        method_labels: list of str
            Names of the methods corresponding to each error list.
        title: str
            Plot title.
        custom_colors: list of str
            Colors for each bundle category.
    """
    
    # Checks 
    if method_labels is None or len(method_labels) != len(errors_list):
        raise ValueError("method_labels must be a list with the same length as errors_list")
    
    if labels is None:
        raise ValueError("labels must be provided (e.g., bundle categories)")
    
    if custom_colors is not None and len(custom_colors) != len(labels):
        raise ValueError("Length of custom_colors must match the number of bundle categories (labels)")

    # Build DataFrame
    df_data = {method_labels[i]: errors_list[i] for i in range(len(errors_list))}
    df_data["Category"] = labels
    df = pd.DataFrame(df_data)
    df_plot = df.set_index("Category").T

    # Plot
    ax = df_plot.plot(
        kind="bar", stacked=True, figsize=(7, 5),
        color=custom_colors, edgecolor="black"
    )

    # Style
    ax.set_ylabel(ylabel, fontsize=14)
    ax.set_xlabel("", fontsize=14)
    ax.set_title(title, fontsize=16, weight="bold")
    ax.legend(title="Bundle Category", bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.tick_params(axis='x', labelrotation=0, labelsize=12)
    ax.tick_params(axis='y', labelsize=12)

    _, ymax = ax.get_ylim()

    # Annotate total error below each bar
    totals = df_plot.sum(axis=1).values
    for i, total in enumerate(totals):
        txt = r"$\mathbf{Total\ Error}$" + "\n" + f"{total:.0f}"
        ax.text(
            i, total+ymax*0.022,  # position just above the x-axis
            txt,
            ha="center", va="bottom", fontsize=12,
            bbox=dict(boxstyle="round,pad=0.3", facecolor='white',
                      edgecolor='gray', alpha=0.95)
        )

    if ylim is not None:
        plt.ylim(0,ylim)

    plt.tight_layout()
    plt.show()

    return df

