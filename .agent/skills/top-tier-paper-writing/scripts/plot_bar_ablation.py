#!/usr/bin/env python3
"""
Publication-Quality Grouped Bar Chart Plotter for Ablation Studies.
Adheres to IEEE/ACM formatting guidelines with Okabe-Ito colors and error bars.
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt

OKABE_ITO = {
    "blue": "#0072B2",          # Full model
    "orange": "#E69F00",        # Variant 1
    "bluish_green": "#009E73",  # Variant 2
    "vermilion": "#D55E00",     # Baseline / Degraded
    "gray": "#7F7F7F"
}

def plot_ablation(output_path="fig_ablation.pdf"):
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8,
        "legend.fontsize": 7.5,
        "legend.frameon": False,
        "figure.figsize": (3.4, 2.3),
        "figure.autolayout": True,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.grid": True,
        "grid.alpha": 0.2,
        "grid.linestyle": "--"
    })

    datasets = ["CIFAR-10", "Fashion-MNIST", "MNIST"]
    x = np.arange(len(datasets))
    width = 0.22

    # Performance values (Mean & Std)
    full_model = [90.86, 97.41, 98.04]
    full_err = [0.45, 0.22, 0.15]

    wo_memory = [87.52, 95.80, 96.90]
    wo_memory_err = [0.60, 0.35, 0.25]

    wo_prompter = [84.10, 93.15, 94.80]
    wo_prompter_err = [0.75, 0.40, 0.30]

    fig, ax = plt.subplots()

    # Draw grouped bars with error bars
    rects1 = ax.bar(x - width, full_model, width, yerr=full_err, capsize=3,
                    color=OKABE_ITO["blue"], label="Full FedPE", edgecolor="black", linewidth=0.6)
    rects2 = ax.bar(x, wo_memory, width, yerr=wo_memory_err, capsize=3,
                    color=OKABE_ITO["bluish_green"], label="w/o PKM", edgecolor="black", linewidth=0.6)
    rects3 = ax.bar(x + width, wo_prompter, width, yerr=wo_prompter_err, capsize=3,
                    color=OKABE_ITO["orange"], label="w/o DDAP", edgecolor="black", linewidth=0.6)

    ax.set_ylabel("Accuracy (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(datasets)
    ax.set_ylim(75, 102)
    ax.legend(loc="upper left", ncol=3)

    plt.savefig(output_path, format="pdf", bbox_inches="tight", dpi=300)
    png_path = output_path.replace(".pdf", ".png")
    plt.savefig(png_path, format="png", bbox_inches="tight", dpi=300)
    print(f"Generated ablation PDF: {output_path}")
    print(f"Generated preview PNG: {png_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot grouped bar ablation study.")
    parser.add_argument("--out", type=str, default="fig_ablation.pdf", help="Output PDF file path")
    args = parser.parse_args()
    plot_ablation(args.out)
