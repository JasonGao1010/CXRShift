from pathlib import Path

from scripts.analyze_domain_shift import select_label_matched
from scripts.summarize_results import (
    filename_group_from_path,
    paired_bootstrap_ci,
)


def test_kermany_group_key_matches_conservative_split_unit():
    bacteria = filename_group_from_path(
        "test/PNEUMONIA/person12_bacteria_1.jpeg", "kermany_grouped"
    )
    virus = filename_group_from_path(
        "test/PNEUMONIA/person12_virus_1.jpeg", "kermany_grouped"
    )
    assert bacteria == virus
    assert bacteria.endswith("person12")


def test_paired_bootstrap_reports_candidate_minus_baseline():
    y = [0, 0, 1, 1]
    baseline = [0.4, 0.6, 0.4, 0.6]
    candidate = [0.1, 0.2, 0.8, 0.9]
    groups = ["n1", "n2", "p1", "p2"]

    interval = paired_bootstrap_ci(
        y, baseline, candidate, groups, iterations=200, seed=7
    )

    assert interval["accuracy"][0] >= 0.0
    assert interval["brier_score"][1] < 0.0


def test_label_matching_equalizes_each_label_stratum():
    rows = []
    counts = {
        ("kermany", "NORMAL"): 2,
        ("rsna", "NORMAL"): 4,
        ("kermany", "PNEUMONIA"): 5,
        ("rsna", "PNEUMONIA"): 3,
    }
    for (source, label), count in counts.items():
        for index in range(count):
            rows.append(
                {
                    "path": Path(f"/{source}/{label}/{index}.png"),
                    "source": source,
                    "label": label,
                    "group": f"{source}:{label}:{index}",
                }
            )

    matched = select_label_matched(rows)

    for label, expected in (("NORMAL", 2), ("PNEUMONIA", 3)):
        assert sum(
            row["source"] == "kermany" and row["label"] == label
            for row in matched
        ) == expected
        assert sum(
            row["source"] == "rsna" and row["label"] == label for row in matched
        ) == expected
