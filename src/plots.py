import matplotlib.pyplot as plt

from src.evaluation import OUTCOMES, calibration_table

ACCENT = "#2a78d6"
MUTED = "#8a8985"
TEXT = "#52514e"
OUTCOME_NAMES = {"H": "Home win", "D": "Draw", "A": "Away win"}


def plot_calibration(probs, results, title, n_bins=10, min_matches=20):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    for ax, outcome in zip(axes, OUTCOMES):
        table = calibration_table(probs, results, outcome, n_bins)
        table = table[table["n_matches"] >= min_matches]
        ax.plot([0, 1], [0, 1], color=MUTED, linewidth=1, linestyle="--", label="Perfect calibration")
        ax.plot(table["predicted"], table["observed"], color=ACCENT, linewidth=2,
                marker="o", markersize=6, label="Model")
        ax.set_title(OUTCOME_NAMES[outcome], color=TEXT)
        ax.set_xlabel("Predicted probability", color=TEXT)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.grid(color="#e6e5e1", linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ["top", "right"]:
            ax.spines[side].set_visible(False)
        ax.tick_params(colors=TEXT)
    axes[0].set_ylabel("Observed frequency", color=TEXT)
    axes[0].legend(frameon=False, loc="upper left")
    fig.suptitle(title, color="#0b0b0b")
    fig.tight_layout()
    return fig