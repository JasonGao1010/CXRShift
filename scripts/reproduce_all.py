#!/usr/bin/env python3
"""Run the frozen CXRShift data-to-results reproduction workflow."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from xray_pneumonia.protocol import Identity, artifact_name  # noqa: E402

MODEL_CONFIGS = {
    "DenseNet121": "configs/DenseNet121__ERM.yaml",
    "ConvNeXt-Tiny": "configs/ConvNeXt-Tiny__ERM.yaml",
    "ViT-B/16": "configs/ViT-B16__ERM.yaml",
}
RECIPE_CONFIGS = {
    "ERM": "configs/DenseNet121__ERM.yaml",
    "ERM-Reg": "configs/DenseNet121__ERM-Reg.yaml",
    "JT": "configs/DenseNet121__JT.yaml",
    "JT-DBS": "configs/DenseNet121__JT-DBS.yaml",
}
SEEDS = (42, 43, 44)
RECIPES = ("ERM", "ERM-Reg", "JT", "JT-DBS")


def command(*parts: object) -> list[str]:
    """Build a command with the interpreter used for this process."""
    return [sys.executable, *map(str, parts)]


def run(cmd: list[str], *, dry_run: bool) -> None:
    """Print every command and execute it unless this is a protocol preview."""
    print("+", " ".join(cmd), flush=True)
    if not dry_run:
        subprocess.run(cmd, cwd=ROOT, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=["data", "experiments", "analyze", "verify", "all"],
        default="all",
    )
    parser.add_argument("--kermany-raw", type=Path, default=Path("data/raw/chest_xray"))
    parser.add_argument(
        "--rsna-raw", type=Path, default=Path("data/raw/rsna_pneumonia")
    )
    parser.add_argument("--work-dir", type=Path, default=Path("rebuild"))
    parser.add_argument("--device", default="auto")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow data-stage replacement inside --work-dir only.",
    )
    return parser.parse_args()


def data_stage(args: argparse.Namespace) -> None:
    """Reconstruct both frozen datasets from independently downloaded inputs."""
    work = args.work_dir
    force = ["--force"] if args.force else []
    run(
        command(
            "scripts/prepare_kermany_grouped.py",
            "--source-root",
            args.kermany_raw,
            "--output-root",
            work / "data/kermany_grouped_seed42",
            "--from-manifest",
            "--manifest",
            "data/splits/kermany_grouped_seed42.csv",
            "--summary",
            work / "audit/kermany_grouped_summary.json",
            *force,
        ),
        dry_run=args.dry_run,
    )
    run(
        command(
            "scripts/prepare_rsna_binary.py",
            "--raw-root",
            args.rsna_raw,
            "--images-dir",
            args.rsna_raw / "stage_2_train_images",
            "--member-manifest",
            "data/splits/rsna_available_1707_manifest.csv",
            "--output-root",
            work / "data/rsna_binary",
            "--splits-output",
            work / "audit/rsna_splits.json",
            "--summary-output",
            work / "audit/rsna_dataset_summary.json",
            "--figure-output",
            work / "figures/rsna_class_distribution.png",
            *force,
        ),
        dry_run=args.dry_run,
    )
    run(
        command(
            "scripts/prepare_mixed_binary.py",
            "--source-a",
            work / "data/kermany_grouped_seed42",
            "--source-b",
            work / "data/rsna_binary",
            "--prefix-a",
            "kermany",
            "--prefix-b",
            "rsna",
            "--output-root",
            work / "data/kermany_rsna_mixed",
            "--summary-output",
            work / "audit/mixed_dataset_summary.json",
            *force,
        ),
        dry_run=args.dry_run,
    )


def train(args: argparse.Namespace, recipe: str, model: str, seed: int) -> Path:
    """Train one canonical model/strategy/seed identity."""
    work = args.work_dir
    identity = Identity(model, recipe, seed)
    config = RECIPE_CONFIGS[recipe] if model == "DenseNet121" else MODEL_CONFIGS[model]
    data_root = work / (
        "data/kermany_rsna_mixed"
        if recipe.startswith("JT")
        else "data/kermany_grouped_seed42"
    )
    summary = work / f"results/{identity.run_id}__training.json"
    run(
        command(
            "scripts/train.py",
            "--config",
            config,
            "--data-root",
            data_root,
            "--results-dir",
            work / "results",
            "--checkpoints-dir",
            work / "checkpoints",
            "--seed",
            seed,
            "--device",
            args.device,
            "--json-output",
            summary,
        ),
        dry_run=args.dry_run,
    )
    return summary


def evaluate(
    args: argparse.Namespace,
    recipe: str,
    model: str,
    seed: int,
    summary: Path,
    dataset: str,
    split: str,
) -> None:
    """Evaluate one trained identity and retain per-image probabilities."""
    work = args.work_dir
    identity = Identity(model, recipe, seed)
    dataset_id = "Kermany-FG" if dataset == "kermany" else "RSNA-1707"
    root = work / (
        "data/kermany_grouped_seed42" if dataset == "kermany" else "data/rsna_binary"
    )
    run(
        command(
            "scripts/evaluate.py",
            "--training-summary",
            summary,
            "--data-root",
            root,
            "--split",
            split,
            "--device",
            args.device,
            "--json-output",
            work
            / "results"
            / artifact_name(identity, dataset_id, split, "evaluation", "json"),
            "--predictions-output",
            work
            / "results"
            / artifact_name(identity, dataset_id, split, "predictions", "csv"),
            "--no-update-latest",
        ),
        dry_run=args.dry_run,
    )


def experiment_stage(args: argparse.Namespace) -> None:
    for model in MODEL_CONFIGS:
        for seed in SEEDS:
            summary = train(args, "ERM", model, seed)
            evaluate(args, "ERM", model, seed, summary, "kermany", "test")
            evaluate(args, "ERM", model, seed, summary, "rsna", "test")
    for recipe in RECIPES[1:]:
        for seed in SEEDS:
            summary = train(args, recipe, "DenseNet121", seed)
            evaluate(args, recipe, "DenseNet121", seed, summary, "kermany", "test")
            evaluate(args, recipe, "DenseNet121", seed, summary, "rsna", "test")


def analyze_stage(args: argparse.Namespace) -> None:
    work = args.work_dir
    run(
        command(
            "scripts/audit_integrity.py",
            "--dataset",
            work / "data/kermany_grouped_seed42",
            "--dataset",
            work / "data/rsna_binary",
            "--results-dir",
            work / "results",
            "--output",
            work / "audit/integrity.json",
        ),
        dry_run=args.dry_run,
    )
    run(
        command(
            "scripts/summarize_results.py",
            "--results-dir",
            work / "results",
            "--output-json",
            work / "results/CXRShift__main-summary.json",
            "--output-csv",
            work / "results/CXRShift__main-summary.csv",
            "--require-complete",
        ),
        dry_run=args.dry_run,
    )
    run(
        command(
            "scripts/analyze_domain_shift.py",
            "--kermany",
            work / "data/kermany_grouped_seed42",
            "--rsna",
            work / "data/rsna_binary",
            "--output",
            work / "results/CXRShift__source-analysis.json",
        ),
        dry_run=args.dry_run,
    )


def verify_stage(args: argparse.Namespace) -> None:
    run(
        command("scripts/verify_reproduction.py", "--work-dir", args.work_dir),
        dry_run=args.dry_run,
    )


def main() -> int:
    args = parse_args()
    if not args.work_dir.is_absolute():
        args.work_dir = ROOT / args.work_dir
    run(command("scripts/check_protocol.py"), dry_run=args.dry_run)
    for name, fn in (
        ("data", data_stage),
        ("experiments", experiment_stage),
        ("analyze", analyze_stage),
        ("verify", verify_stage),
    ):
        if args.stage in {name, "all"}:
            fn(args)
    if not args.dry_run:
        receipt = args.work_dir / "reproduction_receipt.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(
            json.dumps(
                {
                    "status": "complete"
                    if args.stage in {"all", "verify"}
                    else "stage_complete",
                    "stage": args.stage,
                    "environment": {
                        "python": sys.version,
                        "platform": platform.platform(),
                        "executable": sys.executable,
                    },
                },
                indent=2,
            )
            + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
