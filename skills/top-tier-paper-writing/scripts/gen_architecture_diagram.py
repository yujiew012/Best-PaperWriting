#!/usr/bin/env python3
"""
Publication-Quality System Architecture Diagram Generator.
Uses pure Matplotlib Patches to generate vector PDF/PNG diagrams.
Enforces Modern Minimal academic aesthetics, numbered steps ①–⑥, and crisp borders.
"""

import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_badge(ax, x, y, num_str, bg_color="#D55E00", text_color="white"):
    """Draws a numbered circle badge ①–⑥ for workflow steps."""
    circle = patches.Circle((x, y), 0.18, facecolor=bg_color, edgecolor="black", linewidth=0.8, zorder=10)
    ax.add_patch(circle)
    ax.text(x, y, num_str, ha="center", va="center", color=text_color, fontsize=8, fontweight="bold", zorder=11)

def draw_block(ax, x, y, w, h, text, subtext="", bg_color="#EBF3FB", border_color="#0072B2"):
    """Draws a rounded modern-minimal academic component box."""
    box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.1",
                                facecolor=bg_color, edgecolor=border_color, linewidth=1.2, zorder=2)
    ax.add_patch(box)
    if subtext:
        ax.text(x + w / 2, y + h * 0.62, text, ha="center", va="center", fontsize=8.5, fontweight="bold", color="#111111", zorder=3)
        ax.text(x + w / 2, y + h * 0.28, subtext, ha="center", va="center", fontsize=7.0, color="#444444", zorder=3)
    else:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.5, fontweight="bold", color="#111111", zorder=3)

def draw_arrow(ax, x1, y1, x2, y2, label=""):
    """Draws a clean directional data flow arrow."""
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->,head_width=0.25,head_length=0.35",
                                color="#222222", lw=1.2), zorder=4)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + 0.15
        ax.text(mx, my, label, ha="center", va="center", fontsize=7.2, color="#333333", zorder=5)

def build_architecture_diagram(output_path="fig_framework.pdf"):
    # Size suitable for double-column or 1.5-column (e.g. 6.8 x 2.6 inches)
    fig, ax = plt.subplots(figsize=(6.8, 2.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")

    # Client-side Container (Dashed grey boundary)
    client_box = patches.FancyBboxPatch((0.2, 0.2), 6.0, 3.6, boxstyle="round,pad=0.1",
                                       facecolor="#FAFAFA", edgecolor="#999999", linestyle="--", linewidth=1.0)
    ax.add_patch(client_box)
    ax.text(0.5, 3.55, "Edge Client Node (k)", fontsize=8.5, fontweight="bold", color="#555555")

    # Server-side Container
    server_box = patches.FancyBboxPatch((6.8, 0.2), 3.0, 3.6, boxstyle="round,pad=0.1",
                                       facecolor="#F5F9F6", edgecolor="#009E73", linestyle="--", linewidth=1.0)
    ax.add_patch(server_box)
    ax.text(7.1, 3.55, "Central Aggregation Server", fontsize=8.5, fontweight="bold", color="#009E73")

    # 1. Input Data
    draw_block(ax, 0.5, 1.4, 1.1, 1.1, "Local Data", "Batch X_k", bg_color="#FFFFFF", border_color="#666666")

    # 2. DDAP Module (Prompt Generation)
    draw_block(ax, 2.2, 2.3, 1.6, 1.1, "DDAP Module", "Dynamic Prompter", bg_color="#E8F4F8", border_color="#0072B2")
    draw_arrow(ax, 1.6, 2.0, 2.2, 2.7, label="")
    draw_badge(ax, 1.9, 2.4, "1")

    # 3. Base Feature Encoder
    draw_block(ax, 2.2, 0.5, 1.6, 1.1, "Base Encoder", "f_k = Enc(X_k)", bg_color="#FFFFFF", border_color="#333333")
    draw_arrow(ax, 1.6, 1.9, 2.2, 1.1, label="")
    draw_badge(ax, 1.9, 1.5, "2")

    # 4. Joint Inference & Classification Head
    draw_block(ax, 4.4, 1.4, 1.5, 1.1, "Classifier Head", "[f_k, p_k] -> Logits", bg_color="#EBF3FB", border_color="#0072B2")
    draw_arrow(ax, 3.8, 2.7, 4.4, 2.1, label="Prompt p_k")
    draw_badge(ax, 4.1, 2.5, "3")
    draw_arrow(ax, 3.8, 1.1, 4.4, 1.8, label="Feature f_k")
    draw_badge(ax, 4.1, 1.4, "4")

    # 5. Inter-round PKM Constraint
    pkm_box = patches.FancyBboxPatch((2.2, 3.5), 1.6, 0.45, boxstyle="round,pad=0.04",
                                    facecolor="#FDEEE6", edgecolor="#D55E00", linewidth=1.0)
    ax.add_patch(pkm_box)
    ax.text(3.0, 3.72, "PKM Regularizer", ha="center", va="center", fontsize=7.2, fontweight="bold", color="#D55E00")
    ax.annotate("", xy=(3.0, 3.4), xytext=(3.0, 3.5),
                arrowprops=dict(arrowstyle="->", color="#D55E00", lw=1.0))
    draw_badge(ax, 3.0, 3.45, "5", bg_color="#D55E00")

    # 6. Aggregation & Model Sync
    draw_block(ax, 7.3, 1.4, 2.0, 1.2, "Model Aggregation", "FedAvg w = sum(w_k)", bg_color="#EAF6EE", border_color="#009E73")
    # Uplink arrow
    draw_arrow(ax, 5.9, 2.2, 7.3, 2.2, label="Local Update w_k")
    draw_badge(ax, 6.6, 2.45, "6")
    # Downlink arrow
    draw_arrow(ax, 7.3, 1.6, 5.9, 1.6, label="Global Model w")

    plt.savefig(output_path, format="pdf", bbox_inches="tight", dpi=300)
    png_path = output_path.replace(".pdf", ".png")
    plt.savefig(png_path, format="png", bbox_inches="tight", dpi=300)
    print(f"Generated architecture PDF: {output_path}")
    print(f"Generated preview PNG: {png_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate publication architecture diagram.")
    parser.add_argument("--out", type=str, default="fig_architecture.pdf", help="Output PDF file path")
    args = parser.parse_args()
    build_architecture_diagram(args.out)
