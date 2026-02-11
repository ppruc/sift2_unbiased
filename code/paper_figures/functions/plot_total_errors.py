import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter, MaxNLocator

def plot_total_errors(
    error_list,
    plot_title="",
    rotate_xticks=None,
    minimal=False,
    order=None,
    palette=None,
):
    """
    Draws a bar chart of total errors per pipeline, with consistent color mapping.
    Uses explicit palette assignment instead of hue merging.
    """
    labels, values = zip(*error_list)
    labels = list(labels)
    values = list(values)

    # use custom or global palette
    if palette is None:
        palette = sns.color_palette()

    # ensure order consistency if provided
    if order is not None:
        label_to_val = dict(zip(labels, values))
        labels = [lbl for lbl in order if lbl in label_to_val]
        values = [label_to_val[lbl] for lbl in labels]

    _, ax = plt.subplots(figsize=(7, 5))

    # manually assign colors by label index
    bar_colors = [palette[i % len(palette)] for i in range(len(labels))]

    bars = sns.barplot(
        x=labels,
        y=values,
        palette=bar_colors,
        edgecolor='black',
        ax=ax
    )

    # annotate bars
    for bar, val in zip(bars.patches, values):
        x = bar.get_x() + bar.get_width() / 2
        y = bar.get_height() - 15000
        ax.annotate(
            f"{val:.0f}",
            xy=(x, y),
            xytext=(0, 8),
            textcoords='offset points',
            ha='center',
            va='bottom',
            fontsize=12,
            fontweight='bold',
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor='white',
                alpha=0.6,
                edgecolor='gray'
            )
        )

    # y-axis formatting
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0f}"))
    ax.yaxis.set_major_locator(MaxNLocator(nbins='auto'))

    if not minimal:
        ax.set_title(plot_title, fontsize=16, fontweight='bold')
        ax.set_ylabel(plot_title, fontsize=18)
    else:
        ax.set_title('')
        ax.xaxis.label.set_visible(False)
        ax.yaxis.label.set_visible(False)

    # rotate xticks if requested
    if rotate_xticks is not None:
        plt.setp(ax.get_xticklabels(), rotation=rotate_xticks, ha='right')

    ax.yaxis.set_label_position('right')
    ax.yaxis.tick_right()
    ax.tick_params(axis='y', which='both', length=0)
    plt.xticks(fontsize=14, fontweight='bold')
    plt.yticks(fontsize=14)

    plt.tight_layout()
    plt.show()