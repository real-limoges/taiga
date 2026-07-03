# PROVENANCE

Where every input came from, how it was processed, and what was produced. This
project builds a BEAST2-ready cognate matrix and an Indo-Iranian-anchored
calibration scheme from UraLex 2.0. **No phylogenetic inference is run here** —
that is a deliberately separate downstream phase.

> Note: the initial brief referred to `PROVENANCE.md` and `artifacts/SCHEMA.md`
> as pre-existing template skeletons. At session start the repository contained
> only `LICENSE`; these files were therefore authored from scratch. See
> `NOTES.md` §0.

## 1. Source dataset

| Field | Value |
| --- | --- |
| Name | UraLex — Uralic basic vocabulary with cognate and loanword information |
| Version | 2.0 (CLDF release) |
| Repository | https://github.com/lexibank/uralex |
| Pinned commit | `0ce4fc7ea8147c9b3175b786eccf87d3a1c7f7e1` |
| Concept DOI | 10.5281/zenodo.4777568 |
| License | CC-BY-4.0 (see `data/uralex_cldf_v2.0/LICENSE_UraLex.txt`) |
| Format | CLDF Wordlist |

Acquisition: `git clone https://github.com/lexibank/uralex` at the pinned commit.
The five CLDF tables the pipeline reads (`languages.csv`, `parameters.csv`,
`forms.csv`, `cognates.csv`, `borrowings.csv`) plus `cldf-metadata.json` and the
upstream license are vendored **verbatim** into `data/uralex_cldf_v2.0/` so the
pipeline is reproducible offline. Nothing in the vendored files was modified.

Primary citations (per upstream documentation) are reproduced in
`data/uralex_cldf_v2.0/SOURCE.md`.

## 2. Scope of the data used

- **27 varieties** appear in `forms.csv`: 26 attested languages + 1 partial
  Proto-Uralic reconstruction (`Language_ID = 0`, shown as `Proto-Uralic*`).
  Subgroups (attested): Saami ×7, Finnic ×8, Mordvin ×1, Mari ×1, Permic ×3,
  Ugric ×3, Samoyed ×3.
- **313 meanings**, **10,231 forms**, **9,751 cognate judgements**,
  **2,184 borrowing records**.
- Cognate signal is taken from the **root-meaning** coding
  (`Cognacy` / `Cognateset_ID`, e.g. `40-a`), which is inheritance-based; the
  integer `form_set` (correlate) coding is intentionally NOT used.
- Borrowing signal is taken **entirely** from `borrowings.csv`
  (the `forms.csv::Loan` column is empty in this release).

## 3. Processing pipeline (`stages/`)

Discrete, named, individually re-runnable stages. `python3 stages/run_all.py`
runs them in order; each also runs standalone and writes its own artifacts.

| Stage | Script | Does | Key outputs |
| --- | --- | --- | --- |
| 0 | `stage0_config.py` | All curation *policy*: paths, gap semantics, source classifier, Indo-Iranian layer labels | (imported by all) |
| 1 | `stage1_load.py` | Load + validate CLDF tables, check invariants (27 varieties, referential integrity) | `stage1_load_report.json` |
| 2 | `stage2_gaps.py` | Classify the 3 gap markers; build per-(lang,meaning) status | `gap_report.{json,csv}` |
| 3 | `stage3_loans.py` | Loan classification + horizontal-transfer exclusion | `loanword_exclusions.csv`, `loan_exclusion_report.json` |
| 4 | `stage4_matrix.py` | Build binary presence/absence matrix (default + baseline) | `cognate_matrix.{nex,csv}`, `matrix_report.json` |
| 5 | `stage5_calibration.py` | Measure Indo-Iranian layer distribution; derive calibration node + scheme | `calibration_scheme.json`, `indo_iranian_layer_sets.csv` |

Intermediate hand-off files live in `artifacts/_intermediate/` (regenerated on
every run; safe to delete).

Environment: Python 3.11, standard library only (`csv`, `json`, `collections`).
No third-party dependencies, no network access at run time.

## 4. Curation decisions (summary; full rationale in `artifacts/SCHEMA.md`)

- **Gaps.** `[No equivalent]` → structural absence (`0`); `[Form not found]` and
  `[Not reconstructable]` → missing (`?`). One quirk row (`0-62-1`) honoured as a
  gap despite carrying a real cognate code.
- **Loans.** Whole cognate sets excluded when cross-language sharing is
  borrowing-driven (rules E1/E2/E3); individual loan cells in surviving
  multi-language sets recoded to `?`; single-language loans kept as
  autapomorphies. Every excluded set is listed with its reason in
  `loanword_exclusions.csv` (340 sets excluded).
- **Matrix.** Binary meaning-partitioned root-meaning coding; constant characters
  dropped (logged). Default = loan-excluded (deliverable); baseline = no
  exclusion (for comparison).
- **Calibration.** Indo-Iranian (Proto-Indo-Iranian, ~4000 BP) contact layer →
  **minimum-age lower bound of ~4000 BP on the Finno-Ugric crown node** (primary),
  with a documented conservative alternative on the Finno-Permic node. Explicitly
  *not* Proto-Uralic and *not* a single branch protolanguage.

## 5. What is deliberately NOT here

- No BEAST2 XML, no MCMC, no tree, no root-age or topology estimate. The
  calibration scheme is an *input specification* for that separate phase.
- No modification of the upstream UraLex data.

## 6. Reproating

```
python3 stages/run_all.py     # regenerates everything under artifacts/
```

Same input commit + same code ⇒ identical artifacts (pure stdlib, deterministic).
