# Experiment identity protocol

CXRShift gives every run a canonical identity built from the backbone, training
strategy, and seed:

```text
CXRShift__{model}__{strategy}__s{seed}
```

Artifacts extend that identity with the dataset, split, and artifact type:

```text
CXRShift__DenseNet121__JT-DBS__s42__RSNA-1707__test__predictions.csv
```

## Canonical names

| Component | Identifier | Definition |
|---|---|---|
| Backbone | `DenseNet121` | torchvision DenseNet-121 |
| Backbone | `ConvNeXt-Tiny` | torchvision ConvNeXt Tiny |
| Backbone | `ViT-B/16` | torchvision Vision Transformer B/16 |
| Dataset | `Kermany-FG` | Frozen filename-grouped Kermany split |
| Dataset | `RSNA-1707` | Frozen 1,707-member RSNA audit subset |
| Strategy | `ERM` | Kermany-only empirical risk minimization |
| Strategy | `ERM-Reg` | ERM with color jitter and label smoothing |
| Strategy | `JT` | Joint Kermany and RSNA training |
| Strategy | `JT-DBS` | Joint training with domain-balanced sampling |

The identifiers describe implemented mechanisms; they do not imply algorithmic
novelty. Legacy names remain readable by the analysis code solely to preserve
compatibility with the original experiment outputs. New artifacts always use
the canonical scheme defined in `naming_protocol.yaml`.
