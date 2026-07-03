# taiga — UraLex → BEAST2 cognate matrix + Indo-Iranian calibration

A BEAST2-ready binary cognate matrix for 27 Uralic varieties, and a justified
node calibration anchored on the Indo-Iranian loanword contact layer, built from
**UraLex v2.0** (CLDF; DOI 10.5281/zenodo.4777568, CC-BY-4.0).

**No phylogenetic inference is run here.** This repo produces the *inputs* to a
later BEAST2 phase (matrix + calibration), and nothing else — by design.

## What's here

```
data/uralex_cldf_v2.0/   vendored UraLex CLDF tables (pinned commit) + license
stages/                  re-runnable curation pipeline (stage0..stage5, run_all)
artifacts/               all generated outputs
  cognate_matrix.nex/csv          <- the DEFAULT (loan-excluded) matrix
  cognate_matrix_baseline_*        <- no-loan-exclusion comparison
  calibration_scheme.json          <- the calibration deliverable
  loanword_exclusions.csv          <- every excluded loan set, with reasons
  gap_report.{json,csv}            <- gap-marker handling
  indo_iranian_layer_sets.csv      <- the Indo-Iranian layer distribution
  SCHEMA.md                        <- artifact catalogue + full calibration argument
PROVENANCE.md            source, pipeline, decisions
NOTES.md                 working log
```

## Run it

```
python3 stages/run_all.py     # regenerates everything under artifacts/ (stdlib only)
```

## Headline results

- **Matrix:** 27 taxa × 3,448 binary characters (983 parsimony-informative);
  loan exclusion removes ~367 informative horizontal-transfer characters vs the
  baseline.
- **Gaps:** `[No equivalent]` → structural absence; `[Form not found]` /
  `[Not reconstructable]` → missing. 481 gaps handled explicitly.
- **Loans:** 340 cognate sets excluded as horizontal transfer (documented
  individually in `loanword_exclusions.csv`).
- **Calibration:** the Indo-Iranian (~4,000 BP) layer places a **minimum-age
  lower bound of ~4,000 BP on the Finno-Ugric crown node** (conservative
  alternative: the Finno-Permic node) — explicitly *not* Proto-Uralic and *not* a
  single branch protolanguage. Full argument in `artifacts/SCHEMA.md` Part D.

See `artifacts/SCHEMA.md` for details and `PROVENANCE.md` for provenance.
