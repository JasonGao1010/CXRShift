import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "results/CXRShift__main-summary.json"


def load_summary() -> dict:
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


def test_readme_headline_table_matches_machine_readable_summary():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    summary = load_summary()

    groups = {(row["dataset"], row["model"]): row for row in summary["groups"]}
    for dataset, model in (
        ("Kermany-FG", "DenseNet121"),
        ("Kermany-FG", "ConvNeXt-Tiny"),
        ("Kermany-FG", "ViT-B/16"),
        ("RSNA-1707", "DenseNet121"),
        ("RSNA-1707", "ConvNeXt-Tiny"),
        ("RSNA-1707", "ViT-B/16"),
    ):
        value = groups[(dataset, model)]["ensemble"]["balanced_accuracy"] * 100
        assert f"{value:.2f}%" in readme


def test_release_contains_exactly_the_complete_prediction_matrix():
    prediction_files = sorted((ROOT / "results").glob("*__predictions.csv"))
    assert len(prediction_files) == 36

    summary = load_summary()
    referenced = set()
    for group in summary["groups"]:
        referenced.update(group["prediction_files"])
    for comparison in summary["paired_comparisons"]:
        referenced.update(comparison["candidate_prediction_files"])

    expected = {path.relative_to(ROOT).as_posix() for path in prediction_files}
    assert referenced == expected


def test_prediction_paths_are_relative_and_records_are_aligned():
    for path in sorted((ROOT / "results").glob("*__predictions.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert rows
        assert len({row["path"] for row in rows}) == len(rows)
        assert all(not Path(row["path"]).is_absolute() for row in rows)


def test_public_tree_contains_no_dataset_derived_medical_images():
    images = {
        path.relative_to(ROOT).as_posix()
        for suffix in ("*.png", "*.jpg", "*.jpeg", "*.dcm")
        for path in ROOT.rglob(suffix)
        if ".git" not in path.parts and "rebuild" not in path.parts
    }
    assert images == {"figures/cross_source_summary.png"}


def test_public_narrative_preserves_the_key_scope_conditions():
    text = " ".join(
        "\n".join(
            [
                (ROOT / "README.md").read_text(encoding="utf-8"),
                (ROOT / "data/README.md").read_text(encoding="utf-8"),
            ]
        )
        .lower()
        .split()
    )
    for statement in (
        "not a verified patient identifier",
        "prevalence-representative clinical cohort",
        "not zero-shot generalization",
        "not intended for clinical decision-making",
    ):
        assert statement in text
