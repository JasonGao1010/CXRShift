# Reproducing CXRShift

This document separates two reproducibility targets:

1. **Numerical audit** — recompute the reported tables and intervals from the
   committed per-image predictions. No medical images or GPU are required.
2. **Full rebuild** — reconstruct both datasets from provider downloads, train
   all 18 model instances, and compare the rebuilt metrics with the committed
   evidence. This workflow is implemented but has not been independently run
   end to end for this release.

## Environment

The reference environment uses Python 3.13. Exact package versions are pinned in
`requirements.txt`. A CUDA-capable GPU is strongly recommended for the full
training matrix; the numerical audit runs on CPU.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
```

## Data layout

Download the Kermany chest X-ray package from Mendeley Data and place its
distributed directories under:

```text
data/raw/chest_xray/
  train/{NORMAL,PNEUMONIA}/
  val/{NORMAL,PNEUMONIA}/
  test/{NORMAL,PNEUMONIA}/
```

Download the official RSNA Pneumonia Detection Challenge training archive and
arrange it as:

```text
data/raw/rsna_pneumonia/
  stage_2_train_images/*.dcm
  stage_2_train_labels.csv
  stage_2_detailed_class_info.csv
```

The preparation stage reconstructs the memberships in `data/splits/`. It fails
on missing members, label mismatches, split conflicts, or file-hash mismatches.
The RSNA manifest records hashes for all 1,707 DICOM files, but the official
archive reconstruction described here has not yet been executed as a clean
release verification. Historical acquisition records and their limits are
documented in [`data/README.md`](data/README.md).

## Numerical audit

Recompute the six architecture groups and six paired strategy comparisons:

```bash
python scripts/summarize_results.py \
  --results-dir results \
  --output-json rebuild/CXRShift__main-summary.json \
  --output-csv rebuild/CXRShift__main-summary.csv \
  --require-complete
```

The committed test suite checks the headline values, prediction coverage,
grouping semantics, source-record boundaries, and protocol identities:

```bash
python -m pytest -q
python scripts/check_protocol.py
```

## Full rebuild (implemented, not release-verified)

Inspect the complete command sequence without executing it:

```bash
python scripts/reproduce_all.py --dry-run --stage all
```

Run every stage:

```bash
python scripts/reproduce_all.py --stage all --device cuda
```

New data, checkpoints, predictions, and reports are written under `rebuild/`;
the committed evidence in `results/` is never overwritten. Individual stages
can also be run in order:

```bash
python scripts/reproduce_all.py --stage data
python scripts/reproduce_all.py --stage experiments --device cuda
python scripts/reproduce_all.py --stage analyze
python scripts/reproduce_all.py --stage verify
```

## Experiment matrix

| Strategy | Backbone(s) | Seeds | Training sources |
|---|---|---|---|
| ERM | DenseNet121, ConvNeXt-Tiny, ViT-B/16 | 42, 43, 44 | Kermany-FG |
| ERM-Reg | DenseNet121 | 42, 43, 44 | Kermany-FG |
| JT | DenseNet121 | 42, 43, 44 | Kermany-FG + RSNA-1707 train/validation |
| JT-DBS | DenseNet121 | 42, 43, 44 | Same as JT, with source-balanced sampling |

Each trained model is evaluated on the Kermany-FG and RSNA-1707 test
partitions. The analysis averages the three predicted probabilities per image,
then computes metrics once on the ensemble.

## Verification criteria

`scripts/verify_reproduction.py` checks:

- 5,856 Kermany images and 1,707 frozen RSNA members pass the data-identity
  checks;
- all six architecture groups and six paired strategy comparisons are present;
- sample counts and bootstrap-group counts match the reference evidence;
- balanced accuracy, sensitivity, specificity, AUROC, and AUPRC remain within
  the predeclared 5% relative tolerance across software and hardware stacks.

The verifier writes `rebuild/reproduction_verification.json` with status
`VERIFIED` only when every criterion is satisfied. This status would establish
agreement of a newly executed rebuild within the declared tolerance; no such
release verification file is committed. Retraining may vary across software
and hardware stacks, while recomputing statistics from the committed
predictions is deterministic.
