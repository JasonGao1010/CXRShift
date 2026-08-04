# Command-line entry points

Run commands from the repository root. Published evidence is read-only; new
outputs belong under the ignored `rebuild/` directory.

| Script | Purpose |
|---|---|
| `prepare_kermany_grouped.py` | Reconstruct and verify Kermany-FG from its frozen manifest |
| `prepare_rsna_binary.py` | Reconstruct RSNA-1707 from the official challenge archive |
| `prepare_mixed_binary.py` | Build the joint-training directory without copying image bytes |
| `train.py` | Train one model/strategy/seed identity |
| `evaluate.py` | Export metrics and per-image probabilities for one dataset split |
| `summarize_results.py` | Form three-seed ensembles and grouped-bootstrap comparisons |
| `analyze_domain_shift.py` | Measure label-matched source separability |
| `audit_integrity.py` | Check split groups, duplicate hashes, and stored evaluations |
| `verify_reproduction.py` | Compare a clean rebuild with the published reference |
| `reproduce_all.py` | Execute the complete data-to-verification workflow |

Useful commands:

```bash
python -m pytest -q
python scripts/check_protocol.py
python scripts/reproduce_all.py --dry-run --stage all
```

The full workflow and acceptance criteria are documented in
[`REPRODUCIBILITY.md`](../REPRODUCIBILITY.md).
