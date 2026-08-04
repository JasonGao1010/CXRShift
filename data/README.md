# Data provenance and split semantics

CXRShift distributes manifests and derived predictions, not medical images.
Reproduction requires independent downloads from the dataset providers and
compliance with their terms. The repository's MIT license applies only to the
original code. See [`../DATA_LICENSE.md`](../DATA_LICENSE.md) for the licensing
boundary of the distributed artifacts.

## Kermany-FG

**Source.** Daniel Kermany, Kang Zhang, and Michael Goldbaum,
[*Labeled Optical Coherence Tomography (OCT) and Chest X-Ray Images for
Classification*](https://data.mendeley.com/datasets/rscbjbr9sj/2), Mendeley
Data, Version 2 (2018), DOI
[10.17632/rscbjbr9sj.2](https://doi.org/10.17632/rscbjbr9sj.2), licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The package contains pediatric chest X-rays from Guangzhou Women and Children's
Medical Center. CXRShift uses the directory labels `NORMAL` and `PNEUMONIA`;
bacterial and viral filename tokens are not separate prediction classes.

The distributed package has 5,856 readable images. Its original 16-image
validation partition is too small for the intended comparison, so CXRShift
constructs a frozen split using conservative, subtype-agnostic filename
clusters:

| Split | NORMAL | PNEUMONIA | Images | Filename clusters |
|---|---:|---:|---:|---:|
| Train | 1,113 | 2,994 | 4,107 | 2,183 |
| Validation | 156 | 423 | 579 | 311 |
| Test | 314 | 856 | 1,170 | 624 |

The grouping key is a sensitivity device, not a verified patient identifier.
The public package does not provide a patient table that would justify a
patient-disjoint claim. The frozen manifest contains the assigned split and
SHA-256 digest for every image:

[`splits/kermany_grouped_seed42.csv`](splits/kermany_grouped_seed42.csv)

Rebuild the split from a downloaded package:

```bash
python scripts/prepare_kermany_grouped.py \
  --source-root data/raw/chest_xray \
  --output-root rebuild/data/kermany_grouped_seed42 \
  --from-manifest \
  --manifest data/splits/kermany_grouped_seed42.csv \
  --summary rebuild/audit/kermany_grouped_summary.json
```

## RSNA-1707

**Source.** The
[RSNA Pneumonia Detection Challenge](https://www.rsna.org/education/ai-resources-and-training/ai-image-challenge/rsna-pneumonia-detection-challenge-2018)
and its official
[data terms and attribution requirements](https://www.rsna.org/-/media/Files/RSNA/Education/AI-resources-and-training/AI-image-challenge/pneumonia-detection-challenge-terms-of-use-and-attribution.ashx?hash=FF7A635F6DFFAD31A30C8715DFA3B8FC21131543&la=en).
The NIH Clinical Center provided the underlying images; RSNA and the Society for
Thoracic Radiology supplied the challenge annotations. Users must also follow
the attribution requirements stated in the official terms.

### Required attribution

The RSNA-derived manifest and predictions in this repository are redistributed
with the attribution required by the challenge terms:

- The underlying [NIH Chest X-ray Dataset](https://nihcc.app.box.com/v/ChestXray-NIHCC)
  was provided by the NIH Clinical Center. See X. Wang, Y. Peng, L. Lu, Z. Lu,
  M. Bagheri, and R. M. Summers, “ChestX-ray8: Hospital-scale Chest X-ray
  Database and Benchmarks on Weakly-Supervised Classification and Localization
  of Common Thorax Diseases,” *Proceedings of the IEEE Conference on Computer
  Vision and Pattern Recognition*, pp. 3462–3471, 2017.
- The RSNA–Society of Thoracic Radiology challenge images and annotations are
  available from the [official challenge page](https://www.rsna.org/education/ai-resources-and-training/ai-image-challenge/rsna-pneumonia-detection-challenge-2018).
  See G. Shih *et al.*, “Augmenting the National Institutes of Health Chest
  Radiograph Dataset with Expert Annotations of Possible Pneumonia,”
  *Radiology: Artificial Intelligence*, 1(1):e180041, 2019,
  [doi:10.1148/ryai.2019180041](https://doi.org/10.1148/ryai.2019180041).

The conversion maps challenge `Target=1` to the local directory name
`PNEUMONIA` and `Target=0` to `NORMAL`. These names denote the challenge target
and target-negative classes; they do not establish clinical diagnosis or a
healthy control population.

RSNA-1707 is a fixed, approximately class-balanced audit subset originally
frozen from locally available challenge members. It is deliberately retained
as a stable stress set rather than presented as a prevalence-representative
sample:

| Split | Target negative | Target positive | Images |
|---|---:|---:|---:|
| Train | 560 | 492 | 1,052 |
| Validation | 107 | 106 | 213 |
| Test | 215 | 227 | 442 |

Each `patientId` appears in exactly one split. The manifest records membership,
target, split, and raw/processed hashes:

[`splits/rsna_available_1707_manifest.csv`](splits/rsna_available_1707_manifest.csv)

### Historical acquisition record

The original local subset was assembled in more than one acquisition batch.
Two retained downloader reports associate 1,573 of the 1,707 members with the
Hugging Face mirror `Baldezo313/rsna-pneumonia-dataset`: an earlier report lists
88 members and a later report lists all 1,573. Their verified local report
hashes are recorded in
[`splits/rsna_available_1707_manifest_summary.json`](splits/rsna_available_1707_manifest_summary.json).
The reports themselves are not distributed.

No retained report establishes the acquisition route for the remaining 134
members. Their `source_batch`, `source_provider`, and `source_report` fields are
therefore left as `unknown`; they are not retrospectively attributed to either
the mirror or the official archive. The manifest's path fields describe the
historical local layout and should not be interpreted as files included in this
repository. The summary publishes separate membership hashes for the full,
report-traced, and untraced sets so this boundary can be checked exactly.

For future reconstruction, the official RSNA challenge archive is the
authoritative input. The command below verifies each selected DICOM against the
raw hash in the manifest. That clean official-archive reconstruction has not
been executed independently for this release.

Reconstruct the fixed subset from the official complete training archive:

```bash
python scripts/prepare_rsna_binary.py \
  --raw-root data/raw/rsna_pneumonia \
  --images-dir data/raw/rsna_pneumonia/stage_2_train_images \
  --member-manifest data/splits/rsna_available_1707_manifest.csv \
  --output-root rebuild/data/rsna_binary \
  --splits-output rebuild/audit/rsna_splits.json \
  --summary-output rebuild/audit/rsna_dataset_summary.json \
  --figure-output rebuild/figures/rsna_class_distribution.png
```

The command fails on missing members, target mismatches, invalid split values,
or DICOM hash mismatches.

## Interpretation of cross-source metrics

Kermany directory labels and RSNA challenge targets are related but not
identical constructs. The two sources also differ in population, acquisition,
and preprocessing. CXRShift therefore reports a combined cross-source stress
result. It does not attribute the observed gap to a single hospital, scanner,
or causal mechanism.

Because RSNA-1707 is near-balanced, sensitivity, specificity, balanced accuracy,
and AUROC support the stated comparisons. Precision, AUPRC, Brier score, and
calibration estimates should not be interpreted as estimates for a clinical
population prevalence.
