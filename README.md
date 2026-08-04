# CXRShift

[![CI](https://github.com/JasonGao1010/CXRShift/actions/workflows/ci.yml/badge.svg)](https://github.com/JasonGao1010/CXRShift/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/JasonGao1010/CXRShift)](https://github.com/JasonGao1010/CXRShift/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-2f6f62.svg)](LICENSE)

**An auditable study of cross-source robustness in chest X-ray
classification.** Across three ImageNet-pretrained backbones and three random
seeds, balanced accuracy decreases from **97.27–98.17%** on Kermany-FG to
**65.91–66.95%** on RSNA-1707. The consistency of this drop across architectures
shows that changing the backbone alone does not resolve the source shift.

![Cross-source balanced accuracy and training-strategy effects](figures/cross_source_summary.png)

## Study design

CXRShift evaluates DenseNet121, ConvNeXt-Tiny, and ViT-B/16 under a fixed
protocol:

- three training seeds (42, 43, and 44) per model and training strategy;
- probability-level ensembling before metric computation;
- a decision threshold fixed at 0.5 for the primary operating-point metrics;
- filename-grouped resampling for Kermany-FG and `patientId`-grouped resampling
  for RSNA-1707;
- 5,000-iteration grouped bootstrap intervals and paired comparisons on
  identical resamples.

The public evidence package contains the frozen manifests, 36 per-image
prediction files, the complete numerical summary, and the code required to
recompute every reported value. Raw medical images and model checkpoints are
not redistributed.

## Results

The primary table is computed from the mean positive-class probability across
the three seeds.

| Backbone | Kermany-FG balanced accuracy | RSNA-1707 balanced accuracy | RSNA-1707 specificity |
|---|---:|---:|---:|
| DenseNet121 | 97.65% | 65.91% | 35.35% |
| ConvNeXt-Tiny | 97.27% | 66.95% | 41.40% |
| ViT-B/16 | 98.17% | 65.94% | 36.28% |

The RSNA error profile is asymmetric: all three models retain high sensitivity
while producing substantially more false positives. Training interventions
alter this trade-off:

| DenseNet121 strategy | RSNA-1707 balanced accuracy | Change from ERM (95% grouped CI) |
|---|---:|---:|
| ERM | 65.91% | — |
| ERM-Reg | 72.33% | +6.41 pp (+3.47, +9.41) |
| Joint training (JT) | 78.13% | +12.22 pp (+8.02, +16.38) |
| JT with source-balanced sampling (JT-DBS) | 77.22% | +11.31 pp (+7.00, +15.68) |

JT and JT-DBS use RSNA training and validation labels. They measure adaptation
to a known source, not zero-shot generalization to an unseen institution.

The machine-readable source of truth is
[`results/CXRShift__main-summary.json`](results/CXRShift__main-summary.json).

## Technical contributions

- A conservative Kermany split that keeps filename-derived clusters together
  without presenting those clusters as verified patient identities.
- A frozen 1,707-member RSNA audit subset that can be reconstructed from the
  official challenge archive and checked against file hashes.
- A single experiment identity protocol spanning model, strategy, seed,
  dataset, split, and artifact type.
- Grouped uncertainty estimates and paired strategy comparisons computed from
  committed per-image predictions rather than copied table values.
- A clean data-to-results pipeline that retrains all 18 model instances and
  writes new outputs outside the published evidence directory.

## Verify the published evidence

The lightweight verification path does not require either image dataset:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/check_protocol.py
python scripts/summarize_results.py \
  --results-dir results \
  --output-json rebuild/CXRShift__main-summary.json \
  --output-csv rebuild/CXRShift__main-summary.csv \
  --require-complete
```

For a full rebuild from separately downloaded Kermany and official RSNA data:

```bash
python scripts/reproduce_all.py --dry-run --stage all
python scripts/reproduce_all.py --stage all --device cuda
```

The full run trains 18 model instances and evaluates each on both test sets.
See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) for the data layout, experiment
matrix, and verification criteria.

## Interpretation

- Kermany-FG uses conservative filename clusters because the public package
  does not provide a verified patient table. It must not be described as a
  patient-disjoint cohort.
- RSNA-1707 is a fixed, near-balanced audit subset and its test partition was
  used for exploratory model and strategy comparisons. It is not a
  prevalence-representative clinical cohort or an untouched confirmation set.
- Kermany directory labels and RSNA challenge targets differ in population,
  acquisition process, and label construction. The measured gap is therefore a
  cross-source stress result, not a causal estimate of any single mechanism.
- This repository supports research evaluation only and is not intended for
  clinical decision-making.

Dataset provenance, attribution, and exact split semantics are documented in
[`data/README.md`](data/README.md).

## Repository structure

```text
configs/        Model and training configurations
data/splits/    Frozen membership and integrity manifests
figures/        Aggregate result figure; no medical images
protocol/       Canonical experiment identities
results/        Main summary and per-image prediction evidence
scripts/        Data preparation, training, evaluation, and analysis
src/            Shared dataset and protocol utilities
tests/          Focused semantic and numerical checks
```

## Authorship and license

Jinze Gao designed the study and implemented the data, training, evaluation,
statistical-analysis, and reproducibility pipelines.

The MIT license covers the original code only. Dataset licenses and terms remain
with their respective providers. If you use the software or published evidence,
please cite the metadata in [`CITATION.cff`](CITATION.cff).
