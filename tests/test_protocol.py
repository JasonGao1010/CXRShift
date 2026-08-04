from pathlib import Path
from types import SimpleNamespace

import yaml

from scripts.train import training_identity
from xray_pneumonia.protocol import (
    Identity,
    artifact_name,
    legacy_family,
    load_protocol,
)

ROOT = Path(__file__).resolve().parents[1]


def test_final_protocol_has_stable_unversioned_names():
    protocol = load_protocol()
    assert protocol["protocol_id"] == "CXRShift"
    assert set(protocol["recipes"]) == {"ERM", "ERM-Reg", "JT", "JT-DBS"}
    assert set(protocol["datasets"]) == {"Kermany-FG", "RSNA-1707"}


def test_run_and_artifact_names_are_complete_and_unambiguous():
    identity = Identity("DenseNet121", "JT-DBS", 42)
    assert identity.run_id == "CXRShift__DenseNet121__JT-DBS__s42"
    assert artifact_name(identity, "RSNA-1707", "test", "predictions", "csv") == (
        "CXRShift__DenseNet121__JT-DBS__s42__RSNA-1707__test__predictions.csv"
    )


def test_legacy_result_families_remain_readable():
    assert legacy_family("ERM") == "strict"
    assert legacy_family("ERM-Reg") == "robust"
    assert legacy_family("JT") == "mixed_simple"
    assert legacy_family("JT-DBS") == "mixed_domain_balanced"


def test_joint_training_configs_and_persisted_identity_are_explicit():
    expectations = {
        "configs/DenseNet121__JT.yaml": ("JT", []),
        "configs/DenseNet121__JT-DBS.yaml": ("JT-DBS", ["kermany", "rsna"]),
    }
    for path, (recipe, prefixes) in expectations.items():
        config = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
        protocol = config["protocol"]
        assert protocol == {
            "id": "CXRShift",
            "model": "DenseNet121",
            "recipe": recipe,
            "training_dataset": "Kermany-FG+RSNA-1707",
        }
        assert config["training"].get("domain_balanced_prefixes", []) == prefixes
        settings = SimpleNamespace(
            protocol_id=protocol["id"],
            model_id=protocol["model"],
            recipe_id=protocol["recipe"],
            training_dataset_id=protocol["training_dataset"],
        )
        assert training_identity(settings) == protocol
