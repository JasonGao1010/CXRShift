import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/splits/rsna_available_1707_manifest.csv"
SUMMARY = ROOT / "data/splits/rsna_available_1707_manifest_summary.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def membership_sha256(patient_ids: list[str]) -> str:
    payload = "\n".join(sorted(patient_ids)) + "\n"
    return hashlib.sha256(payload.encode()).hexdigest()


def test_rsna_source_record_boundaries_match_the_manifest():
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    traced = [row["patientId"] for row in rows if row["source_report"] != "unknown"]
    untraced = [row["patientId"] for row in rows if row["source_report"] == "unknown"]

    assert sha256(MANIFEST) == summary["manifest"]["sha256"]
    assert len(rows) == summary["member_count"] == 1707
    assert len(traced) == summary["source_record_coverage"]["retained_report_members"]
    assert len(untraced) == summary["source_record_coverage"]["untraced_members"] == 134
    assert membership_sha256([row["patientId"] for row in rows]) == summary[
        "membership_identity"
    ]["all_1707_sha256"]
    assert membership_sha256(traced) == summary["membership_identity"][
        "report_traced_1573_sha256"
    ]
    assert membership_sha256(untraced) == summary["membership_identity"][
        "untraced_134_sha256"
    ]
