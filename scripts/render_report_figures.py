#!/usr/bin/env python3
"""Render the aggregate CXRShift figure from the machine-readable summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODEL_ORDER = ("DenseNet121", "ConvNeXt-Tiny", "ViT-B/16")
STRATEGY_ORDER = ("ERM", "ERM-Reg", "JT", "JT-DBS")
COLORS = {"Kermany-FG": "#235b74", "RSNA-1707": "#c76549"}


def load_summary(path: Path) -> dict[str, Any]:
    """Load a summary and reject files without the required result matrices."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not payload.get("groups") or not payload.get("paired_comparisons"):
        raise ValueError("Summary does not contain the required result matrices")
    return payload


def canonical_dataset(value: str) -> str:
    """Normalize the two legacy dataset tokens retained for compatibility."""
    return {"kermany_grouped": "Kermany-FG", "rsna": "RSNA-1707"}.get(
        value, value
    )


def canonical_strategy(row: dict[str, Any]) -> str:
    """Read a strategy from either the canonical or original summary schema."""
    if row.get("candidate_recipe"):
        return str(row["candidate_recipe"])
    return {
        "robust": "ERM-Reg",
        "mixed_simple": "JT",
        "mixed_domain_balanced": "JT-DBS",
    }[row["candidate_family"]]


def add_value_labels(axis: Any, bars: Any) -> None:
    """Place compact percentage labels above bars without changing the scale."""
    for bar in bars:
        value = float(bar.get_height())
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            value + 1.0,
            f"{value:.1f}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color="#29343a",
        )


def render(summary: dict[str, Any], output: Path) -> None:
    """Render baseline source shift and DenseNet strategy comparisons."""
    baseline = {
        (canonical_dataset(row["dataset"]), row["model"]):
        row["ensemble"]["balanced_accuracy"] * 100
        for row in summary["groups"]
    }
    strategies = {
        ("ERM", dataset): baseline[(dataset, "DenseNet121")]
        for dataset in COLORS
    }
    for row in summary["paired_comparisons"]:
        dataset = canonical_dataset(row["dataset"])
        strategies[(canonical_strategy(row), dataset)] = (
            row["candidate_ensemble"]["balanced_accuracy"] * 100
        )

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#aeb7bc",
            "axes.labelcolor": "#29343a",
            "xtick.color": "#48545a",
            "ytick.color": "#48545a",
        }
    )
    figure, axes = plt.subplots(1, 2, figsize=(10.4, 4.25), constrained_layout=True)
    figure.patch.set_facecolor("white")

    width = 0.34
    x_models = np.arange(len(MODEL_ORDER))
    for offset, dataset in ((-width / 2, "Kermany-FG"), (width / 2, "RSNA-1707")):
        bars = axes[0].bar(
            x_models + offset,
            [baseline[(dataset, model)] for model in MODEL_ORDER],
            width,
            label=dataset,
            color=COLORS[dataset],
        )
        add_value_labels(axes[0], bars)
    axes[0].set_title("Backbone comparison", loc="left", weight="bold")
    axes[0].set_ylabel("Balanced accuracy (%)")
    axes[0].set_xticks(x_models, MODEL_ORDER)
    axes[0].set_ylim(50, 103)
    axes[0].grid(axis="y", color="#e5e9eb", linewidth=0.8)
    axes[0].legend(frameon=False, loc="lower left")

    x_strategies = np.arange(len(STRATEGY_ORDER))
    for offset, dataset in ((-width / 2, "Kermany-FG"), (width / 2, "RSNA-1707")):
        bars = axes[1].bar(
            x_strategies + offset,
            [strategies[(strategy, dataset)] for strategy in STRATEGY_ORDER],
            width,
            color=COLORS[dataset],
        )
        add_value_labels(axes[1], bars)
    axes[1].set_title("DenseNet121 training strategies", loc="left", weight="bold")
    axes[1].set_xticks(x_strategies, STRATEGY_ORDER)
    axes[1].set_ylim(50, 103)
    axes[1].grid(axis="y", color="#e5e9eb", linewidth=0.8)

    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("results/CXRShift__main-summary.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("figures/cross_source_summary.png"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = args.summary if args.summary.is_absolute() else ROOT / args.summary
    output = args.output if args.output.is_absolute() else ROOT / args.output
    render(load_summary(summary), output)
    print(f"Wrote {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
