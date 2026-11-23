#!/usr/bin/env python3
"""
Publication-Quality Academic Curve Plotter (Multi-Seed Shaded Area).
Adheres to IEEE/ACM Conference & Transactions specifications.
Enforces Okabe-Ito colorblind-safe palette, serif typography, and vector PDF output.
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt

# Okabe-Ito Colorblind-Safe Palette
OKABE_ITO = {
    "blue": "#0072B2",          # Primary method
    "orange": "#E69F00",        # Baseline 1
    "bluish_green": "#009E73",  # Baseline 2 / Variant
    "vermilion": "#D55E00",     # Adverse / Attack / Degraded
    "reddish_purple": "#CC79A7",# Baseline 3
    "sky_blue": "#56B4E9",      # Light support
    "yellow": "#F0E442",
    "black": "#000000"
}

def set_academic_style(single_col=True):
    """Sets global matplotlib rcParams for IEEE/ACM publication standards."""
    # IEEE single column width: 3.3-3.5 in, double column width: 6.8-7.0 in
    width = 3.4 if single_col else 6.9
    height = 2.4 if single_col else 3.2
    
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "Computer Modern Roman"],
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 7.5,
        "legend.frameon": False,
        "mathtext.fontset": "stix",
        "figure.figsize": (width, height),
        "figure.autolayout": True,
        "lines.linewidth": 1.5,
        "lines.markersize": 4,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "--"
    })

def generate_synthetic_data():
    """Generates synthetic benchmark convergence curves with multiple seeds."""
    rounds = np.arange(1, 101)
    
    # Method: Fast convergence, high stability (Our method)
    our_mean = 90 - 45 * np.exp(-rounds / 15)
    our_std = 1.2 * np.exp(-rounds / 40) + 0.3
    
    # Baseline 1: Moderate convergence, fluctuations
    b1_mean = 85 - 45 * np.exp(-rounds / 25) + 1.5 * np.sin(rounds / 5) * np.exp(-rounds / 50)
    b1_std = 2.5 * np.exp(-rounds / 60) + 0.8
    
    # Baseline 2: Catastrophic forgetting / oscillations under dynamic drift
    drift = np.where(rounds > 50, 6.0 * np.sin((rounds - 50) / 4), 0.0)
    b2_mean = 82 - 45 * np.exp(-rounds / 20) - drift
    b2_std = 3.5 * np.ones_like(rounds)
    
    return rounds, (our_mean, our_std), (b1_mean, b1_std), (b2_mean, b2_std)

def plot_curves(output_path="fig_convergence.pdf"):
    set_academic_style(single_col=True)
    rounds, (our_m, our_s), (b1_m, b1_s), (b2_m, b2_s) = generate_synthetic_data()
    
    fig, ax = plt.subplots()
    
    # 1. Plot Our Method (Blue, solid line, circular marker)
    ax.plot(rounds, our_m, color=OKABE_ITO["blue"], linestyle="-", marker="o", 
            markevery=10, label="FedPE (Ours)")
    ax.fill_between(rounds, our_m - our_s, our_m + our_s, color=OKABE_ITO["blue"], alpha=0.18)
    
    # 2. Plot Baseline 1 (Orange, dashed line, square marker)
    ax.plot(rounds, b1_m, color=OKABE_ITO["orange"], linestyle="--", marker="s", 
            markevery=10, label="pFedPG")
    ax.fill_between(rounds, b1_m - b1_s, b1_m + b1_s, color=OKABE_ITO["orange"], alpha=0.15)
    
    # 3. Plot Baseline 2 (Vermilion, dash-dot line, diamond marker)
    ax.plot(rounds, b2_m, color=OKABE_ITO["vermilion"], linestyle="-.", marker="d", 
            markevery=10, label="FedAvg")
    ax.fill_between(rounds, b2_m - b2_s, b2_m + b2_s, color=OKABE_ITO["vermilion"], alpha=0.15)
    
    # Formatting
    ax.set_xlabel("Communication Rounds")
    ax.set_ylabel("Test Accuracy (%)")
    ax.set_xlim(0, 100)
    ax.set_ylim(40, 95)
    ax.legend(loc="lower right")
    
    # Save vector PDF & preview PNG
    plt.savefig(output_path, format="pdf", bbox_inches="tight", dpi=300)
    png_path = output_path.replace(".pdf", ".png")
    plt.savefig(png_path, format="png", bbox_inches="tight", dpi=300)
    print(f"Generated publication vector PDF: {output_path}")
    print(f"Generated preview PNG: {png_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot publication-quality convergence curves.")
    parser.add_argument("--out", type=str, default="fig_convergence.pdf", help="Output PDF file path")
    args = parser.parse_args()
    plot_curves(args.out)
